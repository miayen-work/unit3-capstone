import boto3

redshift = boto3.client("redshift", region_name="us-east-1")
c = redshift.describe_clusters(ClusterIdentifier="unit3-capstone-redshift")["Clusters"][0]
print("PubliclyAccessible:", c.get("PubliclyAccessible"))
print("Endpoint:", c.get("Endpoint"))
print("VpcSecurityGroups:", c.get("VpcSecurityGroups"))
print("ClusterSubnetGroupName:", c.get("ClusterSubnetGroupName"))
