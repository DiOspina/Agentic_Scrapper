import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, Enum, Index, ForeignKey, JSON, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class WorkflowStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class WorkflowTrigger(str, enum.Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    EVENT = "event"
    FILE_UPLOAD = "file_upload"


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workflow_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    n8n_workflow_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[WorkflowStatus] = mapped_column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT, nullable=False)
    trigger_type: Mapped[WorkflowTrigger] = mapped_column(Enum(WorkflowTrigger), default=WorkflowTrigger.MANUAL, nullable=False)

    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    schedule_cron: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    webhook_path: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Agent Configuration
    agents_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    enabled_agents: Mapped[List[str]] = mapped_column(JSON, default=["scraper", "analyst", "synthesizer"])

    # Notifications
    notify_on_success: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_on_failure: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_channels: Mapped[List[str]] = mapped_column(JSON, default=[])

    # Stats
    total_executions: Mapped[int] = mapped_column(Integer, default=0)
    successful_executions: Mapped[int] = mapped_column(Integer, default=0)
    failed_executions: Mapped[int] = mapped_column(Integer, default=0)
    last_execution_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    executions: Mapped[list["Execution"]] = relationship("Execution", back_populates="workflow")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="workflow", cascade="all, delete-orphan")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        Index("ix_workflows_status_trigger", "status", "trigger_type"),
        Index("ix_workflows_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, workflow_id='{self.workflow_id}', name='{self.name}', status='{self.status}')>"