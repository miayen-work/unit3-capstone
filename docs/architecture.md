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

## Test results

_Fill in after end-to-end testing (Day 4), including both required harder
synthesis queries and their citations._
