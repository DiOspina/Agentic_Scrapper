import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Enum, Index, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionType(str, enum.Enum):
    SCRAPING = "scraping"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    FULL_PIPELINE = "full_pipeline"


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    execution_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    execution_type: Mapped[ExecutionType] = mapped_column(Enum(ExecutionType), nullable=False)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False)

    # Input/Output
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    workflow_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workflows.id"), nullable=True)
    parent_execution_id: Mapped[Optional[int]] = mapped_column(ForeignKey("executions.id"), nullable=True)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Retry
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    # Relationships
    workflow: Mapped[Optional["Workflow"]] = relationship("Workflow", back_populates="executions")
    parent_execution: Mapped[Optional["Execution"]] = relationship("Execution", remote_side=[id], back_populates="child_executions")
    child_executions: Mapped[list["Execution"]] = relationship("Execution", back_populates="parent_execution")
    logs: Mapped[list["AgentLog"]] = relationship("AgentLog", back_populates="execution", cascade="all, delete-orphan")
    metrics: Mapped[list["Metric"]] = relationship("Metric", back_populates="execution", cascade="all, delete-orphan")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_executions_execution_type_status", "execution_type", "status"),
        Index("ix_executions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Execution(id={self.id}, execution_id='{self.execution_id}', type='{self.execution_type}', status='{self.status}')>"