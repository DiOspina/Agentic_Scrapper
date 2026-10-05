"""
Metrics endpoints for monitoring and observability.
"""
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.db.database import get_db
from app.models.execution import Execution, ExecutionStatus
from app.models.metric import Metric, MetricType
from app.models.document import Document, DocumentStatus
from app.services.metrics import get_metrics_service, get_execution_stats
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/prometheus")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    metrics_service = get_metrics_service()
    metrics_service.update_system_metrics()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/summary")
async def metrics_summary():
    """Get metrics summary."""
    metrics_service = get_metrics_service()
    return metrics_service.get_summary()


@router.get("/executions/stats")
async def execution_stats(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get execution statistics."""
    return await get_execution_stats(db, days)


@router.get("/executions/by-status")
async def executions_by_status(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get execution counts by status."""
    from datetime import datetime, timedelta

    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(Execution.status, func.count(Execution.id))
        .where(Execution.created_at >= since)
        .group_by(Execution.status)
    )

    return {
        "period_days": days,
        "data": [
            {"status": row[0].value, "count": row[1]}
            for row in result.all()
        ],
    }


@router.get("/executions/by-type")
async def executions_by_type(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get execution counts by type."""
    from datetime import datetime, timedelta

    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(Execution.execution_type, func.count(Execution.id))
        .where(Execution.created_at >= since)
        .group_by(Execution.execution_type)
    )

    return {
        "period_days": days,
        "data": [
            {"type": row[0].value, "count": row[1]}
            for row in result.all()
        ],
    }


@router.get("/executions/duration-trend")
async def execution_duration_trend(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get execution duration trend over time."""
    from datetime import datetime, timedelta

    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(Execution.created_at).label("date"),
            func.avg(Execution.duration_seconds).label("avg_duration"),
            func.count(Execution.id).label("count"),
        )
        .where(Execution.created_at >= since, Execution.duration_seconds.isnot(None))
        .group_by(func.date(Execution.created_at))
        .order_by(func.date(Execution.created_at))
    )

    return {
        "period_days": days,
        "data": [
            {
                "date": row[0].isoformat() if row[0] else None,
                "avg_duration_seconds": float(row[1]) if row[1] else 0,
                "count": row[2],
            }
            for row in result.all()
        ],
    }


@router.get("/agents/performance")
async def agent_performance():
    """Get agent performance metrics."""
    metrics_service = get_metrics_service()
    summary = metrics_service.get_summary()

    return {
        "agents": summary.get("agents", {}),
    }


@router.get("/documents/stats")
async def document_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get document statistics."""
    # Total documents
    total_result = await db.execute(select(func.count(Document.id)))
    total = total_result.scalar()

    # By status
    status_result = await db.execute(
        select(Document.status, func.count(Document.id))
        .group_by(Document.status)
    )
    by_status = {row[0].value: row[1] for row in status_result.all()}

    # By type
    type_result = await db.execute(
        select(Document.document_type, func.count(Document.id))
        .group_by(Document.document_type)
    )
    by_type = {row[0].value: row[1] for row in type_result.all()}

    # Total size
    size_result = await db.execute(select(func.sum(Document.file_size)))
    total_size = size_result.scalar() or 0

    # Total chunks
    chunks_result = await db.execute(select(func.sum(Document.chunk_count)))
    total_chunks = chunks_result.scalar() or 0

    return {
        "total_documents": total,
        "by_status": by_status,
        "by_type": by_type,
        "total_size_bytes": total_size,
        "total_chunks": total_chunks,
    }


@router.get("/vector-store/stats")
async def vector_store_stats():
    """Get vector store statistics."""
    from app.services.vector_store import get_vector_store

    try:
        vector_store = get_vector_store()
        info = await vector_store.get_collection_info()
        return info
    except Exception as e:
        logger.error("Failed to get vector store stats", error=str(e))
        return {"error": str(e)}


@router.get("/system")
async def system_metrics():
    """Get system metrics."""
    import psutil

    return {
        "cpu": {
            "percent": psutil.cpu_percent(interval=0.1),
            "count": psutil.cpu_count(),
        },
        "memory": {
            "percent": psutil.virtual_memory().percent,
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        },
        "disk": {
            "percent": psutil.disk_usage("/").percent,
            "total_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
            "free_gb": round(psutil.disk_usage("/").free / (1024**3), 2),
        },
        "network": {
            "bytes_sent": psutil.net_io_counters().bytes_sent,
            "bytes_recv": psutil.net_io_counters().bytes_recv,
        },
    }