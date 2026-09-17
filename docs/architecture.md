# Architecture

_To be filled in once the reference architecture diagram is provided in class._

## Data flow (fill in / adjust once diagram is available)

1. Upload -> S3 (raw PDFs, CSVs, JSONs)
2. S3 event -> Lambda
   - PDF -> Textract -> chunk -> Sentence Transformers embed -> RDS (text) + OpenSearch (vectors)
   - CSV/JSON -> Glue Crawler (catalog) -> Glue ETL (normalize/validate) -> Redshift
3. AI query layer (Bedrock/Claude via inference-profile ARN):
   - Router decides OpenSearch vs Redshift vs both
   - Redshift path: NL-to-SQL -> sql_validation/validator.py -> execute -> answer
   - OpenSearch path: retrieve chunks -> grounded answer with citations
   - Both: combine into a single cited answer
4. Tokenomics: every Bedrock call logged (tokenomics/tracker.py) -> cost summary
5. Charts: matplotlib from Redshift data -> charts/

## Implementation constraints and adaptations

This project's sandbox AWS account and dev network imposed a few real
constraints that shaped implementation decisions:

1. **Bedrock embedding models denied** (`amazon.titan-embed-text-v2:0`,
   `cohere.embed-english-v3`) -- confirmed a structural sandbox
   permissions gap, not fixable by choosing a different model. Fixed by
   generating embeddings locally with Sentence Transformers instead.

2. **No Docker available locally** -- Sentence Transformers + PyTorch is
   too large for a plain zip-based Lambda (~250MB unzipped limit), and
   building a Linux-compatible package without Docker isn't feasible on
   Windows. Fixed by splitting the PDF pipeline: the ingestion Lambda
   (Textract + chunking + write to RDS/S3) is a small zip package using
   only `boto3` and `pg8000` (pure-Python Postgres driver, no compiled
   binaries); embedding generation runs as a separate local `boto3`
   script. This still satisfies every Bronze requirement, just splits
   *where* the embedding step physically executes.

3. **IAM restrictions in the sandbox account**: the account could not
   create new VPCs (`ec2:CreateVpc` denied) or attach AWS managed
   policies with "FullAccess" in the name (explicit deny), and could not
   modify a Redshift cluster's associated IAM roles at all
   (`redshift:ModifyClusterIamRoles` denied). Worked around by using the
   existing default VPC, using scoped-down managed policies (e.g.
   `AmazonS3ReadOnlyAccess`) or custom inline policies instead of
   FullAccess ones, and using access-key-based `CREDENTIALS` in Redshift
   `COPY` statements instead of an attached IAM role.

4. **Local dev network blocks direct Postgres connections** (port 5432)
   while allowing normal HTTPS/AWS-API traffic -- confirmed by testing
   with two different Postgres drivers (both failed the same way) and by
   successfully connecting instead from AWS CloudShell (which runs
   inside AWS's network). Fixed by having the ingestion Lambda write
   extracted chunks to **both** RDS (raw text, satisfying the
   requirement) and a JSON file in S3; the local embedding script reads
   pending chunks from S3 (plain HTTPS) instead of querying RDS directly,
   avoiding the blocked path entirely.

5. **Glue Crawler creation denied** (`glue:CreateCrawler`) for this IAM
   user, while `glue:CreateDatabase` and `glue:CreateTable` both work.
   Fixed by defining the Glue database and table schemas directly via
   boto3 (`boto3_scripts/create_glue_catalog.py`), replicating exactly
   what a crawler would have discovered from `customers.csv` and
   `product_inventory.json`.

6. **RDS security group** is currently open to `0.0.0.0/0` on port 5432
   rather than IP-restricted, since local dev IPs changed across
   sessions/networks. Documented tradeoff for a short-lived class
   project; the instance is deleted after grading (see below).

## Cleanup (last day, after grading)

Delete these to stop billing/exposure once the project is submitted:
RDS instance (`unit3-capstone-db`), Redshift cluster
(`unit3-capstone-redshift`), OpenSearch domain
(`unit3-capstone-search`).

## Test results

_Fill in after end-to-end testing (Day 4), including both required harder
synthesis queries and their citations._
