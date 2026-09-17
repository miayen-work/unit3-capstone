"""
Generates synthetic test data designed specifically so the two required
"harder" synthesis queries have concrete, checkable answers:

1. Churn query: customers.csv has a deliberately elevated churn rate
   (12%), while retention_strategy.pdf states a target of "below 5%".
   The AI query layer should be able to detect the mismatch by combining
   a Redshift SQL result with a retrieved OpenSearch document.

2. Governance query: customers.csv is missing several fields required by
   data_governance_policy.pdf (source_system, data_owner,
   last_updated_at), while product_inventory.json includes all of them.
   The AI query layer should detect this by combining the Glue Catalog's
   discovered schema with the retrieved policy document.

Writes files locally to data/, then uploads:
    - PDFs to the S3 bucket root (triggers the ingestion Lambda)
    - CSV/JSON to S3 under the "structured/" prefix (for the Glue Crawler)

Usage:
    python boto3_scripts/generate_test_data.py
"""
import csv
import json
import os
from pathlib import Path

import boto3
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv()

BUCKET = os.environ["S3_BUCKET_NAME"]
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))


# ---------------------------------------------------------------------------
# customers.csv -- 50 rows, 6 churned (12% churn rate). Missing governance
# fields: source_system, data_owner, last_updated_at.
# ---------------------------------------------------------------------------
def write_customers_csv():
    path = DATA_DIR / "customers.csv"
    plans = ["basic", "standard", "premium"]
    churned_ids = {5, 12, 18, 27, 33, 44}  # 6 out of 50 = 12%

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "signup_date", "plan_type", "monthly_spend", "churned", "churn_date"])
        for i in range(1, 51):
            churned = i in churned_ids
            signup_month = (i % 12) + 1
            writer.writerow([
                f"CUST{i:04d}",
                f"2025-{signup_month:02d}-01",
                plans[i % 3],
                round(20 + (i % 5) * 15.5, 2),
                "true" if churned else "false",
                "2026-08-15" if churned else "",
            ])
    print(f"wrote {path} (50 rows, 6 churned = 12% churn rate)")
    return path


# ---------------------------------------------------------------------------
# product_inventory.json -- fully compliant with governance policy fields.
# ---------------------------------------------------------------------------
def write_product_inventory_json():
    path = DATA_DIR / "product_inventory.json"
    products = []
    for i in range(1, 16):
        products.append({
            "id": f"PROD{i:04d}",
            "source_system": "inventory-service",
            "data_owner": "supply-chain-team",
            "created_at": "2025-01-10T00:00:00Z",
            "last_updated_at": "2026-09-01T00:00:00Z",
            "product_name": f"Widget Model {i}",
            "price": round(9.99 + i * 3.5, 2),
            "stock_quantity": 100 - i * 4,
        })
    with open(path, "w") as f:
        for product in products:
            f.write(json.dumps(product) + "\n")
    print(f"wrote {path} (15 rows, all governance fields present, JSON Lines format)")
    return path


# ---------------------------------------------------------------------------
# retention_strategy.pdf
# ---------------------------------------------------------------------------
def write_retention_strategy_pdf():
    path = DATA_DIR / "retention_strategy.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Customer Retention Strategy", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7,
        "Our company is committed to maintaining a healthy, loyal customer base "
        "through proactive retention efforts across all subscription tiers.\n\n"
        "Target Churn Rate: We aim to keep monthly customer churn below 5 percent "
        "company-wide, with a healthy target range of 2 to 4 percent based on "
        "industry benchmarks for our subscription tier. Any measured churn rate "
        "at or above 5 percent should be treated as a significant deviation from "
        "target and should trigger an immediate retention review with the "
        "customer success team.\n\n"
        "Retention Tactics: proactive outreach at the 30/60/90 day marks, "
        "loyalty discounts for at-risk accounts identified by declining usage, "
        "and quarterly satisfaction surveys.\n\n"
        "Monitoring: The data warehouse team tracks churn monthly using the "
        "customers table in the Redshift data warehouse. Churn rate is "
        "calculated as the percentage of customers with a non-null churn_date "
        "in the current reporting period."
    )
    pdf.output(str(path))
    print(f"wrote {path}")
    return path


# ---------------------------------------------------------------------------
# data_governance_policy.pdf
# ---------------------------------------------------------------------------
def write_governance_policy_pdf():
    path = DATA_DIR / "data_governance_policy.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Data Governance Policy", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7,
        "All datasets ingested into the enterprise data warehouse must include "
        "the following required metadata fields at the dataset/table level:\n\n"
        "1. A unique record identifier field (e.g., id, customer_id, product_id)\n"
        "2. source_system - identifying which system originated the data\n"
        "3. data_owner - the team or individual responsible for the dataset\n"
        "4. created_at - timestamp the record was created\n"
        "5. last_updated_at - timestamp the record was last modified\n\n"
        "Any dataset missing one or more of these required fields must be "
        "flagged during the Glue Crawler cataloging process, and the "
        "responsible data owner must be notified so the dataset can be "
        "remediated before it is used for downstream analytics or reporting. "
        "Datasets should not be considered production-ready for BI or AI query "
        "purposes until they are fully compliant with this policy."
    )
    pdf.output(str(path))
    print(f"wrote {path}")
    return path


def upload(local_path: Path, s3_key: str):
    s3.upload_file(str(local_path), BUCKET, s3_key)
    print(f"uploaded s3://{BUCKET}/{s3_key}")


def main():
    customers_csv = write_customers_csv()
    inventory_json = write_product_inventory_json()
    retention_pdf = write_retention_strategy_pdf()
    governance_pdf = write_governance_policy_pdf()

    upload(retention_pdf, retention_pdf.name)
    upload(governance_pdf, governance_pdf.name)
    upload(customers_csv, f"structured/customers/{customers_csv.name}")
    upload(inventory_json, f"structured/product_inventory/{inventory_json.name}")


if __name__ == "__main__":
    main()
