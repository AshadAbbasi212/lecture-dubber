from datetime import datetime, timezone
import uuid
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    job_id: Mapped[str] = mapped_column(String, nullable=False)
    media_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="usage_records")
