import boto3

rds = boto3.client("rds", region_name="us-east-1")
db = rds.describe_db_instances(DBInstanceIdentifier="unit3-capstone-db")["DBInstances"][0]
print("Master username:", db["MasterUsername"])
