FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY . /app

# Compose의 build context가 backend이므로 필요한 백엔드 의존성을 설치한다.
RUN python -m pip install --upgrade pip && \
    python -m pip install \
        fastapi \
        google-genai \
        httpx \
        openai \
        pydantic \
        python-dotenv \
        python-multipart \
        uvicorn

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
