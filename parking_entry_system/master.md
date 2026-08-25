# 주차장 차량 출입 시스템 마스터 설계서

## 1. 목표와 범위

`C:\mini_agent\parking_entry_system`에 `mini_agent_03_tool`과 같은 FastAPI + Streamlit 분리 구조의 교육용 주차장 출입 시스템을 만든다.

같은 번호판 이미지와 동일한 차량 조회 Tool을 사용하지만, 의사결정 주체가 다른 두 시스템을 별도 페이지로 제공한다.

1. **Workflow 주차 시스템**: 정해진 1~4단계를 Backend가 항상 같은 순서로 실행한다.
2. **AI Agent 주차 시스템**: AI Agent가 번호판 인식 결과를 해석하고 공용 Tool 호출 여부 및 사용자 안내를 결정한다.

초기 범위는 입차 승인 판단까지다. 실제 차단기·CCTV 장비를 제어하지 않으며, 화면에는 `gate_command: open | keep_closed`라는 시뮬레이션 결과만 표시한다.

## 2. 필수 사용자 흐름

두 페이지 모두 아래의 기본 흐름을 따른다.

```text
1. Streamlit 카메라로 차량 번호판 이미지를 캡처한다.
2. Backend가 Vision/OCR로 차량 번호를 인식·추출한다.
3. 공용 vehicle_lookup Tool이 Docker PostgreSQL의 차량 데이터를 조회한다.
4. 등록·활성 차량이면 Backend가 출입을 승인하고, 아니면 차단기를 닫은 상태로 유지한다.
```

카메라 UI는 `mini_agent_01_llm/frontend/app_pages/09_camera_voice_guide.py` 수준을 따른다.

- `st.camera_input`으로 브라우저 권한을 받은 뒤 사진을 촬영한다.
- 촬영 사진 미리보기, 분석 중 Spinner, 결과·오류 안내를 한 페이지에서 보여 준다.
- 번호판 이미지에 개인정보가 포함될 수 있으므로 이미지와 인식 번호는 요청 처리 목적 외 저장하지 않는다.
- 초기 개발·자동화 테스트에서는 카메라 없이 테스트 이미지 업로드 또는 명시적인 번호판 입력을 허용할 수 있으나, 기본 UX는 카메라 촬영이다.

## 3. 두 시스템의 차이

| 구분 | Workflow 주차 시스템 | AI Agent 주차 시스템 |
|---|---|---|
| 페이지 | `04_workflow_parking_entry.py` | `05_agent_parking_entry.py` |
| 제어 방식 | Backend 코드가 OCR → Tool → 정책 평가를 고정 순서로 실행 | Agent가 OCR 결과의 신뢰도·형식을 보고 Tool 호출 또는 재촬영 요청을 결정 |
| Tool | `vehicle_lookup` 공용 Tool 한 개 | 동일한 `vehicle_lookup` 공용 Tool 한 개 |
| 승인 권한 | Backend 정책 함수만 승인·거절 결정 | Agent는 권고와 설명만 생성하고 최종 승인은 Backend 정책 함수가 결정 |
| Trace | 고정 4단계 상태 | Agent 판단, Tool Call, Tool Result, 최종 정책 결과 |

**보안 원칙:** AI Agent는 차단기 개방을 직접 실행할 수 없다. `vehicle_lookup`은 읽기 전용이며, 최종 `approved` 및 `gate_command`는 서버의 결정적 정책 함수가 생성한다.

## 4. 공용 Tool 계약

두 시스템이 공유하는 Tool은 하나뿐이다.

```text
Tool name: vehicle_lookup
Purpose: PostgreSQL에서 번호판 기준 차량 출입 등록 상태를 읽기 전용으로 조회
```

### 입력

```json
{
  "plate_number": "12가3456"
}
```

