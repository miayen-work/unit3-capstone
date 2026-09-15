"""
Test suite for the SQL validator. Run standalone before wiring the
validator into a live Redshift connection.

Usage:
    python sql_validation/test_validator.py
"""
from validator import validate_sql

CASES = [
    ("SELECT * FROM customers WHERE churned = true", True),
    ("select id, name from orders limit 10", True),
    ("DROP TABLE customers", False),
    ("SELECT * FROM customers; DROP TABLE customers;", False),  # stacked-query attack
    ("UPDATE customers SET churned = false", False),
    ("INSERT INTO customers VALUES (1, 'test')", False),
    ("SELECT * FROM information_schema.tables", True),
]


def run():
    passed = 0
    for query, expected_valid in CASES:
        result = validate_sql(query)
        ok = result["valid"] == expected_valid
        status = "PASS" if ok else "FAIL"
        passed += ok
        print(f"[{status}] valid={result['valid']:<5} expected={expected_valid:<5} reason={result['reason']!r:<45} query={query!r}")
    print(f"\n{passed}/{len(CASES)} passed")


if __name__ == "__main__":
    run()
