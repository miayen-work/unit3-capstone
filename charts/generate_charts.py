"""
Generates 2+ charts from Redshift data using matplotlib, saved as PNG
files in this directory.

Needs a direct Postgres-wire connection to Redshift (pg8000) -- if your
local network blocks that (see docs/architecture.md), run this from AWS
CloudShell instead:

    pip install --user pg8000 matplotlib python-dotenv
    python generate_charts.py

(CloudShell needs the REDSHIFT_* and AWS_REGION env vars available --
either export them directly, or copy your .env file over and this script
will pick it up via python-dotenv.)

Usage:
    python charts/generate_charts.py
"""
import os

import matplotlib

matplotlib.use("Agg")  # headless backend -- no display needed
import matplotlib.pyplot as plt
import pg8000.native
from dotenv import load_dotenv

load_dotenv()

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_connection():
    return pg8000.native.Connection(
        host=os.environ["REDSHIFT_HOST"],
        port=int(os.environ["REDSHIFT_PORT"]),
        database=os.environ["REDSHIFT_DB_NAME"],
        user=os.environ["REDSHIFT_USER"],
        password=os.environ["REDSHIFT_PASSWORD"],
    )


def chart_churn_breakdown(conn):
    rows = conn.run(
        "SELECT churned, COUNT(*) AS count FROM customers GROUP BY churned ORDER BY churned;"
    )
    labels = ["Active" if not r[0] else "Churned" for r in rows]
    counts = [r[1] for r in rows]

    plt.figure(figsize=(6, 5))
    bars = plt.bar(labels, counts, color=["#4C72B0", "#C44E52"])
    plt.title("Customer Churn Breakdown")
    plt.ylabel("Number of Customers")
    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3, str(count), ha="center")
    plt.tight_layout()
    path = os.path.join(OUT_DIR, "churn_breakdown.png")
    plt.savefig(path)
    plt.close()
    print(f"wrote {path}")


def chart_avg_spend_by_plan(conn):
    rows = conn.run(
        "SELECT plan_type, AVG(monthly_spend) AS avg_spend FROM customers GROUP BY plan_type ORDER BY plan_type;"
    )
    labels = [r[0] for r in rows]
    values = [float(r[1]) for r in rows]

    plt.figure(figsize=(6, 5))
    bars = plt.bar(labels, values, color="#55A868")
    plt.title("Average Monthly Spend by Plan Type")
    plt.ylabel("Average Monthly Spend ($)")
    for bar, value in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f"${value:.2f}", ha="center")
    plt.tight_layout()
    path = os.path.join(OUT_DIR, "avg_spend_by_plan.png")
    plt.savefig(path)
    plt.close()
    print(f"wrote {path}")


def chart_inventory_stock_levels(conn):
    rows = conn.run(
        "SELECT product_name, stock_quantity FROM product_inventory ORDER BY product_name;"
    )
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]

    plt.figure(figsize=(9, 5))
    plt.bar(labels, values, color="#8172B2")
    plt.title("Product Inventory Stock Levels")
    plt.ylabel("Stock Quantity")
    plt.xticks(rotation=60, ha="right")
    plt.tight_layout()
    path = os.path.join(OUT_DIR, "inventory_stock_levels.png")
    plt.savefig(path)
    plt.close()
    print(f"wrote {path}")


def main():
    conn = get_connection()
    try:
        chart_churn_breakdown(conn)
        chart_avg_spend_by_plan(conn)
        chart_inventory_stock_levels(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
