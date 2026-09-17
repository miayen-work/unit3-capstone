"""
Starts the Glue ETL job run and polls until it finishes, passing
Redshift connection details as run-time arguments (kept out of the
persisted job definition).

Usage:
    python boto3_scripts/run_glue_job.py
"""
import os
import time

import boto3
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
JOB_NAME = "unit3-capstone-etl"

glue = boto3.client("glue", region_name=REGION)

run = glue.start_job_run(
    JobName=JOB_NAME,
    Arguments={
        "--REDSHIFT_HOST": os.environ["REDSHIFT_HOST"],
        "--REDSHIFT_PORT": os.environ["REDSHIFT_PORT"],
        "--REDSHIFT_DB": os.environ["REDSHIFT_DB_NAME"],
        "--REDSHIFT_USER": os.environ["REDSHIFT_USER"],
        "--REDSHIFT_PASSWORD": os.environ["REDSHIFT_PASSWORD"],
        "--GLUE_DATABASE": "unit3_capstone_db",
    },
)
run_id = run["JobRunId"]
print(f"started job run {run_id}")

while True:
    time.sleep(15)
    status = glue.get_job_run(JobName=JOB_NAME, RunId=run_id)["JobRun"]
    state = status["JobRunState"]
    print("state:", state)
    if state in ("SUCCEEDED", "FAILED", "STOPPED", "TIMEOUT", "ERROR"):
        if state != "SUCCEEDED":
            print("error message:", status.get("ErrorMessage"))
        break
