import pytest
from backend.app.core.security import hash_password, verify_password


def test_password_hashing():
    pwd = "secretLectureDubberPassword!2026"
    h = hash_password(pwd)
    assert h != pwd
    assert verify_password(pwd, h)
    assert not verify_password("wrongPassword", h)


def test_auth_flow(client):
    # Register
    reg_resp = client.post("/api/auth/register", json={
        "email": "learner@university.edu",
        "password": "mySecurePassword123"
    })
    assert reg_resp.status_code == 200
    token = reg_resp.json()["access_token"]
    assert token

    # Duplicate registration should be rejected
    dup_resp = client.post("/api/auth/register", json={
        "email": "learner@university.edu",
        "password": "mySecurePassword123"
    })
    assert dup_resp.status_code == 400

    # Login
    login_resp = client.post("/api/auth/login", json={
        "email": "learner@university.edu",
        "password": "mySecurePassword123"
    })
    assert login_resp.status_code == 200
    assert login_resp.json()["access_token"]

    # Invalid password login
    bad_resp = client.post("/api/auth/login", json={
        "email": "learner@university.edu",
        "password": "incorrectPassword"
    })
    assert bad_resp.status_code == 401

    # /api/me with valid token
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "learner@university.edu"

    # /api/me without token
    unauth_resp = client.get("/api/auth/me")
    assert unauth_resp.status_code == 401
