"""
Tests for the ML prediction pipeline — 3-Phase Adaptive System.

Covers:
- score_to_risk_level thresholds (recalibrated to HIGH>=0.50, MEDIUM>=0.20)
- Feature vector lengths for all 3 phases
- Phase-aware mock scoring (heuristic fallback)
- SHAP summary generation
- Students list API (auth guard + response shape)
- 3-phase upload parameter validation
"""
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


# ── API Guard Tests ────────────────────────────────────────────────────────────

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


# ── score_to_risk_level — recalibrated thresholds ─────────────────────────────

def test_score_high():
    from ml.predict import score_to_risk_level
    assert score_to_risk_level(0.50) == "HIGH"
    assert score_to_risk_level(0.75) == "HIGH"
    assert score_to_risk_level(0.95) == "HIGH"


def test_score_medium():
    from ml.predict import score_to_risk_level
    assert score_to_risk_level(0.20) == "MEDIUM"
    assert score_to_risk_level(0.35) == "MEDIUM"
    assert score_to_risk_level(0.49) == "MEDIUM"


def test_score_low():
    from ml.predict import score_to_risk_level
    assert score_to_risk_level(0.00) == "LOW"
    assert score_to_risk_level(0.10) == "LOW"
    assert score_to_risk_level(0.19) == "LOW"


# ── Feature vector lengths — all 3 phases ─────────────────────────────────────

def test_feature_vector_phase0_length():
    """Phase 0: 30 features (no grades)."""
    from ml.preprocess import get_feature_vector, PHASE_FEATURES
    row = {"absences": 10, "studytime": 2, "failures": 1}
    vec = get_feature_vector(row, phase=0)
    assert len(vec) == len(PHASE_FEATURES[0]) == 30


def test_feature_vector_phase1_length():
    """Phase 1: 31 features (+G1)."""
    from ml.preprocess import get_feature_vector, PHASE_FEATURES
    row = {"absences": 10, "studytime": 2, "failures": 1, "G1": 8}
    vec = get_feature_vector(row, phase=1)
    assert len(vec) == len(PHASE_FEATURES[1]) == 31


def test_feature_vector_phase2_length():
    """Phase 2: 32 features (+G1+G2)."""
    from ml.preprocess import get_feature_vector, PHASE_FEATURES
    row = {"absences": 10, "studytime": 2, "failures": 1, "G1": 8, "G2": 7}
    vec = get_feature_vector(row, phase=2)
    assert len(vec) == len(PHASE_FEATURES[2]) == 32


def test_feature_vector_invalid_phase():
    """Phase 3 does not exist — should raise ValueError."""
    from ml.preprocess import get_feature_vector
    with pytest.raises(ValueError):
        get_feature_vector({}, phase=3)


# ── G1/G2 NOT in Phase 0 ──────────────────────────────────────────────────────

def test_g1_g2_absent_in_phase0():
    """G1 and G2 must not appear in Phase 0 feature list."""
    from ml.preprocess import PHASE_FEATURES
    assert "G1" not in PHASE_FEATURES[0]
    assert "G2" not in PHASE_FEATURES[0]


def test_g1_present_in_phase1():
    from ml.preprocess import PHASE_FEATURES
    assert "G1" in PHASE_FEATURES[1]
    assert "G2" not in PHASE_FEATURES[1]


def test_g1_g2_present_in_phase2():
    from ml.preprocess import PHASE_FEATURES
    assert "G1" in PHASE_FEATURES[2]
    assert "G2" in PHASE_FEATURES[2]


# ── Mock scoring heuristic — all 3 phases ─────────────────────────────────────

def test_mock_score_high_risk_student():
    """A student with many absences + failures should score high."""
    from ml.predict import _mock_score
    row = {"absences": 50, "failures": 3, "studytime": 1, "Walc": 5}
    score = _mock_score(row, phase=0)
    assert score >= 0.50, f"Expected HIGH risk, got {score}"


def test_mock_score_low_risk_student():
    """A model student should score low."""
    from ml.predict import _mock_score
    row = {"absences": 0, "failures": 0, "studytime": 4, "Walc": 1}
    score = _mock_score(row, phase=0)
    assert score < 0.40, f"Expected LOW risk, got {score}"


def test_mock_score_phase1_higher_with_bad_g1():
    """Phase 1 with a bad G1 (score=3) should score higher than phase 0."""
    from ml.predict import _mock_score
    row = {"absences": 10, "failures": 1, "studytime": 2, "Walc": 2, "G1": 3}
    score_p0 = _mock_score(row, phase=0)
    score_p1 = _mock_score(row, phase=1)
    assert score_p1 >= score_p0, "Phase 1 with bad G1 should have >= risk than phase 0"


def test_mock_score_phase2_higher_with_bad_g2():
    """Phase 2 with a bad G2 should score higher than phase 1."""
    from ml.predict import _mock_score
    row = {"absences": 10, "failures": 1, "studytime": 2, "Walc": 2, "G1": 4, "G2": 3}
    score_p1 = _mock_score(row, phase=1)
    score_p2 = _mock_score(row, phase=2)
    assert score_p2 >= score_p1, "Phase 2 with bad G2 should have >= risk than phase 1"


