from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.models.alert import AlertStatus, AlertChannel


class AlertCreate(BaseModel):
    workflow_id: Optional[int] = None
    execution_id: Optional[int] = None
    title: str
    message: str
    severity: str = "info"
    channel: AlertChannel
    recipient: str
    payload: Optional[Dict[str, Any]] = None


class AlertResponse(BaseModel):
    id: int
    alert_id: str
    workflow_id: Optional[int] = None
    execution_id: Optional[int] = None
    title: str
    message: str
    severity: str
    channel: AlertChannel
    recipient: str
    status: AlertStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int
    total_pages: int