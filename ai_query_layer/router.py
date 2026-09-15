# Given a natural-language question, decide whether it needs OpenSearch
# (semantic/document search), Redshift (SQL/structured data), or both.
#
# The two required "harder" synthesis queries need the "both" path: query
# each source, then combine into ONE answer citing both -- not two
# separate answers, not just the first source checked.
#
# TODO: implement on top of boto3_scripts/test_bedrock.py's invoke_claude().
