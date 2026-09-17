import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")
sg = ec2.describe_security_groups(GroupIds=["sg-01ede1f2ba5b83b33"])["SecurityGroups"][0]

print("Inbound rules:")
for perm in sg["IpPermissions"]:
    print(" -", perm.get("IpProtocol"), perm.get("FromPort"), "-", perm.get("ToPort"),
          "sources:", [r["CidrIp"] for r in perm.get("IpRanges", [])])
