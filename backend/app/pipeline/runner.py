import json
import time
from pathlib import Path
from typing import Optional, Callable
from sqlalchemy.orm import Session

from backend.app.core.logging import logger
from backend.app.core.events import broadcaster
from backend.app.db.models.job import Job
from backend.app.db.models.segment import Segment
from backend.app.db.models.artifact import Artifact
from backend.app.pipeline.state_machine import (
    JobStatus,
    PipelineStage,
    STAGE_ORDER,
    validate_status_transition,
    get_next_stage,
    compute_overall_progress,
)
from backend.app.storage.local import storage


class PipelineRunner:
    """Executes stages for a job, updating DB state, artifacts, and SSE events."""

    def __init__(self, db: Session, mock_execution: bool = False):
        self.db = db
        self.mock_execution = mock_execution

    def run_next_stage(self, job_id: str) -> bool:
        """
        Executes the current stage for job_id.
        Returns True if job made progress or completed, False if waiting or failed.
        """
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return False

        if job.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELED.value, JobStatus.AWAITING_REVIEW.value]:
            return False

        current_stage = PipelineStage(job.stage)
        options = json.loads(job.options_json) if job.options_json else {}
        skip_review = options.get("skip_review", False)

        logger.info(f"Running job {job.id}: stage={current_stage.value}, status={job.status}")

        # Transition status to running if queued
        if job.status == JobStatus.QUEUED.value:
            validate_status_transition(job.status, JobStatus.RUNNING.value)
            job.status = JobStatus.RUNNING.value
            self.db.commit()

        # Broadcast start of stage
        job.progress = compute_overall_progress(current_stage, 0.0)
        self._notify_progress(job)

        try:
            # Check if artifact for this stage already exists (idempotency check)
            if self._is_stage_already_complete(job, current_stage):
                logger.info(f"Stage {current_stage.value} already complete for job {job.id}; skipping.")
            else:
                # Execute stage logic
                self._execute_stage(job, current_stage, options)

            # Stage finished - update progress
            job.progress = compute_overall_progress(current_stage, 1.0)
            self._notify_progress(job)

            # Check if we should pause for review
            if current_stage == PipelineStage.TRANSLATING and not skip_review:
                logger.info(f"Job {job.id} entering awaiting_review")
                validate_status_transition(job.status, JobStatus.AWAITING_REVIEW.value)
                job.status = JobStatus.AWAITING_REVIEW.value
                # Next stage when approved will be synthesizing
                job.stage = PipelineStage.SYNTHESIZING.value
                self.db.commit()
                self._notify_progress(job)
                return True

            # Advance to next stage
            next_stage = get_next_stage(current_stage)
            if next_stage == PipelineStage.COMPLETED:
                logger.info(f"Job {job.id} completed successfully!")
                validate_status_transition(job.status, JobStatus.COMPLETED.value)
                job.status = JobStatus.COMPLETED.value
                job.stage = PipelineStage.COMPLETED.value
                job.progress = 100
            else:
                job.stage = next_stage.value

            self.db.commit()
            self._notify_progress(job)
            return True

        except Exception as e:
            logger.exception(f"Error executing stage {current_stage.value} for job {job.id}: {e}")
            job.status = JobStatus.FAILED.value
            job.error = str(e)
            self.db.commit()
            self._notify_progress(job)
            return False

    def _is_stage_already_complete(self, job: Job, stage: PipelineStage) -> bool:
        """Idempotency check: verify if output artifacts for this stage exist in DB and storage."""
        expected_kind = f"{stage.value}_output"
        artifact = self.db.query(Artifact).filter(
            Artifact.job_id == job.id,
            Artifact.stage == stage.value
        ).first()
        if artifact and storage.exists(artifact.path):
            return True
        return False

    def _execute_stage(self, job: Job, stage: PipelineStage, options: dict) -> None:
        """Executes stage work. In Phase 1 or with mock_execution, uses deterministic dummy stages."""
        job_dir = f"jobs/{job.id}"

        if stage == PipelineStage.INGESTING:
            out_key = f"{job_dir}/source.mp4"
            if not storage.exists(out_key):
                storage.put(out_key, b"FAKE_MP4_SOURCE_VIDEO_BYTES")
            self._record_artifact(job, "source_video", out_key, stage)

        elif stage == PipelineStage.EXTRACTING:
            out_key = f"{job_dir}/audio/original.wav"
            storage.put(out_key, b"FAKE_ORIGINAL_WAV_BYTES")
            self._record_artifact(job, "original_wav", out_key, stage)

        elif stage == PipelineStage.SEPARATING:
            voc_key = f"{job_dir}/audio/vocals.wav"
            bg_key = f"{job_dir}/audio/background.wav"
            storage.put(voc_key, b"FAKE_VOCALS_BYTES")
            storage.put(bg_key, b"FAKE_BACKGROUND_BYTES")
            self._record_artifact(job, "vocals_wav", voc_key, stage)
            self._record_artifact(job, "background_wav", bg_key, stage)

        elif stage == PipelineStage.TRANSCRIBING:
            trans_key = f"{job_dir}/transcript.json"
            transcript_data = {
                "detected_language": job.source_lang or "en",
                "segments": [
                    {"idx": 1, "start": 0.0, "end": 4.5, "text": "Welcome to the lecture on computer algorithms."},
                    {"idx": 2, "start": 4.6, "end": 9.2, "text": "Today we will analyze time and space complexity."}
                ]
            }
            storage.put(trans_key, json.dumps(transcript_data).encode("utf-8"))
            self._record_artifact(job, "transcript_json", trans_key, stage)

        elif stage == PipelineStage.TRANSLATING:
            trans_key = f"{job_dir}/translation.json"
            # Create segments in DB
            translations = [
                ("Welcome to the lecture on computer algorithms.", "کمپیوٹر الگورتھم کے لیکچر میں خوش آمدید۔"),
                ("Today we will analyze time and space complexity.", "آج ہم وقت اور جگہ کی پیچیدگی کا تجزیہ کریں گے۔")
            ]
            # Clean up existing segments if retrying
            self.db.query(Segment).filter(Segment.job_id == job.id).delete()
            for i, (src, tgt) in enumerate(translations, 1):
                seg = Segment(
                    job_id=job.id,
                    idx=i,
                    start=(i - 1) * 5.0,
                    end=i * 4.8,
                    speaker="speaker_0",
                    src_text=src,
                    tgt_text=tgt,
                    edited_by_user=False
                )
                self.db.add(seg)
            self.db.commit()

            storage.put(trans_key, json.dumps({"segments": translations}, ensure_ascii=False).encode("utf-8"))
            self._record_artifact(job, "translation_json", trans_key, stage)

        elif stage == PipelineStage.SYNTHESIZING:
            tts_key = f"{job_dir}/dub_vocals.wav"
            storage.put(tts_key, b"FAKE_DUB_VOCALS_BYTES")
            self._record_artifact(job, "dub_vocals", tts_key, stage)

        elif stage == PipelineStage.MIXING:
            mix_key = f"{job_dir}/dub_mix.wav"
            storage.put(mix_key, b"FAKE_DUB_MIX_BYTES")
            self._record_artifact(job, "dub_mix", mix_key, stage)

        elif stage == PipelineStage.MUXING:
            final_key = f"{job_dir}/output/final.mp4"
            storage.put(final_key, b"FAKE_FINAL_MUXED_MP4_BYTES")
            self._record_artifact(job, "final_video", final_key, stage)

    def _record_artifact(self, job: Job, kind: str, path: str, stage: PipelineStage) -> None:
        artifact = Artifact(
            job_id=job.id,
            kind=kind,
            path=path,
            stage=stage.value
        )
        self.db.add(artifact)
        self.db.commit()

    def _notify_progress(self, job: Job) -> None:
        event = {
            "job_id": job.id,
            "status": job.status,
            "stage": job.stage,
            "progress": job.progress,
            "error": job.error
        }
        broadcaster.broadcast_sync(job.id, event)
