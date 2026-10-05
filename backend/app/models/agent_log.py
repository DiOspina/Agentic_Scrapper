import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Enum, Index, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class AgentType(str, enum.Enum):
    SCRAPER = "scraper"
    ANALYST = "analyst"
    SYNTHESIZER = "synthesizer"
    ORCHESTRATOR = "orchestrator"


class LogLevel(str, enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_type: Mapped[AgentType] = mapped_column(Enum(AgentType), nullable=False, index=True)
    level: Mapped[LogLevel] = mapped_column(Enum(LogLevel), default=LogLevel.INFO, nullable=False)

    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Context
    step_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tool_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Performance
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Relationships
    execution: Mapped["Execution"] = relationship("Execution", back_populates="logs")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_agent_logs_execution_agent", "execution_id", "agent_type"),
        Index("ix_agent_logs_level_created", "level", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AgentLog(id={self.id}, execution_id={self.execution_id}, agent='{self.agent_type}', level='{self.level}')>"