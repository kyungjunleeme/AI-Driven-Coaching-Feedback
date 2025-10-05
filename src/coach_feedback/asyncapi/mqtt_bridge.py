from __future__ import annotations
import os
import json

try:
    import paho.mqtt.client as mqtt
except Exception:
    mqtt = None

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_COMMAND = os.getenv("MQTT_TOPIC_COMMAND", "sessions/+/commands")
TOPIC_FEEDBACK = os.getenv("MQTT_TOPIC_FEEDBACK", "sessions/{session_id}/feedback")
HTTP_PUBLISH = os.getenv("ASYNCAPI_SERVER_URL", "http://localhost:8002") + "/publish/{session_id}"


def _http_publish(session_id: str, event: dict):
    import requests

    url = HTTP_PUBLISH.format(session_id=session_id)
    try:
        requests.post(url, json=event, timeout=5)
    except Exception:
        pass


def start_bridge():
    if mqtt is None:
        raise RuntimeError("paho-mqtt not installed. Install extra: mqtt")
    client = mqtt.Client()

    def on_connect(client, userdata, flags, rc, properties=None):
        client.subscribe(TOPIC_COMMAND)

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return
        # Extract session_id from topic 'sessions/<id>/commands'
        parts = msg.topic.split("/")
        session_id = parts[1] if len(parts) >= 3 else payload.get("session_id")
        if payload.get("type") != "RequestFeedback":
            return
        # forward to HTTP command endpoint (server will run pipeline and broadcast)
        import requests

        url = (
            os.getenv("ASYNCAPI_SERVER_URL", "http://localhost:8002")
            + f"/commands/request-feedback/{session_id}"
        )
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception:
            pass

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    return client
