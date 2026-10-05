from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.models.workflow import WorkflowStatus, WorkflowTrigger


class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    trigger_type: WorkflowTrigger = WorkflowTrigger.MANUAL
    config: Optional[Dict[str, Any]] = None
    schedule_cron: Optional[str] = None
    webhook_path: Optional[str] = None
    agents_config: Optional[Dict[str, Any]] = None
    enabled_agents: List[str] = ["scraper", "analyst", "synthesizer"]
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_channels: List[str] = []


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[WorkflowStatus] = None
    trigger_type: Optional[WorkflowTrigger] = None
    config: Optional[Dict[str, Any]] = None
    schedule_cron: Optional[str] = None
    webhook_path: Optional[str] = None
    agents_config: Optional[Dict[str, Any]] = None
    enabled_agents: Optional[List[str]] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notification_channels: Optional[List[str]] = None


class WorkflowResponse(BaseModel):
    id: int
    workflow_id: str
    n8n_workflow_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    status: WorkflowStatus
    trigger_type: WorkflowTrigger
    config: Optional[Dict[str, Any]] = None
    schedule_cron: Optional[str] = None
    webhook_path: Optional[str] = None
    agents_config: Optional[Dict[str, Any]] = None
    enabled_agents: List[str]
    notify_on_success: bool
    notify_on_failure: bool
    notification_channels: List[str]
    total_executions: int
    successful_executions: int
    failed_executions: int
    last_execution_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class WorkflowExecuteRequest(BaseModel):
    input_data: Optional[Dict[str, Any]] = None
    trigger_type: WorkflowTrigger = WorkflowTrigger.MANUAL
    webhook_payload: Optional[Dict[str, Any]] = None