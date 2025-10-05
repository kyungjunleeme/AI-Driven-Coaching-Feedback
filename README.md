See project for details.


## Security & Integrations
- **Cognito JWT(FastAPI 미들웨어)**: 환경변수 `AUTH_REQUIRED=1`, `COGNITO_USER_POOL_ID`, `COGNITO_AUDIENCE` 설정 → GraphQL `/graphql`에 Bearer JWT 필수.
- **AppSync IAM 요청 유틸**: `post_graphql_iam(endpoint, query, variables)`로 SigV4 서명 후 GraphQL POST.

## Bedrock 병렬화(멀티청크×멀티스텝)
- `score_chunks_steps(texts, step_ids, max_workers, timeout_s, retries, calls_per_sec, initial_stagger_ms)`
- `top_step_per_chunk(texts)` → 각 청크의 최상 스텝 ID 리스트 반환


## AsyncAPI (WebSocket) — GraphQL 대체
- 스펙: `src/coach_feedback/asyncapi/asyncapi.yaml` (AsyncAPI **3.0.0**)
- 서버 실행:
```bash
make asyncapi-server   # ws://localhost:8002
```
- 파이프라인에서 자동 브로드캐스트(옵션):
```bash
export ASYNCAPI_ENABLE=1
export ASYNCAPI_SERVER_URL=http://localhost:8002
```
- 이벤트 타입:
  - `FeedbackCreated` — 채널 `sessions/{sessionId}/feedback`
  - `TranscriptChunkAppended` — 채널 `sessions/{sessionId}/transcript` (샘플 훅은 이후 추가 가능)
- 커맨드(수신): `RequestFeedback` — 채널 `sessions/{sessionId}/commands` (서버는 WS로 수신만, 실제 실행 훅은 필요 시 연결)

### 클라이언트 수신 예시 (Node/브라우저)
```js
const ws = new WebSocket("ws://localhost:8002/ws/sessions/abcd1234");
ws.onmessage = (ev) => console.log("event:", ev.data);
```

### 파이썬에서 퍼블리시
```python
from src.coach_feedback.asyncapi.publisher import publish_event
publish_event("abcd1234", "FeedbackCreated", {"session_id":"abcd1234", "step_focus": 11, "feedback": {...}})
```
