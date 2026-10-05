"""
Chat endpoints for conversational RAG.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.db.database import get_db
from app.services.vector_store import get_vector_store
from app.services.llm import get_llm, get_embeddings
from app.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatSessionCreate,
    ChatSessionResponse,
)
from app.models.document import Document
import uuid
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()

# In-memory session storage (use Redis in production)
chat_sessions: Dict[str, Dict[str, Any]] = {}


class ChatSessionInDB(BaseModel):
    session_id: str
    title: Optional[str] = None
    messages: List[ChatMessage] = []
    context: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    now = __import__("datetime").datetime.utcnow().isoformat()

    session = {
        "session_id": session_id,
        "title": session_data.title or "New Chat",
        "messages": [],
        "context": session_data.initial_context or {},
        "created_at": now,
        "updated_at": now,
    }

    chat_sessions[session_id] = session

    return ChatSessionResponse(**session)


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    limit: int = Query(20, ge=1, le=100),
):
    """List chat sessions."""
    sessions = sorted(
        chat_sessions.values(),
        key=lambda x: x["updated_at"],
        reverse=True,
    )
    return [ChatSessionResponse(**s) for s in sessions[:limit]]


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
):
    """Get chat session by ID."""
    session = chat_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return ChatSessionResponse(**session)


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
):
    """Delete a chat session."""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del chat_sessions[session_id]
    return {"message": "Session deleted"}


@router.post("/sessions/{session_id}/message", response_model=ChatResponse)
async def send_message(
    session_id: str,
    request: ChatRequest,
):
    """Send a message in a chat session."""
    session = chat_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Add user message
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=__import__("datetime").datetime.utcnow(),
    )
    session["messages"].append(user_message)

    # Get relevant context from vector store if RAG enabled
    sources = []
    context_text = ""

    if request.use_rag:
        try:
            vector_store = get_vector_store()
            results = await vector_store.similarity_search_with_score(
                request.message,
                k=request.top_k,
                score_threshold=0.7,
            )

            context_parts = []
            for doc, score in results:
                context_parts.append(doc.page_content)
                sources.append({
                    "content": doc.page_content[:200],
                    "metadata": doc.metadata,
                    "score": score,
                })

            context_text = "\n\n---\n\n".join(context_parts)
        except Exception as e:
            logger.warning("RAG search failed", error=str(e))

    # Build prompt
    system_prompt = """You are an AI assistant for the Agenttic platform. 
Answer questions based on the provided context. 
If the answer cannot be found in the context, say so clearly.
Be concise and helpful."""

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # Add context if available
    if context_text:
        messages.append({
            "role": "system",
            "content": f"Context:\n{context_text}"
        })

    # Add conversation history (last 10 messages)
    for msg in session["messages"][-10:]:
        messages.append({"role": msg.role, "content": msg.content})

    # Call LLM
    llm = get_llm()
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

    lc_messages = []
    for m in messages:
        if m["role"] == "system":
            lc_messages.append(SystemMessage(content=m["content"]))
        elif m["role"] == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_messages.append(AIMessage(content=m["content"]))

    start_time = __import__("time").time()
    response = await llm.ainvoke(
        lc_messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    processing_time_ms = int((__import__("time").time() - start_time) * 1000)

    # Add assistant message
    assistant_message = ChatMessage(
        role="assistant",
        content=response.content,
        timestamp=__import__("datetime").datetime.utcnow(),
        metadata={
            "sources": sources,
            "tokens_used": response.usage_metadata.get("total_tokens") if hasattr(response, "usage_metadata") else None,
        },
    )
    session["messages"].append(assistant_message)
    session["updated_at"] = __import__("datetime").datetime.utcnow().isoformat()

    return ChatResponse(
        message=response.content,
        session_id=session_id,
        sources=sources,
        tokens_used=assistant_message.metadata.get("tokens_used"),
        processing_time_ms=processing_time_ms,
    )


@router.post("/query", response_model=ChatResponse)
async def query_without_session(
    request: ChatRequest,
):
    """Query without creating a session (stateless)."""
    # Get relevant context from vector store if RAG enabled
    sources = []
    context_text = ""

    if request.use_rag:
        try:
            vector_store = get_vector_store()
            results = await vector_store.similarity_search_with_score(
                request.message,
                k=request.top_k,
                score_threshold=0.7,
            )

            context_parts = []
            for doc, score in results:
                context_parts.append(doc.page_content)
                sources.append({
                    "content": doc.page_content[:200],
                    "metadata": doc.metadata,
                    "score": score,
                })

            context_text = "\n\n---\n\n".join(context_parts)
        except Exception as e:
            logger.warning("RAG search failed", error=str(e))

    # Build prompt
    system_prompt = """You are an AI assistant for the Agenttic platform. 
Answer questions based on the provided context. 
If the answer cannot be found in the context, say so clearly.
Be concise and helpful."""

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    if context_text:
        messages.append({
            "role": "system",
            "content": f"Context:\n{context_text}"
        })

    messages.append({"role": "user", "content": request.message})

    # Call LLM
    llm = get_llm()
    from langchain_core.messages import HumanMessage, SystemMessage

    lc_messages = [SystemMessage(content=m["content"]) if m["role"] == "system" else HumanMessage(content=m["content"]) for m in messages]

    start_time = __import__("time").time()
    response = await llm.ainvoke(
        lc_messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    processing_time_ms = int((__import__("time").time() - start_time) * 1000)

    return ChatResponse(
        message=response.content,
        session_id="stateless",
        sources=sources,
        tokens_used=response.usage_metadata.get("total_tokens") if hasattr(response, "usage_metadata") else None,
        processing_time_ms=processing_time_ms,
    )