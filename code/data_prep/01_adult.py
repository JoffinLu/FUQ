#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""01_adult.py -- Build data/processed/adult.npz (+ .json) from the UCI Adult dataset.

Paper alignment (Roy & Mohapatra, UAI 2026, Sec. 6.1.2 + Appendix):
  * 13 raw attributes used as features (all UCI attributes except ``fnlwgt`` and the label
    ``income``); they include ``sex``.
  * sensitive attribute: sex (Male = 1, Female = 0); label: income > 50K -> +1 else -1.

Data used:
  Local read-only copy of the UCI Adult *training* split:
    D:\\...\\fairness_unawareness\\data\\raw\\adult.data   (32,561 rows)
  The local ``adult.test`` copy is TRUNCATED (9,216 complete rows, the file ends in the middle
  of the last record), so it is NOT merged here.  ``adult.data`` alone is the canonical
  training pool used by Zafar et al. and is large enough for the |D'| = |D~| = 1000 protocol.
  This is documented in data/processed/MANIFEST.md.

Pipeline (deterministic, no randomness):
  1. read adult.data (no header, UCI column names), strip surrounding spaces;
  2. drop every row containing a '?' missing token (2,399 rows on the train split);
  3. drop ``fnlwgt`` and ``income`` -> 13 raw attributes;
  4. one-hot encode the 8 categorical attributes with drop_first=True (the model carries an
     intercept, so the first level of each attribute is absorbed by it and no dummy trap);
     the 5 numeric attributes are kept as raw values (NO standardization);
  5. y = +1 if income == '>50K' else -1, z = 1 if sex == 'Male' else 0.

Output:
  data/processed/adult.npz   X (n x p, float64), y (n, int8 in {-1,+1}), z (n, int8 in {0,1})
  data/processed/adult.json  feature_names, sensitive_name, n, p, positive_rate, group_sizes, source, ...
