"""
SHAP explainability module.
Generates per-student SHAP values and a plain-English summary.
"""
import numpy as np
from typing import Dict, Tuple, List
import shap

# Feature display names for plain-English output
FEATURE_LABELS = {
    "absences": "absence rate",
    "failures": "history of past failures",
    "studytime": "weekly study time",
    "Walc": "weekend alcohol consumption",
    "Dalc": "workday alcohol consumption",
    "famsup": "family educational support",
    "health": "health status",
    "goout": "frequency of going out",
    "romantic": "relationship status",
    "internet": "home internet access",
    "age": "age",
    "Medu": "mother's education level",
    "Fedu": "father's education level",
    "higher": "aspiration for higher education",
    "schoolsup": "school extra support",
    "activities": "extracurricular activities",
    "freetime": "free time after school",
    "famrel": "family relationship quality",
    "traveltime": "travel time to school",
    # Engineered features
    "disengagement_ratio": "academic disengagement (absences vs study time)",
    "support_index": "total support level (family + school + tutoring)",
    "alcohol_load": "weekly alcohol consumption load",
    "lifestyle_imbalance": "leisure vs study imbalance",
    "parental_edu": "combined parental education level",
    # Grades
    "G1": "first period grade",
    "G2": "second period grade",
}


_explainers = {}


def compute_shap_values(model, X_vector: list, feature_names: list = None) -> Dict[str, float]:
    """
    Compute SHAP values for a single feature vector.
    Returns a dict mapping feature_name -> shap_value.

    Args:
        model: Trained XGBoost model.
        X_vector: Feature values as a list/array.
        feature_names: Ordered list of feature names matching X_vector.
    """
    X = np.array([X_vector])
    
    model_id = id(model)
    if model_id not in _explainers:
        _explainers[model_id] = shap.TreeExplainer(model)
        
    explainer = _explainers[model_id]
    sv = explainer.shap_values(X)  # shape: (1, n_features)
    # For binary classification, sv may be a list [class0, class1]
    if isinstance(sv, list):
        sv = sv[1]

    if feature_names is None:
        # Fallback: use generic feature names
        feature_names = [f"feature_{i}" for i in range(len(X_vector))]

    return {feat: float(sv[0][i]) for i, feat in enumerate(feature_names)}


def generate_shap_summary(shap_dict: Dict[str, float], risk_level: str) -> str:
    """
    Generate a plain-English explanation from the top SHAP drivers.
    """
    # Sort by absolute SHAP value, descending
    sorted_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
    top_positive = [(f, v) for f, v in sorted_features if v > 0][:3]
    top_negative = [(f, v) for f, v in sorted_features if v < 0][:2]

    parts = []
    if top_positive:
        drivers = ", ".join(
            FEATURE_LABELS.get(f, f) for f, _ in top_positive
        )
        parts.append(f"The primary risk drivers are: {drivers}.")

    if top_negative:
        protectors = ", ".join(
            FEATURE_LABELS.get(f, f) for f, _ in top_negative
        )
        parts.append(f"Protective factors include: {protectors}.")

    if risk_level == "HIGH":
        parts.append("Immediate intervention is strongly recommended.")
    elif risk_level == "MEDIUM":
        parts.append("Monitor closely and consider preventive support.")
    else:
        parts.append("Student appears stable; continue regular check-ins.")

    return " ".join(parts)
