# Care Log MCP Server

육아 도우미 Agent가 아기의 일상 기록을 저장하고 조회할 수 있도록 제공하는 PostgreSQL 기반 MCP 서버입니다. 이 서버는 **Streamable HTTP** 전송 방식을 사용하며, MCP Client는 HTTP 엔드포인트로 연결합니다.

수유, 수면, 기저귀, 성장 기록을 관리하며 오늘의 기록과 누적 기록을 바탕으로 돌봄 패턴을 조회합니다.

## MCP Tools

| Tool | 설명 |
| --- | --- |
| `record_feeding` | 수유 시간, 수유량, 수유 방식을 기록합니다. |
| `record_sleep` | 수면 시작·종료 시간과 수면 상태를 기록합니다. |
| `record_diaper` | 기저귀 교체 시간과 상태를 기록합니다. |
| `record_growth` | 키, 몸무게, 머리둘레 등 성장 정보를 기록합니다. |
| `get_today_logs` | 오늘 등록된 수유·수면·기저귀·성장 기록을 조회합니다. |
| `get_care_pattern` | 기간별 기록을 바탕으로 수유·수면·배변 패턴을 조회합니다. |

## 디렉터리 구조

```text
care-log-mcp-server/
├─ app/
│  ├─ care_log_server.py              # MCP 서버 생성·실행, 6개 Tool 등록
│  │
│  ├─ tools/
│  │  ├─ record_feeding.py            # record_feeding Tool
│  │  ├─ record_sleep.py              # record_sleep Tool
│  │  ├─ record_diaper.py             # record_diaper Tool
│  │  ├─ record_growth.py             # record_growth Tool
│  │  ├─ get_today_logs.py            # get_today_logs Tool
│  │  └─ get_care_pattern.py          # get_care_pattern Tool
│  │
│  ├─ services/
│  │  ├─ feeding_service.py           # 수유 기록 등록·조회
│  │  ├─ sleep_service.py             # 수면 기록 등록·조회
│  │  ├─ diaper_service.py            # 기저귀 기록 등록·조회
│  │  ├─ growth_service.py            # 성장 기록 등록·조회
│  │  ├─ today_log_service.py         # 오늘의 전체 기록 통합 조회
│  │  └─ care_pattern_service.py      # 수유·수면·배변 패턴 계산
│  │
│  ├─ clients/
│  │  └─ postgres_client.py           # PostgreSQL 연결 생성·관리
│  │
│  ├─ schemas/
│  │  ├─ requests.py                  # Tool 입력 Pydantic 모델
│  │  ├─ responses.py                 # Tool 공통 응답 모델
│  │  └─ care_log.py                  # 수유·수면·기저귀·성장 기록 모델
│  │
│  ├─ repositories/
│  │  ├─ feeding_repository.py        # feeding_logs SQL 실행
│  │  ├─ sleep_repository.py          # sleep_logs SQL 실행
│  │  ├─ diaper_repository.py         # diaper_logs SQL 실행
│  │  ├─ growth_repository.py         # growth_logs SQL 실행
│  │  └─ care_log_repository.py       # 오늘 기록 통합 조회 SQL
│  │
│  ├─ db/
│  │  ├─ init/
│  │  │  └─ 001_create_care_logs.sql  # 테이블·인덱스 생성 SQL
│  │  └─ seed/
│  │     └─ 001_sample_care_logs.sql  # 개발·테스트용 예시 데이터
│  │
│  └─ tests/
│     ├─ fixtures/                    # 테스트용 요청·응답 데이터
│     ├─ test_feeding_service.py
│     ├─ test_sleep_service.py
│     ├─ test_diaper_service.py
│     ├─ test_growth_service.py
│     ├─ test_today_log_service.py
│     ├─ test_care_pattern_service.py
│     ├─ test_repositories.py
│     └─ test_care_log_server.py
│
├─ .env.example
├─ docker-compose.yml
├─ Dockerfile
├─ requirements.txt
└─ README.md
```

## 처리 흐름

```text
육아 도우미 Agent
    ↓
MCP Tool (app/tools)
    ↓
Service (app/services)
    ↓
Repository (app/repositories)
    ↓
PostgreSQL
```

각 Tool 파일은 하나의 MCP 기능만 정의합니다. 예를 들어 `record_feeding.py`는 `record_feeding` Tool을 등록하고, `feeding_service.py`를 호출합니다. 서비스는 입력값을 검증한 뒤 `feeding_repository.py`를 통해 PostgreSQL에 수유 기록을 저장합니다.

`care_log_server.py`는 Tool 구현을 직접 포함하지 않고, 각 Tool 파일의 등록 함수를 호출해 MCP 서버에 등록합니다.

```text
care_log_server.py
  ├─ register_record_feeding_tool(mcp)
  ├─ register_record_sleep_tool(mcp)
  ├─ register_record_diaper_tool(mcp)
  ├─ register_record_growth_tool(mcp)
  ├─ register_get_today_logs_tool(mcp)
  └─ register_get_care_pattern_tool(mcp)
```

## MCP 전송 방식: Streamable HTTP

이 서버의 기본 전송 방식은 Streamable HTTP입니다. FastMCP에서는 `transport="http"`가 Streamable HTTP를 의미합니다. 기존 MCP Client 호환이 필요한 경우에는 SSE도 선택할 수 있습니다.

구현 시 `app/care_log_server.py`의 실행부는 아래 형태로 작성합니다.

