"""
Top-level AI query layer entrypoint: routes a natural-language question
to OpenSearch, Redshift, or both, and produces a single answer.

For "both" routes (the required harder synthesis queries), both sources
are retrieved and handed to ONE final Claude call that must combine them
into a single coherent answer citing both -- not two separate answers.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_query_layer.bedrock_client import invoke_claude
from ai_query_layer.document_qa import retrieve_chunks
from ai_query_layer.nl_to_sql import answer_from_sql
from ai_query_layer.router import classify_query


def _doc_context(chunks: list[dict]) -> str:
    return "\n\n".join(f"[Source: {c['s3_key']}]\n{c['chunk_text']}" for c in chunks)


def answer_question(question: str) -> dict:
    routing = classify_query(question)
    route = routing["route"]

    if route == "opensearch":
        chunks = retrieve_chunks(question)
        prompt = (
            f"Answer using ONLY these document excerpts, citing source filenames:\n\n"
            f"{_doc_context(chunks)}\n\nQuestion: {question}\n\nAnswer:"
        )
        answer = invoke_claude(prompt, call_type="response_generation", max_tokens=500)
        return {
            "route": route,
            "routing_reasoning": routing["reasoning"],
            "answer": answer,
            "sources": [c["s3_key"] for c in chunks],
        }

    if route == "redshift":
        sql_result = answer_from_sql(question)
        if not sql_result["valid"]:
            return {
                "route": route,
                "routing_reasoning": routing["reasoning"],
                "answer": f"Could not run query: {sql_result['reason']}",
                "sql": sql_result["sql"],
            }
        prompt = (
            f"The SQL query below was run against the data warehouse to answer the question. "
            f"Give a clear natural-language answer.\n\n"
            f"Question: {question}\nSQL: {sql_result['sql']}\nResult: {sql_result['rows']}\n\nAnswer:"
        )
        answer = invoke_claude(prompt, call_type="response_generation", max_tokens=400)
        return {
            "route": route,
            "routing_reasoning": routing["reasoning"],
            "answer": answer,
            "sql": sql_result["sql"],
            "rows": sql_result["rows"],
        }

    # both
    chunks = retrieve_chunks(question)
    sql_result = answer_from_sql(question)

    sql_context = (
        f"SQL: {sql_result['sql']}\nResult: {sql_result['rows']}"
        if sql_result["valid"]
        else f"SQL query failed validation: {sql_result['reason']}"
    )

    prompt = f"""Answer the question by combining BOTH sources below into ONE coherent answer.
Explicitly cite both the document source(s) and the structured data warehouse result -- do not answer them as two separate answers.

DOCUMENT EXCERPTS:
{_doc_context(chunks)}

STRUCTURED DATA RESULT:
{sql_context}

Question: {question}

Combined answer (citing both sources):"""

    answer = invoke_claude(prompt, call_type="response_generation", max_tokens=600)
    return {
        "route": route,
        "routing_reasoning": routing["reasoning"],
        "answer": answer,
        "sources": [c["s3_key"] for c in chunks],
        "sql": sql_result.get("sql"),
        "rows": sql_result.get("rows"),
    }


if __name__ == "__main__":
    import json

    question = (
        "Does our current customer churn rate (from the data warehouse) align with what "
        "our documented retention strategy says we should be seeing?"
    )
    result = answer_question(question)
    print(json.dumps(result, indent=2, default=str))
