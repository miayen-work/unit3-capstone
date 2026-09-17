"""
Reads pending chunk files from S3 (written by the ingestion Lambda under
the "chunks/" prefix), generates embeddings locally via Sentence
Transformers, and indexes them into OpenSearch. Deletes each chunk file
from S3 once it's been embedded (so re-running only processes new ones).

This deliberately reads chunks from S3 rather than querying RDS directly
-- the local network this project is developed on blocks direct Postgres
connections (port 5432), but allows normal HTTPS/S3 traffic. RDS still
holds the raw text (written directly by the Lambda, which runs inside
AWS and isn't affected by that local restriction) -- this script just
doesn't need to touch RDS to do its job.

Usage:
    python boto3_scripts/generate_embeddings.py
"""
import json
import os

import boto3
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection
from sentence_transformers import SentenceTransformer

load_dotenv()

BUCKET = os.environ["S3_BUCKET_NAME"]
CHUNKS_PREFIX = "chunks/"
INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "documents")
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output size

s3 = boto3.client("s3")
model = SentenceTransformer("all-MiniLM-L6-v2")

opensearch = OpenSearch(
    hosts=[{"host": os.environ["OPENSEARCH_HOST"], "port": 443}],
    http_auth=(os.environ["OPENSEARCH_USER"], os.environ["OPENSEARCH_PASSWORD"]),
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=60,
)


def ensure_index():
    if opensearch.indices.exists(index=INDEX_NAME):
        return
    opensearch.indices.create(
        index=INDEX_NAME,
        body={
            "settings": {"index": {"knn": True}},
            "mappings": {
                "properties": {
                    "s3_key": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "chunk_text": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": EMBEDDING_DIM,
                    },
                }
            },
        },
    )


def list_pending_chunk_files():
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix=CHUNKS_PREFIX):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".json"):
                yield obj["Key"]


def main():
    ensure_index()

    pending = list(list_pending_chunk_files())
    print(f"{len(pending)} chunk file(s) pending embedding")

    for chunks_key in pending:
        # chunks_key looks like "chunks/<original-pdf-s3-key>.json"
        source_s3_key = chunks_key[len(CHUNKS_PREFIX):-len(".json")]

        obj = s3.get_object(Bucket=BUCKET, Key=chunks_key)
        chunks = json.loads(obj["Body"].read())

        for chunk in chunks:
            vector = model.encode(chunk["chunk_text"]).tolist()
            doc_id = f"{source_s3_key}::{chunk['chunk_index']}"

            opensearch.index(
                index=INDEX_NAME,
                id=doc_id,
                body={
                    "s3_key": source_s3_key,
                    "chunk_index": chunk["chunk_index"],
                    "chunk_text": chunk["chunk_text"],
                    "embedding": vector,
                },
            )
            print(f"embedded {doc_id}")

        s3.delete_object(Bucket=BUCKET, Key=chunks_key)


if __name__ == "__main__":
    main()
