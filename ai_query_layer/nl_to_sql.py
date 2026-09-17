"""
Translates a natural-language question into SQL via Claude, validates it
through sql_validation/validator.py, and executes it against Redshift.

NOTE: executing the query needs a direct Postgres-wire connection to
Redshift (pg8000). If your local network blocks that port (see
docs/architecture.md for the confirmed sandbox/network constraint), run
this specific step from AWS CloudShell instead -- the same .env
credentials work fine there.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_query_layer.bedrock_client import invoke_claude
from sql_validation.validator import validate_sql

import pg8000.native
from dotenv import load_dotenv

load_dotenv()

SCHEMA_CONTEXT = """
Table: customers
  customer_id (text, primary key)
  signup_date (date)
  plan_type (text: 'basic', 'standard', 'premium')
  monthly_spend (double precision)
  churned (boolean)
  churn_date (date, null if not churned)

Table: product_inventory
  id (text, primary key)
  source_system (text)
  data_owner (text)
  created_at (timestamp)
  last_updated_at (timestamp)
  product_name (text)
  price (double precision)
  stock_quantity (integer)
"""


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip().rstrip(";").strip()


def generate_sql(question: str) -> str:
    prompt = f"""Given this database schema:
{SCHEMA_CONTEXT}

Write a single PostgreSQL-compatible SELECT query to answer the question below.
Return ONLY the SQL query -- no explanation, no markdown code fences.

Question: {question}
"""
    raw = invoke_claude(prompt, call_type="nl_to_sql", max_tokens=300)
    return _strip_code_fence(raw)


def execute_sql(query: str) -> list[dict]:
    validation = validate_sql(query)
    if not validation["valid"]:
        raise ValueError(f"SQL failed validation: {validation['reason']}")

    conn = pg8000.native.Connection(
        host=os.environ["REDSHIFT_HOST"],
        port=int(os.environ["REDSHIFT_PORT"]),
        database=os.environ["REDSHIFT_DB_NAME"],
        user=os.environ["REDSHIFT_USER"],
        password=os.environ["REDSHIFT_PASSWORD"],
    )
    try:
        rows = conn.run(query)
        columns = [c["name"] for c in conn.columns]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def answer_from_sql(question: str) -> dict:
    sql = generate_sql(question)
    validation = validate_sql(sql)
    if not validation["valid"]:
        return {"sql": sql, "valid": False, "reason": validation["reason"], "rows": None}
    rows = execute_sql(sql)
    return {"sql": sql, "valid": True, "reason": "OK", "rows": rows}


if __name__ == "__main__":
    result = answer_from_sql("What percentage of customers have churned?")
    print(result)
