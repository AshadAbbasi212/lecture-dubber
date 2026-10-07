from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path


@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float
    probability: float = 1.0


@dataclass
class TranscriptSegment:
    idx: int
    start: float
    end: float
    text: str
    words: Optional[List[WordTimestamp]] = None
    speaker: str = "speaker_0"


@dataclass
class ASRResult:
    language: str
    language_probability: float
    duration: float
    segments: List[TranscriptSegment]


@dataclass
class TranslatedSegment:
    idx: int
    start: float
    end: float
    src_text: str
    tgt_text: str
    speaker: str = "speaker_0"
    flagged: bool = False
    flag_reason: Optional[str] = None


class ASREngine(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> ASRResult:
        """Transcribe audio with word-level timestamps and detect language."""
        pass


class SeparatorEngine(ABC):
    @abstractmethod
    def separate(self, audio_path: str, out_dir: str) -> Tuple[str, str]:
        """Separate audio into vocals.wav and background.wav. Returns paths."""
        pass


class TranslatorEngine(ABC):
    @abstractmethod
    def translate(
        self,
        segments: List[TranscriptSegment],
        src_lang: str,
        tgt_lang: str,
        glossary: Optional[Dict[str, str]] = None
    ) -> List[TranslatedSegment]:
        """Translate segments with context and length budget awareness."""
        pass


class TTSEngine(ABC):
    @abstractmethod
    def synthesize(
        self,
        text: str,
        language: str,
        out_path: str,
        reference_audio: Optional[str] = None
    ) -> float:
        """Synthesize speech. Returns duration in seconds."""
        pass


class VoiceConverterEngine(ABC):
    @abstractmethod
    def convert(
        self,
        source_audio_path: str,
        reference_audio_path: str,
        out_path: str
    ) -> str:
        """Transfer voice timbre from reference to source audio. Returns out_path."""
        pass


class LipSyncEngine(ABC):
    """Stub engine interface reserved for Phase 8 milestone."""
    @abstractmethod
    def sync(
        self,
        video_path: str,
        audio_path: str,
        out_path: str
    ) -> str:
        """Apply lip-sync to talking head shots in video. Returns out_path."""
        pass
