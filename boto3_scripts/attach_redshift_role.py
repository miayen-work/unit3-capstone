"""
One-off script: attach an existing IAM role to a Redshift cluster
directly via boto3, bypassing the console flow (which was failing on
an unrelated redshift:RegisterNamespace permission).
"""
import boto3

CLUSTER_ID = "unit3-capstone-redshift"
ROLE_ARN = "arn:aws:iam::415851145619:role/unit3-capstone-redshift-role-read"

redshift = boto3.client("redshift", region_name="us-east-1")

response = redshift.modify_cluster_iam_roles(
    ClusterIdentifier=CLUSTER_ID,
    AddIamRoles=[ROLE_ARN],
)
print(response["Cluster"]["IamRoles"])
