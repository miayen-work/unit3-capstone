"""
Shared Bedrock/Claude client for the AI query layer. Every call logs its
token usage via tokenomics.tracker.log_call for later cost reporting.

Uses the inference-profile ARN pattern required for Claude models on
Bedrock (see boto3_scripts/test_bedrock.py for the original standalone
smoke test this is based on).
"""
import json
import os
import sys
from pathlib import Path

import boto3
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
from tokenomics.tracker import log_call

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
INFERENCE_PROFILE = os.getenv("BEDROCK_INFERENCE_PROFILE", "us.anthropic.claude-sonnet-4-6")

_bedrock = boto3.client("bedrock-runtime", region_name=REGION)
_account_id = boto3.client("sts").get_caller_identity()["Account"]
MODEL_ID = f"arn:aws:bedrock:{REGION}:{_account_id}:inference-profile/{INFERENCE_PROFILE}"


def invoke_claude(prompt: str, call_type: str, max_tokens: int = 800) -> str:
    """Calls Claude via Bedrock and logs token usage under `call_type`."""
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = _bedrock.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
    result = json.loads(response["body"].read())
    text = result["content"][0]["text"]
    usage = result["usage"]
    log_call(call_type, usage["input_tokens"], usage["output_tokens"])
    return text
