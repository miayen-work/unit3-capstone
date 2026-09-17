import boto3

rds = boto3.client("rds", region_name="us-east-1")
db = rds.describe_db_instances(DBInstanceIdentifier="unit3-capstone-db")["DBInstances"][0]
print("Status:", db["DBInstanceStatus"])
print("Pending modified values:", db.get("PendingModifiedValues"))
print("Engine version:", db["EngineVersion"])
print("Parameter group:", db["DBParameterGroups"][0]["DBParameterGroupName"])
