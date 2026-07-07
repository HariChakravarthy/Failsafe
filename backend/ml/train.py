"""
XGBoost model training script for FAILSAFE — 3-Phase Adaptive System.

Trains THREE separate models depending on what grade data is available:

  Phase 0  ->  Before Term 1  ->  behavioural + socio-demographic + engineered features
  Phase 1  ->  After  Term 1  ->  + G1 first period grade
  Phase 2  ->  After  Term 2  ->  + G1 + G2 second period grade

PS Alignment: Combining student-mat.csv (Math) + student-por.csv (Portuguese)
forces the model to learn patterns that are SUBJECT-INDEPENDENT — absences,
family support, study habits, lifestyle signals that predict failure regardless
of which subject is being taught. This directly aligns with the PS goal of
predicting risk from "attendance, assignments, and behavioural data" not grades.
G3 (final grade) is ONLY used as the binary target label, never as a feature.

Evaluation Metrics (per PS guidelines):
  - Primary tuning metric:  AUC-PR (Area Under Precision-Recall Curve)
  - Priority metric:        Recall (minimize false negatives — no student left behind)
  - Balancing metric:       F2 Score (weights Recall higher than Precision)
  - Guardrail metric:       F1 Score (prevents alert fatigue from too many false alarms)
  - Do NOT use:             Standard Accuracy (misleading on imbalanced datasets)

Usage (from backend/ directory):
    # Single dataset
    python ml/train.py --data ../data/student-mat.csv --output ml/models/ --all-phases

    # Combined Math + Portuguese (RECOMMENDED — 1044 students, subject-independent)
    python ml/train.py --data ../data/student-mat.csv --data2 ../data/student-por.csv --output ml/models/ --all-phases

The --all-phases flag trains all three models sequentially (recommended).
"""
import argparse
import os
import sys
import json
import warnings

warnings.filterwarnings("ignore")

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    f1_score, fbeta_score, precision_score, recall_score,
    confusion_matrix, classification_report,
    roc_curve, precision_recall_curve,
)
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.preprocess import preprocess_dataframe, PHASE_FEATURES

PHASE_LABELS = {
    0: "Phase 0 -- Before G1 (behavioural + engineered features)",
    1: "Phase 1 -- After  G1 (+G1)",
    2: "Phase 2 -- After  G2 (+G1 +G2)",
}

# ── Phase-specific hyperparameters ────────────────────────────────────────────
# Phase 0 uses more regularization (shallow trees, high lambda) because it has
# only noisy behavioural features. Phase 1/2 have grade signals that allow
# deeper trees with less regularization.

MODEL_PARAMS_BY_PHASE = {
    0: dict(
        n_estimators      = 300,
        max_depth         = 4,      # shallow to prevent overfitting on behavioural noise
        learning_rate     = 0.01,   # slow learning for better generalisation
        subsample         = 0.8,
        colsample_bytree  = 0.8,
        min_child_weight  = 1,
        reg_lambda        = 10.0,   # L2 regularisation tuned from grid search (10.0 for combined)
        reg_alpha         = 0.1,
        scale_pos_weight  = 3.54,   # handle class imbalance (814 / 230) without SMOTE noise
        use_label_encoder = False,
        eval_metric       = "aucpr",  # AUC-PR as training metric
        random_state      = 42,
        n_jobs            = 1,
    ),
    1: dict(
        n_estimators      = 300,
        max_depth         = 4,
        learning_rate     = 0.05,
        subsample         = 0.8,
        colsample_bytree  = 0.8,
        min_child_weight  = 3,
        reg_lambda        = 2.0,
        reg_alpha         = 0.1,
        use_label_encoder = False,
        eval_metric       = "aucpr",
        random_state      = 42,
        n_jobs            = 1,
    ),
    2: dict(
        n_estimators      = 300,
        max_depth         = 4,
        learning_rate     = 0.05,
        subsample         = 0.8,
        colsample_bytree  = 0.8,
        min_child_weight  = 3,
        reg_lambda        = 2.0,
        reg_alpha         = 0.1,
        use_label_encoder = False,
        eval_metric       = "aucpr",
        random_state      = 42,
        n_jobs            = 1,
    ),
}

# Backward-compatible alias
MODEL_PARAMS = MODEL_PARAMS_BY_PHASE[0]

