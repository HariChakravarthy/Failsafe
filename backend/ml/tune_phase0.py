"""
tune_phase0.py — Phase 0 AUC Improvement Testbed

Tests 4 strategies in a rigorous Stratified 5-Fold CV setup:
  A) Interaction feature engineering
  B) One-Hot Encoding for nominal categoricals
  C) Hyperparameter tuning (grid search)
  D) scale_pos_weight vs SMOTE for class imbalance

Usage (from backend/):
    python ml/tune_phase0.py --data ../data/student-mat.csv
    python ml/tune_phase0.py --data ../data/student-mat.csv --data2 ../data/student-por.csv
"""
import argparse
import os
import sys
import warnings
import time

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.metrics import roc_auc_score, f1_score, recall_score, precision_score, average_precision_score, fbeta_score
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Constants ──────────────────────────────────────────────────────────────────

CATEGORICAL_FEATURES = [
    "school", "sex", "address", "famsize", "Pstatus",
    "Mjob", "Fjob", "reason", "guardian",
    "schoolsup", "famsup", "paid", "activities",
    "nursery", "higher", "internet", "romantic",
]

NUMERIC_FEATURES = [
    "age", "Medu", "Fedu",
    "traveltime", "studytime", "failures",
    "famrel", "freetime", "goout",
    "Dalc", "Walc", "health",
    "absences",
]

# Binary yes/no categoricals (already clean with label encoding)
BINARY_CATS = {"schoolsup", "famsup", "paid", "activities", "nursery",
               "higher", "internet", "romantic"}

# Nominal categoricals that should be one-hot encoded
NOMINAL_CATS = [c for c in CATEGORICAL_FEATURES if c not in BINARY_CATS]
# → school, sex, address, famsize, Pstatus, Mjob, Fjob, reason, guardian

YES_NO_MAP = {"yes": 1, "no": 0}

REDUNDANT_BASE_FEATURES = {
    "absences", "studytime", "Dalc", "Walc", "goout", "freetime",
    "Medu", "Fedu", "schoolsup", "famsup", "paid"
}

BASE_PARAMS = dict(
    n_estimators=300, max_depth=4, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
    reg_lambda=2.0, reg_alpha=0.1, use_label_encoder=False,
    eval_metric="auc", random_state=42, n_jobs=1,
)


# ── Data Loading ───────────────────────────────────────────────────────────────

def load_data(csv_path, csv_path2=None):
    df = pd.read_csv(csv_path, sep=";")
    if csv_path2 and os.path.exists(csv_path2):
        df2 = pd.read_csv(csv_path2, sep=";")
        df = pd.concat([df, df2], ignore_index=True)
        print(f"   Combined: {len(df)} students")
    y = (df["G3"] < 10).astype(int)
    return df, y


# ── Preprocessing Variants ─────────────────────────────────────────────────────

def encode_baseline(df):
    """Current production encoding: label encode all categoricals."""
    out = df.copy()
    le = LabelEncoder()
    for col in CATEGORICAL_FEATURES:
        if col not in out.columns:
            out[col] = 0
            continue
        if out[col].dtype == object:
            lower = out[col].str.lower()
            if set(lower.dropna().unique()) <= {"yes", "no"}:
                out[col] = lower.map(YES_NO_MAP).fillna(0).astype(int)
            else:
                out[col] = le.fit_transform(out[col].astype(str))
    for col in NUMERIC_FEATURES:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
        else:
            out[col] = 0
    features = CATEGORICAL_FEATURES + NUMERIC_FEATURES
    return out[features]


def encode_onehot(df):
    """One-hot encode nominal categoricals; label encode binaries; mitigate absences leak."""
    out = df.copy()
    
    # Absences leak mitigation (Phase 0 = 0 absences)
    if "absences" in out.columns:
        out["absences"] = 0.0

    # Binary categoricals
    for col in BINARY_CATS:
        if col in out.columns and out[col].dtype == object:
            out[col] = out[col].str.lower().map(YES_NO_MAP).fillna(0).astype(int)
        elif col not in out.columns:
            out[col] = 0

    # Nominal categoricals → one-hot
    for col in NOMINAL_CATS:
        if col not in out.columns:
            out[col] = "unknown"
        elif out[col].dtype == object:
            out[col] = out[col].str.lower()

    # Numerics
    for col in NUMERIC_FEATURES:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
        else:
            out[col] = 0

    # Select relevant columns, then one-hot encode nominals
    keep_cols = list(BINARY_CATS) + NOMINAL_CATS + NUMERIC_FEATURES
    out = out[[c for c in keep_cols if c in out.columns]]
    out = pd.get_dummies(out, columns=[c for c in NOMINAL_CATS if c in out.columns],
                          drop_first=False, dtype=int)
    return out


