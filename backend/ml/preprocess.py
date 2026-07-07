"""
ML Preprocessing pipeline — 3-Phase Adaptive System.

FAILSAFE uses three prediction phases based on which grade data is available:

  Phase 0  →  Before Term 1 exams  →  behavioural + socio-demographic + engineered features
  Phase 1  →  After Term 1 exams   →  + G1 first period grade
  Phase 2  →  After Term 2 exams   →  + G1 + G2 second period grade

Per Problem Statement: "not just final grades" — G1/G2 are intermediate assessments,
not final grades, and are valid additional signals when available. Behavioural features
(absences, studytime, failures, Walc, etc.) remain the core foundation in ALL phases.

Encoding strategy:
  - Binary yes/no columns → 0/1 integer encoding
  - Nominal multi-class columns (Mjob, Fjob, reason, guardian, school, sex,
    address, famsize, Pstatus) → One-Hot Encoding (drop_first=False)
  - Engineered interaction features added for stronger behavioural signal
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import json

# ── Base feature sets (shared across all phases) ──────────────────────────────

CATEGORICAL_FEATURES = [
    "school", "sex", "address", "famsize", "Pstatus",
    "Mjob", "Fjob", "reason", "guardian",
    "schoolsup", "famsup", "paid", "activities",
    "nursery", "higher", "internet", "romantic",
]

NUMERIC_FEATURES = [
    # Socio-demographic
    "age", "Medu", "Fedu",
    # Academic behaviour
    "traveltime", "studytime", "failures",
    # Social & lifestyle (behavioural signals per PS)
    "famrel", "freetime", "goout",
    "Dalc", "Walc", "health",
    # Attendance — primary early-warning signal
    "absences",
]

# Engineered interaction features (domain-specific behavioural signals)
ENGINEERED_FEATURES = [
    "disengagement_ratio",   # absences / (studytime + 1)
    "support_index",         # famsup + schoolsup + paid
    "alcohol_load",          # (Dalc * 5) + (Walc * 2)
    "lifestyle_imbalance",   # goout + freetime - studytime
    "parental_edu",          # Medu + Fedu
]

# Base features that are fully represented by engineered interaction features
# and should be excluded from final training features to avoid SHAP dilution.
REDUNDANT_BASE_FEATURES = {
    "absences", "studytime", "Dalc", "Walc", "goout", "freetime",
    "Medu", "Fedu", "schoolsup", "famsup", "paid"
}

# Binary yes/no categoricals (clean with 0/1 mapping)
BINARY_CATS = {"schoolsup", "famsup", "paid", "activities", "nursery",
               "higher", "internet", "romantic"}

# Nominal multi-class categoricals → One-Hot Encoded
NOMINAL_CATS = [c for c in CATEGORICAL_FEATURES if c not in BINARY_CATS]
# → school, sex, address, famsize, Pstatus, Mjob, Fjob, reason, guardian

# Mapping for binary yes/no columns
YES_NO_MAP = {"yes": 1, "no": 0}

# ── Phase-specific feature lists ───────────────────────────────────────────────
# NOTE: PHASE_FEATURES is now dynamically computed after one-hot encoding.
# These base lists define the raw column inputs before encoding.

_BASE_RAW_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES  # 30 raw columns

PHASE_FEATURES = {
    0: _BASE_RAW_FEATURES,                       # 30 raw → expanded after OHE
    1: _BASE_RAW_FEATURES + ["G1"],              # 31 raw
    2: _BASE_RAW_FEATURES + ["G1", "G2"],        # 32 raw
}

# Default — backward-compatible alias
ALL_FEATURES = _BASE_RAW_FEATURES


# ── Core preprocessing functions ───────────────────────────────────────────────

def _add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add domain-specific interaction features that capture compound risks."""
    studytime = pd.to_numeric(df.get("studytime", 1), errors="coerce").fillna(1)
    absences = pd.to_numeric(df.get("absences", 0), errors="coerce").fillna(0)
    famsup = pd.to_numeric(df.get("famsup", 0), errors="coerce").fillna(0)
    schoolsup = pd.to_numeric(df.get("schoolsup", 0), errors="coerce").fillna(0)
    paid = pd.to_numeric(df.get("paid", 0), errors="coerce").fillna(0)
    Dalc = pd.to_numeric(df.get("Dalc", 0), errors="coerce").fillna(0)
    Walc = pd.to_numeric(df.get("Walc", 0), errors="coerce").fillna(0)
    goout = pd.to_numeric(df.get("goout", 0), errors="coerce").fillna(0)
    freetime = pd.to_numeric(df.get("freetime", 0), errors="coerce").fillna(0)
    Medu = pd.to_numeric(df.get("Medu", 0), errors="coerce").fillna(0)
    Fedu = pd.to_numeric(df.get("Fedu", 0), errors="coerce").fillna(0)

    df["disengagement_ratio"] = absences / (studytime + 1)
    df["support_index"] = famsup + schoolsup + paid
    df["alcohol_load"] = (Dalc * 5) + (Walc * 2)
    df["lifestyle_imbalance"] = goout + freetime - studytime
    df["parental_edu"] = Medu + Fedu

    return df


