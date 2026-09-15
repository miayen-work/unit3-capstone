# Lambda: triggered on S3 upload of a PDF.
# Flow: Textract extract -> chunk (500-1000 tokens) -> Sentence Transformers
# embed -> write raw text to RDS, vectors to OpenSearch.
#
# TODO: implement once S3/RDS/OpenSearch resources exist (see Day 2 in plan).


def handler(event, context):
    raise NotImplementedError
