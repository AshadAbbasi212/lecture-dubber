from datetime import datetime, timezone
import uuid
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # source_video, original_wav, vocals_wav, background_wav, transcript_json, translation_json, dub_mix_wav, final_video
    path: Mapped[str] = mapped_column(String, nullable=False)
    stage: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    job = relationship("Job", back_populates="artifacts")
