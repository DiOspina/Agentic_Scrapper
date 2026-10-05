from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.models.agent_log import AgentType, LogLevel


class AgentLogResponse(BaseModel):
    id: int
    execution_id: int
    agent_type: AgentType
    level: LogLevel
    message: str
    details: Optional[Dict[str, Any]] = None
    step_name: Optional[str] = None
    tool_name: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentLogListResponse(BaseModel):
    logs: List[AgentLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int