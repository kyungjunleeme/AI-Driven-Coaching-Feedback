# Repository Guidelines

## Project Structure & Module Organization
- `src/coach_feedback/` — core package (auth, aws, audio, llm, pipelines, asyncapi, graph).
- Entry points: `app.py` (Streamlit UI), `app_graphql.py` (GraphQL), `src/coach_feedback/graph/api.py` (FastAPI app).
- Tests: `tests/` (`test_*.py`). Utilities: `scripts/`. Examples: `examples/`. Templates/config: `src/coach_feedback/templates`, `src/coach_feedback/resources`, `src/coach_feedback/steps.yaml`.

## Build, Test, and Development Commands
- `make venv` — create `.venv` via `uv` (Python 3.12).
- `make sync` — install deps from `pyproject.toml`.
- `make run` or `make ui` — launch Streamlit UI from `app.py`.
- `make api` — run FastAPI app (`http://localhost:8001`).
- `make graphql` — run GraphQL server (Uvicorn).
- `make asyncapi-server` — start WS server on port 8002.
- `make test` — run `pytest -q`.  `make lint` — `ruff` check.  `make format` — `ruff --fix` + `black`.
- `make env` — copy `.env.example` to `.env` (edit before cloud targets).

## Coding Style & Naming Conventions
- Python 3.12, 4‑space indent, add type hints for public APIs.
- Line length 100; `ruff` and `black` configured in `pyproject.toml`.
- Names: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.

## Testing Guidelines
- Framework: `pytest`. Test files live under `tests/` and match `test_*.py`.
- Add/adjust tests for any new or changed behavior; keep tests fast and deterministic.
- Examples: run all `uv run pytest -q`; single file `uv run pytest tests/test_schema.py -q`.

## Commit & Pull Request Guidelines
- History is minimal; use clear, imperative subjects. Prefer Conventional Commits (e.g., `feat: add AsyncAPI server hook`, `fix: handle empty transcript`).
- PRs: focused scope, description of intent, linked issues, and screenshots/logs for UI/server changes.
- Before opening: run `make test` and `make lint`; note any known limitations.

## Security & Configuration Tips
- Auth (GraphQL): set `AUTH_REQUIRED=1`, `COGNITO_USER_POOL_ID`, `COGNITO_AUDIENCE`.
- AsyncAPI: `ASYNCAPI_ENABLE=1`, `ASYNCAPI_SERVER_URL=http://localhost:8002`.
- Avoid committing secrets; prefer environment variables and `.env` (excluded from VCS).

## Agent‑Specific Notes
- Keep patches minimal and scoped; don’t reformat unrelated files.
- Follow the structure above; update tests and docs when changing behavior.
- Use `Makefile` targets and `uv` for all local runs.