"""
import json
import os

from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------- absolute paths
PROJECT_ROOT = Path(r"D:\Desktop\Data\学习类\硕士研究生\文献阅读\DSH\fuq-fairness")
RAW_DIR = Path(os.environ.get("FUQ_RAW_DIR") or (PROJECT_ROOT / "data" / "raw"))
if not (RAW_DIR / "adult.data").exists():
    _LEGACY = Path(r"D:\Desktop\Data\学习类\硕士研究生\文献阅读\机器学习公平性\fairness_unawareness\data\raw")
    if (_LEGACY / "adult.data").exists():
        RAW_DIR = _LEGACY
RAW_TRAIN = RAW_DIR / "adult.data"
OUT_DIR = PROJECT_ROOT / "data" / "processed"
OUT_NPZ = OUT_DIR / "adult.npz"
OUT_JSON = OUT_DIR / "adult.json"

SEED = 20261026  # fixed for project-wide reproducibility; this script has no random operation

# ----------------------------------------------------------------------------- column schema
# Original UCI Adult attributes (train file is headerless).
COLUMNS = [
    "age", "workclass", "fnlwgt", "education", "education-num", "marital-status",
    "occupation", "relationship", "race", "sex", "capital-gain", "capital-loss",
    "hours-per-week", "native-country", "income",
]
CATEGORICAL = [
    "workclass", "education", "marital-status", "occupation",
    "relationship", "race", "sex", "native-country",
]
CONTINUOUS = ["age", "education-num", "capital-gain", "capital-loss", "hours-per-week"]
# The 13 attributes kept as features, in the original UCI attribute order.
ATTR_ORDER = [
    "age", "workclass", "education", "education-num", "marital-status", "occupation",
    "relationship", "race", "sex", "capital-gain", "capital-loss", "hours-per-week",
    "native-country",
]
DROPPED_ATTRS = ["fnlwgt", "income"]  # income is the label, never a feature


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(
        RAW_TRAIN, header=None, names=COLUMNS, skipinitialspace=True, na_values="?"
    )
    raw_n = len(df)
    print(f"[adult] raw rows read from {RAW_TRAIN.name}: {raw_n}")
    print(f"[adult] rows containing '?' missing token: {int(df.isna().any(axis=1).sum())}")

    # Uniform whitespace stripping on the string columns ('?' has already become NaN).
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()

    df = df.dropna().reset_index(drop=True)
    n = len(df)
    print(f"[adult] rows after dropping '?' rows: {n}")

    # ---- encode the 13 attributes (raw order, categoricals one-hot drop-first) --------------
    dummies = pd.get_dummies(
        df[CATEGORICAL], drop_first=True, dummy_na=False, dtype=np.float64
    )

    blocks, feature_names = [], []
    for attr in ATTR_ORDER:
        if attr in CONTINUOUS:
            blocks.append(df[[attr]].to_numpy(dtype=np.float64))
            feature_names.append(attr)
        else:
            cols = [c for c in dummies.columns if c.startswith(attr + "_")]
            if not cols:
                raise RuntimeError(f"no dummy columns found for categorical attribute {attr!r}")
            blocks.append(dummies[cols].to_numpy(dtype=np.float64))
            feature_names.extend(cols)

    X = np.ascontiguousarray(np.hstack(blocks), dtype=np.float64)
    p = X.shape[1]

    y = np.where(df["income"].to_numpy() == ">50K", 1, -1).astype(np.int8)
    z = np.where(df["sex"].to_numpy() == "Male", 1, 0).astype(np.int8)

    # ---- sanity checks ----------------------------------------------------------------------
    assert X.shape == (n, p), X.shape
    assert len(feature_names) == p == len(set(feature_names)), (p, len(feature_names))
    assert np.isfinite(X).all(), "non-finite value in X"
    assert set(np.unique(y)) == {-1, 1}, np.unique(y)
    assert set(np.unique(z)) == {0, 1}, np.unique(z)
    zero_var = np.flatnonzero(X.std(axis=0) == 0)
    assert zero_var.size == 0, f"zero-variance columns: {[feature_names[i] for i in zero_var]}"
    for attr in ("fnlwgt", "income"):
        assert not any(name.startswith(attr) for name in feature_names), f"leak: {attr}"

    pos_rate = float((y == 1).mean())
    n0, n1 = int((z == 0).sum()), int((z == 1).sum())
    p0 = float((y[z == 0] == 1).mean())
    p1 = float((y[z == 1] == 1).mean())
    dup_rows = int(df.duplicated().sum())

    print(f"[adult] X: shape={X.shape} dtype={X.dtype}, finite={np.isfinite(X).all()}")
    print(f"[adult] y: +1={int((y == 1).sum())} (-1={int((y == -1).sum())}), "
          f"positive_rate={pos_rate:.6f}")
    print(f"[adult] z: z=0 {n0} ({n0 / n:.4f}), z=1 {n1} ({n1 / n:.4f}); "
          f"positive_rate|z0={p0:.6f}, positive_rate|z1={p1:.6f}")
    print(f"[adult] p={p}, duplicate rows kept: {dup_rows}")

    # ---- write ------------------------------------------------------------------------------
    np.savez(OUT_NPZ, X=X, y=y, z=z)
    meta = {
        "dataset": "adult",
        "feature_names": feature_names,
        "sensitive_name": "sex",
        "sensitive_definition": {"0": "Female", "1": "Male"},
        "label_definition": {"+1": "income > 50K", "-1": "income <= 50K"},
        "n": int(n),
        "p": int(p),
        "positive_rate": pos_rate,
        "group_sizes": {"0": n0, "1": n1},
        "group_positive_rates": {"0": p0, "1": p1},
        "source": (
            "UCI Machine Learning Repository, Adult (Dua & Graff, 2017); local read-only copy "
            f"of the training split: {RAW_TRAIN}"
        ),
        "source_url": "https://archive.ics.uci.edu/dataset/2/adult",
        "raw_rows": int(raw_n),
        "dropped_missing_rows": int(raw_n - n),
        "duplicate_rows_kept": dup_rows,
        "raw_attributes_used": ATTR_ORDER,
        "excluded_attributes": DROPPED_ATTRS,
        "categorical_attributes": CATEGORICAL,
        "continuous_attributes": CONTINUOUS,
        "categorical_encoding": "one-hot, drop_first=True (first level absorbed by the intercept)",
        "standardized": False,
        "standardization_note": (
            "continuous attributes are kept as raw UCI values; downstream code may z-score "
            "them using the raw column means/stds recorded in feature_mean/feature_std"
        ),
        "feature_mean": [float(v) for v in X.mean(axis=0)],
        "feature_std": [float(v) for v in X.std(axis=0)],
        "randomness": "none (deterministic; no train/test split is performed in data prep)",
        "seed": SEED,
        "adult_test_note": (
            "adult.test NOT merged: the local copy is truncated after 9,216 complete rows "
            "(file ends mid-record), so it cannot serve as the official test split. "
            "adult.data (train split) is used as the full pool; SPEC draws D', D~ and the "
            "training stream randomly from the full pool, so no official split is needed."
        ),
        "paper_alignment": (
            "Roy & Mohapatra UAI 2026 Sec. 6.1.2: 13 features (fnlwgt and income excluded), "
            "sex sensitive, income>50K positive.  Features include sex, as in the paper's "
            "13-attribute count; after one-hot encoding p=%d." % p
        ),
    }
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    print(f"[adult] wrote {OUT_NPZ} ({OUT_NPZ.stat().st_size / 2**20:.2f} MiB)")
    print(f"[adult] wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
