from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "lecture-dubber-insecure-secret-key-change-me"
    DATABASE_URL: str = "sqlite:///./storage/app.db"
    STORAGE_DIR: str = "./storage"
    MAX_UPLOAD_GB: int = 4
    MAX_VIDEO_MINUTES: int = 90
    RETENTION_DAYS: int = 14

    # JWT settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # Rate limiting settings (requests per minute)
    AUTH_RATE_LIMIT_PER_MINUTE: int = 30
    JOB_CREATE_RATE_LIMIT_PER_MINUTE: int = 10

    # Local model configurations from Phase 0
    WHISPER_MODEL: str = "base"
    WHISPER_COMPUTE_TYPE: str = "int8"
    TRANSLATION_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    TTS_MODEL_EN: str = "openvoice_v2"
    TTS_MODEL_UR: str = "piper_ur_openvoice"
    LIPSYNC_MODEL: Optional[str] = None  # Reserved for Phase 8

    # Ingest settings
    MAX_DIMENSION: int = 4096
    ALLOWED_EXTENSIONS: list[str] = [".mp4", ".mov", ".mkv", ".webm"]
    ENABLE_YOUTUBE_IMPORT: bool = True
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    SSRF_TIMEOUT_SECONDS: int = 30
    SSRF_MAX_REDIRECTS: int = 5

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def storage_path(self) -> Path:
        p = Path(self.STORAGE_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_ffmpeg_cmd(self) -> str:
        import shutil
        if shutil.which(self.FFMPEG_PATH):
            return self.FFMPEG_PATH
        # Check standard WinGet path as fallback on Windows
        winget_bin = Path(r"C:\Users\David\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe")
        if winget_bin.is_file():
            return str(winget_bin)
        return self.FFMPEG_PATH

    def get_ffprobe_cmd(self) -> str:
        import shutil
        if shutil.which(self.FFPROBE_PATH):
            return self.FFPROBE_PATH
        winget_bin = Path(r"C:\Users\David\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin\ffprobe.exe")
        if winget_bin.is_file():
            return str(winget_bin)
        return self.FFPROBE_PATH


settings = Settings()
