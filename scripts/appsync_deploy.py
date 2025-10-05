
from __future__ import annotations
import argparse, os, boto3

SCHEMA = '''
type TranscriptChunk { id: String!, speaker: String!, text: String!, ts: String }
type Feedback { step_focus: Int!, praise: String!, improvement: String!, why_it_matters: String!, evidence_quote: [String!]!, student_learning_link: String!, next_step: String! }
type Session { session_id: String!, step_focus: Int!, transcript: [TranscriptChunk!]!, feedback: Feedback!, audio_s3: String, feedback_s3: String }
type Query { getSession(session_id: String!): Session }
schema { query: Query }
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--region", default=os.getenv("AWS_REGION","ap-northeast-2"))
    ap.add_argument("--profile", default=os.getenv("AWS_PROFILE"))
    args = ap.parse_args()

    if args.profile:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
    else:
        session = boto3.Session(region_name=args.region)
    appsync = session.client("appsync", region_name=args.region)

    api = appsync.create_graphql_api(name=args.name, authenticationType="API_KEY")["graphqlApi"]
    print("API ID:", api["apiId"])
    key = appsync.create_api_key(apiId=api["apiId"], description="dev-key")["apiKey"]
    print("API Key:", key["id"])
    appsync.start_schema_creation(apiId=api["apiId"], definition=SCHEMA.encode("utf-8"))
    print("Schema submitted. Add data sources & resolvers from console or extend this script.")
if __name__=="__main__":
    main()
