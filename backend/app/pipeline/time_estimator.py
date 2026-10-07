from typing import Dict, Optional
from backend.app.pipeline.state_machine import PipelineStage, STAGE_ORDER


# Measured real-time factors (RTF = compute_time / audio_duration) from docs/DECISIONS.md benchmarks
# Target: Windows 1 NVIDIA GPU (Quadro / RTX 3060) without lip-sync
STAGE_RTF_GPU: Dict[PipelineStage, float] = {
    PipelineStage.INGESTING: 0.01,
    PipelineStage.EXTRACTING: 0.02,
    PipelineStage.SEPARATING: 0.36,   # Demucs htdemucs on GPU: ~5.4s for 15s
    PipelineStage.TRANSCRIBING: 0.18, # Faster-Whisper base/small: ~0.15-0.20x
    PipelineStage.TRANSLATING: 0.15,  # Qwen2.5 7B Q4: ~20 tok/s across segments
    PipelineStage.SYNTHESIZING: 0.35, # Piper TTS + OpenVoice tone transfer
    PipelineStage.MIXING: 0.03,       # Numpy array buffer + FFmpeg loudnorm
    PipelineStage.LIPSYNCING: 0.0,    # Deferred / skipped in v1
    PipelineStage.MUXING: 0.02,       # Direct stream copy in FFmpeg
    PipelineStage.COMPLETED: 0.0,
}

# Fixed overhead in seconds per stage (initialization, disk I/O, subprocess spawns)
STAGE_FIXED_OVERHEAD_GPU: Dict[PipelineStage, float] = {
    PipelineStage.INGESTING: 2.0,
    PipelineStage.EXTRACTING: 1.0,
    PipelineStage.SEPARATING: 4.0,
    PipelineStage.TRANSCRIBING: 3.0,
    PipelineStage.TRANSLATING: 2.0,
    PipelineStage.SYNTHESIZING: 5.0,
    PipelineStage.MIXING: 3.0,
    PipelineStage.LIPSYNCING: 0.0,
    PipelineStage.MUXING: 3.0,
    PipelineStage.COMPLETED: 0.0,
}

# CPU fallback factors
STAGE_RTF_CPU: Dict[PipelineStage, float] = {
    PipelineStage.INGESTING: 0.01,
    PipelineStage.EXTRACTING: 0.02,
    PipelineStage.SEPARATING: 2.00,   # Demucs CPU: ~31s for 15s
    PipelineStage.TRANSCRIBING: 0.50, # Faster-Whisper CPU INT8: ~0.28-0.73x
    PipelineStage.TRANSLATING: 0.25,
    PipelineStage.SYNTHESIZING: 0.40,
    PipelineStage.MIXING: 0.03,
    PipelineStage.LIPSYNCING: 0.0,
    PipelineStage.MUXING: 0.02,
    PipelineStage.COMPLETED: 0.0,
}


def get_stage_estimated_seconds(
    stage: PipelineStage,
    video_duration: float,
    has_gpu: bool = True
) -> float:
    """Calculates estimated duration in seconds for a specific pipeline stage."""
    rtf_table = STAGE_RTF_GPU if has_gpu else STAGE_RTF_CPU
    rtf = rtf_table.get(stage, 0.0)
    fixed = STAGE_FIXED_OVERHEAD_GPU.get(stage, 2.0)
    return round(fixed + (rtf * max(video_duration, 1.0)), 1)


def estimate_total_pipeline_seconds(
    video_duration: float,
    has_gpu: bool = True
) -> int:
    """
    Returns honest estimate of total pipeline seconds for a lecture of given duration.
    Without lip-sync on GPU, 30 min lecture takes ~25-33 min (~0.9-1.1x duration).
    """
    total = 0.0
    for stage in STAGE_ORDER:
        if stage in [PipelineStage.LIPSYNCING, PipelineStage.COMPLETED]:
            continue
        total += get_stage_estimated_seconds(stage, video_duration, has_gpu=has_gpu)
    return max(1, int(round(total)))


def estimate_remaining_seconds(
    current_stage: PipelineStage,
    current_progress_within_stage: float,
    video_duration: float,
    has_gpu: bool = True
) -> int:
    """
    Computes remaining processing seconds based on active stage and elapsed progress within it.
    Returns 0 if completed.
    """
    if current_stage == PipelineStage.COMPLETED:
        return 0

    try:
        current_idx = STAGE_ORDER.index(current_stage)
    except ValueError:
        return 0

    # Remaining in current stage
    current_stage_total = get_stage_estimated_seconds(current_stage, video_duration, has_gpu=has_gpu)
    current_stage_remaining = current_stage_total * max(0.0, min(1.0, 1.0 - current_progress_within_stage))

    remaining = current_stage_remaining

    # Add upcoming stages
    for i in range(current_idx + 1, len(STAGE_ORDER)):
        stage = STAGE_ORDER[i]
        if stage in [PipelineStage.LIPSYNCING, PipelineStage.COMPLETED]:
            continue
        remaining += get_stage_estimated_seconds(stage, video_duration, has_gpu=has_gpu)

    return max(0, int(round(remaining)))