def test_mock_score_stays_in_range():
    """Score must always be between 0 and 1."""
    from ml.predict import _mock_score
    extreme_row = {"absences": 999, "failures": 999, "studytime": 0, "Walc": 5}
    for phase in [0, 1, 2]:
        score = _mock_score(extreme_row, phase=phase)
        assert 0.0 <= score <= 1.0, f"Score out of range for phase {phase}: {score}"


# ── Trained model loading ──────────────────────────────────────────────────────

def test_model_files_exist():
    """All 3 phase model files should exist after training."""
    import os
    for phase in [0, 1, 2]:
        assert os.path.exists(f"ml/models/model_phase{phase}.pkl"), \
            f"model_phase{phase}.pkl missing — run train.py --all-phases first"
        assert os.path.exists(f"ml/models/scaler_phase{phase}.pkl"), \
            f"scaler_phase{phase}.pkl missing"
        assert os.path.exists(f"ml/models/threshold_phase{phase}.json"), \
            f"threshold_phase{phase}.json missing"


def test_metrics_json_exists():
    """metrics_phase*.json should exist and contain expected keys."""
    import os, json
    for phase in [0, 1, 2]:
        path = f"ml/models/metrics_phase{phase}.json"
        assert os.path.exists(path), f"metrics_phase{phase}.json missing"
        data = json.load(open(path))
        assert "cv" in data
        assert "test" in data
        assert "auc" in data["test"]
        assert "recall" in data["test"]


def test_phase2_auc_better_than_phase0():
    """Phase 2 should always have better AUC than Phase 0 (more features)."""
    import json
    m0 = json.load(open("ml/models/metrics_phase0.json"))["test"]["auc"]
    m2 = json.load(open("ml/models/metrics_phase2.json"))["test"]["auc"]
    assert m2 > m0, f"Phase 2 AUC ({m2}) should be > Phase 0 AUC ({m0})"


def test_trained_model_predicts_valid_phase0():
    """Loaded Phase 0 model produces a probability in [0,1]."""
    from ml.predict import run_simulation
    row = {"absences": 10, "studytime": 2, "failures": 1, "Walc": 3,
           "sex": "M", "address": "U", "school": "GP", "higher": "yes",
           "internet": "yes", "famsup": "yes", "romantic": "no",
           "age": 17, "Medu": 2, "Fedu": 2}
    result = run_simulation(row, phase=0)
    assert "risk_score" in result
    assert 0.0 <= result["risk_score"] <= 1.0
    assert result["risk_level"] in ("HIGH", "MEDIUM", "LOW")
    assert result["phase"] == 0


def test_trained_model_predicts_valid_phase2():
    """Loaded Phase 2 model (+G1+G2) produces higher confidence for a failing student."""
    from ml.predict import run_simulation
    # Student clearly at-risk: low grades, high absences
    row_atrisk = {"absences": 20, "studytime": 1, "failures": 2,
                  "Walc": 4, "G1": 4, "G2": 3,
                  "sex": "M", "address": "R", "school": "GP",
                  "higher": "no", "internet": "no", "famsup": "no",
                  "age": 19, "Medu": 1, "Fedu": 1}
    result = run_simulation(row_atrisk, phase=2)
    assert result["risk_level"] in ("HIGH", "MEDIUM")
    assert result["risk_score"] > 0.10


# ── SHAP summary ──────────────────────────────────────────────────────────────

def test_shap_summary_generates():
    from ml.explain import generate_shap_summary
    shap_dict = {
        "absences":  0.35,
        "failures":  0.28,
        "studytime": -0.20,
        "famsup":    -0.10,
        "Walc":       0.15,
    }
    summary = generate_shap_summary(shap_dict, "HIGH")
    assert isinstance(summary, str)
    assert len(summary) > 20


def test_shap_summary_for_low_risk():
    from ml.explain import generate_shap_summary
    shap_dict = {
        "studytime": -0.30,
        "famsup":    -0.25,
        "higher":    -0.20,
        "absences":   0.02,
        "failures":   0.01,
    }
    summary = generate_shap_summary(shap_dict, "LOW")
    assert isinstance(summary, str)
    assert len(summary) > 10


# ── Upload endpoint phase parameter ───────────────────────────────────────────

def test_upload_rejects_invalid_phase():
    """Phase must be 0, 1, or 2. Phase 5 should be rejected."""
    token = get_token()
    import io
    csv_content = b"student_code,absences,studytime,failures\nS001,5,2,0\n"
    r = client.post(
        "/students/upload?week_number=1&phase=5",
        files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422  # FastAPI validation error


def test_upload_accepts_phase0():
    """Phase 0 upload should succeed without G1/G2 columns."""
    token = get_token()
    import io
    csv_content = (
        b"student_code,absences,studytime,failures,sex,age,school,address,"
        b"famsize,Pstatus,Medu,Fedu,Mjob,Fjob,reason,guardian,"
        b"schoolsup,famsup,paid,activities,nursery,higher,internet,romantic,"
        b"traveltime,famrel,freetime,goout,Dalc,Walc,health\n"
        b"S999,5,2,0,M,17,GP,U,GT3,T,2,2,other,other,course,mother,"
        b"no,yes,no,yes,yes,yes,yes,no,1,4,3,2,1,2,4\n"
    )
    r = client.post(
        "/students/upload?week_number=1&phase=0",
        files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "total_uploaded" in data
    assert data["total_uploaded"] >= 1
