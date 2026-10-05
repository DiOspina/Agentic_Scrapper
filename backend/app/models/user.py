import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, Enum, Index, ForeignKey, JSON, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API_CLIENT = "api_client"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Preferences
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notification_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # API Access
    api_key: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)
    api_key_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    created_workflows: Mapped[list["Workflow"]] = relationship("Workflow", back_populates="created_by")
    uploaded_documents: Mapped[list["Document"]] = relationship("Document", back_populates="uploaded_by")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
        Index("ix_users_role_active", "role", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, user_id='{self.user_id}', email='{self.email}', role='{self.role}')>"