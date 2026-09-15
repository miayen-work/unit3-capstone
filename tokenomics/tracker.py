# Log token usage (input/output tokens, call type) for every Bedrock call:
# classification/routing, NL-to-SQL generation, contextual response
# generation. Each invoke_claude() call should feed its usage here.
#
# TODO: implement a simple in-memory or file-backed log + cost lookup
# table for the Claude model pricing, then produce a summary after a
# 10-query test run (see cost_summary.py).

CALL_LOG = []


def log_call(call_type: str, input_tokens: int, output_tokens: int) -> None:
    CALL_LOG.append({
        "call_type": call_type,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    })
