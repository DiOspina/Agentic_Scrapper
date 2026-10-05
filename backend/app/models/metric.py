import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Enum, Index, ForeignKey, JSON, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class MetricType(str, enum.Enum):
    PERFORMANCE = "performance"
    QUALITY = "quality"
    BUSINESS = "business"
    SYSTEM = "system"
    CUSTOM = "custom"


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_type: Mapped[MetricType] = mapped_column(Enum(MetricType), default=MetricType.CUSTOM, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Context
    labels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Source
    agent_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    step_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    execution: Mapped["Execution"] = relationship("Execution", back_populates="metrics")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_metrics_execution_name", "execution_id", "name"),
        Index("ix_metrics_type_created", "metric_type", "created_at"),
        Index("ix_metrics_name_value", "name", "value"),
    )

    def __repr__(self) -> str:
        return f"<Metric(id={self.id}, name='{self.name}', value={self.value}, type='{self.metric_type}')>"