from backend.app.db.base import Base
from backend.app.db.session import engine
import backend.app.db.models  # ensure models are loaded


def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
