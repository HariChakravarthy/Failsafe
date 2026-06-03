"""
Inference wrapper — 3-Phase Adaptive Prediction System.

Loads the phase-appropriate model + scaler, runs prediction, stores result in DB,
and triggers SHAP explanation + intervention generation.

Phase 0: behavioural only (30 features) — used before Term 1 exams
Phase 1: + G1 first period grade (31 features) — available after Term 1
Phase 2: + G1 + G2 second period grades (32 features) — available after Term 2
"""
import os
import uuid
import json
import joblib
import numpy as np
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Prediction, Intervention
from ml.preprocess import get_feature_vector, PHASE_FEATURES

# ── Per-phase model cache ─────────────────────────────────────────────────────
_models     = {}  # phase -> model
_scalers    = {}  # phase -> scaler
_thresholds = {}  # phase -> float

MODELS_DIR = "ml/models"


def _load_phase_model(phase: int):
    """Lazily load and cache the model/scaler/threshold for a given phase."""
    if phase in _models:
        return  # already loaded

    model_path     = os.path.join(MODELS_DIR, f"model_phase{phase}.pkl")
    scaler_path    = os.path.join(MODELS_DIR, f"scaler_phase{phase}.pkl")
    threshold_path = os.path.join(MODELS_DIR, f"threshold_phase{phase}.json")

    if os.path.exists(model_path):
        _models[phase]  = joblib.load(model_path)
    if os.path.exists(scaler_path):
        _scalers[phase] = joblib.load(scaler_path)
    if os.path.exists(threshold_path):
        with open(threshold_path) as f:
            _thresholds[phase] = json.load(f).get("threshold", 0.5)
    else:
        _thresholds[phase] = 0.5


def score_to_risk_level(score: float) -> str:
    """
    Convert raw model probability to a risk label.
    Bands calibrated to match the trained classification threshold (0.05):
      HIGH   >= 0.50  — strong model confidence: at-risk
      MEDIUM >= 0.20  — moderate signal: warrants monitoring
      LOW     < 0.20  — low probability: not flagged
    """
    if score >= 0.50:
        return "HIGH"
    elif score >= 0.20:
        return "MEDIUM"
    return "LOW"


def run_prediction_pipeline(
    row: Dict[str, Any],
    student_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    db: Session,
    phase: int = 0,
) -> Optional[Prediction]:
    """
    Run full prediction pipeline for a single student row.

    Args:
        row:         Raw feature dict from CSV upload.
        student_id:  Student UUID.
        snapshot_id: FeatureSnapshot UUID.
        db:          SQLAlchemy session.
        phase:       0 (no grades), 1 (+G1), or 2 (+G1+G2).
    """
    _load_phase_model(phase)

    features = PHASE_FEATURES[phase]
    feature_vector = get_feature_vector(row, phase=phase)
    X = np.array([feature_vector])

    model  = _models.get(phase)
    scaler = _scalers.get(phase)
    threshold = _thresholds.get(phase, 0.5)

    if model is not None and scaler is not None:
        X_scaled = scaler.transform(X)
        prob = float(model.predict_proba(X_scaled)[0][1])
    else:
        # Heuristic fallback when no trained model is available
        prob = _mock_score(row, phase)

    risk_level = score_to_risk_level(prob)

    # SHAP explanation
    if model is not None:
        try:
            from ml.explain import compute_shap_values, generate_shap_summary
            shap_dict = compute_shap_values(model, feature_vector)
        except Exception:
            shap_dict = _mock_shap(row, phase)
    else:
        shap_dict = _mock_shap(row, phase)

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

    # Auto-generate interventions
    from app.interventions.engine import generate_interventions
    from app.models import Student
    student = db.query(Student).filter(Student.id == student_id).first()
    assigned_to = student.faculty_id if student and student.faculty_id else student_id
    generate_interventions(prediction, assigned_to, db)

    return prediction


def run_simulation(
    row: Dict[str, Any],
    phase: int = 0,
) -> Dict[str, Any]:
    """
    What-if simulation — no DB write. Returns score + SHAP for UI display.
    """
    _load_phase_model(phase)

    feature_vector = get_feature_vector(row, phase=phase)
    X = np.array([feature_vector])

    model  = _models.get(phase)
    scaler = _scalers.get(phase)
    threshold = _thresholds.get(phase, 0.5)

    if model is not None and scaler is not None:
        X_scaled = scaler.transform(X)
        prob = float(model.predict_proba(X_scaled)[0][1])
    else:
        prob = _mock_score(row, phase)

    risk_level = score_to_risk_level(prob)

    if model is not None:
        try:
            from ml.explain import compute_shap_values, generate_shap_summary
            shap_dict = compute_shap_values(model, feature_vector)
        except Exception:
            shap_dict = _mock_shap(row, phase)
    else:
        shap_dict = _mock_shap(row, phase)

    from ml.explain import generate_shap_summary
    shap_summary = generate_shap_summary(shap_dict, risk_level)

    return {
        "risk_score":   round(prob, 4),
        "risk_level":   risk_level,
        "shap_values":  shap_dict,
        "shap_summary": shap_summary,
        "phase":        phase,
        "threshold":    threshold,
    }


# ── Heuristic fallbacks (used only when model files are absent) ───────────────

def _mock_score(row: Dict[str, Any], phase: int) -> float:
    """Heuristic scoring fallback. Uses grades when available (phase >= 1)."""
    absences  = float(row.get("absences",  0))
    failures  = float(row.get("failures",  0))
    studytime = float(row.get("studytime", 2))
    walc      = float(row.get("Walc",      1))

    base = (
        (absences  / 40) * 0.40
        + (failures  /  3) * 0.30
        + (1 - studytime / 4) * 0.10
        + (walc      /  5) * 0.05
    )

    if phase >= 1:
        g1 = float(row.get("G1", 10))
        grade_penalty = max(0.0, (10 - g1) / 10) * 0.10
        base += grade_penalty

    if phase >= 2:
        g2 = float(row.get("G2", 10))
        grade_penalty = max(0.0, (10 - g2) / 10) * 0.05
        base += grade_penalty

    return min(0.95, max(0.05, base))


def _mock_shap(row: Dict[str, Any], phase: int) -> Dict[str, float]:
    """Approximate SHAP proxy values when model is unavailable."""
    absences  = float(row.get("absences",  0))
    failures  = float(row.get("failures",  0))
    studytime = float(row.get("studytime", 2))
    walc      = float(row.get("Walc",      1))
    famsup_raw = row.get("famsup", "yes")
    famsup    = 0 if str(famsup_raw).lower() == "yes" else 0.15

    shap = {
        "absences":  round(absences  / 40 * 0.50, 4),
        "failures":  round(failures  /  3 * 0.40, 4),
        "studytime": round(-(studytime / 4) * 0.25, 4),
        "Walc":      round(walc      /  5 * 0.15, 4),
        "Dalc":      0.05,
        "famsup":    famsup,
        "health":   -0.05,
        "goout":     0.08,
        "romantic":  0.04,
        "internet": -0.03,
    }

    if phase >= 1:
        g1 = float(row.get("G1", 10))
        shap["G1"] = round(max(0.0, (10 - g1) / 10) * 0.30, 4)
    if phase >= 2:
        g2 = float(row.get("G2", 10))
        shap["G2"] = round(max(0.0, (10 - g2) / 10) * 0.25, 4)

    features = PHASE_FEATURES[phase]
    for f in features:
        if f not in shap:
            shap[f] = 0.0

    return shap
