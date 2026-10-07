from typing import Optional
import uuid
from sqlalchemy import String, Integer, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    start: Mapped[float] = mapped_column(Float, nullable=False)
    end: Mapped[float] = mapped_column(Float, nullable=False)
    speaker: Mapped[str] = mapped_column(String, default="speaker_0", nullable=False)
    src_text: Mapped[str] = mapped_column(Text, nullable=False)
    tgt_text: Mapped[str] = mapped_column(Text, nullable=False)
    edited_by_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tts_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tts_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stretch_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    job = relationship("Job", back_populates="segments")
