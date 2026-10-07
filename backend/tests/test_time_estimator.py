import pytest

from backend.app.pipeline.state_machine import PipelineStage
from backend.app.pipeline.time_estimator import (
    get_stage_estimated_seconds,
    estimate_total_pipeline_seconds,
    estimate_remaining_seconds
)


def test_stage_estimated_seconds():
    # 30-minute lecture (1800s) on GPU
    duration = 1800.0

    # Demucs separation: 4s overhead + 0.36 * 1800s = 652s
    sep_time = get_stage_estimated_seconds(PipelineStage.SEPARATING, duration, has_gpu=True)
    assert 600.0 <= sep_time <= 700.0

    # Transcribing: 3s overhead + 0.18 * 1800s = ~327s
    asr_time = get_stage_estimated_seconds(PipelineStage.TRANSCRIBING, duration, has_gpu=True)
    assert 300.0 <= asr_time <= 360.0

    # Lip-syncing: 0s in v1
    lip_time = get_stage_estimated_seconds(PipelineStage.LIPSYNCING, duration, has_gpu=True)
    assert lip_time == 0.0


def test_estimate_total_pipeline_seconds():
    # 30-minute lecture (1800s)
    total_gpu = estimate_total_pipeline_seconds(1800.0, has_gpu=True)
    # Total on GPU should be between 25 and 35 minutes (1500 - 2100 seconds)
    assert 1500 <= total_gpu <= 2100

    # Total on CPU should be longer (> 40 minutes / 2400 seconds)
    total_cpu = estimate_total_pipeline_seconds(1800.0, has_gpu=False)
    assert total_cpu > total_gpu


def test_estimate_remaining_seconds_progression():
    duration = 1800.0
    total = estimate_total_pipeline_seconds(duration, has_gpu=True)

    # Ingesting stage at start
    rem_start = estimate_remaining_seconds(PipelineStage.INGESTING, 0.0, duration, has_gpu=True)
    assert rem_start >= total - 10

    # Ingesting stage half done
    rem_ingest_half = estimate_remaining_seconds(PipelineStage.INGESTING, 0.5, duration, has_gpu=True)
    assert rem_ingest_half <= rem_start

    # Muxing stage
    rem_mux = estimate_remaining_seconds(PipelineStage.MUXING, 0.0, duration, has_gpu=True)
    assert rem_mux < 60  # Only muxing remaining, which is ~39s

    # Completed stage
    rem_done = estimate_remaining_seconds(PipelineStage.COMPLETED, 1.0, duration, has_gpu=True)
    assert rem_done == 0
