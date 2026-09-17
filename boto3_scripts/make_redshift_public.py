import boto3

redshift = boto3.client("redshift", region_name="us-east-1")
resp = redshift.modify_cluster(
    ClusterIdentifier="unit3-capstone-redshift",
    PubliclyAccessible=True,
)
print("Requested change. New PubliclyAccessible:", resp["Cluster"]["PubliclyAccessible"])
print("Cluster status:", resp["Cluster"]["ClusterStatus"])
