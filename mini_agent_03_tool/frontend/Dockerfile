FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY . /app

# Compose의 build context가 frontend이므로 UI 의존성을 설치한다.
RUN python -m pip install --upgrade pip && \
    python -m pip install streamlit httpx

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
