import json
import os
from datetime import date

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5433/care_log")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

app = FastAPI(title="Care Log API")

class CareLogIn(BaseModel):
    baby_id: str
    recorded_at: str
    details: dict = Field(default_factory=dict)

def connect():
    return psycopg.connect(DATABASE_URL)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/logs/{log_type}")
def record_log(log_type: str, payload: CareLogIn):
    if log_type not in {"feeding", "sleep", "diaper", "growth"}:
        raise HTTPException(404, "Unsupported log type")
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO care_logs (baby_id, log_type, recorded_at, details) VALUES (%s, %s, %s, %s) RETURNING id",
            (payload.baby_id, log_type, payload.recorded_at, json.dumps(payload.details)),
        )
        log_id = cur.fetchone()[0]
    return {"id": log_id, "message": "기록이 저장되었습니다."}

@app.get("/api/logs/today/{baby_id}")
def today_logs(baby_id: str):
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, log_type, recorded_at, details FROM care_logs WHERE baby_id=%s AND recorded_at::date=%s ORDER BY recorded_at", (baby_id, date.today()))
        rows = cur.fetchall()
    return {"date": str(date.today()), "logs": [{"id": r[0], "type": r[1], "recorded_at": r[2].isoformat(), "details": r[3]} for r in rows]}

@app.get("/api/pattern/{baby_id}")
def care_pattern(baby_id: str):
    logs = today_logs(baby_id)["logs"]
    if not os.getenv("OPENAI_API_KEY"):
        return {"summary": "OPENAI_API_KEY를 설정하면 AI 돌봄 요약을 생성합니다.", "logs": logs}
    response = OpenAI().responses.create(
        model=OPENAI_MODEL,
        instructions="당신은 육아 기록 요약 도우미입니다. 진단이나 의료 조언은 하지 말고, 기록된 사실만 한국어로 간결히 정리하세요.",
        input=json.dumps(logs, ensure_ascii=False),
        store=False,
    )
    return {"summary": response.output_text, "logs": logs}
