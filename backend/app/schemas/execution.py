from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.models.execution import ExecutionStatus, ExecutionType


class ExecutionBase(BaseModel):
    execution_type: ExecutionType
    input_data: Optional[Dict[str, Any]] = None
    agent_name: Optional[str] = None
    workflow_id: Optional[int] = None
    parent_execution_id: Optional[int] = None
    max_retries: int = 3


class ExecutionCreate(ExecutionBase):
    pass


class ExecutionUpdate(BaseModel):
    status: Optional[ExecutionStatus] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    retry_count: Optional[int] = None


class ExecutionResponse(BaseModel):
    id: int
    execution_id: str
    execution_type: ExecutionType
    status: ExecutionStatus
    agent_name: Optional[str] = None
    workflow_id: Optional[int] = None
    parent_execution_id: Optional[int] = None
    retry_count: int
    max_retries: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExecutionDetailResponse(ExecutionResponse):
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    logs: List["AgentLogResponse"] = []
    metrics: List["MetricResponse"] = []


class ExecutionListResponse(BaseModel):
    executions: List[ExecutionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Forward references
from app.schemas.agent_log import AgentLogResponse
from app.schemas.metric import MetricResponse

ExecutionDetailResponse.model_rebuild()