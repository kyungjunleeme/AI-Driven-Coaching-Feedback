from __future__ import annotations
from typing import Optional, Dict, Any
import json
import requests
import boto3
from botocore.awsrequest import AWSRequest
from botocore.auth import SigV4Auth
from botocore.credentials import ReadOnlyCredentials
from .config import AWS_REGION, AWS_PROFILE


def _session():
    if AWS_PROFILE:
        return boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    return boto3.Session(region_name=AWS_REGION)


def _creds():
    sess = _session()
    creds = sess.get_credentials()
    frozen = creds.get_frozen_credentials()
    return ReadOnlyCredentials(frozen.access_key, frozen.secret_key, frozen.token)


def post_graphql_iam(
    endpoint: str,
    query: str,
    variables: Optional[Dict[str, Any]] = None,
    operation_name: Optional[str] = None,
) -> Dict[str, Any]:
    payload = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    if operation_name:
        payload["operationName"] = operation_name

    body = json.dumps(payload).encode("utf-8")
    # Build AWS signed request
    req = AWSRequest(
        method="POST", url=endpoint, data=body, headers={"Content-Type": "application/json"}
    )
    SigV4Auth(_creds(), "appsync", AWS_REGION).add_auth(req)
    prepared = requests.PreparedRequest()
    prepared.prepare(method=req.method, url=req.url, headers=dict(req.headers.items()), data=body)
    with requests.Session() as s:
        resp = s.send(prepared, timeout=20)
        resp.raise_for_status()
        return resp.json()
