"""
Creates the Glue database and table definitions directly via boto3,
replicating what a Glue Crawler would have discovered -- the sandbox
account denies glue:CreateCrawler for this IAM user, but glue:CreateTable
and glue:CreateDatabase both work, so we define the same schema info
that automatic discovery would have produced.

Usage:
    python boto3_scripts/create_glue_catalog.py
"""
import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

BUCKET = os.environ["S3_BUCKET_NAME"]
DATABASE = "unit3_capstone_db"

glue = boto3.client("glue", region_name=os.getenv("AWS_REGION", "us-east-1"))

CUSTOMERS_TABLE = {
    "Name": "customers",
    "StorageDescriptor": {
        "Columns": [
            {"Name": "customer_id", "Type": "string"},
            {"Name": "signup_date", "Type": "string"},
            {"Name": "plan_type", "Type": "string"},
            {"Name": "monthly_spend", "Type": "double"},
            {"Name": "churned", "Type": "string"},
            {"Name": "churn_date", "Type": "string"},
        ],
        "Location": f"s3://{BUCKET}/structured/customers/",
        "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
        "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
        "SerdeInfo": {
            "SerializationLibrary": "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
            "Parameters": {"field.delim": ",", "skip.header.line.count": "1"},
        },
    },
    "TableType": "EXTERNAL_TABLE",
    "Parameters": {"classification": "csv", "skip.header.line.count": "1"},
}

PRODUCT_INVENTORY_TABLE = {
    "Name": "product_inventory",
    "StorageDescriptor": {
        "Columns": [
            {"Name": "id", "Type": "string"},
            {"Name": "source_system", "Type": "string"},
            {"Name": "data_owner", "Type": "string"},
            {"Name": "created_at", "Type": "string"},
            {"Name": "last_updated_at", "Type": "string"},
            {"Name": "product_name", "Type": "string"},
            {"Name": "price", "Type": "double"},
            {"Name": "stock_quantity", "Type": "int"},
        ],
        "Location": f"s3://{BUCKET}/structured/product_inventory/",
        "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
        "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
        "SerdeInfo": {
            "SerializationLibrary": "org.openx.data.jsonserde.JsonSerDe",
            "Parameters": {},
        },
    },
    "TableType": "EXTERNAL_TABLE",
    "Parameters": {"classification": "json"},
}


def ensure_database():
    try:
        glue.create_database(DatabaseInput={"Name": DATABASE})
        print(f"created database {DATABASE}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "AlreadyExistsException":
            print(f"database {DATABASE} already exists")
        else:
            raise


def create_table(table_input):
    try:
        glue.create_table(DatabaseName=DATABASE, TableInput=table_input)
        print(f"created table {table_input['Name']}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "AlreadyExistsException":
            print(f"table {table_input['Name']} already exists, updating")
            glue.update_table(DatabaseName=DATABASE, TableInput=table_input)
        else:
            raise


def main():
    ensure_database()
    create_table(CUSTOMERS_TABLE)
    create_table(PRODUCT_INVENTORY_TABLE)


if __name__ == "__main__":
    main()
