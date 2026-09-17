import time
import boto3
from botocore.exceptions import ClientError

rsdata = boto3.client("redshift-data", region_name="us-east-1")

try:
    resp = rsdata.execute_statement(
        ClusterIdentifier="unit3-capstone-redshift",
        Database="dev",
        DbUser="awsuser",
        Sql="SELECT 1 AS test_value;",
    )
    stmt_id = resp["Id"]
    print("execute_statement: OK, id =", stmt_id)

    for _ in range(10):
        time.sleep(1)
        desc = rsdata.describe_statement(Id=stmt_id)
        if desc["Status"] in ("FINISHED", "FAILED", "ABORTED"):
            break
    print("status:", desc["Status"])
    if desc["Status"] == "FINISHED":
        result = rsdata.get_statement_result(Id=stmt_id)
        print("result:", result["Records"])
    else:
        print("error:", desc.get("Error"))
except ClientError as e:
    print("FAILED:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
