
.PHONY: help init venv sync ui run test lint format clean graphql api env

help:
	@echo "Targets: init | venv | sync | ui | run | test | lint | format | clean | graphql | api | env"

init: venv sync

venv:
	uv venv .venv

sync:
	uv sync

ui run:
	uv run streamlit run app.py

test:
	uv run pytest -q

lint:
	uv run ruff check . || true

format:
	uv run ruff check --fix . || true
	uv run black .

clean:
	rm -rf .venv .pytest_cache .ruff_cache .mypy_cache __pycache__ data/sessions

graphql:
	uv run python app_graphql.py

api:
	uv run uvicorn src.coach_feedback.graph.api:app --port 8001 --reload

env:
	cp -n .env.example .env || true
	@echo "Edit .env and export before running cloud targets"


asyncapi-server:
	uv run uvicorn src.coach_feedback.asyncapi.server:app --port 8002 --reload


asyncapi-bridge-mqtt:
	uv run python -c "from src.coach_feedback.asyncapi.mqtt_bridge import start_bridge; c=start_bridge(); import time; print('MQTT bridge running'); time.sleep(999999)"

asyncapi-bridge-kafka:
	uv run python -c "from src.coach_feedback.asyncapi.kafka_bridge import start_bridge; start_bridge()"
