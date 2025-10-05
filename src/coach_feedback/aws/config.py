import os
AWS_REGION=os.getenv('AWS_REGION','ap-northeast-2')
AWS_PROFILE=os.getenv('AWS_PROFILE')
S3_BUCKET=os.getenv('S3_BUCKET')
DDB_TABLE=os.getenv('DDB_TABLE')
BEDROCK_MODEL_ID=os.getenv('BEDROCK_MODEL_ID','anthropic.claude-3-5-sonnet-20240620-v1:0')
CLOUD_MODE_DEFAULT=os.getenv('CLOUD_MODE','0')=='1'
