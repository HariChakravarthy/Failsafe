"""
ML Preprocessing pipeline — 3-Phase Adaptive System.

FAILSAFE uses three prediction phases based on which grade data is available:

  Phase 0  →  Before Term 1 exams  →  30 features (behavioural + socio-demographic only)
  Phase 1  →  After Term 1 exams   →  31 features (+ G1 first period grade)
  Phase 2  →  After Term 2 exams   →  32 features (+ G1 + G2 second period grade)

Per Problem Statement: "not just final grades" — G1/G2 are intermediate assessments,
not final grades, and are valid additional signals when available. Behavioural features
(absences, studytime, failures, Walc, etc.) remain the core foundation in ALL phases.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import joblib
import os

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

# ── Phase-specific feature lists ───────────────────────────────────────────────

# Phase 0: No grade data (start of semester)
FEATURES_PHASE_0 = CATEGORICAL_FEATURES + NUMERIC_FEATURES          # 30 features

# Phase 1: First period grade available (after Term 1 exams)
FEATURES_PHASE_1 = CATEGORICAL_FEATURES + NUMERIC_FEATURES + ["G1"] # 31 features

# Phase 2: Both period grades available (after Term 2 exams)
FEATURES_PHASE_2 = CATEGORICAL_FEATURES + NUMERIC_FEATURES + ["G1", "G2"]  # 32 features

PHASE_FEATURES = {
    0: FEATURES_PHASE_0,
    1: FEATURES_PHASE_1,
    2: FEATURES_PHASE_2,
}

# Default — backward-compatible alias (Phase 2 gives best results)
ALL_FEATURES = FEATURES_PHASE_0   # conservative default; train.py overrides per phase

# Mapping for binary yes/no columns
YES_NO_MAP = {"yes": 1, "no": 0}


# ── Core preprocessing functions ───────────────────────────────────────────────

def _encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Encode categorical columns (yes/no → 0/1, others → label encoded)."""
    le = LabelEncoder()
    for col in CATEGORICAL_FEATURES:
        if col not in df.columns:
            df[col] = 0
            continue
        if df[col].dtype == object:
            lower = df[col].str.lower()
            if set(lower.dropna().unique()) <= {"yes", "no"}:
                df[col] = lower.map(YES_NO_MAP).fillna(0).astype(int)
            else:
                df[col] = le.fit_transform(df[col].astype(str))
    return df


def preprocess_dataframe(df: pd.DataFrame, phase: int = 0) -> pd.DataFrame:
    """
    Full preprocessing pipeline for training/batch DataFrames.

    Args:
        df:    Raw UCI student DataFrame.
        phase: Prediction phase (0 = no grades, 1 = +G1, 2 = +G1+G2).

    Returns:
        DataFrame with exactly the features for the given phase.
    """
    if phase not in PHASE_FEATURES:
        raise ValueError(f"Invalid phase {phase}. Must be 0, 1, or 2.")

    features = PHASE_FEATURES[phase]
    df = df.copy()

    # Encode categoricals
    df = _encode_categoricals(df)

    # Fill/encode numeric features (behavioural base)
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0

    # Encode grade columns if needed for this phase
    for grade_col in ["G1", "G2"]:
        if grade_col in features:
            if grade_col in df.columns:
                df[grade_col] = pd.to_numeric(df[grade_col], errors="coerce").fillna(0)
            else:
                df[grade_col] = 0   # missing grade → 0 (safe fallback)

    return df[features]


def encode_row(row: dict, phase: int = 0) -> dict:
    """Encode a single prediction row dict into numeric values for the given phase."""
    features = PHASE_FEATURES[phase]
    encoded = {}

    for col in CATEGORICAL_FEATURES:
        val = row.get(col, "unknown")
        if isinstance(val, str):
            val_lower = val.lower()
            if val_lower in ("yes", "no"):
                encoded[col] = YES_NO_MAP.get(val_lower, 0)
            else:
                encoded[col] = hash(val_lower) % 100
        else:
            encoded[col] = int(val) if pd.notna(val) else 0

    for col in NUMERIC_FEATURES:
        val = row.get(col, 0)
        try:
            encoded[col] = float(val) if pd.notna(val) else 0.0
        except (ValueError, TypeError):
            encoded[col] = 0.0

    # Grade columns (only for phase 1 and 2)
    for grade_col in ["G1", "G2"]:
        if grade_col in features:
            try:
                encoded[grade_col] = float(row.get(grade_col, 0))
            except (ValueError, TypeError):
                encoded[grade_col] = 0.0

    return encoded


def get_feature_vector(row: dict, phase: int = 0) -> list:
    """Convert a raw row dict to an ordered feature vector for the given phase."""
    if phase not in PHASE_FEATURES:
        raise ValueError(f"Invalid phase {phase}. Must be 0, 1, or 2.")
    features = PHASE_FEATURES[phase]
    encoded = encode_row(row, phase=phase)
    return [encoded.get(f, 0) for f in features]
