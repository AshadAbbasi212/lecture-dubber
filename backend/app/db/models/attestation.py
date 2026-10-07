from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class Attestation(Base):
    __tablename__ = "attestations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    job_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # ownership, voice_consent
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="attestations")
    job = relationship("Job", back_populates="attestations")
