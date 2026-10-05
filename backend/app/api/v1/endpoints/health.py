"""
Health check endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import httpx
import redis.asyncio as redis

from app.db.database import get_db
from app.core.config import settings
from app.services.vector_store import get_vector_store
from app.schemas.common import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check."""
    services = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        services["database"] = "healthy"
    except Exception as e:
        services["database"] = f"unhealthy: {str(e)}"

    # Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        services["redis"] = "healthy"
    except Exception as e:
        services["redis"] = f"unhealthy: {str(e)}"

    # Vector Store (Qdrant)
    try:
        vector_store = get_vector_store()
        info = await vector_store.get_collection_info()
        services["vector_store"] = "healthy"
    except Exception as e:
        services["vector_store"] = f"unhealthy: {str(e)}"

    # n8n
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.N8N_API_URL}/healthz", timeout=5)
            services["n8n"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        services["n8n"] = f"unhealthy: {str(e)}"

    # Overall status
    all_healthy = all(v == "healthy" for v in services.values())
    status = "healthy" if all_healthy else "degraded"

    return HealthCheckResponse(
        status=status,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        services=services,
        timestamp=__import__("datetime").datetime.utcnow().isoformat(),
    )


@router.get("/health/live")
async def liveness_check():
    """Liveness probe."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness probe."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}, 503