- 서버에서 한글·숫자 번호판 형식을 정규화하고 Pydantic으로 검증한다.
- Tool은 OCR이나 이미지 처리를 하지 않는다.
- Tool은 승인·차단기 상태 변경을 하지 않는다.

### 출력

```json
{
  "found": true,
  "plate_number": "12가3456",
  "vehicle_id": "…",
  "owner_label": "홍길동",
  "access_status": "active",
  "access_expires_at": null
}
```

조회 실패도 정상적인 업무 결과로 반환한다.

```json
{
  "found": false,
  "plate_number": "12가3456",
  "access_status": "not_registered"
}
```

## 5. Backend Workflow 명세

### 5.1 1번 시스템: 고정 Workflow

```text
POST /api/parking/workflow/entry
  → 이미지 MIME·크기·시그니처 검증
  → plate_recognition_service.extract_plate(image)
  → 번호판이 없거나 신뢰도 기준 미달이면 재촬영 요청
  → vehicle_lookup(plate_number)
  → evaluate_entry_policy(vehicle_result)
  → 승인/거절 결과와 고정 Trace 반환
```

정책은 다음처럼 결정적이다.

- `found=true`, `access_status=active`, 만료일이 없거나 현재보다 미래: 승인, `gate_command=open`
- 그 외: 거절, `gate_command=keep_closed`
- OCR 실패·번호판 형식 오류: 조회하지 않고 재촬영 요청, `gate_command=keep_closed`

### 5.2 2번 시스템: AI Agent

```text
POST /api/parking/agent/entry
  → 이미지 검증 및 Vision/OCR 번호판 후보 추출
  → parking_entry_agent가 후보·신뢰도·Tool Schema를 받음
  → 번호판이 충분히 명확하면 vehicle_lookup Tool Call 생성
  → 안전 실행기(Allowlist + Pydantic)가 Tool 실행
  → Backend evaluate_entry_policy가 최종 승인/거절 결정
  → Agent가 Tool Result를 바탕으로 사용자 설명과 Trace 생성
```

- OCR 후보가 불명확하면 Agent는 번호판을 추측하거나 Tool을 호출하지 않고 재촬영을 요청한다.
- Tool Call은 최대 1회다. 이 시스템은 다중 Tool Loop를 범위에 포함하지 않는다.
- OpenAI 키가 없는 로컬 환경에서는 결정적 Mock Agent를 제공해 Happy Case를 실행한다.

## 6. 데이터베이스와 Docker

Docker Compose로 PostgreSQL(pgvector 확장 포함)과 Redis를 실행한다.

```text
docker-compose.yml
├─ postgres: pgvector/pgvector 이미지
│  └─ PostgreSQL: 차량 등록 정보, 출입 이벤트
└─ redis: redis 이미지
   └─ OCR 요청 중복 방지, 짧은 TTL의 처리 상태/세션, Rate Limit 보조
```

### PostgreSQL 책임

- `vehicles`: 임의로 삽입한 차량 번호, 소유자 표시명, 활성 여부, 출입 만료일
- `entry_events`: 요청 ID, 인식 번호, 승인 결과, 거절 사유, 생성 시각
- `CREATE EXTENSION vector`: pgvector를 활성화한다. 1차 차량 조회는 정확한 번호판 일치 검색이므로 `vehicles.plate_number`의 unique index를 사용한다.
- pgvector는 1차 승인 판단에 사용하지 않는다. 이후 관리자가 차량 메모·정책 문서를 의미 검색하는 기능을 추가할 때 사용한다.

### Redis 책임

- 동일 이미지 해시의 짧은 TTL 중복 처리 방지
- 요청 상태(`processing`, `completed`, `failed`) 저장
- Redis 장애 시 차량 승인 판단을 임의로 통과시키지 않는다. PostgreSQL 조회가 가능하면 중복 방지 기능만 비활성화하고, 조회 실패 시 출입을 거절한다.

### 초기 데이터

