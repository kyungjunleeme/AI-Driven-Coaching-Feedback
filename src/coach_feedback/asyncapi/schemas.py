from __future__ import annotations

FeedbackCreatedSchema = {
    "type": "object",
    "properties": {
        "type": {"const": "FeedbackCreated"},
        "session_id": {"type": "string"},
        "step_focus": {"type": "integer", "minimum": 1, "maximum": 12},
        "feedback": {"type": "object"},
    },
    "required": ["type", "session_id", "step_focus", "feedback"],
    "additionalProperties": True,
}

RequestFeedbackSchema = {
    "type": "object",
    "properties": {
        "type": {"const": "RequestFeedback"},
        "session_id": {"type": "string"},
        "mode": {"type": "string", "enum": ["local", "cloud"]},
        "audio_ref": {"type": ["string", "null"]},
        "force_step": {"type": ["integer", "null"], "minimum": 1, "maximum": 12},
        "language": {"type": "string", "enum": ["ko", "en"]},
    },
    "required": ["type", "session_id"],
    "additionalProperties": True,
}