def add_interaction_features(X):
    """Add domain-specific engineered interaction features."""
    X = X.copy()

    # Disengagement ratio: high absences + low study = critical risk
    studytime = X["studytime"] if "studytime" in X.columns else 1
    absences = X["absences"] if "absences" in X.columns else 0
    X["disengagement_ratio"] = absences / (studytime + 1)

    # Support index: aggregate support signals
    famsup = X.get("famsup", 0)
    schoolsup = X.get("schoolsup", 0)
    paid = X.get("paid", 0)
    if isinstance(famsup, pd.Series):
        X["support_index"] = famsup + schoolsup + paid
    else:
        X["support_index"] = 0

    # Alcohol load: weekday alcohol is heavier signal than weekend
    Dalc = X["Dalc"] if "Dalc" in X.columns else 0
    Walc = X["Walc"] if "Walc" in X.columns else 0
    X["alcohol_load"] = (Dalc * 5) + (Walc * 2)

    # Lifestyle imbalance: going out + free time - study time
    goout = X["goout"] if "goout" in X.columns else 0
    freetime = X["freetime"] if "freetime" in X.columns else 0
    X["lifestyle_imbalance"] = goout + freetime - studytime

    # Parental education synergy
    Medu = X["Medu"] if "Medu" in X.columns else 0
    Fedu = X["Fedu"] if "Fedu" in X.columns else 0
    X["parental_edu"] = Medu + Fedu

    return X


def drop_redundant_features(X):
    X = X.copy()
    # Exclude disengagement_ratio since absences=0 in Phase 0
    if "disengagement_ratio" in X.columns:
        X = X.drop(columns=["disengagement_ratio"])
    # Exclude redundant base features
    cols_to_drop = [c for c in REDUNDANT_BASE_FEATURES if c in X.columns]
    X = X.drop(columns=cols_to_drop)
    return X


# ── Evaluation Engine ──────────────────────────────────────────────────────────

def tune_threshold(y_true, y_proba, min_recall=0.85):
    best_fallback_t, best_fallback_f1 = 0.5, 0.0
    valid = []
    for t in np.arange(0.05, 0.95, 0.01):
        preds = (y_proba >= t).astype(int)
        if preds.sum() == 0:
            continue
        rec = recall_score(y_true, preds, zero_division=0)
        f1  = f1_score(y_true, preds, zero_division=0)
        if rec >= min_recall:
            valid.append((t, rec, f1))
        if f1 > best_fallback_f1:
            best_fallback_f1, best_fallback_t = f1, t

    if not valid:
        return best_fallback_t

    best_valid = max(valid, key=lambda x: x[2])
    return round(best_valid[0], 2)


def run_cv(X, y, params, use_smote=True, n_splits=5):
    """Run stratified k-fold CV with given params and preprocessing."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    aucs, aucs_pr, f1s, f2s, recs, precs = [], [], [], [], [], []

    for tr_idx, te_idx in skf.split(X, y):
        if isinstance(X, pd.DataFrame):
            Xtr, Xte = X.iloc[tr_idx].values, X.iloc[te_idx].values
            ytr, yte = y.iloc[tr_idx].values, y.iloc[te_idx].values
        else:
            Xtr, Xte = X[tr_idx], X[te_idx]
            ytr, yte = y[tr_idx], y[te_idx]

        if use_smote:
            try:
                from imblearn.over_sampling import SMOTE
                Xtr, ytr = SMOTE(random_state=42).fit_resample(Xtr, ytr)
            except ImportError:
                pass

        sc = MinMaxScaler()
        Xtr_s = sc.fit_transform(Xtr)
        Xte_s = sc.transform(Xte)

        model = XGBClassifier(**params)
        model.fit(Xtr_s, ytr, verbose=False)

        yp = model.predict_proba(Xte_s)[:, 1]
        t = tune_threshold(yte, yp)
        yc = (yp >= t).astype(int)

        aucs.append(roc_auc_score(yte, yp))
        aucs_pr.append(average_precision_score(yte, yp))
        f1s.append(f1_score(yte, yc, zero_division=0))
        f2s.append(fbeta_score(yte, yc, beta=2, zero_division=0))
        recs.append(recall_score(yte, yc, zero_division=0))
        precs.append(precision_score(yte, yc, zero_division=0))

    return {
        "auc_pr_mean": round(np.mean(aucs_pr), 4),
        "auc_pr_std":  round(np.std(aucs_pr), 4),
        "auc_mean": round(np.mean(aucs), 4),
        "auc_std":  round(np.std(aucs), 4),
        "f1_mean":  round(np.mean(f1s), 4),
        "f2_mean":  round(np.mean(f2s), 4),
        "rec_mean": round(np.mean(recs), 4),
        "prec_mean": round(np.mean(precs), 4),
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Tune Phase 0 AUC")
    parser.add_argument("--data", required=True)
    parser.add_argument("--data2", default=None)
    args = parser.parse_args()

    print("=" * 72)
    print("  FAILSAFE — Phase 0 AUC Improvement Testbed")
    print("=" * 72)

    df, y = load_data(args.data, args.data2)
    print(f"   Students: {len(y)} | At-risk: {y.sum()} ({y.mean()*100:.1f}%)")

    results = []

    # ─── BASELINE ─────────────────────────────────────────────────────────
    print("\n[1/8] Baseline (current production)...")
    X_base = encode_baseline(df)
    r = run_cv(X_base, y, BASE_PARAMS, use_smote=True)
    r["config"] = "Baseline (label-encode + SMOTE)"
    results.append(r)
    print(f"       AUC-PR={r['auc_pr_mean']}±{r['auc_pr_std']}  AUC-ROC={r['auc_mean']}  F2={r['f2_mean']}  Rec={r['rec_mean']}")

    # ─── A: Feature Engineering (on baseline encoding) ────────────────────
    print("\n[2/8] + Interaction Features (on label-encoded base)...")
    X_feat = add_interaction_features(X_base)
    r = run_cv(X_feat, y, BASE_PARAMS, use_smote=True)
    r["config"] = "Baseline + Interaction Features"
    results.append(r)
    print(f"       AUC-PR={r['auc_pr_mean']}±{r['auc_pr_std']}  AUC-ROC={r['auc_mean']}  F2={r['f2_mean']}  Rec={r['rec_mean']}")

    # ─── B: One-Hot Encoding ──────────────────────────────────────────────
    print("\n[3/8] One-Hot Encoding (no interactions)...")
    X_oh = encode_onehot(df)
    r = run_cv(X_oh, y, BASE_PARAMS, use_smote=True)
    r["config"] = "One-Hot Encoding"
    results.append(r)
    print(f"       AUC-PR={r['auc_pr_mean']}±{r['auc_pr_std']}  AUC-ROC={r['auc_mean']}  F2={r['f2_mean']}  Rec={r['rec_mean']}")

    # ─── A+B: One-Hot + Interactions ──────────────────────────────────────
    print("\n[4/8] One-Hot + Interaction Features (with Redundant Drop)...")
    X_oh_feat = add_interaction_features(X_oh)
    X_oh_feat = drop_redundant_features(X_oh_feat)
    r = run_cv(X_oh_feat, y, BASE_PARAMS, use_smote=True)
    r["config"] = "One-Hot + Interaction Features"
    results.append(r)
    print(f"       AUC-PR={r['auc_pr_mean']}±{r['auc_pr_std']}  AUC-ROC={r['auc_mean']}  F2={r['f2_mean']}  Rec={r['rec_mean']}")

    # ─── D: scale_pos_weight instead of SMOTE ─────────────────────────────
    neg_count = (y == 0).sum()
    pos_count = (y == 1).sum()
    spw = round(neg_count / pos_count, 2)

    print(f"\n[5/8] Baseline + scale_pos_weight={spw} (no SMOTE)...")
    spw_params = {**BASE_PARAMS, "scale_pos_weight": spw}
    r = run_cv(X_base, y, spw_params, use_smote=False)
    r["config"] = f"Baseline + scale_pos_weight={spw}"
    results.append(r)
    print(f"       AUC-PR={r['auc_pr_mean']}±{r['auc_pr_std']}  AUC-ROC={r['auc_mean']}  F2={r['f2_mean']}  Rec={r['rec_mean']}")

    print(f"\n[6/8] One-Hot + Interactions + scale_pos_weight={spw} (no SMOTE)...")
    r = run_cv(X_oh_feat, y, spw_params, use_smote=False)
    r["config"] = f"One-Hot + Interactions + SPW={spw}"
    results.append(r)
    print(f"       AUC-PR={r['auc_pr_mean']}±{r['auc_pr_std']}  AUC-ROC={r['auc_mean']}  F2={r['f2_mean']}  Rec={r['rec_mean']}")

    # ─── C: Hyperparameter Tuning ─────────────────────────────────────────
    # Use the best encoding from above (One-Hot + Interactions)
    print(f"\n[7/8] Hyperparameter grid (One-Hot + Interactions + SMOTE)...")
    best_grid_r = None
    best_grid_cfg = ""
    grid_count = 0
    for md in [2, 3, 4]:
        for lr in [0.01, 0.03, 0.05, 0.1]:
            for mcw in [1, 3, 5]:
                for rl in [2.0, 5.0, 10.0]:
                    grid_count += 1
                    p = {**BASE_PARAMS,
                         "max_depth": md, "learning_rate": lr,
                         "min_child_weight": mcw, "reg_lambda": rl}
                    r = run_cv(X_oh_feat, y, p, use_smote=True)
                    cfg = f"OH+Feat SMOTE md={md} lr={lr} mcw={mcw} rl={rl}"
                    r["config"] = cfg
                    if best_grid_r is None or r["auc_pr_mean"] > best_grid_r["auc_pr_mean"]:
                        best_grid_r = r
                        best_grid_cfg = cfg
                    if grid_count % 18 == 0:
                        print(f"       ... searched {grid_count} combos, best so far: AUC-PR={best_grid_r['auc_pr_mean']}")

    print(f"       Grid search complete ({grid_count} combos)")
    print(f"       Best: {best_grid_cfg}")
    print(f"       AUC-PR={best_grid_r['auc_pr_mean']}±{best_grid_r['auc_pr_std']}  "
          f"AUC-ROC={best_grid_r['auc_mean']}  F2={best_grid_r['f2_mean']}  Rec={best_grid_r['rec_mean']}")
    results.append(best_grid_r)

    # ─── C+D: Best grid + scale_pos_weight ────────────────────────────────
    print(f"\n[8/8] Best grid params + scale_pos_weight (no SMOTE)...")
    # Extract params from best grid config
    parts = best_grid_cfg.split()
    best_md = int([p for p in parts if p.startswith("md=")][0].split("=")[1])
    best_lr = float([p for p in parts if p.startswith("lr=")][0].split("=")[1])
    best_mcw = int([p for p in parts if p.startswith("mcw=")][0].split("=")[1])
    best_rl = float([p for p in parts if p.startswith("rl=")][0].split("=")[1])
    final_params = {**BASE_PARAMS,
                    "max_depth": best_md, "learning_rate": best_lr,
                    "min_child_weight": best_mcw, "reg_lambda": best_rl,
                    "scale_pos_weight": spw}
    r = run_cv(X_oh_feat, y, final_params, use_smote=False)
    r["config"] = f"OH+Feat SPW md={best_md} lr={best_lr} mcw={best_mcw} rl={best_rl}"
    results.append(r)
    print(f"       AUC-PR={r['auc_pr_mean']}±{r['auc_pr_std']}  AUC-ROC={r['auc_mean']}  F2={r['f2_mean']}  Rec={r['rec_mean']}")

    # ─── RANKED RESULTS ──────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  RANKED RESULTS (by AUC-PR)")
    print("=" * 80)
    results.sort(key=lambda x: x["auc_pr_mean"], reverse=True)
    print(f"  {'Rank':<5} {'AUC-PR':<14} {'AUC-ROC':<10} {'F2':<8} {'F1':<8} {'Recall':<8}  Config")
    print("-" * 80)
    for i, r in enumerate(results):
        marker = " *BEST*" if i == 0 else ""
        print(f"  {i+1:<5} {r['auc_pr_mean']:.4f}±{r['auc_pr_std']:.3f} "
              f"{r['auc_mean']:.4f}     {r['f2_mean']:.4f}  {r['f1_mean']:.4f}  {r['rec_mean']:.4f}   "
              f"{r['config']}{marker}")

    baseline_auc = results[-1]["auc_pr_mean"] if results[-1]["config"].startswith("Baseline (") else results[0]["auc_pr_mean"]
    for r in results:
        if r["config"].startswith("Baseline ("):
            baseline_auc = r["auc_pr_mean"]
            break
    best = results[0]
    improvement = best["auc_pr_mean"] - baseline_auc
    print(f"\n  Baseline AUC-PR : {baseline_auc:.4f}")
    print(f"  Best AUC-PR     : {best['auc_pr_mean']:.4f}  (+{improvement:.4f})")
    print(f"  Best Config     : {best['config']}")
    print()


if __name__ == "__main__":
    main()
