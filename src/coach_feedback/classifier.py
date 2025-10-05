from __future__ import annotations
from typing import List, Dict, Any
import re
import yaml
from .schema import TranscriptChunk, StepEnum, StepLabel, ClassificationOutput


def load_step_yaml(path: str) -> Dict[int, Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {int(k): v for k, v in data.get("steps", {}).items()}


def classify_transcript(
    chunks: List[TranscriptChunk], steps_yaml_path: str
) -> ClassificationOutput:
    steps = load_step_yaml(steps_yaml_path)
    labels: List[StepLabel] = []
    for ch in chunks:
        text = ch.text.lower()
        matched = []
        for sid, meta in steps.items():
            for cue in meta.get("cues", []):
                if re.search(r"\b" + re.escape(cue.lower()) + r"\b", text):
                    matched.append(StepEnum(sid))
                    break
        if not matched and (("학생" in ch.text) or ("students" in text)):
            matched = [StepEnum.LINK_PRAISE_TO_STUDENT_LEARNING]
        conf = 0.6 if matched else 0.2
        labels.append(StepLabel(id=ch.id, step_ids=matched, confidence=conf))
    return ClassificationOutput(labels=labels, notes="heuristic yaml-driven classifier")
