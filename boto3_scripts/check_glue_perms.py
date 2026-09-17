import boto3
from botocore.exceptions import ClientError

glue = boto3.client("glue", region_name="us-east-1")

try:
    glue.create_database(DatabaseInput={"Name": "unit3_capstone_db_test"})
    print("create_database: OK")
except ClientError as e:
    print("create_database FAILED:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])

try:
    glue.get_databases()
    print("get_databases: OK")
except ClientError as e:
    print("get_databases FAILED:", e.response["Error"]["Code"])
