from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "error",
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
