import os
from pathlib import Path
import time
from typing import Optional
import jwt

from backend.app.core.config import settings
from backend.app.storage.interface import Storage


class LocalStorage(Storage):
    def __init__(self, root_dir: Optional[str] = None):
        self.root = Path(root_dir or settings.STORAGE_DIR).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        # Prevent path traversal vulnerabilities
        norm_key = os.path.normpath(key).lstrip("\\/").replace("\\", "/")
        path = (self.root / norm_key).resolve()
        if not str(path).startswith(str(self.root)):
            raise ValueError(f"Path traversal detected: {key}")
        return path

    def put(self, key: str, data: bytes) -> str:
        dest = self._resolve(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Write to temp file then atomic rename
        temp_dest = dest.with_suffix(dest.suffix + f".tmp_{os.getpid()}")
        with open(temp_dest, "wb") as f:
            f.write(data)
        os.replace(temp_dest, dest)
        return str(dest)

    def get(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.is_file():
            raise FileNotFoundError(f"Storage key not found: {key}")
        with open(path, "rb") as f:
            return f.read()

    def exists(self, key: str) -> bool:
        try:
            path = self._resolve(key)
            return path.is_file()
        except ValueError:
            return False

    def delete(self, key: str) -> bool:
        try:
            path = self._resolve(key)
            if path.is_file():
                path.unlink()
                return True
            return False
        except (ValueError, FileNotFoundError):
            return False

    def get_path(self, key: str) -> Path:
        return self._resolve(key)

    def create_signed_token(self, job_id: str, kind: str, expires_in_seconds: int = 3600) -> str:
        payload = {
            "job_id": job_id,
            "kind": kind,
            "exp": int(time.time()) + expires_in_seconds
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def verify_signed_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except (jwt.PyJWTError, Exception):
            return None


# Global singleton instance
storage = LocalStorage()
