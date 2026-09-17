"""
One-time setup: create the document_chunks table in RDS.

Run this once, locally, after RDS is available and .env is filled in.

Usage:
    python boto3_scripts/init_rds_schema.py
"""
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.environ["RDS_HOST"],
    port=os.environ["RDS_PORT"],
    dbname=os.environ["RDS_DB_NAME"],
    user=os.environ["RDS_USER"],
    password=os.environ["RDS_PASSWORD"],
    sslmode="require",
)
conn.autocommit = True

with conn.cursor() as cur:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id SERIAL PRIMARY KEY,
            s3_key TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            word_count INTEGER NOT NULL,
            embedded BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE (s3_key, chunk_index)
        );
        """
    )

print("document_chunks table ready.")
conn.close()
