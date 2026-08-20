from fastapi import FastAPI

from app.routers.agent_router import agent_router


app = FastAPI(title="Mini Agent 03 · Tool Use")
app.openapi_tags = [
    {"name": "01. LLM", "description": "LLM calls, provider comparison, and prompt APIs."},
    {"name": "02. Structured Output", "description": "Structured output and media APIs."},
    {"name": "03. Tool Use", "description": "Tool selection, execution, and agent-loop APIs."},
]
app.include_router(agent_router)
