"""
Tracks token usage and estimated cost for every Bedrock call made by the
AI query layer. Appends each call to tokenomics/call_log.jsonl (so
cost_summary.py can report on it independently of any single process run)
and keeps an in-memory list for immediate use within a script.

Pricing constants are an approximation of Claude Sonnet's on-demand
Bedrock pricing -- update if you have exact current rates.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).parent / "call_log.jsonl"

INPUT_COST_PER_1K_TOKENS = 0.003
OUTPUT_COST_PER_1K_TOKENS = 0.015

CALL_LOG = []


def log_call(call_type: str, input_tokens: int, output_tokens: int) -> dict:
    cost = (input_tokens / 1000) * INPUT_COST_PER_1K_TOKENS + (output_tokens / 1000) * OUTPUT_COST_PER_1K_TOKENS
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "call_type": call_type,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": round(cost, 6),
    }
    CALL_LOG.append(entry)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def reset_log():
    CALL_LOG.clear()
    if LOG_PATH.exists():
        LOG_PATH.unlink()
