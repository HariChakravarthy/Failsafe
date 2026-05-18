import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_register_and_login():
    # Register
    r = client.post("/auth/register", json={
        "name": "Test Faculty",
        "email": "testfaculty@failsafe.test",
        "password": "testpass123",
        "role": "faculty",
        "department": "Computer Science",
    })
    assert r.status_code in (201, 400)  # 400 if already exists

    # Login
    r = client.post("/auth/login", json={
        "email": "testfaculty@failsafe.test",
        "password": "testpass123",
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    return data["access_token"]

def test_login_invalid_credentials():
    r = client.post("/auth/login", json={
        "email": "nobody@failsafe.test",
        "password": "wrongpassword",
    })
    assert r.status_code == 401

def test_me_requires_auth():
    r = client.get("/auth/me")
    assert r.status_code == 403  # No bearer token

def test_me_with_token():
    token = test_register_and_login()
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "testfaculty@failsafe.test"

def test_refresh_token():
    r = client.post("/auth/login", json={
        "email": "testfaculty@failsafe.test",
        "password": "testpass123",
    })
    if r.status_code != 200:
        pytest.skip("User not registered yet")
    refresh = r.json()["refresh_token"]
    r2 = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    assert "access_token" in r2.json()
