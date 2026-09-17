import boto3
from botocore.exceptions import ClientError

glue = boto3.client("glue", region_name="us-east-1")

try:
    glue.get_jobs()
    print("get_jobs: OK")
except ClientError as e:
    print("get_jobs FAILED:", e.response["Error"]["Code"])

try:
    glue.create_job(
        Name="perm-test-job-delete-me",
        Role="unit3-capstone-glue-role",
        Command={"Name": "glueetl", "ScriptLocation": f"s3://unit3-capstone-miayen-docs/scripts/test.py"},
    )
    print("create_job: OK")
    glue.delete_job(JobName="perm-test-job-delete-me")
except ClientError as e:
    print("create_job FAILED:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
