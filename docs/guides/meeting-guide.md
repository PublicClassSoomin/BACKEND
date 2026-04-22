# Meeting 도메인 & 화자분리 서버 연동 명세서

> 신입 개발자를 위한 가이드 — "데이터가 어디서 왔고, 어디에 저장되고, 어떻게 읽히는가"를 중심으로 설명합니다.

---

## 1. 전체 흐름 한눈에 보기

```
[화자분리 서버(외부)]
    │
    │  STT 결과물 (speaker_id + 발화 텍스트 + 타임스탬프)
    ▼
[Redis]  ←──────── 실시간 발화 저장 (회의 중 휘발성 데이터)
    │
    │  회의 종료 후 AI 처리
    ▼
[MongoDB] ←─────── 회의 요약, 챗봇 로그 (영구 보존)
[PostgreSQL] ←──── 회의 메타데이터, 화자 프로필 (구조적 데이터)
```

**핵심 원칙**: 회의 중 실시간 발화는 **Redis**(빠르고 휘발성), 회의 후 결과물은 **MongoDB/PostgreSQL**(영구 보존).

---

## 2. 데이터베이스별 역할

| DB | 저장 데이터 | 이유 |
|---|---|---|
| **Redis** | 실시간 발화 스트림, 화자 이름 매핑 | 빠른 읽기/쓰기, 회의 중에만 필요 |
| **MongoDB** | 회의 요약본, 챗봇 대화 로그, 이전 회의 컨텍스트 | 스키마가 유동적인 문서 저장 |
| **PostgreSQL** | 회의 메타데이터, 참석자, 화자 프로필, 안건 | 관계형 데이터, 영구 보존 |

---

## 3. Redis 스키마 상세

### 3-1. 발화 리스트 `meeting:{meeting_id}:utterances`

- **자료구조**: List (순서 있는 배열)
- **TTL**: 24시간 (86400초)
- **쓰기**: 화자분리 서버가 발화 1건 발생할 때마다 `RPUSH`
- **읽기**: AI 요약/챗봇이 `LRANGE 0 -1`로 전체 조회

**저장 포맷 (JSON 문자열 1건)**:

```json
{
  "speaker_id": "spk_001",
  "content": "오늘 회의 시작하겠습니다.",
  "timestamp": "2026-04-17T10:00:00"
}
```

| 필드 | 타입 | 필수 여부 | 설명 |
|---|---|---|---|
| `speaker_id` | string | **선택** | 화자분리 서버가 부여한 화자 식별자. 없으면 키 자체를 생략 |
| `content` | string | **필수** | 발화 텍스트 (STT 결과) |
| `timestamp` | string | **필수** | ISO 8601 형식. 예: `2026-04-17T10:00:00` |

> **중요**: `speaker_id`가 없어도 저장해야 합니다. 없는 경우 서버에서 "알 수 없음"으로 표시합니다.

---

### 3-2. 화자 이름 매핑 `meeting:{meeting_id}:speakers`

- **자료구조**: Hash
- **TTL**: 24시간 (86400초)
- **쓰기**: 회의 시작 전 또는 참석자가 화자 등록할 때 `HSET`
- **읽기**: 발화를 화면에 표시할 때 `HGETALL`

**저장 포맷**:

```
Key: meeting:test-001:speakers
Field        Value
─────────────────────
spk_001   →  박지수
spk_002   →  이민준
```

> `spk_003`처럼 분리는 됐지만 이름이 없는 화자는 해시에 넣지 않아도 됩니다.  
> 서버가 자동으로 "화자1", "화자2" 등으로 순번을 부여합니다.

---

### 3-3. 요약 캐시 `meeting:{meeting_id}:partial_summary`

- **자료구조**: String
- **TTL**: 1시간 (3600초)
- **쓰기**: AI 요약 노드가 생성 직후 저장
- **읽기**: 다음 요약 요청 시 증분 처리에 활용

> 화자분리 서버는 이 키를 직접 건드릴 필요 없습니다.

---

## 4. MongoDB 컬렉션 상세

### 4-1. `meeting_contexts` — 이전 회의 요약

AI가 현재 회의와 관련된 **이전 회의 내용**을 검색할 때 사용합니다.

