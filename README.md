# Unit 3 Capstone: Intelligent Document Search Pipeline

AWS pipeline for ingesting unstructured (PDF) and structured (CSV/JSON)
documents, making them searchable via semantic search (OpenSearch) and
SQL (Redshift), with a Bedrock/Claude-powered natural-language query layer.

## Status

Bronze checklist (see full list in `docs/requirements.md`):

- [ ] S3 stores raw PDFs, CSVs, and JSONs
- [ ] Lambda triggers on upload; calls Textract for PDFs
- [ ] Textract extracts and chunks PDF text (500-1000 tokens)
- [ ] Sentence Transformers generates document embeddings
- [ ] Raw text stored in RDS; embeddings in OpenSearch
- [ ] Glue Crawler catalogs and discovers data schemas
- [ ] Glue ETL normalizes, validates, and loads CSV/JSON into Redshift
- [ ] Redshift consolidates structured and vector data
- [ ] Matplotlib charts (2+) visualize Redshift data
- [ ] Lambda and boto3 automate flows
- [ ] IAM secures resources
- [ ] AI query layer: routing, NL-to-SQL, contextual document response
- [ ] SQL validation layer implemented and tested (5+ cases)
- [ ] Tokenomics logging + 10-query cost summary
- [ ] Both harder synthesis queries answered, citing both sources

## Project layout

```
boto3_scripts/     Infra setup + standalone smoke tests (run test_bedrock.py first)
lambda/            Lambda function handlers (PDF ingest, ETL triggers)
glue_jobs/         Glue Crawler config + ETL job scripts
ai_query_layer/     Routing, NL-to-SQL, document QA (built on Bedrock)
sql_validation/     SQL validator + its test suite
tokenomics/         Per-call token/cost logging + summary report
charts/             Matplotlib chart generation from Redshift data
docs/               Architecture diagram, setup notes, test results
data/               Local sample PDFs / CSV / JSON for testing
tests/              End-to-end pipeline tests
```

## Setup

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # fill in AWS account id, region, resource names
```

## First thing to run

Before building anything else, confirm Bedrock access works:

```bash
python boto3_scripts/test_bedrock.py
```

If that doesn't return a real response, stop and fix AWS/Bedrock access
before writing any routing or SQL-generation logic.

## Architecture

See `docs/architecture.md` (diagram + data flow to be added once provided in class).
