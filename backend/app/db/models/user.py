from datetime import datetime, timezone
import uuid
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    attestations = relationship("Attestation", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="user", cascade="all, delete-orphan")
