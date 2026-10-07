from enum import Enum
from typing import Dict, List, Optional


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class PipelineStage(str, Enum):
    INGESTING = "ingesting"
    EXTRACTING = "extracting"
    SEPARATING = "separating"
    TRANSCRIBING = "transcribing"
    TRANSLATING = "translating"
    SYNTHESIZING = "synthesizing"
    MIXING = "mixing"
    LIPSYNCING = "lipsyncing"  # Reserved for Phase 8 milestone
    MUXING = "muxing"
    COMPLETED = "completed"


STAGE_ORDER: List[PipelineStage] = [
    PipelineStage.INGESTING,
    PipelineStage.EXTRACTING,
    PipelineStage.SEPARATING,
    PipelineStage.TRANSCRIBING,
    PipelineStage.TRANSLATING,
    PipelineStage.SYNTHESIZING,
    PipelineStage.MIXING,
    PipelineStage.MUXING,
    PipelineStage.COMPLETED,
]

STAGE_PROGRESS_BASE: Dict[PipelineStage, int] = {
    PipelineStage.INGESTING: 5,
    PipelineStage.EXTRACTING: 10,
    PipelineStage.SEPARATING: 25,
    PipelineStage.TRANSCRIBING: 45,
    PipelineStage.TRANSLATING: 60,
    PipelineStage.SYNTHESIZING: 85,
    PipelineStage.MIXING: 92,
    PipelineStage.LIPSYNCING: 95,
    PipelineStage.MUXING: 98,
    PipelineStage.COMPLETED: 100,
}


class InvalidStateTransitionError(ValueError):
    """Raised when an illegal status or stage transition is attempted."""
    pass


VALID_STATUS_TRANSITIONS: Dict[JobStatus, List[JobStatus]] = {
    JobStatus.QUEUED: [JobStatus.RUNNING, JobStatus.CANCELED],
    JobStatus.RUNNING: [JobStatus.RUNNING, JobStatus.AWAITING_REVIEW, JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED],
    JobStatus.AWAITING_REVIEW: [JobStatus.RUNNING, JobStatus.CANCELED, JobStatus.FAILED],
    JobStatus.FAILED: [JobStatus.QUEUED, JobStatus.CANCELED],  # Retry allows going back to queued
    JobStatus.CANCELED: [],  # Terminal
    JobStatus.COMPLETED: [],  # Terminal
}


def validate_status_transition(current: str, target: str) -> None:
    curr_enum = JobStatus(current)
    tgt_enum = JobStatus(target)
    allowed = VALID_STATUS_TRANSITIONS.get(curr_enum, [])
    if tgt_enum not in allowed:
        raise InvalidStateTransitionError(
            f"Invalid status transition from '{current}' to '{target}'. Allowed: {[s.value for s in allowed]}"
        )


def get_next_stage(
    current_stage: PipelineStage,
    skip_review: bool = False,
    enable_lipsync: bool = False
) -> PipelineStage:
    if current_stage == PipelineStage.MIXING and enable_lipsync:
        return PipelineStage.LIPSYNCING
    if current_stage == PipelineStage.LIPSYNCING:
        return PipelineStage.MUXING

    try:
        idx = STAGE_ORDER.index(current_stage)
        if idx + 1 < len(STAGE_ORDER):
            return STAGE_ORDER[idx + 1]
        return PipelineStage.COMPLETED
    except ValueError:
        raise InvalidStateTransitionError(f"Unknown stage: {current_stage}")


def compute_overall_progress(stage: PipelineStage, stage_progress: float = 0.0) -> int:
    """Compute overall job percentage (0..100) from current stage and within-stage progress."""
    base = STAGE_PROGRESS_BASE.get(stage, 0)
    # Next base or 100
    try:
        idx = STAGE_ORDER.index(stage)
        next_base = STAGE_PROGRESS_BASE.get(STAGE_ORDER[min(idx + 1, len(STAGE_ORDER) - 1)], 100)
    except ValueError:
        next_base = base
    
    stage_span = max(0, next_base - base)
    total = base + (stage_span * max(0.0, min(1.0, stage_progress)))
    return int(round(total))
