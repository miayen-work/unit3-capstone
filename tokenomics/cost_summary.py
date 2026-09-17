"""
Runs 10 representative queries through the AI query layer (including
both required harder synthesis queries), then prints a tokenomics
summary from the call log: total calls per type, total tokens, and
estimated cost.

Usage:
    python tokenomics/cost_summary.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_query_layer.query_engine import answer_question
from tokenomics.tracker import CALL_LOG, LOG_PATH, reset_log

TEST_QUERIES = [
    "What is our target churn rate according to the retention strategy?",
    "How many customers are on the premium plan?",
    (
        "Does our current customer churn rate (from the data warehouse) align with "
        "what our documented retention strategy says we should be seeing?"
    ),
    (
        "Based on our data governance policy documents, are any of the currently-ingested "
        "datasets missing required metadata fields (check against the Glue Catalog)?"
    ),
    "What is the average monthly spend across all customers?",
    "What fields does our data governance policy require for all datasets?",
    "How many products are in our inventory?",
    "What retention tactics does our strategy document recommend?",
    "Which products have the lowest stock quantity?",
    (
        "Who owns the product_inventory dataset according to its metadata, and does "
        "that satisfy our governance policy's ownership requirement?"
    ),
]


def run_test_queries():
    reset_log()
    for i, question in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] {question}")
        try:
            result = answer_question(question)
            print(f"  route: {result['route']}")
            print(f"  answer: {result['answer'][:200]}...")
        except Exception as e:
            print(f"  ERROR: {e}")


def print_summary():
    if not CALL_LOG:
        print("\nNo calls logged -- did the test queries run?")
        return

    by_type = defaultdict(lambda: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost": 0.0})
    for entry in CALL_LOG:
        t = by_type[entry["call_type"]]
        t["calls"] += 1
        t["input_tokens"] += entry["input_tokens"]
        t["output_tokens"] += entry["output_tokens"]
        t["cost"] += entry["estimated_cost_usd"]

    print("\n" + "=" * 70)
    print("TOKENOMICS SUMMARY -- 10 query test run")
    print("=" * 70)
    total_calls = total_input = total_output = 0
    total_cost = 0.0
    for call_type, stats in by_type.items():
        print(
            f"{call_type:20s}  calls={stats['calls']:3d}  "
            f"input_tokens={stats['input_tokens']:6d}  "
            f"output_tokens={stats['output_tokens']:6d}  "
            f"cost=${stats['cost']:.4f}"
        )
        total_calls += stats["calls"]
        total_input += stats["input_tokens"]
        total_output += stats["output_tokens"]
        total_cost += stats["cost"]
    print("-" * 70)
    print(
        f"{'TOTAL':20s}  calls={total_calls:3d}  "
        f"input_tokens={total_input:6d}  "
        f"output_tokens={total_output:6d}  "
        f"cost=${total_cost:.4f}"
    )
    print("=" * 70)
    print(f"\nFull call log: {LOG_PATH}")


if __name__ == "__main__":
    run_test_queries()
    print_summary()
