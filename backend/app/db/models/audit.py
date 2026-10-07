from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