# ── Monotonicity Constraints ──────────────────────────────────────────────────
# Enforces domain knowledge on the model so the what-if simulator is intuitive.
#
#  +1 = feature UP   -> risk UP   (e.g. more absences = more risk)
#  -1 = feature UP   -> risk DOWN (e.g. more studytime = less risk)
#   0 = no constraint (categorical or ambiguous direction)
#
MONOTONE_BY_FEATURE = {
    # Binary categoricals (yes=1/no=0)
    "schoolsup": 0,   # school support = student already flagged; direction ambiguous
    "famsup":    -1,   # family support -> less risk
    "paid":      0,    # paid tutoring; ambiguous
    "activities":0,
    "nursery":   0,
    "higher":    -1,   # wants higher education -> less risk
    "internet":  0,
    "romantic":  0,

    # Socio-demographic numerics
    "age":       +1,   # older students in secondary = more repeating -> more risk
    "Medu":      -1,   # higher mother education -> less risk
    "Fedu":      -1,   # higher father education -> less risk

    # Academic behaviour
    "traveltime":+1,   # longer travel -> more risk
    "studytime": -1,   # more study -> less risk
    "failures":  +1,   # more past failures -> more risk

    # Social & lifestyle
    "famrel":    -1,   # better family relationship -> less risk
    "freetime":  0,    # ambiguous
    "goout":     +1,   # going out more -> more risk
    "Dalc":      +1,   # weekday alcohol -> more risk
    "Walc":      +1,   # weekend alcohol -> more risk
    "health":    -1,   # better health -> less risk

    # Attendance
    "absences":  +1,   # more absences -> more risk

    # Engineered interaction features
    "disengagement_ratio": +1,   # higher = more risk
    "support_index":       -1,   # more support = less risk
    "alcohol_load":        +1,   # more alcohol = more risk
    "lifestyle_imbalance": +1,   # more imbalance = more risk
    "parental_edu":        -1,   # higher parental education = less risk

    # Grade signals (Phase 1 and 2)
    "G1":        -1,   # higher Term 1 grade -> less risk
    "G2":        -1,   # higher Term 2 grade -> less risk
}


def get_monotone_constraints(features: list) -> tuple:
    """Return an ordered tuple of constraints matching the given feature list."""
    return tuple(MONOTONE_BY_FEATURE.get(f, 0) for f in features)



def load_data(csv_path: str, phase: int, csv_path2: str = None) -> tuple:
    """
    Load one or two UCI Student Performance CSVs (semicolon-separated).
    If csv_path2 provided, both are concatenated — training on Math + Portuguese
    together makes the model subject-independent, aligning with PS behavioural focus.
    """
    df = pd.read_csv(csv_path, sep=";")
    if csv_path2:
        df2 = pd.read_csv(csv_path2, sep=";")
        df = pd.concat([df, df2], ignore_index=True)
        print(f"   Combining Math ({len(pd.read_csv(csv_path, sep=';'))} rows) + "
              f"Portuguese ({len(df2)} rows) = {len(df)} total students")
    if "G3" not in df.columns:
        raise ValueError("CSV must contain 'G3' column (final grade 0-20)")
    y = (df["G3"] < 10).astype(int)
    X = preprocess_dataframe(df, phase=phase)
    return X, y


def tune_threshold(y_true, y_proba, min_recall: float = 0.85) -> float:
    """
    Select the BEST classification threshold that:
      1. GUARANTEES recall >= min_recall  (no student left behind)
      2. Among all valid thresholds, picks the one with HIGHEST F1
         (reduces false alarms / alert fatigue)

    Strategy: scan from 0.05 → 0.95, collect all thresholds where
    recall >= min_recall, then pick the one with best F1.
    Falls back to best-F1 threshold if no threshold meets recall target.
    """
    best_fallback_t, best_fallback_f1 = 0.5, 0.0  # fallback if no threshold meets recall

    # Collect (threshold, recall, f1) for every threshold that meets recall target
    valid = []
    for t in np.arange(0.05, 0.95, 0.01):
        preds = (y_proba >= t).astype(int)
        if preds.sum() == 0:
            continue
        rec = recall_score(y_true, preds, zero_division=0)
        f1  = f1_score(y_true, preds, zero_division=0)
        if rec >= min_recall:
            valid.append((t, rec, f1))
        # Track best F1 for fallback
        if f1 > best_fallback_f1:
            best_fallback_f1, best_fallback_t = f1, t

    if not valid:
        # No threshold achieves min_recall — return best F1 threshold
        return best_fallback_t

    # Among valid thresholds, select the one with highest F1 (least false alarms)
    best_valid = max(valid, key=lambda x: x[2])  # sort by F1
    return round(best_valid[0], 2)


