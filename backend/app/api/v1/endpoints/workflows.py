"""
Workflow endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.workflow import Workflow, WorkflowStatus, WorkflowTrigger
from app.models.execution import Execution
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse,
    WorkflowExecuteRequest,
)
from app.services.n8n_client import N8nClient, WORKFLOW_TEMPLATES
from app.agents.orchestrator import OrchestratorAgent, PipelineConfig
from app.agents.scraper import ScrapingConfig
from app.agents.analyst import AnalysisConfig
from app.agents.synthesizer import ReportConfig
from app.services.metrics import get_metrics_service
import uuid
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()

n8n_client = N8nClient()


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow."""
    workflow_id = str(uuid.uuid4())

    # Create in n8n if webhook trigger
    n8n_workflow_id = None
    if workflow_data.trigger_type == WorkflowTrigger.WEBHOOK and workflow_data.webhook_path:
        try:
            n8n_workflow = {
                "name": workflow_data.name,
                "nodes": [],
                "connections": {},
                "active": False,
                "settings": {},
            }
            # This would create a proper n8n workflow
            # For now, just store the path
            n8n_workflow_id = workflow_data.webhook_path
        except Exception as e:
            logger.warning("Failed to create n8n workflow", error=str(e))

    workflow = Workflow(
        workflow_id=workflow_id,
        n8n_workflow_id=n8n_workflow_id,
        name=workflow_data.name,
        description=workflow_data.description,
        status=WorkflowStatus.DRAFT,
        trigger_type=workflow_data.trigger_type,
        config=workflow_data.config,
        schedule_cron=workflow_data.schedule_cron,
        webhook_path=workflow_data.webhook_path,
        agents_config=workflow_data.agents_config,
        enabled_agents=workflow_data.enabled_agents,
        notify_on_success=workflow_data.notify_on_success,
        notify_on_failure=workflow_data.notify_on_failure,
        notification_channels=workflow_data.notification_channels,
    )

    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)

    return workflow


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[WorkflowStatus] = None,
    trigger_type: Optional[WorkflowTrigger] = None,
    db: AsyncSession = Depends(get_db),
):
    """List workflows with pagination and filters."""
    query = select(Workflow).order_by(desc(Workflow.created_at))

    if status:
        query = query.where(Workflow.status == status)
    if trigger_type:
        query = query.where(Workflow.trigger_type == trigger_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    workflows = result.scalars().all()

    return WorkflowListResponse(
        workflows=workflows,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/templates")
async def list_templates():
    """List available workflow templates."""
    return {
        "templates": [
            {
                "id": key,
                "name": value["name"],
                "description": f"Template for {key.replace('_', ' ')}",
            }
            for key, value in WORKFLOW_TEMPLATES.items()
        ]
    }


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get workflow by ID."""
    result = await db.execute(select(Workflow).where(Workflow.workflow_id == workflow_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow


@router.post("/{workflow_id}/execute", response_model=dict)
async def execute_workflow(
    workflow_id: str,
    execute_request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Execute a workflow."""
    result = await db.execute(select(Workflow).where(Workflow.workflow_id == workflow_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Create execution record
    execution_id = str(uuid.uuid4())
    execution = Execution(
        execution_id=execution_id,
        execution_type=workflow.agents_config.get("execution_type", "full_pipeline")
        if workflow.agents_config
        else "full_pipeline",
        status=ExecutionStatus.PENDING,
        input_data=execute_request.input_data,
        workflow_id=workflow.id,
    )

    db.add(execution)
    await db.commit()

    # Update workflow stats
    workflow.total_executions += 1
    workflow.last_execution_at = __import__("datetime").datetime.utcnow()
    await db.commit()

    # Run in background
    background_tasks.add_task(
        run_workflow_background,
        execution_id,
        workflow,
        execute_request,
    )

    return {
        "execution_id": execution_id,
        "status": "started",
        "message": "Workflow execution started",
    }


async def run_workflow_background(
    execution_id: str,
    workflow: Workflow,
    execute_request: WorkflowExecuteRequest,
):
    """Run workflow in background."""
    from app.db.database import AsyncSessionLocal
    from app.agents.orchestrator import OrchestratorAgent, PipelineConfig
    from app.services.llm import get_llm
    from app.models.execution import ExecutionStatus
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Update status
        result = await db.execute(select(Execution).where(Execution.execution_id == execution_id))
        execution = result.scalar_one_or_none()
        if execution:
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = __import__("datetime").datetime.utcnow()
            await db.commit()

    try:
        llm = get_llm()

        # Build pipeline config from workflow
        pipeline_config = PipelineConfig(
            scraping_config=ScrapingConfig(**(workflow.agents_config.get("scraper", {}) if workflow.agents_config else {})),
            analysis_config=AnalysisConfig(**(workflow.agents_config.get("analyst", {}) if workflow.agents_config else {})),
            report_config=ReportConfig(**(workflow.agents_config.get("synthesizer", {}) if workflow.agents_config else {})),
            notification_channels=workflow.notification_channels,
        )

        orchestrator = OrchestratorAgent(llm=llm, config=pipeline_config)

        result = await orchestrator.run_pipeline(
            execution_id=execution_id,
            input_data=execute_request.input_data or {},
            workflow_id=workflow.id,
        )

        async with AsyncSessionLocal() as db:
            result_db = await db.execute(select(Execution).where(Execution.execution_id == execution_id))
            execution = result_db.scalar_one_or_none()
            if execution:
                execution.status = ExecutionStatus.COMPLETED if result["success"] else ExecutionStatus.FAILED
                execution.output_data = result
                execution.error_message = "; ".join(result["errors"]) if result["errors"] else None
                execution.completed_at = __import__("datetime").datetime.utcnow()
                if execution.started_at:
                    execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
                await db.commit()

                # Update workflow stats
                workflow_result = await db.execute(select(Workflow).where(Workflow.id == workflow.id))
                wf = workflow_result.scalar_one_or_none()
                if wf:
                    if result["success"]:
                        wf.successful_executions += 1
                    else:
                        wf.failed_executions += 1
                    await db.commit()

    except Exception as e:
        logger.error("Workflow execution failed", execution_id=execution_id, error=str(e))
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Execution).where(Execution.execution_id == execution_id))
            execution = result.scalar_one_or_none()
            if execution:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(e)
                execution.completed_at = __import__("datetime").datetime.utcnow()
                await db.commit()

                workflow_result = await db.execute(select(Workflow).where(Workflow.id == workflow.id))
                wf = workflow_result.scalar_one_or_none()
                if wf:
                    wf.failed_executions += 1
                    await db.commit()


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_update: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update workflow."""
    result = await db.execute(select(Workflow).where(Workflow.workflow_id == workflow_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    update_data = workflow_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)

    # Sync with n8n if active
    if workflow.n8n_workflow_id and "status" in update_data:
        try:
            if update_data["status"] == WorkflowStatus.ACTIVE:
                await n8n_client.activate_workflow(workflow.n8n_workflow_id)
            elif update_data["status"] in [WorkflowStatus.PAUSED, WorkflowStatus.ARCHIVED]:
                await n8n_client.deactivate_workflow(workflow.n8n_workflow_id)
        except Exception as e:
            logger.warning("Failed to sync with n8n", error=str(e))

    await db.commit()
    await db.refresh(workflow)
    return workflow


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a workflow."""
    result = await db.execute(select(Workflow).where(Workflow.workflow_id == workflow_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Delete from n8n
    if workflow.n8n_workflow_id:
        try:
            await n8n_client.delete_workflow(workflow.n8n_workflow_id)
        except Exception as e:
            logger.warning("Failed to delete from n8n", error=str(e))

    await db.delete(workflow)
    await db.commit()

    return {"message": "Workflow deleted successfully"}


@router.get("/{workflow_id}/executions", response_model=List[dict])
async def get_workflow_executions(
    workflow_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get executions for a workflow."""
    result = await db.execute(select(Workflow).where(Workflow.workflow_id == workflow_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    query = select(Execution).where(Execution.workflow_id == workflow.id).order_by(desc(Execution.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    executions = result.scalars().all()

    return [
        {
            "execution_id": e.execution_id,
            "status": e.status.value,
            "started_at": e.started_at,
            "completed_at": e.completed_at,
            "duration_seconds": e.duration_seconds,
        }
        for e in executions
    ]