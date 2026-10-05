from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    use_rag: bool = True
    top_k: int = 5
    temperature: float = 0.1
    max_tokens: int = 4000


class ChatResponse(BaseModel):
    message: str
    session_id: str
    sources: List[Dict[str, Any]] = []
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    processing_time_ms: Optional[int] = None


class ChatSessionCreate(BaseModel):
    title: Optional[str] = None
    initial_context: Optional[Dict[str, Any]] = None


class ChatSessionResponse(BaseModel):
    session_id: str
    title: Optional[str] = None
    messages: List[ChatMessage] = []
    context: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime