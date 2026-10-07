from typing import Optional
from sqlalchemy.orm import Session
from backend.app.core.logging import logger
from backend.app.db.models.job import Job
from backend.app.pipeline.state_machine import JobStatus


class JobQueue:
    """DB-backed queue interface for job scheduling and resume recovery."""

    @staticmethod
    def fetch_next_job(db: Session) -> Optional[Job]:
        """
        Picks the oldest runnable job:
        Prioritizes:
        1. Jobs currently 'running' that need their next stage executed.
        2. Jobs that are 'queued'.
        """
        # First check currently running jobs that are ready for the next stage
        running_job = db.query(Job).filter(
            Job.status == JobStatus.RUNNING.value
        ).order_by(Job.updated_at.asc()).first()
        if running_job:
            return running_job

        # Next check queued jobs
        queued_job = db.query(Job).filter(
            Job.status == JobStatus.QUEUED.value
        ).order_by(Job.created_at.asc()).first()
        return queued_job

    @staticmethod
    def recover_orphaned_jobs(db: Session) -> int:
        """
        Recovers jobs left in 'running' state after a crash/restart.
        They remain in 'running' (or reset to 'running') to resume at their current stage.
        """
        orphaned = db.query(Job).filter(Job.status == JobStatus.RUNNING.value).all()
        count = len(orphaned)
        if count > 0:
            logger.info(f"Recovered {count} in-progress jobs to resume from current stage.")
        return count
