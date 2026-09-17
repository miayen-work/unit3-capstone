"""
Given a natural-language question, decides whether it needs OpenSearch
(semantic/document search), Redshift (SQL/structured data), or both.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_query_layer.bedrock_client import invoke_claude

ROUTING_PROMPT = """You are a routing assistant for a data platform with two sources:
- OPENSEARCH: semantic search over document text (PDFs such as policies, strategies, reports)
- REDSHIFT: SQL queries over structured tables:
    customers (customer_id, signup_date, plan_type, monthly_spend, churned, churn_date)
    product_inventory (id, source_system, data_owner, created_at, last_updated_at, product_name, price, stock_quantity)

Given the user's question, decide which source(s) are needed to answer it.
A question needs BOTH only if answering it truly requires combining a document (policy/strategy) with structured/warehouse data -- not just because both topics are mentioned.

Respond with ONLY a JSON object, no other text:
{{"route": "opensearch" | "redshift" | "both", "reasoning": "<one sentence>"}}

Question: {question}
"""


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in routing response: {text!r}")
    return json.loads(match.group(0))


def classify_query(question: str) -> dict:
    prompt = ROUTING_PROMPT.format(question=question)
    response_text = invoke_claude(prompt, call_type="routing", max_tokens=200)
    return _extract_json(response_text)


if __name__ == "__main__":
    import pprint

    test_questions = [
        "What does our retention strategy say about acceptable churn?",
        "How many customers have churned?",
        "Does our current churn rate align with our documented retention strategy?",
    ]
    for q in test_questions:
        print(q)
        pprint.pprint(classify_query(q))
        print()
