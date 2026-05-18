"""
SHAP explainability module.
Generates per-student SHAP values and a plain-English summary.
"""
import numpy as np
from typing import Dict, Tuple, List
import shap
from ml.preprocess import ALL_FEATURES

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
}


def compute_shap_values(model, X_vector: list) -> Dict[str, float]:
    """
    Compute SHAP values for a single feature vector.
    Returns a dict mapping feature_name → shap_value.
    """
    import numpy as np
    X = np.array([X_vector])
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X)  # shape: (1, n_features)
    # For binary classification, sv may be a list [class0, class1]
    if isinstance(sv, list):
        sv = sv[1]
    return {feat: float(sv[0][i]) for i, feat in enumerate(ALL_FEATURES)}


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
