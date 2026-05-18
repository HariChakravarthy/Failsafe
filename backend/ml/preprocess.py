"""
ML Preprocessing pipeline.
Handles encoding, scaling, and feature alignment for the XGBoost model.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import joblib
import os

# Feature columns used during training — must match exactly
CATEGORICAL_FEATURES = [
    "school", "sex", "address", "famsize", "Pstatus",
    "Mjob", "Fjob", "reason", "guardian",
    "schoolsup", "famsup", "paid", "activities",
    "nursery", "higher", "internet", "romantic",
]

NUMERIC_FEATURES = [
    "age", "Medu", "Fedu", "traveltime", "studytime",
    "failures", "famrel", "freetime", "goout",
    "Dalc", "Walc", "health", "absences",
]

ALL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES

# Mapping for binary yes/no columns
YES_NO_MAP = {"yes": 1, "no": 0}


def encode_row(row: dict) -> dict:
    """Encode a single row dict into numeric values."""
    encoded = {}
    for col in CATEGORICAL_FEATURES:
        val = row.get(col, "unknown")
        if isinstance(val, str):
            val_lower = val.lower()
            if val_lower in ("yes", "no"):
                encoded[col] = YES_NO_MAP.get(val_lower, 0)
            else:
                # Simple hash-based encode for unseen categoricals
                encoded[col] = hash(val_lower) % 100
        else:
            encoded[col] = int(val) if pd.notna(val) else 0

    for col in NUMERIC_FEATURES:
        val = row.get(col, 0)
        try:
            encoded[col] = float(val) if pd.notna(val) else 0.0
        except (ValueError, TypeError):
            encoded[col] = 0.0

    return encoded


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Full preprocessing pipeline for a training/batch DataFrame."""
    df = df.copy()

    # Binary encode yes/no columns
    yes_no_cols = [c for c in CATEGORICAL_FEATURES if c in df.columns]
    for col in yes_no_cols:
        if df[col].dtype == object:
            df[col] = df[col].str.lower().map(YES_NO_MAP).fillna(0).astype(int)

    # Label-encode remaining string categoricals
    le = LabelEncoder()
    for col in CATEGORICAL_FEATURES:
        if col in df.columns and df[col].dtype == object:
            df[col] = le.fit_transform(df[col].astype(str))

    # Fill missing numerics
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Add missing columns with 0
    for col in ALL_FEATURES:
        if col not in df.columns:
            df[col] = 0

    return df[ALL_FEATURES]


def get_feature_vector(row: dict) -> list:
    """Convert a raw row dict to an ordered feature vector."""
    encoded = encode_row(row)
    return [encoded.get(f, 0) for f in ALL_FEATURES]