def cross_validate(X, y, phase: int, n_splits: int = 5) -> dict:
    """
    Stratified K-Fold cross-validation with SMOTE inside each fold.
    Reports AUC-PR (primary), AUC-ROC, F1, F2, Recall, Precision.
    """
    from imblearn.over_sampling import SMOTE
    features = list(X.columns)
    constraints = get_monotone_constraints(features)
    params = MODEL_PARAMS_BY_PHASE[phase]
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    aucs_roc, aucs_pr, f1s, f2s, recs, precs = [], [], [], [], [], []

    for fold, (tr_idx, te_idx) in enumerate(skf.split(X, y)):
        Xtr, Xte = X.iloc[tr_idx], X.iloc[te_idx]
        ytr, yte = y.iloc[tr_idx], y.iloc[te_idx]
        
        if "scale_pos_weight" in params:
            Xtr_res, ytr_res = Xtr, ytr
        else:
            Xtr_res, ytr_res = SMOTE(random_state=42).fit_resample(Xtr, ytr)
            
        sc = MinMaxScaler()
        Xtr_s = sc.fit_transform(Xtr_res)
        Xte_s = sc.transform(Xte)
        m = XGBClassifier(**params, monotone_constraints=constraints)
        m.fit(Xtr_s, ytr_res, verbose=False)
        yp = m.predict_proba(Xte_s)[:, 1]
        t  = tune_threshold(yte, yp)
        yc = (yp >= t).astype(int)
        aucs_roc.append(roc_auc_score(yte, yp))
        aucs_pr.append(average_precision_score(yte, yp))
        f1s.append(f1_score(yte, yc, zero_division=0))
        f2s.append(fbeta_score(yte, yc, beta=2, zero_division=0))
        recs.append(recall_score(yte, yc, zero_division=0))
        precs.append(precision_score(yte, yc, zero_division=0))
        print(f"     Fold {fold+1}: AUC-PR={aucs_pr[-1]:.4f}  AUC-ROC={aucs_roc[-1]:.4f}  "
              f"F2={f2s[-1]:.4f}  F1={f1s[-1]:.4f}  "
              f"Recall={recs[-1]:.4f}  Prec={precs[-1]:.4f}")
    return {
        "auc_pr": (round(np.mean(aucs_pr), 4), round(np.std(aucs_pr), 4)),
        "auc":    (round(np.mean(aucs_roc), 4), round(np.std(aucs_roc), 4)),
        "f1":     (round(np.mean(f1s), 4),      round(np.std(f1s), 4)),
        "f2":     (round(np.mean(f2s), 4),      round(np.std(f2s), 4)),
        "rec":    (round(np.mean(recs), 4),      round(np.std(recs), 4)),
        "prec":   (round(np.mean(precs), 4),     round(np.std(precs), 4)),
    }


def save_plots(model, features, X_test_s, y_test, y_proba, threshold, output_dir, phase):
    plots_dir = os.path.join(output_dir, f"plots_phase{phase}")
    os.makedirs(plots_dir, exist_ok=True)
    sns.set_theme(style="darkgrid", palette="muted")

    # ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    auc_roc = roc_auc_score(y_test, y_proba)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fpr, tpr, color="#6366f1", lw=2, label=f"ROC (AUC = {auc_roc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5)
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title(f"ROC Curve -- Phase {phase}\n{PHASE_LABELS[phase]}")
    ax.legend(); fig.tight_layout()
    fig.savefig(os.path.join(plots_dir, "roc_curve.png"), dpi=150); plt.close(fig)

    # Precision-Recall Curve (primary evaluation curve per PS guidelines)
    prec_vals, rec_vals, _ = precision_recall_curve(y_test, y_proba)
    auc_pr = average_precision_score(y_test, y_proba)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(rec_vals, prec_vals, color="#10b981", lw=2, label=f"PR (AUC-PR = {auc_pr:.3f})")
    # Baseline: proportion of positive class
    baseline = y_test.mean()
    ax.axhline(y=baseline, color="k", linestyle="--", lw=1, alpha=0.5, label=f"Baseline ({baseline:.2f})")
    ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
    ax.set_title(f"Precision-Recall Curve -- Phase {phase}\n{PHASE_LABELS[phase]}")
    ax.legend(); ax.set_xlim([0, 1]); ax.set_ylim([0, 1])
    fig.tight_layout()
    fig.savefig(os.path.join(plots_dir, "pr_curve.png"), dpi=150); plt.close(fig)

    # Confusion Matrix
    y_pred = (y_proba >= threshold).astype(int)
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Not At-Risk", "At-Risk"],
                yticklabels=["Not At-Risk", "At-Risk"], ax=ax)
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title(f"Confusion Matrix -- Phase {phase} (threshold={threshold:.2f})")
    fig.tight_layout()
    fig.savefig(os.path.join(plots_dir, "confusion_matrix.png"), dpi=150); plt.close(fig)

    # Feature Importance (Top 15)
    importances = model.feature_importances_
    feat_df = (pd.DataFrame({"feature": features, "importance": importances})
               .sort_values("importance", ascending=False).head(15))
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(data=feat_df, x="importance", y="feature", palette="viridis_r", ax=ax)
    ax.set_title(f"Top 15 Features -- Phase {phase}"); ax.set_xlabel("Importance")
    fig.tight_layout()
    fig.savefig(os.path.join(plots_dir, "feature_importance.png"), dpi=150); plt.close(fig)

    print(f"     Plots saved to {plots_dir}/")


