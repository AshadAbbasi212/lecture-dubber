import signal
import sys
import time
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.core.logging import logger, setup_logging
from backend.app.db.session import SessionLocal
from backend.app.db.init_db import init_db
from backend.app.pipeline.runner import PipelineRunner
from backend.app.pipeline.state_machine import PipelineStage
from backend.app.worker.queue import JobQueue
from backend.app.worker.gpu_lock import acquire_gpu_lock

# Stages requiring GPU lock
GPU_STAGES = {
    PipelineStage.SEPARATING.value,
    PipelineStage.TRANSCRIBING.value,
    PipelineStage.SYNTHESIZING.value,
    PipelineStage.LIPSYNCING.value,
}


class DubberWorker:
    def __init__(self, poll_interval: float = 1.0, mock_execution: bool = False):
        self.poll_interval = poll_interval
        self.mock_execution = mock_execution
        self.running = False
        self._setup_signals()

    def _setup_signals(self):
        def _handle_stop(signum, frame):
            logger.info("Shutdown signal received. Stopping worker gracefully...")
            self.running = False

        try:
            signal.signal(signal.SIGINT, _handle_stop)
            signal.signal(signal.SIGTERM, _handle_stop)
        except (ValueError, AttributeError):
            # In non-main thread or special windows environment
            pass

    def run_once(self, db: Optional[Session] = None) -> bool:
        """
        Executes a single step: picks one job and advances its stage.
        Returns True if work was done, False if queue was empty.
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            job = JobQueue.fetch_next_job(db)
            if not job:
                return False

            runner = PipelineRunner(db, mock_execution=self.mock_execution)
            is_gpu_stage = job.stage in GPU_STAGES

            if is_gpu_stage:
                with acquire_gpu_lock():
                    runner.run_next_stage(job.id)
            else:
                runner.run_next_stage(job.id)

            return True
        finally:
            if close_db:
                db.close()

    def start(self):
        setup_logging()
        init_db()
        logger.info("Lecture Dubber Worker started. Polling for jobs...")
        self.running = True

        # Crash recovery
        with SessionLocal() as db:
            JobQueue.recover_orphaned_jobs(db)

        while self.running:
            try:
                worked = self.run_once()
                if not worked:
                    time.sleep(self.poll_interval)
            except Exception as e:
                logger.exception(f"Unexpected error in worker loop: {e}")
                time.sleep(self.poll_interval)

        logger.info("Worker stopped.")


if __name__ == "__main__":
    worker = DubberWorker()
    worker.start()
