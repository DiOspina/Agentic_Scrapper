"""
n8n integration endpoints.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.database import get_db
from app.services.n8n_client import N8nClient, N8nWebhookHandler, WORKFLOW_TEMPLATES
from app.models.workflow import Workflow
from app.models.execution import Execution, ExecutionStatus
from app.models.alert import Alert, AlertStatus, AlertChannel
from app.services.metrics import get_metrics_service
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()

n8n_client = N8nClient()
webhook_handler = N8nWebhookHandler()


class WebhookPayload(BaseModel):
    event_type: str
    payload: Dict[str, Any]


@router.post("/webhook/{webhook_path}")
async def receive_webhook(
    webhook_path: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Receive webhook from n8n."""
    payload = await request.json()

    logger.info("Webhook received", path=webhook_path, payload_keys=list(payload.keys()))

    # Handle based on webhook path
    if webhook_path == "execution-complete":
        await handle_execution_complete(payload, db)
    elif webhook_path == "execution-failed":
        await handle_execution_failed(payload, db)
    elif webhook_path == "data-extracted":
        await handle_data_extracted(payload, db)
    elif webhook_path == "alert-trigger":
        await handle_alert_trigger(payload, db)

    # Also process through generic handler
    event_type = payload.get("event_type", webhook_path)
    result = await webhook_handler.handle_webhook(event_type, payload)

    return {"status": "received", "result": result}


async def handle_execution_complete(payload: Dict[str, Any], db: AsyncSession):
    """Handle execution completion webhook."""
    execution_id = payload.get("execution_id")
    if not execution_id:
        return

    result = await db.execute(select(Execution).where(Execution.execution_id == execution_id))
    execution = result.scalar_one_or_none()

    if execution:
        execution.status = ExecutionStatus.COMPLETED
        execution.output_data = payload.get("output_data")
        execution.completed_at = __import__("datetime").datetime.utcnow()
        if execution.started_at:
            execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
        await db.commit()


async def handle_execution_failed(payload: Dict[str, Any], db: AsyncSession):
    """Handle execution failure webhook."""
    execution_id = payload.get("execution_id")
    if not execution_id:
        return

    result = await db.execute(select(Execution).where(Execution.execution_id == execution_id))
    execution = result.scalar_one_or_none()

    if execution:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = payload.get("error", "Unknown error")
        execution.completed_at = __import__("datetime").datetime.utcnow()
        await db.commit()


async def handle_data_extracted(payload: Dict[str, Any], db: AsyncSession):
    """Handle data extraction webhook."""
    # This would create documents from extracted data
    pass


async def handle_alert_trigger(payload: Dict[str, Any], db: AsyncSession):
    """Handle alert trigger webhook."""
    alert = Alert(
        alert_id=__import__("uuid").uuid4().hex,
        workflow_id=payload.get("workflow_id"),
        execution_id=payload.get("execution_id"),
        title=payload.get("title", "Alert"),
        message=payload.get("message", ""),
        severity=payload.get("severity", "info"),
        channel=AlertChannel(payload.get("channel", "webhook")),
        recipient=payload.get("recipient", ""),
        payload=payload,
    )
    db.add(alert)
    await db.commit()


@router.post("/trigger-workflow")
async def trigger_n8n_workflow(
    workflow_id: str,
    data: Optional[Dict[str, Any]] = None,
):
    """Trigger an n8n workflow."""
    try:
        result = await n8n_client.execute_workflow(workflow_id, data=data)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error("Failed to trigger n8n workflow", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-webhook")
async def trigger_webhook(
    webhook_path: str,
    payload: Dict[str, Any],
):
    """Trigger a webhook endpoint in n8n."""
    try:
        result = await n8n_client.trigger_webhook(webhook_path, payload)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error("Failed to trigger webhook", webhook_path=webhook_path, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows")
async def list_n8n_workflows(
    active: Optional[bool] = None,
):
    """List n8n workflows."""
    try:
        workflows = await n8n_client.list_workflows(active=active)
        return {"workflows": workflows}
    except Exception as e:
        logger.error("Failed to list n8n workflows", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}")
async def get_n8n_workflow(
    workflow_id: str,
):
    """Get n8n workflow by ID."""
    try:
        workflow = await n8n_client.get_workflow(workflow_id)
        return workflow
    except Exception as e:
        logger.error("Failed to get n8n workflow", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/import")
async def import_n8n_workflow(
    workflow_json: Dict[str, Any],
):
    """Import workflow from JSON."""
    try:
        workflow = await n8n_client.import_workflow(workflow_json)
        return {"success": True, "workflow": workflow}
    except Exception as e:
        logger.error("Failed to import workflow", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_n8n_templates():
    """List available workflow templates."""
    return {
        "templates": [
            {
                "id": key,
                "name": value["name"],
                "nodes_count": len(value["nodes"]),
            }
            for key, value in WORKFLOW_TEMPLATES.items()
        ]
    }


@router.get("/templates/{template_id}")
async def get_n8n_template(
    template_id: str,
):
    """Get workflow template by ID."""
    if template_id not in WORKFLOW_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    return WORKFLOW_TEMPLATES[template_id]


@router.post("/templates/{template_id}/deploy")
async def deploy_template(
    template_id: str,
    workflow_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Deploy a template as a new workflow."""
    if template_id not in WORKFLOW_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    template = WORKFLOW_TEMPLATES[template_id]

    # Create in n8n
    try:
        n8n_workflow = {
            "name": workflow_name,
            "nodes": template["nodes"],
            "connections": template["connections"],
            "active": False,
            "settings": {},
        }
        created = await n8n_client.create_workflow(n8n_workflow)

        # Create in our DB
        workflow = Workflow(
            workflow_id=__import__("uuid").uuid4().hex,
            n8n_workflow_id=created.get("id"),
            name=workflow_name,
            description=f"Deployed from template: {template_id}",
            status=WorkflowStatus.DRAFT,
            trigger_type=WorkflowTrigger.WEBHOOK,
        )
        db.add(workflow)
        await db.commit()

        return {"success": True, "workflow": created}
    except Exception as e:
        logger.error("Failed to deploy template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions")
async def list_n8n_executions(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
):
    """List n8n executions."""
    try:
        executions = await n8n_client.get_executions(workflow_id=workflow_id, status=status, limit=limit)
        return {"executions": executions}
    except Exception as e:
        logger.error("Failed to list n8n executions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def n8n_health():
    """Check n8n health."""
    healthy = await n8n_client.health_check()
    return {"healthy": healthy, "url": n8n_client.base_url}