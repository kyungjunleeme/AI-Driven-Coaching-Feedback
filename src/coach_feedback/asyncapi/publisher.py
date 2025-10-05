from __future__ import annotations
import os
import requests

ASYNCAPI_SERVER = os.getenv("ASYNCAPI_SERVER_URL", "http://localhost:8002")


def publish_event(session_id: str, event_type: str, payload: dict) -> bool:
    url = f"{ASYNCAPI_SERVER}/publish/{session_id}"
    msg = {"type": event_type, **payload}
    try:
        resp = requests.post(url, json=msg, timeout=5)
        resp.raise_for_status()
        return True
    except Exception:
        return False
