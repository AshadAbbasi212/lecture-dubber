from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import decode_access_token, rate_limiter
from backend.app.db.session import get_db
from backend.app.db.models.user import User

security_scheme = HTTPBearer(auto_error=False)


def check_auth_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    allowed = rate_limiter.is_allowed(
        f"auth:{client_ip}",
        max_requests=settings.AUTH_RATE_LIMIT_PER_MINUTE,
        window_seconds=60
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please slow down."
        )


def check_job_create_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    allowed = rate_limiter.is_allowed(
        f"job_create:{client_ip}",
        max_requests=settings.JOB_CREATE_RATE_LIMIT_PER_MINUTE,
        window_seconds=60
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many jobs created recently. Please wait."
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    user_id = payload["sub"]
    return db.query(User).filter(User.id == user_id).first()
