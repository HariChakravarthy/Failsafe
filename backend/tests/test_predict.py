import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_token():
    client.post("/auth/register", json={
        "name": "Predict Tester",
        "email": "predict@failsafe.com",
        "password": "testpass123",
        "role": "faculty",
    })
    r = client.post("/auth/login", json={
        "email": "predict@failsafe.com",
        "password": "testpass123",
    })
    if r.status_code != 200:
        pytest.skip("Could not login")
    return r.json()["access_token"]

def test_students_list_requires_auth():
    r = client.get("/students")
    assert r.status_code == 403

def test_students_list_with_auth():
    token = get_token()
    r = client.get("/students", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data

def test_prediction_mock_scoring():
    """Test that mock scoring produces valid risk levels without a trained model."""
    from ml.predict import score_to_risk_level
    assert score_to_risk_level(0.8) == "HIGH"
    assert score_to_risk_level(0.5) == "MEDIUM"
    assert score_to_risk_level(0.2) == "LOW"

def test_feature_vector_length():
    from ml.preprocess import get_feature_vector, ALL_FEATURES
    row = {"absences": 10, "studytime": 2, "failures": 1}
    vec = get_feature_vector(row)
    assert len(vec) == len(ALL_FEATURES)

def test_shap_summary_generates():
    from ml.explain import generate_shap_summary
    shap_dict = {
        "absences": 0.35,
        "failures": 0.28,
        "studytime": -0.20,
        "famsup": -0.10,
        "Walc": 0.15,
    }
    summary = generate_shap_summary(shap_dict, "HIGH")
    assert isinstance(summary, str)
    assert len(summary) > 20
