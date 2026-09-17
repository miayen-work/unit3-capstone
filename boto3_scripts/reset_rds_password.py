"""
Resets the RDS master password. Edit NEW_PASSWORD below, run it, then
update RDS_PASSWORD in .env to match.
"""
import boto3

NEW_PASSWORD = "ChangeMe123!"  # <-- edit this to a real password before running

rds = boto3.client("rds", region_name="us-east-1")
rds.modify_db_instance(
    DBInstanceIdentifier="unit3-capstone-db",
    MasterUserPassword=NEW_PASSWORD,
    ApplyImmediately=True,
)
print("Password reset requested -- takes ~1 minute to apply. Update .env to match NEW_PASSWORD.")
