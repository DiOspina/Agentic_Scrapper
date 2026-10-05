from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.models.metric import MetricType


class MetricCreate(BaseModel):
    execution_id: int
    name: str
    metric_type: MetricType = MetricType.CUSTOM
    value: float
    unit: Optional[str] = None
    labels: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    agent_type: Optional[str] = None
    step_name: Optional[str] = None


class MetricResponse(BaseModel):
    id: int
    execution_id: int
    name: str
    metric_type: MetricType
    value: float
    unit: Optional[str] = None
    labels: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    agent_type: Optional[str] = None
    step_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MetricListResponse(BaseModel):
    metrics: List[MetricResponse]
    total: int
    page: int
    page_size: int
    total_pages: int