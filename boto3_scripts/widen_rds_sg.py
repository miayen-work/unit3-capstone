import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")
SG_ID = "sg-01ede1f2ba5b83b33"

try:
    ec2.revoke_security_group_ingress(
        GroupId=SG_ID,
        IpPermissions=[{
            "IpProtocol": "tcp",
            "FromPort": 5432,
            "ToPort": 5432,
            "IpRanges": [{"CidrIp": "24.206.73.50/32"}],
        }],
    )
    print("Removed old IP-specific rule.")
except Exception as e:
    print("Skip removing old rule (may not exist or already gone):", e)

ec2.authorize_security_group_ingress(
    GroupId=SG_ID,
    IpPermissions=[{
        "IpProtocol": "tcp",
        "FromPort": 5432,
        "ToPort": 5432,
        "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "unit3-capstone: open for dev/testing, documented tradeoff"}],
    }],
)
print("Added 0.0.0.0/0 rule on port 5432.")