`backend/db/seed.sql` 또는 동등한 seed 스크립트에 테스트용 번호판을 삽입한다. 실제 개인정보나 실제 차량 번호는 사용하지 않는다.

| plate_number | owner_label | access_status | access_expires_at |
|---|---|---|---|
| `12가3456` | `테스트 차량 A` | active | null |
| `34나5678` | `테스트 차량 B` | inactive | null |
| `56다7890` | `테스트 차량 C` | active | 과거 날짜 |

## 7. 목표 디렉터리 구조

```text
parking_entry_system/
├─ master.md
├─ README.md
├─ requirements.txt
├─ .env.example
├─ docker-compose.yml
├─ db/
│  ├─ init.sql
│  └─ seed.sql
├─ frontend/
│  ├─ app.py
│  ├─ app_pages/
│  │  ├─ 01_home.py
│  │  ├─ 02_environment.py
│  │  ├─ 04_workflow_parking_entry.py
│  │  └─ 05_agent_parking_entry.py
│  ├─ clients/parking_client.py
│  └─ core/api_client.py
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ core/config.py
│  │  ├─ routers/parking_router.py
│  │  ├─ schemas/parking.py
│  │  ├─ services/plate_recognition_service.py
│  │  ├─ services/parking_workflow_service.py
│  │  ├─ services/entry_policy_service.py
│  │  ├─ agents/parking_entry_agent.py
│  │  ├─ repositories/vehicle_repository.py
│  │  └─ tools/vehicle_lookup.py
│  └─ tests/
│     ├─ test_vehicle_lookup.py
│     ├─ test_workflow_entry_api.py
│     └─ test_agent_entry_api.py
└─ docs/
   ├─ database.md
   └─ agent-vs-workflow.md
```

## 8. API와 공통 응답

```text
POST /api/parking/workflow/entry
POST /api/parking/agent/entry
GET  /health
```

두 입차 API는 공통 결과 형식을 사용한다.

```json
{
  "system_type": "workflow | agent",
  "request_id": "uuid",
  "recognized_plate_number": "12가3456",
  "recognition_confidence": 0.98,
  "approved": true,
  "gate_command": "open | keep_closed",
  "reason": "등록된 활성 차량입니다.",
  "tool_result": {},
  "trace": []
}
```

## 9. 검증과 완료 기준

자동화 테스트는 실제 카메라·외부 Vision API·Docker 의존 없이 Fake OCR과 테스트 DB를 사용한다.

- 등록·활성 차량: 두 시스템 모두 승인 및 `open`
- 미등록 차량: 두 시스템 모두 거절 및 `keep_closed`
- 비활성·만료 차량: 거절
- OCR 번호판 없음 또는 신뢰도 미달: Tool 호출 없이 재촬영 요청
- Agent: 허용되지 않은 Tool 이름·잘못된 인수는 안전 실행기에서 차단
- Workflow와 Agent: 같은 `vehicle_lookup` 구현을 사용함을 테스트로 보장

1차 완료 조건은 두 Streamlit 페이지가 분리되어 있고, 카메라 입력부터 PostgreSQL 조회와 승인 결과 표시까지 동작하며, 두 시스템이 단 하나의 공용 DB 조회 Tool을 사용하고 실제 차단기 제어 없이 안전하게 시뮬레이션하는 것이다.

## 10. 구현 순서

1. Docker Compose, PostgreSQL 초기 스키마·seed, Redis 연결을 준비한다.
2. `vehicle_lookup` Tool과 Repository를 만든 뒤 DB 조회 단위 테스트를 작성한다.
3. 번호판 이미지 검증·Vision/OCR 추출 서비스를 만든다.
4. 고정 Workflow API와 Workflow 페이지를 구현한다.
5. 동일 Tool Schema를 사용하는 Agent API와 Agent 페이지를 구현한다.
6. 승인 정책·중복 요청·오류 처리를 통합하고 전체 테스트를 실행한다.
