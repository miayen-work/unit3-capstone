"""
Glue ETL job: reads the customers and product_inventory tables from the
Glue Data Catalog (schemas defined in boto3_scripts/create_glue_catalog.py,
replicating what a crawler would have discovered), normalizes/validates
them, and loads them into Redshift.

Writes to Redshift via Spark's JDBC writer using the standard PostgreSQL
driver (Redshift is wire-compatible with Postgres for basic SQL at this
scale) -- this avoids needing an IAM role attached to the Redshift
cluster or staging through S3 via COPY, since attaching an IAM role to
this sandbox's Redshift cluster is blocked (see docs/architecture.md).
"""
import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import col, to_date, when

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "REDSHIFT_HOST",
        "REDSHIFT_PORT",
        "REDSHIFT_DB",
        "REDSHIFT_USER",
        "REDSHIFT_PASSWORD",
        "GLUE_DATABASE",
    ],
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

jdbc_url = f"jdbc:postgresql://{args['REDSHIFT_HOST']}:{args['REDSHIFT_PORT']}/{args['REDSHIFT_DB']}"
jdbc_props = {
    "user": args["REDSHIFT_USER"],
    "password": args["REDSHIFT_PASSWORD"],
    "driver": "org.postgresql.Driver",
}

# ---------------------------------------------------------------------
# customers: normalize types, drop duplicates/invalid rows
# ---------------------------------------------------------------------
customers_dyf = glueContext.create_dynamic_frame.from_catalog(
    database=args["GLUE_DATABASE"], table_name="customers"
)
customers_df = customers_dyf.toDF()

customers_df = (
    customers_df.withColumn("monthly_spend", col("monthly_spend").cast("double"))
    .withColumn("churned", when(col("churned") == "true", True).otherwise(False))
    .withColumn(
        "churn_date",
        when((col("churn_date").isNull()) | (col("churn_date") == ""), None).otherwise(
            to_date(col("churn_date"))
        ),
    )
    .filter(col("customer_id").isNotNull())
    .dropDuplicates(["customer_id"])
)

customers_df.write.jdbc(url=jdbc_url, table="customers", mode="overwrite", properties=jdbc_props)

# ---------------------------------------------------------------------
# product_inventory: normalize types, drop duplicates/invalid rows
# ---------------------------------------------------------------------
inventory_dyf = glueContext.create_dynamic_frame.from_catalog(
    database=args["GLUE_DATABASE"], table_name="product_inventory"
)
inventory_df = inventory_dyf.toDF()

inventory_df = (
    inventory_df.withColumn("price", col("price").cast("double"))
    .withColumn("stock_quantity", col("stock_quantity").cast("int"))
    .filter(col("id").isNotNull())
    .dropDuplicates(["id"])
)

inventory_df.write.jdbc(url=jdbc_url, table="product_inventory", mode="overwrite", properties=jdbc_props)

job.commit()
