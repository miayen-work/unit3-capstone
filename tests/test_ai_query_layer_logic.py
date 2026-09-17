"""
Unit tests for AI query layer logic that does NOT require a live Bedrock
call -- JSON parsing of routing responses, SQL code-fence stripping, and
the SQL-validator gate inside execute_sql(). These verify the code is
correct independent of the Bedrock model-access issue blocking live runs
(see docs/architecture.md).

Usage:
    python tests/test_ai_query_layer_logic.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_query_layer.router import _extract_json
from ai_query_layer.nl_to_sql import _strip_code_fence, execute_sql

passed = 0
failed = 0


def check(label, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"[PASS] {label}")
    else:
        failed += 1
        print(f"[FAIL] {label}")


# --- router._extract_json -----------------------------------------------
check(
    "extract_json: plain JSON",
    _extract_json('{"route": "opensearch", "reasoning": "doc question"}')
    == {"route": "opensearch", "reasoning": "doc question"},
)
check(
    "extract_json: JSON with surrounding text",
    _extract_json('Sure, here you go:\n{"route": "redshift", "reasoning": "sql question"}\nHope that helps!')
    == {"route": "redshift", "reasoning": "sql question"},
)
check(
    "extract_json: JSON in markdown code fence",
    _extract_json('```json\n{"route": "both", "reasoning": "needs both"}\n```')
    == {"route": "both", "reasoning": "needs both"},
)
try:
    _extract_json("no json here at all")
    check("extract_json: raises on missing JSON", False)
except ValueError:
    check("extract_json: raises on missing JSON", True)

# --- nl_to_sql._strip_code_fence -----------------------------------------
check(
    "strip_code_fence: plain query",
    _strip_code_fence("SELECT * FROM customers") == "SELECT * FROM customers",
)
check(
    "strip_code_fence: trailing semicolon removed",
    _strip_code_fence("SELECT * FROM customers;") == "SELECT * FROM customers",
)
check(
    "strip_code_fence: markdown fence with language tag",
    _strip_code_fence("```sql\nSELECT * FROM customers;\n```") == "SELECT * FROM customers",
)
check(
    "strip_code_fence: markdown fence no language tag",
    _strip_code_fence("```\nSELECT * FROM customers\n```") == "SELECT * FROM customers",
)

# --- nl_to_sql.execute_sql validator gate (no DB connection needed) ------
try:
    execute_sql("DROP TABLE customers")
    check("execute_sql: rejects DROP before connecting", False)
except ValueError as e:
    check("execute_sql: rejects DROP before connecting", "Blocked" in str(e))

try:
    execute_sql("SELECT * FROM customers; DROP TABLE customers;")
    check("execute_sql: rejects stacked query before connecting", False)
except ValueError as e:
    check("execute_sql: rejects stacked query before connecting", "Blocked" in str(e))

try:
    execute_sql("UPDATE customers SET churned = false")
    check("execute_sql: rejects UPDATE before connecting", False)
except ValueError as e:
    check("execute_sql: rejects UPDATE before connecting", "Blocked" in str(e))

print(f"\n{passed}/{passed + failed} passed")
