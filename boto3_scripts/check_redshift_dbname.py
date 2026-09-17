import boto3

redshift = boto3.client("redshift", region_name="us-east-1")
c = redshift.describe_clusters(ClusterIdentifier="unit3-capstone-redshift")["Clusters"][0]
print("DBName:", c.get("DBName"))