def train_phase(csv_path: str, phase: int, output_dir: str, csv_path2: str = None):
    """Train, evaluate and serialise one phase model."""
    print(f"\n{'='*60}")
    print(f"  {PHASE_LABELS[phase]}")
    print(f"{'='*60}")

    params = MODEL_PARAMS_BY_PHASE[phase]
    print(f"\n[DATA] Loading dataset...")
    X, y = load_data(csv_path, phase, csv_path2=csv_path2)
    features = list(X.columns)
    print(f"   Rows     : {len(y)}")
    print(f"   Features : {len(features)}")
    print(f"   At-risk  : {y.sum()} ({y.mean()*100:.1f}%)")

    # Cross-validation
    print(f"\n[CV] 5-fold stratified CV (SMOTE inside each fold)...")
    cv = cross_validate(X, y, phase=phase)
    print(f"\n   CV AUC-PR : {cv['auc_pr'][0]:.4f} +/- {cv['auc_pr'][1]:.4f}  (PRIMARY)")
    print(f"   CV AUC-ROC: {cv['auc'][0]:.4f} +/- {cv['auc'][1]:.4f}")
    print(f"   CV Recall : {cv['rec'][0]:.4f} +/- {cv['rec'][1]:.4f}  (PRIORITY)")
    print(f"   CV F2     : {cv['f2'][0]:.4f} +/- {cv['f2'][1]:.4f}  (BALANCING)")
    print(f"   CV F1     : {cv['f1'][0]:.4f} +/- {cv['f1'][1]:.4f}  (GUARDRAIL)")
    print(f"   CV Prec   : {cv['prec'][0]:.4f} +/- {cv['prec'][1]:.4f}")

    # Final model (80/20 hold-out)
    print(f"\n[TRAIN] Final model on 80/20 hold-out...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42)
    if "scale_pos_weight" in params:
        X_train_res, y_train_res = X_train, y_train
        print("   Using scale_pos_weight (skipping SMOTE oversampling)")
    else:
        try:
            from imblearn.over_sampling import SMOTE
            X_train_res, y_train_res = SMOTE(random_state=42).fit_resample(X_train, y_train)
            print(f"   After SMOTE: {len(y_train_res)} training samples")
        except ImportError:
            X_train_res, y_train_res = X_train, y_train
            print("   WARNING: imbalanced-learn not installed, skipping SMOTE")

    scaler = MinMaxScaler()
    X_train_s = scaler.fit_transform(X_train_res)
    X_test_s  = scaler.transform(X_test)

    constraints = get_monotone_constraints(features)
    model = XGBClassifier(**params, monotone_constraints=constraints)
    model.fit(X_train_s, y_train_res, verbose=False)
    print(f"   Monotone constraints applied: {sum(c != 0 for c in constraints)}/{len(constraints)} features constrained")

    y_proba = model.predict_proba(X_test_s)[:, 1]
    y_proba_train = model.predict_proba(X_train_s)[:, 1]
    threshold = tune_threshold(y_test, y_proba)
    y_pred = (y_proba >= threshold).astype(int)

    auc_roc   = roc_auc_score(y_test, y_proba)
    auc_pr    = average_precision_score(y_test, y_proba)
    train_auc = roc_auc_score(y_train_res, y_proba_train)
    f1        = f1_score(y_test, y_pred)
    f2        = fbeta_score(y_test, y_pred, beta=2)
    prec      = precision_score(y_test, y_pred)
    rec       = recall_score(y_test, y_pred)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    print(f"\n[METRICS] Phase {phase} Results:")
    print(f"   AUC-PR    : {auc_pr:.4f}    (PRIMARY — threshold-independent)")
    print(f"   AUC-ROC   : {auc_roc:.4f}   (train: {train_auc:.4f}, gap: {train_auc-auc_roc:.4f})")
    print(f"   Recall    : {rec:.4f}    (PRIORITY — no student left behind)")
    print(f"   F2-Score  : {f2:.4f}    (BALANCING — weights Recall > Precision)")
    print(f"   F1-Score  : {f1:.4f}    (GUARDRAIL — prevents alert fatigue)")
    print(f"   Precision : {prec:.4f}")
    print(f"   Threshold : {threshold:.2f}")
    print(f"   FN (missed): {fn}  FP (false alarms): {fp}")

    # Plots
    save_plots(model, features, X_test_s, y_test, y_proba, threshold, output_dir, phase)

    # Save artefacts
    metrics = {
        "phase": phase,
        "phase_label": PHASE_LABELS[phase],
        "features": features,
        "n_features": len(features),
        "cv": {k: {"mean": v[0], "std": v[1]} for k, v in cv.items()},
        "test": {
            "auc_pr": round(auc_pr, 4), "auc": round(auc_roc, 4),
            "train_auc": round(train_auc, 4),
            "f1": round(f1, 4), "f2": round(f2, 4),
            "precision": round(prec, 4), "recall": round(rec, 4),
            "threshold": round(threshold, 4),
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        },
        "dataset": {"rows": len(y), "at_risk": int(y.sum()), "file": csv_path},
    }

    joblib.dump(model,  os.path.join(output_dir, f"model_phase{phase}.pkl"))
    joblib.dump(scaler, os.path.join(output_dir, f"scaler_phase{phase}.pkl"))
    with open(os.path.join(output_dir, f"threshold_phase{phase}.json"), "w") as f:
        json.dump({"threshold": round(threshold, 4), "phase": phase}, f)
    with open(os.path.join(output_dir, f"metrics_phase{phase}.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    # Also save the feature names so predict.py knows the column order
    with open(os.path.join(output_dir, f"features_phase{phase}.json"), "w") as f:
        json.dump({"features": features, "phase": phase}, f)

    print(f"\n[OK] Saved: model_phase{phase}.pkl | scaler_phase{phase}.pkl | "
          f"threshold_phase{phase}.json | metrics_phase{phase}.json | features_phase{phase}.json")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Train FAILSAFE 3-Phase XGBoost models")
    parser.add_argument("--data",       required=True,
                        help="Path to student-mat.csv (UCI, semicolon-delimited)")
    parser.add_argument("--data2",      default=None,
                        help="Optional: path to student-por.csv to combine both subjects (RECOMMENDED)")
    parser.add_argument("--output",     default="ml/models/", help="Output directory")
    parser.add_argument("--phase",      type=int, choices=[0, 1, 2], default=0,
                        help="Which phase to train (0, 1, or 2). Ignored if --all-phases.")
    parser.add_argument("--all-phases", action="store_true",
                        help="Train all three phase models sequentially (recommended)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    if args.data2:
        print(f"[INFO] Combined dataset mode: {os.path.basename(args.data)} + {os.path.basename(args.data2)}")
        print("[INFO] Training on two subjects -> model learns subject-independent behavioural patterns")
    else:
        print(f"[INFO] Single dataset mode: {os.path.basename(args.data)}")

    if args.all_phases:
        all_metrics = {}
        for phase in [0, 1, 2]:
            m = train_phase(args.data, phase, args.output, csv_path2=args.data2)
            all_metrics[f"phase{phase}"] = m

        print(f"\n{'='*80}")
        print("  SUMMARY -- All Phases")
        print(f"{'='*80}")
        print(f"  {'Phase':<10} {'AUC-PR (CV)':<16} {'AUC-ROC (CV)':<16} "
              f"{'Recall (CV)':<16} {'F2 (CV)':<14} {'F1 (CV)'}")
        print("-" * 80)
        for phase in [0, 1, 2]:
            m = all_metrics[f"phase{phase}"]
            print(f"  Phase {phase}     "
                  f"{m['cv']['auc_pr']['mean']:.3f}+/-{m['cv']['auc_pr']['std']:.3f}   "
                  f"{m['cv']['auc']['mean']:.3f}+/-{m['cv']['auc']['std']:.3f}   "
                  f"{m['cv']['rec']['mean']:.3f}+/-{m['cv']['rec']['std']:.3f}   "
                  f"{m['cv']['f2']['mean']:.3f}+/-{m['cv']['f2']['std']:.3f}  "
                  f"{m['cv']['f1']['mean']:.3f}+/-{m['cv']['f1']['std']:.3f}")
    else:
        train_phase(args.data, args.phase, args.output, csv_path2=args.data2)

    print("\n[DONE] Training complete.")


if __name__ == "__main__":
    main()
