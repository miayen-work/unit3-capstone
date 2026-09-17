import boto3

rds = boto3.client("rds", region_name="us-east-1")
db = rds.describe_db_instances(DBInstanceIdentifier="unit3-capstone-db")["DBInstances"][0]
print("IAM DB auth enabled:", db.get("IAMDatabaseAuthenticationEnabled"))
print("CA cert identifier:", db.get("CACertificateIdentifier"))

params = rds.describe_db_parameters(DBParameterGroupName="default.postgres18")["Parameters"]
for p in params:
    if p["ParameterName"] in ("rds.force_ssl", "ssl"):
        print(p["ParameterName"], "=", p.get("ParameterValue"))
