"""
Execution endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.execution import Execution, ExecutionStatus, ExecutionType
from app.models.agent_log import AgentLog
from app.models.metric import Metric
from app.schemas.execution import (
    ExecutionCreate,
    ExecutionUpdate,
    ExecutionResponse,
    ExecutionDetailResponse,
    ExecutionListResponse,
)
from app.schemas.agent_log import AgentLogListResponse
from app.schemas.metric import MetricListResponse
from app.agents.orchestrator import OrchestratorAgent, PipelineConfig
from app.agents.scraper import ScrapingConfig
from app.agents.analyst import AnalysisConfig
from app.agents.synthesizer import ReportConfig
from app.services.metrics import get_metrics_service, track_execution
import uuid
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("", response_model=ExecutionResponse, status_code=201)
async def create_execution(
    execution_data: ExecutionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new execution."""
    execution_id = str(uuid.uuid4())

    execution = Execution(
        execution_id=execution_id,
        execution_type=execution_data.execution_type,
        status=ExecutionStatus.PENDING,
        input_data=execution_data.input_data,
        agent_name=execution_data.agent_name,
        workflow_id=execution_data.workflow_id,
        parent_execution_id=execution_data.parent_execution_id,
        max_retries=execution_data.max_retries,
    )

    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # Run in background
    background_tasks.add_task(run_execution_background, execution_id, execution_data)

    logger.info("Execution created", execution_id=execution_id, type=execution_data.execution_type)
    return execution


async def run_execution_background(execution_id: str, execution_data: ExecutionCreate):
    """Run execution in background."""
    from app.db.database import AsyncSessionLocal
    from app.agents.orchestrator import OrchestratorAgent, PipelineConfig
    from app.services.llm import get_llm
    from app.models.execution import ExecutionStatus
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Update status to running
        result = await db.execute(select(Execution).where(Execution.execution_id == execution_id))
        execution = result.scalar_one_or_none()
        if execution:
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = __import__("datetime").datetime.utcnow()
            await db.commit()

    try:
        # Configure pipeline
        llm = get_llm()
        pipeline_config = PipelineConfig(
            scraping_config=ScrapingConfig(**execution_data.input_data.get("scraping_config", {})),
            analysis_config=AnalysisConfig(**execution_data.input_data.get("analysis_config", {})),
            report_config=ReportConfig(**execution_data.input_data.get("report_config", {})),
        )

        orchestrator = OrchestratorAgent(llm=llm, config=pipeline_config)

        result = await orchestrator.run_pipeline(
            execution_id=execution_id,
            input_data=execution_data.input_data,
            workflow_id=execution_data.workflow_id,
        )

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Execution).where(Execution.execution_id == execution_id))
            execution = result.scalar_one_or_none()
            if execution:
                execution.status = ExecutionStatus.COMPLETED if result["success"] else ExecutionStatus.FAILED
                execution.output_data = result
                execution.error_message = "; ".join(result["errors"]) if result["errors"] else None
                execution.completed_at = __import__("datetime").datetime.utcnow()
                if execution.started_at:
                    execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
                await db.commit()

    except Exception as e:
        logger.error("Execution failed", execution_id=execution_id, error=str(e))
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Execution).where(Execution.execution_id == execution_id))
            execution = result.scalar_one_or_none()
            if execution:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(e)
                execution.completed_at = __import__("datetime").datetime.utcnow()
                await db.commit()


@router.get("", response_model=ExecutionListResponse)
async def list_executions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ExecutionStatus] = None,
    execution_type: Optional[ExecutionType] = None,
    workflow_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """List executions with pagination and filters."""
    query = select(Execution).order_by(desc(Execution.created_at))

    if status:
        query = query.where(Execution.status == status)
    if execution_type:
        query = query.where(Execution.execution_type == execution_type)
    if workflow_id:
        query = query.where(Execution.workflow_id == workflow_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    executions = result.scalars().all()

    return ExecutionListResponse(
        executions=executions,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{execution_id}", response_model=ExecutionDetailResponse)
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get execution by ID with logs and metrics."""
    result = await db.execute(
        select(Execution)
        .options(selectinload(Execution.logs), selectinload(Execution.metrics))
        .where(Execution.execution_id == execution_id)
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return execution


@router.get("/{execution_id}/logs", response_model=AgentLogListResponse)
async def get_execution_logs(
    execution_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    level: Optional[str] = None,
    agent_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get logs for an execution."""
    # Verify execution exists
    exec_result = await db.execute(select(Execution).where(Execution.execution_id == execution_id))
    execution = exec_result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    query = select(AgentLog).where(AgentLog.execution_id == execution.id).order_by(AgentLog.created_at)

    if level:
        query = query.where(AgentLog.level == level)
    if agent_type:
        query = query.where(AgentLog.agent_type == agent_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return AgentLogListResponse(
        logs=logs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{execution_id}/metrics", response_model=MetricListResponse)
async def get_execution_metrics(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get metrics for an execution."""
    exec_result = await db.execute(select(Execution).where(Execution.execution_id == execution_id))
    execution = exec_result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    result = await db.execute(
        select(Metric).where(Metric.execution_id == execution.id).order_by(Metric.created_at)
    )
    metrics = result.scalars().all()

    return MetricListResponse(
        metrics=metrics,
        total=len(metrics),
        page=1,
        page_size=len(metrics),
        total_pages=1,
    )


@router.patch("/{execution_id}", response_model=ExecutionResponse)
async def update_execution(
    execution_id: str,
    execution_update: ExecutionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update execution."""
    result = await db.execute(select(Execution).where(Execution.execution_id == execution_id))
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    update_data = execution_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(execution, field, value)

    await db.commit()
    await db.refresh(execution)
    return execution


@router.post("/{execution_id}/cancel", response_model=ExecutionResponse)
async def cancel_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running execution."""
    result = await db.execute(select(Execution).where(Execution.execution_id == execution_id))
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if execution.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="Execution cannot be cancelled")

    execution.status = ExecutionStatus.CANCELLED
    execution.completed_at = __import__("datetime").datetime.utcnow()
    await db.commit()
    await db.refresh(execution)
    return execution