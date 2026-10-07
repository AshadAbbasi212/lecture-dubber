import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import get_db
import backend.app.db.models  # ensure models are loaded
from backend.app.main import app
from backend.app.storage.local import LocalStorage

# Setup shared in-memory SQLite database using StaticPool
TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_env(tmp_path_factory):
    test_storage_dir = tmp_path_factory.mktemp("test_storage")
    settings.STORAGE_DIR = str(test_storage_dir)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Registers and logs in a test user, returning Bearer auth headers."""
    resp = client.post("/api/auth/register", json={
        "email": "testuser@example.com",
        "password": "strongPassword123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