def _encode_binary_cats(df: pd.DataFrame) -> pd.DataFrame:
    """Encode binary yes/no categoricals to 0/1."""
    for col in BINARY_CATS:
        if col not in df.columns:
            df[col] = 0
            continue
        if df[col].dtype == object:
            df[col] = df[col].str.lower().map(YES_NO_MAP).fillna(0).astype(int)
    return df



def preprocess_dataframe(df: pd.DataFrame, phase: int = 0) -> pd.DataFrame:
    """
    Full preprocessing pipeline for training/batch DataFrames.

    Uses One-Hot Encoding for nominal categoricals and adds engineered
    interaction features for stronger behavioural signal.

    Args:
        df:    Raw UCI student DataFrame.
        phase: Prediction phase (0 = no grades, 1 = +G1, 2 = +G1+G2).

    Returns:
        DataFrame with encoded features for the given phase.
    """
    if phase not in (0, 1, 2):
        raise ValueError(f"Invalid phase {phase}. Must be 0, 1, or 2.")

    df = df.copy()

    # 1. Encode binary categoricals (yes/no → 0/1)
    df = _encode_binary_cats(df)

    # 2. Prepare nominal categoricals for one-hot encoding
    for col in NOMINAL_CATS:
        if col not in df.columns:
            df[col] = "unknown"
        elif df[col].dtype == object:
            df[col] = df[col].str.lower()

    # 3. Fill/encode numeric features
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0

    # Absences scale & leak mitigation
    if "absences" in df.columns:
        if phase == 0:
            df["absences"] = 0.0
        elif phase == 1:
            df["absences"] = df["absences"] / 3.0
        elif phase == 2:
            df["absences"] = df["absences"] / 1.5

    # 4. Encode grade columns if needed for this phase
    for grade_col in ["G1", "G2"]:
        if grade_col in PHASE_FEATURES.get(phase, []):
            if grade_col in df.columns:
                df[grade_col] = pd.to_numeric(df[grade_col], errors="coerce").fillna(0)
            else:
                df[grade_col] = 0

    # 5. Add engineered interaction features
    df = _add_engineered_features(df)

    # 6. Select columns for this phase (filtering out redundant features to avoid SHAP dilution)
    binary_cols = [c for c in BINARY_CATS if c not in REDUNDANT_BASE_FEATURES]
    numeric_cols = [c for c in NUMERIC_FEATURES if c not in REDUNDANT_BASE_FEATURES]
    
    engineered_cols = ENGINEERED_FEATURES[:]
    if phase == 0:
        # Exclude disengagement_ratio since absences=0 in Phase 0
        if "disengagement_ratio" in engineered_cols:
            engineered_cols.remove("disengagement_ratio")

    grade_cols = []
    if phase >= 1:
        grade_cols.append("G1")
    if phase >= 2:
        grade_cols.append("G2")

    keep_cols = (sorted(binary_cols) + NOMINAL_CATS + sorted(numeric_cols) +
                 engineered_cols + grade_cols)
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols]

    # 7. One-Hot encode nominal multi-class columns
    nominal_present = [c for c in NOMINAL_CATS if c in df.columns]
    if nominal_present:
        df = pd.get_dummies(df, columns=nominal_present,
                            drop_first=False, dtype=int)

    return df


def encode_row(row: dict, phase: int = 0) -> dict:
    """Encode a single prediction row dict into numeric values for the given phase."""
    # Build a single-row DataFrame and run through the full pipeline
    row_df = pd.DataFrame([row])
    processed = preprocess_dataframe(row_df, phase=phase)
    return processed.iloc[0].to_dict()


def get_feature_vector(row: dict, phase: int = 0) -> list:
    """Convert a raw row dict to an ordered feature vector for the given phase."""
    if phase not in (0, 1, 2):
        raise ValueError(f"Invalid phase {phase}. Must be 0, 1, or 2.")
    row_df = pd.DataFrame([row])
    processed = preprocess_dataframe(row_df, phase=phase)
    
    # Align features if saved features list exists
    base_dir = os.path.dirname(os.path.abspath(__file__))
    features_path = os.path.join(base_dir, "models", f"features_phase{phase}.json")
    if os.path.exists(features_path):
        with open(features_path) as f:
            saved_features = json.load(f).get("features", [])
        for col in saved_features:
            if col not in processed.columns:
                processed[col] = 0
        processed = processed[saved_features]
    else:
        # Fallback if no saved features (e.g. before training)
        encoded = encode_row(row, phase=phase)
        return list(encoded.values())
        
    return list(processed.iloc[0].values)


def get_feature_names(df: pd.DataFrame, phase: int = 0) -> list:
    """Get the ordered list of feature names after preprocessing a sample DataFrame."""
    processed = preprocess_dataframe(df.head(1), phase=phase)
    return list(processed.columns)