```json
{
  "meeting_id": "test-000",
  "title": "2026-04-10 백엔드 아키텍처 사전 논의",
  "summary": "FastAPI 도메인 구조 개편 필요성에 대해 논의함. 인증 모듈 JWT 토큰 만료 처리 누락 이슈 제기됨...",
  "created_at": "2026-04-10T10:00:00"
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `meeting_id` | string | 회의 고유 ID |
| `title` | string | 회의 제목 |
| `summary` | string | AI가 생성한 회의 전체 요약 |
| `created_at` | datetime | 생성 시각 |

**인덱스**: `summary`와 `title` 필드에 `$text` 인덱스 필요 (키워드 검색용)

```python
# 인덱스 생성 예시
col.create_index([("summary", "text"), ("title", "text")], name="summary_text")
```

---

### 4-2. `chatbot_logs` — 챗봇 대화 이력

챗봇 세션의 **대화 맥락 유지**에 사용됩니다.

```json
{
  "meeting_id": "test-001",
  "session_id": "sess-abc123",
  "role": "user",
  "content": "이번 회의에서 결정된 내용이 뭔가요?",
  "function_type": "chat",
  "timestamp": "2026-04-17T10:30:00"
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `meeting_id` | string | 회의 ID |
| `session_id` | string | 챗봇 세션 ID (유저별 구분) |
| `role` | string | `"user"` 또는 `"assistant"` |
| `content` | string | 메시지 내용 |
| `function_type` | string | `"chat"`, `"summary"`, `"search"` 등 |
| `timestamp` | datetime | 저장 시각 |

---

## 5. PostgreSQL 테이블 상세

### 5-1. `meetings` — 회의 메타데이터

```python
class Meeting(Base):
    id            # 회의 고유 번호 (자동 증가)
    workspace_id  # 어느 워크스페이스의 회의인지
    created_by    # 회의 생성자 (user_id)
    title         # 회의 제목
    status        # "scheduled" | "in_progress" | "done"
    room_name     # 회의실 이름
    scheduled_at  # 예정 시각
    started_at    # 실제 시작 시각
    ended_at      # 종료 시각
```

---

### 5-2. `speaker_profiles` — 화자 음성 지문

화자분리 서버가 참조하는 **화자 등록 정보**입니다.

```python
class SpeakerProfile(Base):
    id                  # 프로필 고유 번호
    user_id             # 어느 유저의 프로필인지
    workspace_id        # 어느 워크스페이스 소속인지
    voice_model_path    # 음성 모델 파일 경로 (S3 등)
    diarization_method  # "stereo" | "diarization"
    is_verified         # 등록 완료 여부
```

---

### 5-3. `meeting_participants` — 참석자

```python
class MeetingParticipant(Base):
    meeting_id    # 어느 회의인지
    user_id       # 참석자 user_id
    speaker_label # 화자분리 서버의 speaker_id와 매핑 (예: "spk_001")
    is_host       # 호스트 여부
```

> `speaker_label`이 Redis의 `speaker_id`와 **연결 고리**입니다.  
> 화자분리 서버가 "spk_001"로 발화를 기록하면, 이 테이블에서 `speaker_label = "spk_001"`인 참석자를 찾아 이름을 가져옵니다.

---

## 6. 화자분리 서버가 해야 할 일 (체크리스트)

### 회의 시작 시
- [ ] PostgreSQL `meetings` 테이블에서 `meeting_id` 확인
- [ ] PostgreSQL `meeting_participants`에서 참석자 목록 + `speaker_label` 조회
- [ ] Redis `meeting:{id}:speakers` 해시에 `{ speaker_label: 이름 }` 저장

### 발화 발생 시 (실시간)
- [ ] STT 결과를 아래 포맷으로 직렬화
  ```json
  { "speaker_id": "spk_001", "content": "...", "timestamp": "ISO8601" }
  ```
- [ ] Redis `RPUSH meeting:{id}:utterances <JSON문자열>` 실행
- [ ] `speaker_id`를 모르는 경우 키를 **생략**하고 `content`와 `timestamp`만 저장

### 회의 종료 시
- [ ] PostgreSQL `meetings` 테이블의 `status`를 `"done"`, `ended_at`을 현재 시각으로 업데이트

---

## 7. 화자 이름 결정 로직 (`_resolve_speaker`)

화자분리 서버가 저장한 `speaker_id`를 **표시 이름으로 변환**하는 로직입니다.  
코드 위치: `app/utils/redis_utils.py`

```
speaker_id 값          |  speakers 해시에 있음?  |  최종 표시 이름
───────────────────────|─────────────────────────|──────────────────
None / 키 없음          |  -                      |  "알 수 없음"
"spk_001"              |  있음 (박지수)           |  "박지수"
"spk_003"              |  없음                   |  "화자1" (첫 번째 미매핑 화자)
"spk_004"              |  없음                   |  "화자2" (두 번째 미매핑 화자)
```

> 동일한 `speaker_id`는 항상 같은 번호의 "화자N"이 됩니다.  
> (루프 전체에서 `anon_map` 딕셔너리를 공유하기 때문)

---

## 8. 테스트 방법

### 더미 데이터 삽입

```bash
# 기본 실행 (meeting_id = test-001)
python scripts/seed_dummy.py

# meeting_id 지정
python scripts/seed_dummy.py --meeting-id my-meeting-123

# 기존 데이터 삭제 후 재삽입
python scripts/seed_dummy.py --flush
```

삽입되는 더미 데이터:
- Redis: 발화 10건 (정상 화자, 이름 미등록 화자, speaker_id 없는 화자 포함)
- MongoDB: 이전 회의 요약 1건

### API 테스트 (서버 실행 후 `/docs` 접속)

```
POST /api/v1/knowledge/meetings/{meeting_id}/chatbot/summary
POST /api/v1/knowledge/meetings/{meeting_id}/chatbot/message
```

---

## 9. Redis 키 전체 목록 요약

| 키 패턴 | 자료구조 | 쓰는 곳 | 읽는 곳 | TTL |
|---|---|---|---|---|
| `meeting:{id}:utterances` | List | 화자분리 서버 | AI 요약, 챗봇 | 24시간 |
| `meeting:{id}:speakers` | Hash | 화자분리 서버 | AI 요약, 챗봇 | 24시간 |
| `meeting:{id}:partial_summary` | String | AI 요약 노드 | AI 요약 노드 | 1시간 |

---

## 10. 자주 하는 실수

| 실수 | 올바른 방법 |
|---|---|
| `speaker_id`가 없을 때 `"unknown"` 문자열 저장 | 키 자체를 생략 (`content`, `timestamp`만 저장) |
| Redis에 JSON이 아닌 Python 객체 저장 | 반드시 `json.dumps()` 후 저장 |
| 발화마다 `speakers` 해시를 새로 덮어씀 | 회의 시작 시 한 번만 `HSET`, 참석자 추가 시 `HSET` 추가 |
| TTL 설정 누락 | `EXPIRE meeting:{id}:utterances 86400` 필수 |
| MongoDB `$text` 검색 인덱스 없이 `find` 사용 | `summary_text` 인덱스 생성 후 사용 |
