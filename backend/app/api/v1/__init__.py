"""
API v1 router.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    executions,
    documents,
    workflows,
    agents,
    chat,
    metrics,
    health,
    n8n,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(n8n.router, prefix="/n8n", tags=["n8n"])