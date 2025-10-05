from __future__ import annotations
import os
import json

try:
    from kafka import KafkaConsumer
except Exception:
    KafkaConsumer = None

TOPIC_COMMAND = os.getenv("KAFKA_TOPIC_COMMAND", "sessions.commands")
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")


def start_bridge():
    if KafkaConsumer is None:
        raise RuntimeError("kafka-python not installed. Install extra: kafka")
    consumer = KafkaConsumer(
        TOPIC_COMMAND,
        bootstrap_servers=BOOTSTRAP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="coach-feedback-bridge",
    )
    import requests

    base = os.getenv("ASYNCAPI_SERVER_URL", "http://localhost:8002")
    for msg in consumer:
        payload = msg.value
        if not isinstance(payload, dict):
            continue
        if payload.get("type") != "RequestFeedback":
            continue
        session_id = payload.get("session_id", "unknown")
        try:
            requests.post(
                f"{base}/commands/request-feedback/{session_id}", json=payload, timeout=10
            )
        except Exception:
            pass
