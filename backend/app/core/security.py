from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
import time
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
import jwt

from backend.app.core.config import settings

ph = PasswordHasher()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


class RateLimiter:
    """Simple in-memory sliding window rate limiter."""
    def __init__(self):
        self._history: Dict[str, List[float]] = {}

    def is_allowed(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        now = time.time()
        window_start = now - window_seconds
        
        timestamps = self._history.get(key, [])
        # Prune old timestamps
        timestamps = [ts for ts in timestamps if ts > window_start]
        
        if len(timestamps) >= max_requests:
            self._history[key] = timestamps
            return False
            
        timestamps.append(now)
        self._history[key] = timestamps
        return True


rate_limiter = RateLimiter()
