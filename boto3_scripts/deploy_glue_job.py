"""
Uploads the ETL script to S3 and creates (or updates) the Glue job.

Usage:
    python boto3_scripts/deploy_glue_job.py
"""
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

BUCKET = os.environ["S3_BUCKET_NAME"]
REGION = os.getenv("AWS_REGION", "us-east-1")
JOB_NAME = "unit3-capstone-etl"
SCRIPT_LOCAL = Path(__file__).parent.parent / "glue_jobs" / "csv_json_etl.py"
SCRIPT_S3_KEY = "scripts/csv_json_etl.py"

s3 = boto3.client("s3", region_name=REGION)
glue = boto3.client("glue", region_name=REGION)

iam = boto3.client("iam")
role_arn = iam.get_role(RoleName="unit3-capstone-glue-role")["Role"]["Arn"]

s3.upload_file(str(SCRIPT_LOCAL), BUCKET, SCRIPT_S3_KEY)
print(f"uploaded script to s3://{BUCKET}/{SCRIPT_S3_KEY}")

job_config = {
    "Role": role_arn,
    "Command": {
        "Name": "glueetl",
        "ScriptLocation": f"s3://{BUCKET}/{SCRIPT_S3_KEY}",
        "PythonVersion": "3",
    },
    "GlueVersion": "4.0",
    "WorkerType": "G.1X",
    "NumberOfWorkers": 2,
    "Timeout": 15,
    "DefaultArguments": {
        "--TempDir": f"s3://{BUCKET}/glue-temp/",
        "--job-language": "python",
    },
}

try:
    glue.create_job(Name=JOB_NAME, **job_config)
    print(f"created job {JOB_NAME}")
except ClientError as e:
    if e.response["Error"]["Code"] == "AlreadyExistsException":
        glue.update_job(JobName=JOB_NAME, JobUpdate=job_config)
        print(f"updated existing job {JOB_NAME}")
    else:
        raise
