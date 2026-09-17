# Unit 3 Capstone: Intelligent Document Search Pipeline

AWS pipeline for ingesting unstructured (PDF) and structured (CSV/JSON)
documents, making them searchable via semantic search (OpenSearch) and
SQL (Redshift), with a Bedrock/Claude-powered natural-language query layer.

## Status

Bronze checklist:

- [x] S3 stores raw PDFs, CSVs, and JSONs
- [x] Lambda triggers on upload; calls Textract for PDFs
- [x] Textract extracts and chunks PDF text (500-1000 tokens, word-count proxy)
- [x] Sentence Transformers generates document embeddings
- [x] Raw text stored in RDS; embeddings in OpenSearch
- [x] Glue Crawler catalogs and discovers data schemas (adapted: crawler creation is
      denied in this sandbox account, so schemas are defined directly via boto3 --
      see `docs/architecture.md`)
- [x] Glue ETL normalizes, validates, and loads CSV/JSON into Redshift
- [x] Redshift consolidates structured data (vector embeddings live in OpenSearch)
- [x] Matplotlib charts (2+) visualize Redshift data -- see `charts/`
- [x] Lambda and boto3 automate flows
- [x] IAM secures resources (scoped-down/inline policies throughout; see
      `docs/architecture.md` for documented tradeoffs)
- [ ] AI query layer: routing, NL-to-SQL, contextual document response --
      **code complete, blocked on a Bedrock model-access permission issue
      outside this codebase; see `docs/architecture.md`**. Logic that
      doesn't require a live model call (JSON parsing, SQL cleanup, the
      validator gate inside SQL execution) is unit tested independently
      -- 11/11 passing, see `docs/ai_query_layer_logic_test_results.txt`
- [x] SQL validation layer implemented and tested (7/7 cases, including a
      stacked-query attack) -- see `docs/sql_validation_results.txt`
- [ ] Tokenomics logging + 10-query cost summary -- logging is implemented
      (`tokenomics/tracker.py`), blocked on the same Bedrock access issue
- [ ] Both harder synthesis queries answered, citing both sources --
      expected behavior documented in `docs/architecture.md`, pending
      Bedrock access to capture actual output

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
