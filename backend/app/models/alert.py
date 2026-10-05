import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Enum, Index, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class AlertStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    READ = "read"


class AlertChannel(str, enum.Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    alert_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    workflow_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workflows.id"), nullable=True)
    execution_id: Mapped[Optional[int]] = mapped_column(ForeignKey("executions.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)  # info, warning, critical

    channel: Mapped[AlertChannel] = mapped_column(Enum(AlertChannel), nullable=False)
    recipient: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.PENDING, nullable=False)

    # Delivery tracking
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Payload
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    workflow: Mapped[Optional["Workflow"]] = relationship("Workflow", back_populates="alerts")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_alerts_status_channel", "status", "channel"),
        Index("ix_alerts_created_at", "created_at"),
        Index("ix_alerts_workflow_execution", "workflow_id", "execution_id"),
    )

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, alert_id='{self.alert_id}', channel='{self.channel}', status='{self.status}')>"