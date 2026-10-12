from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import decode_access_token, rate_limiter
from backend.app.db.session import get_db
from backend.app.db.models.user import User

security_scheme = HTTPBearer(auto_error=False)


DEFAULT_USER_ID = "default-local-user"
DEFAULT_USER_EMAIL = "local@lecturedubber.internal"


def _get_or_create_default_user(db: Session) -> User:
    # First check if there is an existing user in DB
    user = db.query(User).first()
    if user:
        return user

    # Otherwise create default local user
    user = User(
        id=DEFAULT_USER_ID,
        email=DEFAULT_USER_EMAIL,
        password_hash="none",
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        return db.query(User).first()


def check_auth_rate_limit(request: Request):
    # No rate limiting in local zero-auth mode
    pass


def check_job_create_rate_limit(request: Request):
    # No rate limiting in local zero-auth mode
    pass


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    if credentials:
        payload = decode_access_token(credentials.credentials)
        if payload and "sub" in payload:
            user = db.query(User).filter(User.id == payload["sub"]).first()
            if user:
                return user

    if credentials is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if getattr(settings, "REQUIRE_AUTH", False) or getattr(settings, "APP_ENV", "") == "test":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Zero-auth bypass: Return local default user for local dev UI
    return _get_or_create_default_user(db)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        if payload and "sub" in payload:
            return db.query(User).filter(User.id == payload["sub"]).first()
    except Exception:
        return None
    return None
