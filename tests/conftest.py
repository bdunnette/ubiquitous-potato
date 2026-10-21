import os

# Ensure local test runs use standard sqlite by default unless explicitly testing s3 sqlite
os.environ["USE_S3_SQLITE"] = "false"
os.environ["DEBUG"] = "True"
