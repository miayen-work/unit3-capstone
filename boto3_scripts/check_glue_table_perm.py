import boto3
from botocore.exceptions import ClientError

glue = boto3.client("glue", region_name="us-east-1")

try:
    glue.create_table(
        DatabaseName="unit3_capstone_db_test",
        TableInput={
            "Name": "perm_test_table",
            "StorageDescriptor": {
                "Columns": [{"Name": "id", "Type": "string"}],
                "Location": "s3://unit3-capstone-miayen-docs/structured/",
            },
            "TableType": "EXTERNAL_TABLE",
        },
    )
    print("create_table: OK")
    glue.delete_table(DatabaseName="unit3_capstone_db_test", Name="perm_test_table")
except ClientError as e:
    print("create_table FAILED:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
