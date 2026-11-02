#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""02_compas.py -- Build data/processed/compas.npz (+ .json) from ProPublica COMPAS.

Paper alignment (Roy & Mohapatra, UAI 2026, Sec. 6.2.2 + Appendix):
  * ProPublica COMPAS (Larson, 2016) ``compas-scores-two-years`` format, preprocessed as in
    Zafar et al. (2019): after preprocessing the dataset contains 5,278 subjects with
    5 features; Race is the sensitive attribute; label = recidivism within two years.

Preprocessing (reproduces the paper's 5,278 rows):
  1. keep rows with      -30 <= days_b_screening_arrest <= 30
  2. keep rows with      is_recid != -1
  3. keep rows with      c_charge_degree != 'O'
  4. keep rows with      score_text != 'N/A'
  5. keep rows with      race in {African-American, Caucasian}
     (steps 1-4 alone give 6,172 rows -- exactly ProPublica's analysis set; the extra
      restriction to the two racial groups used by Zafar et al. gives exactly 5,278 rows,
      hence it is the step that reproduces the paper's count.)
  Note: the four listed filters are no-ops beyond step 1 on this particular file except that
  they are applied in order for reproducibility/auditability.

Features (5): sex, age, race, priors_count, c_charge_degree
  * sex: Male = 1, Female = 0
  * race: African-American = 1, Caucasian = 0  (this column equals the sensitive attribute z)
  * c_charge_degree: F (felony) = 1, M (misdemeanor) = 0
  * age, priors_count: raw numeric values (NO standardization)
Label: two_year_recid -> +1 if recidivated within two years else -1.
Sensitive: z = 1 if African-American else 0.

Output:
  data/processed/compas.npz   X (n x 5, float64), y (n, int8 in {-1,+1}), z (n, int8 in {0,1})
  data/processed/compas.json  metadata
"""
import json
import os

from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------- project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = Path(os.environ.get("FUQ_RAW_DIR") or (PROJECT_ROOT / "data" / "raw"))
RAW_COMPAS = RAW_DIR / "compas.csv"
OUT_DIR = PROJECT_ROOT / "data" / "processed"
OUT_NPZ = OUT_DIR / "compas.npz"
OUT_JSON = OUT_DIR / "compas.json"

SEED = 20261026  # fixed for project-wide reproducibility; this script has no random operation

FEATURES = ["sex", "age", "race", "priors_count", "c_charge_degree"]
EXPECTED_N = 5278  # Zafar et al. (2019) / Roy & Mohapatra (2026) preprocessing count


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RAW_COMPAS)
    raw_n = len(df)
    print(f"[compas] raw rows read from {RAW_COMPAS.name}: {raw_n}")

    # 1. screening window
    m = df["days_b_screening_arrest"].between(-30, 30)
    print(f"[compas] after days_b_screening_arrest in [-30, 30]: {int(m.sum())}")
    df = df[m]
    # 2. valid recidivism outcome
    m = df["is_recid"] != -1
    print(f"[compas] after is_recid != -1: {int(m.sum())}")
    df = df[m]
    # 3. charge degree (drop 'O' = ordinary traffic offences)
    m = df["c_charge_degree"] != "O"
    print(f"[compas] after c_charge_degree != 'O': {int(m.sum())}")
    df = df[m]
    # 4. valid risk score text
    m = df["score_text"] != "N/A"
    print(f"[compas] after score_text != 'N/A': {int(m.sum())}")
    df = df[m]
    print(f"[compas] after the four ProPublica filters: {len(df)} rows "
          f"(= ProPublica analysis subset); race counts: {df['race'].value_counts().to_dict()}")
    # 5. two-group race definition used by Zafar et al. (== the paper's 5,278)
    m = df["race"].isin(["African-American", "Caucasian"])
    df = df[m].reset_index(drop=True)
    n = len(df)
    print(f"[compas] after race in {{African-American, Caucasian}}: {n}")

    if n != EXPECTED_N:
        print(f"[compas] WARNING: expected {EXPECTED_N} rows (paper/Zafar count), got {n}")

    # ---- encode the 5 features --------------------------------------------------------------
    X = np.empty((n, len(FEATURES)), dtype=np.float64)
    sex = df["sex"].to_numpy()
    race = df["race"].to_numpy()
    charge = df["c_charge_degree"].to_numpy()
    assert set(np.unique(sex)) == {"Male", "Female"}, np.unique(sex)
    assert set(np.unique(race)) == {"African-American", "Caucasian"}, np.unique(race)
    assert set(np.unique(charge)) == {"F", "M"}, np.unique(charge)

    X[:, 0] = (sex == "Male").astype(np.float64)
    X[:, 1] = df["age"].to_numpy(dtype=np.float64)
    X[:, 2] = (race == "African-American").astype(np.float64)
    X[:, 3] = df["priors_count"].to_numpy(dtype=np.float64)
    X[:, 4] = (charge == "F").astype(np.float64)

    y = np.where(df["two_year_recid"].to_numpy() == 1, 1, -1).astype(np.int8)
    z = X[:, 2].astype(np.int8)

    # ---- sanity checks ----------------------------------------------------------------------
    assert X.shape == (n, len(FEATURES)), X.shape
    assert np.isfinite(X).all(), "non-finite value in X"
    assert not df["two_year_recid"].isna().any(), "NaN in two_year_recid"
    assert set(np.unique(y)) == {-1, 1}, np.unique(y)
    assert set(np.unique(z)) == {0, 1}, np.unique(z)
    zero_var = np.flatnonzero(X.std(axis=0) == 0)
    assert zero_var.size == 0, f"zero-variance columns: {[FEATURES[i] for i in zero_var]}"

    pos_rate = float((y == 1).mean())
    n0, n1 = int((z == 0).sum()), int((z == 1).sum())
    p0 = float((y[z == 0] == 1).mean())
    p1 = float((y[z == 1] == 1).mean())
    print(f"[compas] X: shape={X.shape} dtype={X.dtype}, finite={np.isfinite(X).all()}")
    print(f"[compas] y: +1={int((y == 1).sum())} (-1={int((y == -1).sum())}), "
          f"positive_rate={pos_rate:.6f}")
    print(f"[compas] z: z=0 {n0} ({n0 / n:.4f}), z=1 {n1} ({n1 / n:.4f}); "
          f"positive_rate|z0={p0:.6f}, positive_rate|z1={p1:.6f}")

    # ---- write ------------------------------------------------------------------------------
    np.savez(OUT_NPZ, X=X, y=y, z=z)
    meta = {
        "dataset": "compas",
        "feature_names": FEATURES,
        "sensitive_name": "race",
        "sensitive_definition": {"0": "Caucasian", "1": "African-American"},
        "label_definition": {"+1": "two_year_recid == 1", "-1": "two_year_recid == 0"},
        "n": int(n),
        "p": len(FEATURES),
        "positive_rate": pos_rate,
        "group_sizes": {"0": n0, "1": n1},
        "group_positive_rates": {"0": p0, "1": p1},
        "source": (
            "ProPublica COMPAS recidivism data (Larson, 2016), compas-scores-two-years format; "
            f"local read-only copy: {RAW_COMPAS}"
        ),
        "source_url": "https://github.com/propublica/compas-analysis",
        "raw_rows": int(raw_n),
        "preprocessing": [
            "days_b_screening_arrest in [-30, 30]",
            "is_recid != -1",
            "c_charge_degree != 'O'",
            "score_text != 'N/A'",
            "race in {African-American, Caucasian}",
        ],
        "propublica_filter_rows": 6172,
        "zafar_race_restriction_note": (
            "The four ProPublica filters give 6,172 rows; restricting to the two racial groups "
            "used by Zafar et al. (2019) gives exactly the paper's 5,278 subjects.  "
            "z is therefore binary African-American vs Caucasian."
        ),
        "categorical_encoding": (
            "sex -> Male=1/Female=0; race -> African-American=1/Caucasian=0; "
            "c_charge_degree -> F=1/M=0; age and priors_count kept as raw values"
        ),
        "standardized": False,
        "standardization_note": (
            "age and priors_count are raw; downstream code may z-score them using the raw "
            "column means/stds recorded in feature_mean/feature_std.  A z-score would change "
            "the effective R^2 scale, so it is left to the modelling code."
        ),
        "feature_mean": [float(v) for v in X.mean(axis=0)],
        "feature_std": [float(v) for v in X.std(axis=0)],
        "randomness": "none (deterministic; no train/test split is performed in data prep)",
        "seed": SEED,
        "paper_alignment": (
            "Roy & Mohapatra UAI 2026 Sec. 6.2.2: 5,278 subjects, 5 features "
            "(sex, age, race, priors_count, c_charge_degree), race sensitive, DM experiment.  "
            "The race column is also kept inside X (as the paper lists race among the 5 "
            "features); z is the identical binary column."
        ),
    }
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    print(f"[compas] wrote {OUT_NPZ} ({OUT_NPZ.stat().st_size / 2**10:.1f} KiB)")
    print(f"[compas] wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
