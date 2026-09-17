"""
Retrieves relevant document chunks from OpenSearch via semantic (k-NN)
search and generates a grounded answer citing sources.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_query_layer.bedrock_client import invoke_claude

from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection
from sentence_transformers import SentenceTransformer

load_dotenv()

INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "documents")

_model = None
_opensearch = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_opensearch():
    global _opensearch
    if _opensearch is None:
        _opensearch = OpenSearch(
            hosts=[{"host": os.environ["OPENSEARCH_HOST"], "port": 443}],
            http_auth=(os.environ["OPENSEARCH_USER"], os.environ["OPENSEARCH_PASSWORD"]),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=60,
        )
    return _opensearch


def retrieve_chunks(question: str, k: int = 4) -> list[dict]:
    vector = _get_model().encode(question).tolist()
    resp = _get_opensearch().search(
        index=INDEX_NAME,
        body={
            "size": k,
            "query": {"knn": {"embedding": {"vector": vector, "k": k}}},
        },
    )
    return [
        {"s3_key": hit["_source"]["s3_key"], "chunk_text": hit["_source"]["chunk_text"], "score": hit["_score"]}
        for hit in resp["hits"]["hits"]
    ]


def answer_from_documents(question: str, chunks: list[dict] = None) -> dict:
    if chunks is None:
        chunks = retrieve_chunks(question)

    context = "\n\n".join(f"[Source: {c['s3_key']}]\n{c['chunk_text']}" for c in chunks)
    prompt = f"""Answer the question using ONLY the document excerpts below. Cite the source filename(s) you used.

{context}

Question: {question}

Answer (with citations):"""

    answer = invoke_claude(prompt, call_type="document_qa", max_tokens=500)
    return {"answer": answer, "sources": list({c["s3_key"] for c in chunks})}


if __name__ == "__main__":
    result = answer_from_documents("What is our target churn rate according to the retention strategy?")
    print(result["answer"])
    print("Sources:", result["sources"])
