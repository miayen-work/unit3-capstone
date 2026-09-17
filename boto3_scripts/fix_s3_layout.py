import boto3

BUCKET = "unit3-capstone-miayen-docs"
s3 = boto3.client("s3", region_name="us-east-1")

moves = [
    ("structured/customers.csv", "structured/customers/customers.csv"),
    ("structured/product_inventory.json", "structured/product_inventory/product_inventory.json"),
]

for old_key, new_key in moves:
    s3.copy_object(Bucket=BUCKET, CopySource={"Bucket": BUCKET, "Key": old_key}, Key=new_key)
    s3.delete_object(Bucket=BUCKET, Key=old_key)
    print(f"moved {old_key} -> {new_key}")
