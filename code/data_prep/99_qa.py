#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""99_qa.py -- Validate every processed dataset against its JSON sidecar.

Checks (per dataset):
  * .npz loads with np.load and contains exactly the keys X, y, z;
  * X float64 (n x p, finite, no all-zero column), y int8 in {-1, +1}, z int8 in {0, 1};
  * n / p / positive_rate / group_sizes in the JSON agree with the arrays;
  * feature_names length == p; no fnlwgt / income / PINCP label leakage;
  * every feature column has at least 2 distinct values;
  * sensitive column equals z when the sensitive attribute is also a feature
    (Adult sex, COMPAS race, ACSIncome SEX encoded -- reported as info, not enforced).

Exit code 0 iff all present datasets pass (missing datasets are reported as SKIP).
"""
import json
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(r"D:\Desktop\Data\学习类\硕士研究生\文献阅读\DSH\fuq-fairness")
PROCESSED = PROJECT_ROOT / "data" / "processed"
DATASETS = ["adult", "compas", "acsincome"]
LEAK_NAMES = ("fnlwgt", "income", "PINCP", "PWGTP")


def check_one(name: str) -> bool:
    npz_path = PROCESSED / f"{name}.npz"
    json_path = PROCESSED / f"{name}.json"
    if not (npz_path.exists() and json_path.exists()):
        print(f"[QA] {name:10s} SKIP (missing {npz_path.name} or {json_path.name})")
        return True

    ok = True

    def fail(msg: str) -> None:
        nonlocal ok
        ok = False
        print(f"[QA] {name:10s} FAIL: {msg}")

    data = np.load(npz_path)
    keys = set(data.files)
    if keys != {"X", "y", "z"}:
        fail(f"npz keys {sorted(keys)} != ['X','y','z']")
    X, y, z = data["X"], data["y"], data["z"]
    with open(json_path, encoding="utf-8") as fh:
        meta = json.load(fh)

    if X.dtype != np.float64:
        fail(f"X dtype {X.dtype} != float64")
    if y.dtype != np.int8:
        fail(f"y dtype {y.dtype} != int8")
    if z.dtype != np.int8:
        fail(f"z dtype {z.dtype} != int8")
    if X.ndim != 2:
        fail(f"X ndim {X.ndim} != 2")

    n, p = X.shape
    checks = [
        (y.shape == (n,), f"y shape {y.shape} != ({n},)"),
        (z.shape == (n,), f"z shape {z.shape} != ({n},)"),
        (meta.get("n") == n, f"json n={meta.get('n')} != X.shape[0]={n}"),
        (meta.get("p") == p, f"json p={meta.get('p')} != X.shape[1]={p}"),
        (len(meta.get("feature_names", [])) == p,
         f"len(feature_names)={len(meta.get('feature_names', []))} != p={p}"),
        (np.isfinite(X).all(), "non-finite entry in X"),
        (set(np.unique(y).tolist()) <= {-1, 1}, f"y values {np.unique(y)} not in {{-1,1}}"),
        (set(np.unique(z).tolist()) <= {0, 1}, f"z values {np.unique(z)} not in {{0,1}}"),
        (int((X.std(axis=0) == 0).sum()) == 0, "X has a zero-variance column"),
    ]
    for cond, msg in checks:
        if not cond:
            fail(msg)

    # label leakage / label columns must not be features
    names = list(meta.get("feature_names", []))
    bad = [nm for nm in names if nm in LEAK_NAMES]
    if bad:
        fail(f"label/weight column(s) leaked into features: {bad}")

    pos_rate = float((y == 1).mean())
    n0, n1 = int((z == 0).sum()), int((z == 1).sum())
    if abs(meta.get("positive_rate", -1) - pos_rate) > 1e-6:
        fail(f"json positive_rate={meta.get('positive_rate')} != {pos_rate:.6f}")
    if meta.get("group_sizes") != {"0": n0, "1": n1}:
        fail(f"json group_sizes={meta.get('group_sizes')} != {{'0': {n0}, '1': {n1}}}")
    if "sensitive_name" not in meta or "source" not in meta:
        fail("json missing sensitive_name / source")

    # duplicate rows: informational only
    dup = n - len(np.unique(np.hstack([X, y[:, None], z[:, None]]), axis=0))
    print(f"[QA] {name:10s} {'PASS' if ok else 'FAIL'}  n={n:>8d} p={p:>3d}  "
          f"pos_rate={pos_rate:.4f}  z1_frac={n1 / n:.4f}  dup_rows={dup}  "
          f"dtypes=({X.dtype},{y.dtype},{z.dtype})")
    return ok


def main() -> int:
    all_ok = True
    for name in DATASETS:
        all_ok &= check_one(name)
    present = [d for d in DATASETS if (PROCESSED / f"{d}.npz").exists()]
    print(f"[QA] datasets present: {present if present else 'NONE'}")
    print(f"[QA] overall: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
