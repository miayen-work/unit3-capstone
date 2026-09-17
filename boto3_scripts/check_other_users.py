import boto3

redshift = boto3.client("redshift", region_name="us-east-1")
c = redshift.describe_clusters(ClusterIdentifier="unit3-capstone-redshift")["Clusters"][0]
print("Redshift master username:", c["MasterUsername"])

opensearch = boto3.client("opensearch", region_name="us-east-1")
cfg = opensearch.describe_domain_config(DomainName="unit3-capstone-search")["DomainConfig"]
master_opts = cfg.get("AdvancedSecurityOptions", {}).get("Options", {}).get("MasterUserOptions", {})
print("OpenSearch master username:", master_opts.get("MasterUserName", "(not visible via this call)"))
