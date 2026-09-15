"""
Standalone smoke test for Bedrock/Claude access.

Run this FIRST, before building any routing or SQL-generation logic on
top of Bedrock. Claude models on Bedrock (including claude-sonnet-4-6)
require the inference-profile ARN as the model id, not the bare model
name -- calling with just "anthropic.claude-sonnet-4-6-v1:0" returns a
ValidationException.

Usage:
    python boto3_scripts/test_bedrock.py
"""
import json
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
INFERENCE_PROFILE = os.getenv("BEDROCK_INFERENCE_PROFILE", "us.anthropic.claude-sonnet-4-6")

bedrock = boto3.client("bedrock-runtime", region_name=REGION)
account_id = boto3.client("sts").get_caller_identity()["Account"]

MODEL_ID = f"arn:aws:bedrock:{REGION}:{account_id}:inference-profile/{INFERENCE_PROFILE}"


def invoke_claude(prompt: str, max_tokens: int = 500) -> dict:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = bedrock.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
    result = json.loads(response["body"].read())
    return {
        "text": result["content"][0]["text"],
        "input_tokens": result["usage"]["input_tokens"],
        "output_tokens": result["usage"]["output_tokens"],
    }


if __name__ == "__main__":
    print(f"Calling model: {MODEL_ID}")
    result = invoke_claude("Reply with exactly: Bedrock connection OK")
    print(result)
