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
from backend.app.core.config import settings
from backend.app.db.models.attestation import Attestation
from backend.app.ingest.media_probe import probe_media_file, standardize_to_mp4, MediaValidationError
from backend.app.ingest.ssrf import download_safe_url, SSRFSecurityError, OversizeFileError
from backend.app.ingest.share_links import resolve_share_link
from backend.app.ingest.youtube import download_youtube_video, YouTubeImportError
from backend.app.pipeline.audio_extractor import extract_audio_tracks
from backend.app.engines.separation.demucs_separator import DemucsSeparatorEngine
from backend.app.engines.asr.faster_whisper_asr import FasterWhisperASREngine
from backend.app.engines.translation.llm_translator import LocalLLMTranslator
from backend.app.engines.base import TranscriptSegment, TranslatedSegment
from backend.app.pipeline.reference_clip import build_reference_clip
from backend.app.pipeline.timing_fit import calculate_timing_fit, apply_audio_time_stretch
from backend.app.engines.tts.voice_synthesizer import VoiceSynthesizer
from backend.app.pipeline.audio_mixer import assemble_timeline_vocals, mix_vocals_and_background
from backend.app.pipeline.video_muxer import mux_video_and_audio, export_dub_mp3, AVSyncDriftError
from backend.app.pipeline.time_estimator import estimate_remaining_seconds
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
            target_path = storage.get_path(out_key)
            target_path.parent.mkdir(parents=True, exist_ok=True)

            if self.mock_execution:
                if not storage.exists(out_key):
                    storage.put(out_key, b"FAKE_MP4_SOURCE_VIDEO_BYTES")
                self._record_artifact(job, "source_video", out_key, stage)
                return

            if job.source_type == "upload":
                upload_file_key = f"uploads/{job.source_ref}/source.mp4"
                if not storage.exists(upload_file_key):
                    if storage.exists(job.source_ref):
                        upload_file_key = job.source_ref
                    else:
                        raise FileNotFoundError(f"Uploaded source not found for reference: {job.source_ref}")

                source_upload_path = storage.get_path(upload_file_key)
                standardize_to_mp4(source_upload_path, target_path)

            elif job.source_type in ["url", "drive", "dropbox"]:
                resolved_url = resolve_share_link(job.source_ref)
                temp_download_path = target_path.with_suffix(".tmp.bin")
                try:
                    download_safe_url(resolved_url, temp_download_path)
                    standardize_to_mp4(temp_download_path, target_path)
                finally:
                    if temp_download_path.exists():
                        temp_download_path.unlink()

            elif job.source_type == "youtube":
                if not settings.ENABLE_YOUTUBE_IMPORT:
                    raise YouTubeImportError("YouTube import is disabled by administrator.")

                attestation = self.db.query(Attestation).filter(
                    Attestation.job_id == job.id,
                    Attestation.kind == "ownership"
                ).first()
                if not attestation:
                    raise ValueError("YouTube import requires explicit user ownership/permission attestation.")

                temp_yt_path = target_path.with_suffix(".yt.mp4")
                try:
                    download_youtube_video(job.source_ref, temp_yt_path)
                    standardize_to_mp4(temp_yt_path, target_path)
                finally:
                    if temp_yt_path.exists():
                        temp_yt_path.unlink()
            else:
                raise ValueError(f"Unsupported source_type '{job.source_type}'")

            # Validate resulting source.mp4 with ffprobe
            probe_result = probe_media_file(target_path)
            logger.info(f"Ingested media successfully for job {job.id}: {probe_result.duration:.2f}s, {probe_result.size_bytes} bytes")
            self._record_artifact(job, "source_video", out_key, stage)

        elif stage == PipelineStage.EXTRACTING:
            out_key = f"{job_dir}/audio/original.wav"
            asr_key = f"{job_dir}/audio/asr_16k.wav"

            if self.mock_execution:
                if not storage.exists(out_key):
                    storage.put(out_key, b"FAKE_ORIGINAL_WAV_BYTES")
                if not storage.exists(asr_key):
                    storage.put(asr_key, b"FAKE_ASR_WAV_BYTES")
                self._record_artifact(job, "original_wav", out_key, stage)
                self._record_artifact(job, "asr_wav", asr_key, stage)
                return

            source_video_path = storage.get_path(f"{job_dir}/source.mp4")
            audio_dir = storage.get_path(f"{job_dir}/audio")
            extract_audio_tracks(source_video_path, audio_dir)

            self._record_artifact(job, "original_wav", out_key, stage)
            self._record_artifact(job, "asr_wav", asr_key, stage)

        elif stage == PipelineStage.SEPARATING:
            voc_key = f"{job_dir}/audio/vocals.wav"
            bg_key = f"{job_dir}/audio/background.wav"

            if self.mock_execution:
                if not storage.exists(voc_key):
                    storage.put(voc_key, b"FAKE_VOCALS_BYTES")
                if not storage.exists(bg_key):
                    storage.put(bg_key, b"FAKE_BACKGROUND_BYTES")
                self._record_artifact(job, "vocals_wav", voc_key, stage)
                self._record_artifact(job, "background_wav", bg_key, stage)
                return

            orig_audio_path = storage.get_path(f"{job_dir}/audio/original.wav")
            audio_dir = storage.get_path(f"{job_dir}/audio")
            separator = DemucsSeparatorEngine()
            separator.separate(str(orig_audio_path), str(audio_dir))

            self._record_artifact(job, "vocals_wav", voc_key, stage)
            self._record_artifact(job, "background_wav", bg_key, stage)

        elif stage == PipelineStage.TRANSCRIBING:
            trans_key = f"{job_dir}/transcript.json"

            if self.mock_execution:
                transcript_data = {
                    "detected_language": job.source_lang or "en",
                    "language_probability": 0.99,
                    "segments": [
                        {"idx": 1, "start": 0.0, "end": 4.5, "text": "Welcome to the lecture on computer algorithms."},
                        {"idx": 2, "start": 4.6, "end": 9.2, "text": "Today we will analyze time and space complexity."}
                    ]
                }
                storage.put(trans_key, json.dumps(transcript_data, ensure_ascii=False).encode("utf-8"))
                self._record_artifact(job, "transcript_json", trans_key, stage)
                return

            vocals_path = storage.get_path(f"{job_dir}/audio/vocals.wav")
            if not vocals_path.exists():
                vocals_path = storage.get_path(f"{job_dir}/audio/asr_16k.wav")

            asr_engine = FasterWhisperASREngine()
            asr_res = asr_engine.transcribe(str(vocals_path), language=job.source_lang)

            if not job.source_lang:
                job.source_lang = asr_res.language
                self.db.commit()

            transcript_payload = {
                "detected_language": asr_res.language,
                "language_probability": asr_res.language_probability,
                "duration": asr_res.duration,
                "segments": [
                    {
                        "idx": s.idx,
                        "start": s.start,
                        "end": s.end,
                        "text": s.text,
                        "speaker": s.speaker
                    }
                    for s in asr_res.segments
                ]
            }
            storage.put(trans_key, json.dumps(transcript_payload, ensure_ascii=False, indent=2).encode("utf-8"))
            self._record_artifact(job, "transcript_json", trans_key, stage)

        elif stage == PipelineStage.TRANSLATING:
            trans_key = f"{job_dir}/translation.json"

            if self.mock_execution:
                translations = [
                    ("Welcome to the lecture on computer algorithms.", "کمپیوٹر الگورتھم کے لیکچر میں خوش آمدید۔"),
                    ("Today we will analyze time and space complexity.", "آج ہم وقت اور جگہ کی پیچیدگی کا تجزیہ کریں گے۔")
                ]
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
                        edited_by_user=False,
                        flagged=False
                    )
                    self.db.add(seg)
                self.db.commit()

                storage.put(trans_key, json.dumps({"segments": translations}, ensure_ascii=False).encode("utf-8"))
                self._record_artifact(job, "translation_json", trans_key, stage)
                return

            transcript_raw = storage.get(f"{job_dir}/transcript.json")
            transcript_dict = json.loads(transcript_raw.decode("utf-8"))
            raw_segs = transcript_dict.get("segments", [])

            transcript_segments = [
                TranscriptSegment(
                    idx=s["idx"],
                    start=s["start"],
                    end=s["end"],
                    text=s["text"],
                    speaker=s.get("speaker", "speaker_0")
                )
                for s in raw_segs
            ]

            translator = LocalLLMTranslator()
            translated_segs = translator.translate(
                segments=transcript_segments,
                src_lang=job.source_lang or "en",
                tgt_lang=job.target_lang,
                glossary=options.get("glossary")
            )

            self.db.query(Segment).filter(Segment.job_id == job.id).delete()
            for ts in translated_segs:
                db_seg = Segment(
                    job_id=job.id,
                    idx=ts.idx,
                    start=ts.start,
                    end=ts.end,
                    speaker=ts.speaker,
                    src_text=ts.src_text,
                    tgt_text=ts.tgt_text,
                    edited_by_user=False,
                    flagged=ts.flagged,
                    flag_reason=ts.flag_reason
                )
                self.db.add(db_seg)
            self.db.commit()

            translation_payload = {
                "source_lang": job.source_lang or "en",
                "target_lang": job.target_lang,
                "segments": [
                    {
                        "idx": ts.idx,
                        "start": ts.start,
                        "end": ts.end,
                        "src_text": ts.src_text,
                        "tgt_text": ts.tgt_text,
                        "flagged": ts.flagged,
                        "flag_reason": ts.flag_reason
                    }
                    for ts in translated_segs
                ]
            }
            storage.put(trans_key, json.dumps(translation_payload, ensure_ascii=False, indent=2).encode("utf-8"))
            self._record_artifact(job, "translation_json", trans_key, stage)

        elif stage == PipelineStage.SYNTHESIZING:
            tts_key = f"{job_dir}/dub_vocals.wav"

            if self.mock_execution:
                segments = self.db.query(Segment).filter(Segment.job_id == job.id).order_by(Segment.idx.asc()).all()
                for seg in segments:
                    seg_key = f"{job_dir}/tts/seg_{seg.idx:04d}.wav"
                    if not storage.exists(seg_key):
                        storage.put(seg_key, b"FAKE_TTS_SEG_BYTES")
                    seg.tts_path = seg_key
                    seg.tts_duration = max(0.5, seg.end - seg.start)
                    seg.stretch_ratio = 1.0
                self.db.commit()

                if not storage.exists(tts_key):
                    storage.put(tts_key, b"FAKE_DUB_VOCALS_BYTES")
                self._record_artifact(job, "dub_vocals", tts_key, stage)
                return

            segments = self.db.query(Segment).filter(Segment.job_id == job.id).order_by(Segment.idx.asc()).all()
            if not segments:
                raise ValueError(f"No translation segments found to synthesize for job {job.id}")

            clone_voice = options.get("clone_voice", True)
            ref_clip_path = None
            if clone_voice:
                ref_clip_key = f"{job_dir}/audio/ref_clip.wav"
                ref_clip_file = storage.get_path(ref_clip_key)
                if ref_clip_file.is_file() and ref_clip_file.stat().st_size > 0:
                    ref_clip_path = ref_clip_file
                else:
                    vocals_file = storage.get_path(f"{job_dir}/audio/vocals.wav")
                    if not vocals_file.is_file():
                        vocals_file = storage.get_path(f"{job_dir}/audio/original.wav")
                    if vocals_file.is_file():
                        try:
                            ref_clip_path = build_reference_clip(
                                vocals_path=vocals_file,
                                segments=segments,
                                output_path=ref_clip_file,
                                target_duration=15.0
                            )
                            self._record_artifact(job, "reference_clip", ref_clip_key, stage)
                        except Exception as e:
                            logger.warning(f"Could not build reference clip for job {job.id}: {e}; proceeding without cloning")
                            ref_clip_path = None

            synthesizer = VoiceSynthesizer()
            for i, seg in enumerate(segments):
                seg_rel_key = f"{job_dir}/tts/seg_{seg.idx:04d}.wav"
                seg_abs_path = storage.get_path(seg_rel_key)
                seg_abs_path.parent.mkdir(parents=True, exist_ok=True)

                # Checkpoint check: skip already synthesized segments (enables mid-stage crash recovery)
                if seg.tts_duration and seg.tts_path and seg_abs_path.is_file() and seg_abs_path.stat().st_size > 0:
                    logger.info(f"Segment {seg.idx} already synthesized ({seg.tts_duration:.2f}s); skipping.")
                    continue

                slot_duration = max(0.5, seg.end - seg.start)
                prev_end = segments[i - 1].end if i > 0 else 0.0
                avail_pre = max(0.0, seg.start - prev_end)
                next_start = segments[i + 1].start if (i + 1 < len(segments)) else (seg.end + 10.0)
                avail_post = max(0.0, next_start - seg.end)

                raw_seg_path = seg_abs_path.with_suffix(".raw.wav")
                try:
                    raw_dur = synthesizer.synthesize_segment(
                        text=seg.tgt_text,
                        language=job.target_lang,
                        out_path=raw_seg_path,
                        reference_clip=ref_clip_path,
                        clone_voice=clone_voice
                    )

                    fit_decision = calculate_timing_fit(
                        original_duration=slot_duration,
                        tts_duration=raw_dur,
                        available_pre_silence=avail_pre,
                        available_post_silence=avail_post
                    )

                    if fit_decision.status in ["stretched", "borrowed_silence"] and abs(fit_decision.effective_stretch_ratio - 1.0) > 0.02:
                        apply_audio_time_stretch(raw_seg_path, seg_abs_path, fit_decision.effective_stretch_ratio)
                    else:
                        import shutil
                        shutil.copy(raw_seg_path, seg_abs_path)

                    probe = probe_media_file(seg_abs_path)
                    seg.tts_path = seg_rel_key
                    seg.tts_duration = probe.duration
                    seg.stretch_ratio = fit_decision.effective_stretch_ratio
                    self.db.commit()

                    seg_progress = (i + 1) / len(segments)
                    job.progress = compute_overall_progress(stage, seg_progress)
                    self._notify_progress(job)
                finally:
                    if raw_seg_path.exists():
                        raw_seg_path.unlink()

            source_mp4 = storage.get_path(f"{job_dir}/source.mp4")
            if source_mp4.is_file():
                total_duration = probe_media_file(source_mp4).duration
            else:
                total_duration = max([s.end for s in segments], default=10.0) + 2.0

            dub_vocals_path = storage.get_path(tts_key)
            assemble_timeline_vocals(segments, total_duration, dub_vocals_path)
            self._record_artifact(job, "dub_vocals", tts_key, stage)

        elif stage == PipelineStage.MIXING:
            mix_key = f"{job_dir}/dub_mix.wav"
            if self.mock_execution:
                if not storage.exists(mix_key):
                    storage.put(mix_key, b"FAKE_DUB_MIX_BYTES")
                self._record_artifact(job, "dub_mix", mix_key, stage)
                return

            dub_vocals_path = storage.get_path(f"{job_dir}/dub_vocals.wav")
            if not dub_vocals_path.is_file():
                raise FileNotFoundError(f"Dubbed vocals file missing for job {job.id}: {dub_vocals_path}")

            bg_path = storage.get_path(f"{job_dir}/audio/background.wav")
            mix_path = storage.get_path(mix_key)
            ducking_db = float(options.get("ducking_db", 12.0))
            target_lufs = float(options.get("target_lufs", -16.0))

            mix_vocals_and_background(
                dub_vocals_path=dub_vocals_path,
                background_path=bg_path,
                output_mix_path=mix_path,
                ducking_db=ducking_db,
                target_lufs=target_lufs
            )
            self._record_artifact(job, "dub_mix", mix_key, stage)

        elif stage == PipelineStage.MUXING:
            final_key = f"{job_dir}/output/final.mp4"
            audio_mp3_key = f"{job_dir}/output/dub_audio.mp3"

            if self.mock_execution:
                if not storage.exists(final_key):
                    storage.put(final_key, b"FAKE_FINAL_MUXED_MP4_BYTES")
                if not storage.exists(audio_mp3_key):
                    storage.put(audio_mp3_key, b"FAKE_DUB_AUDIO_MP3_BYTES")
                self._record_artifact(job, "final_video", final_key, stage)
                self._record_artifact(job, "dub_audio", audio_mp3_key, stage)
                return

            video_path = storage.get_path(f"{job_dir}/source.mp4")
            audio_path = storage.get_path(f"{job_dir}/dub_mix.wav")
            out_video_path = storage.get_path(final_key)
            out_mp3_path = storage.get_path(audio_mp3_key)

            if not video_path.is_file():
                raise FileNotFoundError(f"Source video missing for job {job.id}: {video_path}")
            if not audio_path.is_file():
                raise FileNotFoundError(f"Dubbed audio mix missing for job {job.id}: {audio_path}")

            # Mux video with dubbed audio, verify duration match & A/V sync drift
            mux_video_and_audio(
                video_path=video_path,
                audio_path=audio_path,
                output_path=out_video_path,
                target_lang=job.target_lang or "ur",
                tolerance_seconds=2.0
            )

            # Export MP3 audio for audio-only download option
            try:
                export_dub_mp3(audio_path, out_mp3_path)
                self._record_artifact(job, "dub_audio", audio_mp3_key, stage)
            except Exception as e:
                logger.warning(f"Could not export MP3 for job {job.id}: {e}; continuing with final video")

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
        est_rem = None
        try:
            curr_stage = PipelineStage(job.stage)
            source_file = storage.get_path(f"jobs/{job.id}/source.mp4")
            v_dur = probe_media_file(source_file).duration if source_file.is_file() else 60.0
            est_rem = estimate_remaining_seconds(curr_stage, 0.5, v_dur)
        except Exception:
            est_rem = None

        event = {
            "job_id": job.id,
            "status": job.status,
            "stage": job.stage,
            "progress": job.progress,
            "error": job.error,
            "estimated_seconds_remaining": est_rem
        }
        broadcaster.broadcast_sync(job.id, event)