```python
import os

if __name__ == "__main__":
    mcp.run(
        transport=os.getenv("MCP_TRANSPORT", "http"),
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("MCP_PORT", "8000")),
    )
```

구현과 실행이 완료되면 MCP Client가 연결할 기본 엔드포인트는 다음과 같습니다.

```text
http://127.0.0.1:8000/mcp
```

로컬 외부 Docker 컨테이너 또는 다른 호스트에서도 접속해야 하면 `MCP_HOST=0.0.0.0`으로 실행합니다. 운영 환경에서는 인증과 HTTPS를 별도로 구성합니다.

### SSE 선택 지원

SSE는 이전 MCP 웹 전송 방식입니다. 이 서버는 기본값으로 Streamable HTTP를 사용하지만, SSE만 지원하는 Client와 연동해야 한다면 `.env`에서 전송 방식을 변경할 수 있습니다.

```env
MCP_TRANSPORT=sse
```

SSE로 실행했을 때 MCP Client는 다음 엔드포인트로 연결합니다.

```text
http://127.0.0.1:8000/sse
```

`MCP_TRANSPORT=http`은 Streamable HTTP(`/mcp`)를, `MCP_TRANSPORT=sse`는 SSE(`/sse`)를 사용합니다. 한 번의 서버 실행에서는 둘 중 하나만 선택합니다.

## 역할 구분

| 위치 | 역할 |
| --- | --- |
| `app/tools/` | MCP Client가 호출하는 Tool을 기능별로 정의합니다. |
| `app/services/` | 입력 검증, 기록 처리, 패턴 계산 등 업무 로직을 처리합니다. |
| `app/schemas/` | Tool 입력과 응답의 데이터 형식을 Pydantic 모델로 정의합니다. |
| `app/repositories/` | PostgreSQL에 `INSERT`, `SELECT` 등의 SQL을 실행합니다. |
| `app/clients/postgres_client.py` | PostgreSQL 연결을 생성·관리합니다. |
| `app/db/init/` | 테이블과 인덱스를 생성하는 SQL을 관리합니다. |
| `app/db/seed/` | 로컬 개발·테스트에 필요한 예시 데이터를 관리합니다. |

## 실행 환경

- Python 3.11 이상
- PostgreSQL
- psycopg
- FastMCP 2.3 이상, 3.0 미만 (Streamable HTTP 및 SSE 사용)

## 생성 후 작성 순서

1. `app/db/init/001_create_care_logs.sql`에 PostgreSQL 테이블과 인덱스를 정의합니다.
2. `app/clients/postgres_client.py`에 PostgreSQL 연결 코드를 작성합니다.
3. `app/schemas/`에 Tool 입력·응답 Pydantic 모델을 정의합니다.
4. `app/repositories/`에 각 테이블의 SQL 실행 함수를 작성합니다.
5. `app/services/`에 입력 검증과 돌봄 기록 처리 로직을 작성합니다.
6. `app/tools/`에 Tool별 등록 함수를 작성합니다.
7. `app/care_log_server.py`에서 6개 Tool 등록 함수를 불러와 MCP 서버에 등록합니다.
8. `app/tests/`에 Service, Repository, Tool 테스트를 작성합니다.

## 필수 파일 책임

| 파일 또는 폴더 | 반드시 포함할 내용 |
| --- | --- |
| `app/care_log_server.py` | FastMCP 인스턴스 생성, 6개 Tool 등록, 서버 실행 |
| `app/tools/*.py` | Tool 하나와 해당 Tool의 등록 함수 하나 |
| `app/schemas/requests.py` | Tool별 입력 Pydantic 모델 |
| `app/schemas/responses.py` | 공통 성공·실패 응답 모델 |
| `app/services/*.py` | 입력 검증과 업무 처리 로직 |
| `app/repositories/*.py` | PostgreSQL `INSERT`, `SELECT`, `UPDATE` SQL 실행 함수 |
| `app/clients/postgres_client.py` | 환경 변수 기반 PostgreSQL 연결 함수 |
| `app/db/init/001_create_care_logs.sql` | `feeding_logs`, `sleep_logs`, `diaper_logs`, `growth_logs` 테이블 생성 |
| `app/db/seed/001_sample_care_logs.sql` | 선택: 로컬 테스트용 예시 기록 |

## 의존성 기준

`requirements.txt`에는 최소한 아래 패키지를 포함합니다.

```text
fastmcp>=2.3,<3.0
psycopg[binary]>=3.2
pydantic>=2.0
python-dotenv>=1.0
```


## 환경 변수

`.env.example`을 복사하여 `.env` 파일을 만든 뒤 PostgreSQL 정보를 설정합니다.

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
POSTGRES_DB=care_log
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
MCP_TRANSPORT=http
MCP_HOST=127.0.0.1
MCP_PORT=8000
```

## 구현 상태

현재는 서버 구조와 구현 기준을 정의하는 단계이며, 백엔드 코드와 프런트엔드 파일은 아직 생성되지 않았습니다. 따라서 현재 실행할 명령은 없습니다.

구현 완료 후 `app/care_log_server.py`를 Streamable HTTP 방식으로 실행하고, MCP Client는 앞서 정의한 `http://127.0.0.1:8000/mcp` 엔드포인트에 연결합니다.

## 참고

이 서버는 기록과 조회를 담당합니다. 의료적 판단, 진단, 응급 상황 대응은 `child_healthcare_server`와 같은 별도 서버에서 처리합니다.
