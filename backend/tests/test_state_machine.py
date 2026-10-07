import pytest
from backend.app.pipeline.state_machine import (
    JobStatus,
    PipelineStage,
    validate_status_transition,
    get_next_stage,
    compute_overall_progress,
    InvalidStateTransitionError
)


def test_valid_status_transitions():
    # Queued -> Running
    validate_status_transition("queued", "running")
    # Running -> Awaiting Review
    validate_status_transition("running", "awaiting_review")
    # Awaiting Review -> Running (Approve)
    validate_status_transition("awaiting_review", "running")
    # Running -> Completed
    validate_status_transition("running", "completed")
    # Running -> Failed
    validate_status_transition("running", "failed")
    # Failed -> Queued (Retry)
    validate_status_transition("failed", "queued")


def test_invalid_status_transitions():
    # Cannot jump queued -> completed directly
    with pytest.raises(InvalidStateTransitionError):
        validate_status_transition("queued", "completed")

    # Completed is terminal
    with pytest.raises(InvalidStateTransitionError):
        validate_status_transition("completed", "running")

    # Canceled is terminal
    with pytest.raises(InvalidStateTransitionError):
        validate_status_transition("canceled", "running")


def test_stage_progression():
    s = PipelineStage.INGESTING
    s = get_next_stage(s)
    assert s == PipelineStage.EXTRACTING
    s = get_next_stage(s)
    assert s == PipelineStage.SEPARATING
    s = get_next_stage(s)
    assert s == PipelineStage.TRANSCRIBING
    s = get_next_stage(s)
    assert s == PipelineStage.TRANSLATING
    s = get_next_stage(s)
    assert s == PipelineStage.SYNTHESIZING
    s = get_next_stage(s)
    assert s == PipelineStage.MIXING
    s = get_next_stage(s)
    assert s == PipelineStage.MUXING
    s = get_next_stage(s)
    assert s == PipelineStage.COMPLETED


def test_compute_overall_progress():
    p0 = compute_overall_progress(PipelineStage.INGESTING, 0.0)
    assert p0 >= 0
    p1 = compute_overall_progress(PipelineStage.MUXING, 1.0)
    assert p1 >= 95
    p_comp = compute_overall_progress(PipelineStage.COMPLETED, 1.0)
    assert p_comp == 100
