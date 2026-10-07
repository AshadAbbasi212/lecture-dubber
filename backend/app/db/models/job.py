from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String, index=True, default="queued", nullable=False)
    stage: Mapped[str] = mapped_column(String, default="ingesting", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)  # upload, url, youtube
    source_ref: Mapped[str] = mapped_column(String, nullable=False)   # upload_id or url
    source_lang: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_lang: Mapped[str] = mapped_column(String, nullable=False)  # en, ur
    options_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="jobs")
    segments = relationship("Segment", back_populates="job", cascade="all, delete-orphan", order_by="Segment.idx")
    artifacts = relationship("Artifact", back_populates="job", cascade="all, delete-orphan")
    attestations = relationship("Attestation", back_populates="job", cascade="all, delete-orphan")
