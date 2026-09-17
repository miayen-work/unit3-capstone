import boto3
from botocore.exceptions import ClientError

ec2 = boto3.client("ec2", region_name="us-east-1")
SG_ID = "sg-01ede1f2ba5b83b33"

try:
    ec2.authorize_security_group_ingress(
        GroupId=SG_ID,
        IpPermissions=[{
            "IpProtocol": "tcp",
            "FromPort": 5439,
            "ToPort": 5439,
            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "unit3-capstone: open for Glue/dev access"}],
        }],
    )
    print("Added 0.0.0.0/0 rule on port 5439.")
except ClientError as e:
    if e.response["Error"]["Code"] == "InvalidPermission.Duplicate":
        print("Rule already exists.")
    else:
        raise
