import os
import streamlit as st
from dotenv import load_dotenv
import requests

load_dotenv()
API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="육아 도우미", page_icon="👶")
st.title("👶 Care Log")
baby_id = st.text_input("아기 ID", "baby-001")
log_type = st.selectbox("기록 종류", ["feeding", "sleep", "diaper", "growth"])
recorded_at = st.text_input("기록 시간 (ISO 형식)", "2026-08-31T09:00:00+09:00")
details = st.text_area("상세 내용 (JSON)", '{"amount_ml": 160}')

if st.button("기록 저장"):
    try:
        response = requests.post(f"{API_URL}/api/logs/{log_type}", json={"baby_id": baby_id, "recorded_at": recorded_at, "details": __import__("json").loads(details)}, timeout=20)
        response.raise_for_status(); st.success(response.json()["message"])
    except Exception as error: st.error(str(error))

left, right = st.columns(2)
if left.button("오늘 기록 조회"):
    st.json(requests.get(f"{API_URL}/api/logs/today/{baby_id}", timeout=20).json())
if right.button("AI 패턴 요약"):
    st.write(requests.get(f"{API_URL}/api/pattern/{baby_id}", timeout=60).json().get("summary"))
