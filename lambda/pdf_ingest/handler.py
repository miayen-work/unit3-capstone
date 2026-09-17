"""
Lambda: triggered on S3 upload of a PDF.

Flow: Textract extract -> chunk (500-1000 tokens, approximated by word
count) -> write raw chunks to RDS AND to a JSON file in S3.

Embedding generation (Sentence Transformers) happens in a SEPARATE local
script (boto3_scripts/generate_embeddings.py), not in this Lambda -- the
Sentence Transformers + PyTorch dependency is too large for a plain zip
Lambda package (~250MB unzipped limit) and building a Linux-compatible
package requires Docker, which isn't available in this environment. This
Lambda only needs boto3 (built into the Lambda runtime) and pg8000 (a
pure-Python Postgres driver, so no compiled binaries to worry about).

The chunks are ALSO written to S3 (not just RDS) because the local
network this project is developed on blocks direct Postgres-protocol
connections (port 5432) but allows normal HTTPS/AWS-API traffic. Reading
chunks back from S3 (via boto3, which is just HTTPS) lets the local
embedding script work without needing a direct RDS connection from the
dev machine. Lambda itself connects to RDS fine since it runs inside AWS.

Environment variables required (set on the Lambda function):
    RDS_HOST, RDS_PORT, RDS_DB_NAME, RDS_USER, RDS_PASSWORD
"""
import json
import os
import re
import time
import urllib.parse

import boto3
import pg8000.native

textract = boto3.client("textract")
s3 = boto3.client("s3")

MIN_WORDS_PER_CHUNK = 375   # ~500 tokens
MAX_WORDS_PER_CHUNK = 750   # ~1000 tokens

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def extract_text(bucket: str, key: str) -> str:
    """Run Textract (async) on the PDF and return its full extracted text."""
    start_resp = textract.start_document_text_detection(
        DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}}
    )
    job_id = start_resp["JobId"]

    status = "IN_PROGRESS"
    deadline = time.time() + 600  # 10 minutes, well under Lambda's 15 min cap
    while status == "IN_PROGRESS":
        if time.time() > deadline:
            raise TimeoutError(f"Textract job {job_id} did not finish in time")
        time.sleep(5)
        result = textract.get_document_text_detection(JobId=job_id)
        status = result["JobStatus"]

    if status != "SUCCEEDED":
        raise RuntimeError(f"Textract job {job_id} ended with status {status}")

    lines = []
    next_token = None
    while True:
        kwargs = {"JobId": job_id}
        if next_token:
            kwargs["NextToken"] = next_token
        page = textract.get_document_text_detection(**kwargs)
        for block in page["Blocks"]:
            if block["BlockType"] == "LINE":
                lines.append(block["Text"])
        next_token = page.get("NextToken")
        if not next_token:
            break

    return "\n".join(lines)


def chunk_text(text: str) -> list[str]:
    """Group sentences into chunks of roughly 500-1000 tokens (word-count proxy)."""
    sentences = SENTENCE_SPLIT_RE.split(text)

    chunks = []
    current: list[str] = []
    current_words = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        word_count = len(sentence.split())

        if current_words + word_count > MAX_WORDS_PER_CHUNK and current_words >= MIN_WORDS_PER_CHUNK:
            chunks.append(" ".join(current))
            current = []
            current_words = 0

        current.append(sentence)
        current_words += word_count

    if current:
        chunks.append(" ".join(current))

    return chunks


def store_chunks(s3_key: str, chunks: list[str]) -> None:
    conn = pg8000.native.Connection(
        host=os.environ["RDS_HOST"],
        port=int(os.environ["RDS_PORT"]),
        database=os.environ["RDS_DB_NAME"],
        user=os.environ["RDS_USER"],
        password=os.environ["RDS_PASSWORD"],
    )
    try:
        for i, chunk in enumerate(chunks):
            conn.run(
                """
                INSERT INTO document_chunks (s3_key, chunk_index, chunk_text, word_count)
                VALUES (:s3_key, :chunk_index, :chunk_text, :word_count)
                ON CONFLICT (s3_key, chunk_index) DO UPDATE
                    SET chunk_text = EXCLUDED.chunk_text, word_count = EXCLUDED.word_count
                """,
                s3_key=s3_key,
                chunk_index=i,
                chunk_text=chunk,
                word_count=len(chunk.split()),
            )
    finally:
        conn.close()


def store_chunks_to_s3(bucket: str, s3_key: str, chunks: list[str]) -> str:
    chunks_key = f"chunks/{s3_key}.json"
    body = json.dumps(
        [{"chunk_index": i, "chunk_text": c, "word_count": len(c.split())} for i, c in enumerate(chunks)]
    )
    s3.put_object(Bucket=bucket, Key=chunks_key, Body=body.encode("utf-8"), ContentType="application/json")
    return chunks_key


def handler(event, context):
    results = []
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        if not key.lower().endswith(".pdf"):
            continue

        text = extract_text(bucket, key)
        chunks = chunk_text(text)
        store_chunks(key, chunks)
        chunks_key = store_chunks_to_s3(bucket, key, chunks)

        results.append({"key": key, "chunks_stored": len(chunks), "chunks_json": chunks_key})

    return {"processed": results}
