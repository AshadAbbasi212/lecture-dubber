from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional


class Storage(ABC):
    """Abstract storage interface for decoupling local filesystem from cloud S3."""

    @abstractmethod
    def put(self, key: str, data: bytes) -> str:
        """Write bytes to storage key."""
        pass

    @abstractmethod
    def get(self, key: str) -> bytes:
        """Read bytes from storage key."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from storage."""
        pass

    @abstractmethod
    def get_path(self, key: str) -> Path:
        """Return local filesystem Path for this key (raises if outside storage root)."""
        pass

    @abstractmethod
    def create_signed_token(self, job_id: str, kind: str, expires_in_seconds: int = 3600) -> str:
        """Create a short-lived signed token for secure artifact download."""
        pass

    @abstractmethod
    def verify_signed_token(self, token: str) -> Optional[dict]:
        """Verify signed download token and return payload (job_id, kind) or None."""
        pass
