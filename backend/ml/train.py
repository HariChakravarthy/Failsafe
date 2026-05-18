"""
XGBoost model training script.

Usage:
    python ml/train.py --data data/raw/student-mat.csv --output ml/models/

The script:
1. Loads the UCI student CSV
2. Engineers features via preprocess.py
3. Applies SMOTE for class balance
4. Trains XGBoost with GridSearchCV
5. Evaluates and serialises model + scaler
"""
import argparse
import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report,
)
from xgboost import XGBClassifier

# Handle import path when run from backend/ dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.preprocess import preprocess_dataframe, ALL_FEATURES


def load_data(csv_path: str) -> tuple:
    df = pd.read_csv(csv_path)
    # Binarise target: G3 < 10 → at-risk (1)
    if "G3" not in df.columns:
        raise ValueError("CSV must contain 'G3' column")
    y = (df["G3"] < 10).astype(int)
    X = preprocess_dataframe(df)
    return X, y


def main():
    parser = argparse.ArgumentParser(description="Train FAILSAFE XGBoost model")
    parser.add_argument("--data", required=True, help="Path to student CSV (semicolon-separated)")
    parser.add_argument("--output", default="ml/models/", help="Output directory for model files")
    parser.add_argument("--no-smote", action="store_true", help="Disable SMOTE oversampling")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    print("📂 Loading data...")
    X, y = load_data(args.data)
    print(f"   Dataset shape: {X.shape}, at-risk: {y.sum()} / {len(y)}")

    # Train / Val / Test split (70/15/15 stratified)
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42)

    # SMOTE
    if not args.no_smote:
        try:
            from imblearn.over_sampling import SMOTE
            sm = SMOTE(random_state=42)
            X_train, y_train = sm.fit_resample(X_train, y_train)
            print(f"   After SMOTE: {len(y_train)} training samples")
        except ImportError:
            print("   ⚠ imbalanced-learn not installed, skipping SMOTE")

    # Scale
    scaler = MinMaxScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)

    # Hyperparameter grid
    param_grid = {
        "n_estimators": [200, 400],
        "max_depth": [4, 6],
        "learning_rate": [0.05, 0.1],
        "subsample": [0.8, 1.0],
        "colsample_bytree": [0.8, 1.0],
    }

    print("🔍 Running GridSearchCV...")
    base_model = XGBClassifier(
        use_label_encoder=False,
        eval_metric="auc",
        random_state=42,
        n_jobs=1,
    )
    grid = GridSearchCV(base_model, param_grid, cv=5, scoring="roc_auc", n_jobs=1, verbose=1)
    grid.fit(X_train_s, y_train, eval_set=[(X_val_s, y_val)], verbose=False)

    model = grid.best_estimator_
    print(f"   Best params: {grid.best_params_}")

    # Evaluate
    y_pred_proba = model.predict_proba(X_test_s)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    auc = roc_auc_score(y_test, y_pred_proba)
    f1 = f1_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)

    print("\n📊 Evaluation Results:")
    print(f"   AUC-ROC  : {auc:.4f}  (target ≥ 0.88)")
    print(f"   F1       : {f1:.4f}  (target ≥ 0.82)")
    print(f"   Precision: {prec:.4f}  (target ≥ 0.78)")
    print(f"   Recall   : {rec:.4f}  (target ≥ 0.85)")
    print("\n" + classification_report(y_test, y_pred, target_names=["Not At-Risk", "At-Risk"]))

    # Serialise
    model_path = os.path.join(args.output, "xgboost_model.pkl")
    scaler_path = os.path.join(args.output, "scaler.pkl")
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    print(f"\n✅ Model saved to {model_path}")
    print(f"✅ Scaler saved to {scaler_path}")


if __name__ == "__main__":
    main()
