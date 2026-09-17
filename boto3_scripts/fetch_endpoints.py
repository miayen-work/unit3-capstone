"""
One-off helper: print connection endpoints for RDS, OpenSearch, Redshift,
and list S3 buckets, so they can be copied into .env.

Usage:
    python boto3_scripts/fetch_endpoints.py
"""
import boto3

REGION = "us-east-1"

rds = boto3.client("rds", region_name=REGION)
for db in rds.describe_db_instances()["DBInstances"]:
    ep = db.get("Endpoint", {})
    print("RDS:", db["DBInstanceIdentifier"], "-", ep.get("Address"), ep.get("Port"))

opensearch = boto3.client("opensearch", region_name=REGION)
for name in opensearch.list_domain_names()["DomainNames"]:
    d = opensearch.describe_domain(DomainName=name["DomainName"])["DomainStatus"]
    print("OpenSearch:", d["DomainName"], "-", d.get("Endpoint") or d.get("Endpoints"))

redshift = boto3.client("redshift", region_name=REGION)
for c in redshift.describe_clusters()["Clusters"]:
    ep = c.get("Endpoint", {})
    print("Redshift:", c["ClusterIdentifier"], "-", ep.get("Address"), ep.get("Port"), "status:", c["ClusterStatus"])

s3 = boto3.client("s3", region_name=REGION)
for b in s3.list_buckets()["Buckets"]:
    print("S3 bucket:", b["Name"])
