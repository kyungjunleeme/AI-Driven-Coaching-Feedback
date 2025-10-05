
from __future__ import annotations
from typing import Any, Dict
import json, boto3, os
from .config import AWS_REGION, AWS_PROFILE, S3_BUCKET

def _session():
    if AWS_PROFILE:
        return boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    return boto3.Session(region_name=AWS_REGION)

def _s3():
    return _session().client("s3", region_name=AWS_REGION)

def upload_file(local_path: str, key: str, bucket: str | None = None) -> str:
    bucket = bucket or S3_BUCKET
    if not bucket: raise RuntimeError("S3_BUCKET not set")
    _s3().upload_file(local_path, bucket, key)
    return f"s3://{bucket}/{key}"

def upload_json(obj: Dict[str, Any], key: str, bucket: str | None = None) -> str:
    bucket = bucket or S3_BUCKET
    if not bucket: raise RuntimeError("S3_BUCKET not set")
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    _s3().put_object(Bucket=bucket, Key=key, Body=body, ContentType="application/json; charset=utf-8")
    return f"s3://{bucket}/{key}"
