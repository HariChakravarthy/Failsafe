"""
Inference wrapper.
Loads the trained model + scaler, runs prediction, stores result in DB,
and triggers SHAP explanation + intervention generation.
"""
import os
import uuid
import joblib
import numpy as np
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Prediction, Intervention
from app.config import settings
from ml.preprocess import get_feature_vector, ALL_FEATURES

_model = None
_scaler = None


def _load_model():
    global _model, _scaler
    if _model is None and os.path.exists(settings.MODEL_PATH):
        _model = joblib.load(settings.MODEL_PATH)
    if _scaler is None and os.path.exists(settings.SCALER_PATH):
        _scaler = joblib.load(settings.SCALER_PATH)


def score_to_risk_level(score: float) -> str:
    if score >= 0.65:
        return "HIGH"
    elif score >= 0.35:
        return "MEDIUM"
    return "LOW"


def run_prediction_pipeline(
    row: Dict[str, Any],
    student_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    db: Session,
) -> Optional[Prediction]:
    """
    Run full prediction pipeline for a single student row.
    1. Feature vector extraction
    2. Model scoring (or mock scoring if model not trained yet)
    3. SHAP explanation
    4. Persist Prediction + Interventions
    """
    _load_model()

    feature_vector = get_feature_vector(row)
    X = np.array([feature_vector])

    if _model is not None:
        if _scaler is not None:
            X = _scaler.transform(X)
        prob = float(_model.predict_proba(X)[0][1])
    else:
        # Heuristic mock scoring when model not trained yet
        absences = float(row.get("absences", 0))
        failures = float(row.get("failures", 0))
        studytime = float(row.get("studytime", 2))
        prob = min(0.95, max(0.05, (absences / 40) * 0.5 + (failures / 3) * 0.35 + (1 - studytime / 4) * 0.15))

    risk_level = score_to_risk_level(prob)

    # SHAP values
    if _model is not None:
        try:
            from ml.explain import compute_shap_values, generate_shap_summary
            shap_dict = compute_shap_values(_model, feature_vector)
        except Exception:
            shap_dict = _mock_shap(row)
    else:
        shap_dict = _mock_shap(row)

    from ml.explain import generate_shap_summary
    shap_summary = generate_shap_summary(shap_dict, risk_level)

    prediction = Prediction(
        student_id=student_id,
        snapshot_id=snapshot_id,
        risk_score=round(prob, 4),
        risk_level=risk_level,
        shap_values=shap_dict,
        shap_summary=shap_summary,
    )
    db.add(prediction)
    db.flush()

    # Generate interventions
    from app.interventions.engine import generate_interventions
    # Use student's faculty_id as assigned_to (or a system user)
    from app.models import Student
    student = db.query(Student).filter(Student.id == student_id).first()
    assigned_to = student.faculty_id if student and student.faculty_id else student_id
    generate_interventions(prediction, assigned_to, db)

    return prediction


def _mock_shap(row: Dict[str, Any]) -> Dict[str, float]:
    """Generate approximate SHAP proxy values from raw feature values when model is unavailable."""
    absences = float(row.get("absences", 0))
    failures = float(row.get("failures", 0))
    studytime = float(row.get("studytime", 2))
    walc = float(row.get("Walc", 1))
    famsup_raw = row.get("famsup", "yes")
    famsup = 0 if str(famsup_raw).lower() == "yes" else 0.15

    return {
        "absences": round(absences / 40 * 0.5, 4),
        "failures": round(failures / 3 * 0.4, 4),
        "studytime": round(-(studytime / 4) * 0.25, 4),
        "Walc": round(walc / 5 * 0.15, 4),
        "Dalc": 0.05,
        "famsup": famsup,
        "health": -0.05,
        "goout": 0.08,
        "romantic": 0.04,
        "internet": -0.03,
        **{f: 0.0 for f in ALL_FEATURES if f not in {
            "absences", "failures", "studytime", "Walc", "Dalc",
            "famsup", "health", "goout", "romantic", "internet",
        }},
    }


def run_simulation(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run prediction pipeline for a single row without DB updates/interventions.
    """
    _load_model()

    feature_vector = get_feature_vector(row)
    X = np.array([feature_vector])

    if _model is not None:
        if _scaler is not None:
            X = _scaler.transform(X)
        prob = float(_model.predict_proba(X)[0][1])
    else:
        # Heuristic mock scoring when model not trained yet
        absences = float(row.get("absences", 0))
        failures = float(row.get("failures", 0))
        studytime = float(row.get("studytime", 2))
        prob = min(0.95, max(0.05, (absences / 40) * 0.5 + (failures / 3) * 0.35 + (1 - studytime / 4) * 0.15))

    risk_level = score_to_risk_level(prob)

    # SHAP values
    if _model is not None:
        try:
            from ml.explain import compute_shap_values
            shap_dict = compute_shap_values(_model, feature_vector)
        except Exception:
            shap_dict = _mock_shap(row)
    else:
        shap_dict = _mock_shap(row)

    from ml.explain import generate_shap_summary
    shap_summary = generate_shap_summary(shap_dict, risk_level)

    return {
        "risk_score": round(prob, 4),
        "risk_level": risk_level,
        "shap_values": shap_dict,
        "shap_summary": shap_summary,
    }

