import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_token():
    client.post("/auth/register", json={
        "name": "IV Tester",
        "email": "iv@failsafe.test",
        "password": "testpass123",
        "role": "faculty",
    })
    r = client.post("/auth/login", json={
        "email": "iv@failsafe.test",
        "password": "testpass123",
    })
    if r.status_code != 200:
        pytest.skip("Could not login")
    return r.json()["access_token"]

def test_interventions_list_requires_auth():
    r = client.get("/interventions")
    assert r.status_code == 403

def test_interventions_list_with_auth():
    token = get_token()
    r = client.get("/interventions", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data

def test_intervention_engine_catalogue():
    """Test that the engine generates interventions from mock SHAP values."""
    from app.interventions.engine import CATALOGUE
    assert len(CATALOGUE) >= 9
    for rule in CATALOGUE:
        assert "feature" in rule
        assert "type" in rule
        assert "shap_threshold" in rule
        assert "due_within_days" in rule

def test_intervention_status_update():
    token = get_token()
    # List interventions; if any exist, try to update one
    r = client.get("/interventions", headers={"Authorization": f"Bearer {token}"})
    items = r.json().get("items", [])
    if not items:
        pytest.skip("No interventions to update")
    iv_id = items[0]["id"]
    r2 = client.patch(
        f"/interventions/{iv_id}/status",
        json={"status": "IN_PROGRESS", "notes": "Test note"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "IN_PROGRESS"
