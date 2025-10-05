from __future__ import annotations
from typing import Any, Dict
import boto3
import time
from .config import AWS_REGION, AWS_PROFILE, DDB_TABLE


def _session():
    if AWS_PROFILE:
        return boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    return boto3.Session(region_name=AWS_REGION)


def _ddb():
    return _session().resource("dynamodb", region_name=AWS_REGION)


def put_feedback(session_id: str, payload: Dict[str, Any]) -> None:
    if not DDB_TABLE:
        return
    tbl = _ddb().Table(DDB_TABLE)
    item = {"session_id": session_id, "ts": int(time.time()), **payload}
    tbl.put_item(Item=item)
