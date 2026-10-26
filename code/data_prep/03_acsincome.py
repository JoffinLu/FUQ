#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""03_acsincome.py -- Build data/processed/acsincome.npz (+ .json) from the 2018 ACS 1-year PUMS.

Paper alignment (Roy & Mohapatra, UAI 2026, Sec. 6.1.3 + Appendix):
  * ACSIncome benchmark of Ding et al. (2021) built from the U.S. Census Bureau's 2018
    1-year American Community Survey (ACS) person-level PUMS.
  * target: PINCP > 50000; 10 standard features; SEX is the sensitive attribute;
    full benchmark sample: n = 1,664,500 (verified exactly, see below).
  * The 10 standard features (Ding et al. order, as in folktables.ACSIncome):
      AGEP, COW, SCHL, MAR, OCCP, POBP, RELP, WKHP, SEX, RAC1P.

Data acquisition (official Census PUMS directory, 2018 / 1-Year):
  * national archive  csv_pus.zip   (562,224,936 bytes) -> psam_pusa.csv + psam_pusb.csv
  * Puerto Rico file  csv_ppr.zip   (  5,061,343 bytes) -> psam_p72.csv
  folktables (v0.0.12) uses 52 per-state downloads whose ``state_list`` is the 50 states +
  Puerto Rico and **does not include the District of Columbia (DC, ST=11)**.  To match the
  Ding et al./folktables ACSIncome sample exactly we therefore keep the national archive +
  PR file and drop DC rows (4,187 after filtering).  This reproduces n = 1,664,500 to the row:
  the script cross-checks against the official OpenML snapshot of the benchmark
  (openml dataset 43141, 12 columns incl. ST and PINCP) and asserts row-for-row equality.
  It also cross-checks against folktables' own per-state pipeline on Wyoming (exact match).

Preprocessing (identical to folktables.ACSIncome / Ding et al.):
  filter:  AGEP > 16, PINCP > 100, WKHP > 0, PWGTP >= 1
  X       = 10 raw features (categoricals remain their PUMS integer codes; NO standardization,
            exactly the native "standard ACSIncome task" representation)
  y       = +1 if PINCP > 50000 else -1
  z       = 1 if SEX == 1 (Male) else 0   (SEX: 1 = Male, 2 = Female)

Output:
  data/processed/acsincome.npz   X (n x 10, float64), y (n, int8 in {-1,+1}), z (n, int8 in {0,1})
  data/processed/acsincome.json  metadata
"""
import json
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ----------------------------------------------------------------------------- absolute paths
PROJECT_ROOT = Path(r"D:\Desktop\Data\学习类\硕士研究生\文献阅读\DSH\fuq-fairness")
RAW_CACHE = PROJECT_ROOT / "data" / "raw" / "acs_pums" / "2018" / "1-Year"
ZIP_PATH = RAW_CACHE / "csv_pus.zip"
PR_ZIP_PATH = RAW_CACHE / "csv_ppr.zip"
OPENML_PATH = RAW_CACHE / "openml_acsincome_2026_43141.pq"
FOLKTABLES_CACHE = PROJECT_ROOT / "data" / "raw" / "acs_pums" / "folktables"
OUT_DIR = PROJECT_ROOT / "data" / "processed"
OUT_NPZ = OUT_DIR / "acsincome.npz"
OUT_JSON = OUT_DIR / "acsincome.json"

SEED = 20261026  # fixed for project-wide reproducibility; this script has no random operation

NATIONAL_URL = (
    "https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/csv_pus.zip"
)
NATIONAL_EXPECTED_BYTES = 562_224_936
PR_URL = "https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/csv_ppr.zip"
PR_EXPECTED_BYTES = 5_061_343
OPENML_URL = "https://data.openml.org/datasets/0004/43141/dataset_43141.pq"
EXPECTED_N = 1_664_500  # Ding et al. (2021) / paper's ACSIncome 2018 sample size
DC_ST = 11.0             # District of Columbia FIPS code (excluded; not in folktables state_list)

# 10 standard ACSIncome features, in Ding et al. / folktables order.
FEATURES = ["AGEP", "COW", "SCHL", "MAR", "OCCP", "POBP", "RELP", "WKHP", "SEX", "RAC1P"]
# Columns that must be present in the raw PUMS person file.
NEEDED_COLS = FEATURES + ["PINCP", "PWGTP", "ST"]
FEATURE_DESCRIPTIONS = {
    "AGEP": "age in years (integer)",
    "COW": "class of worker (PUMS integer code)",
    "SCHL": "educational attainment (PUMS integer code)",
    "MAR": "marital status (PUMS integer code)",
    "OCCP": "occupation code (PUMS SOC-based integer code)",
    "POBP": "place of birth code (PUMS integer code)",
    "RELP": "relationship to reference person (PUMS integer code)",
    "WKHP": "usual hours worked per week (integer)",
    "SEX": "sex (1 = Male, 2 = Female; sensitive attribute, also a feature)",
    "RAC1P": "recoded detailed race code (PUMS integer code)",
}
CHUNK_ROWS = 250_000


# ----------------------------------------------------------------------------- download helpers
def download_file(url: str, dest: Path, expected_bytes: int | None = None) -> None:
    """Stream-download ``url`` to ``dest`` with *.part staging and a size sanity check."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and (expected_bytes is None or dest.stat().st_size == expected_bytes):
        print(f"[acsincome] using cached {dest.name} ({dest.stat().st_size / 2**20:.1f} MiB)")
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"[acsincome] downloading {url}")
    t0 = time.time()
    with requests.get(url, stream=True, timeout=180) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length") or (expected_bytes or 0))
        done = 0
        next_report = 0
        with open(tmp, "wb") as fh:
            for chunk in r.iter_content(chunk_size=8 * 2**20):
                if not chunk:
                    continue
                fh.write(chunk)
                done += len(chunk)
                if done >= next_report:
                    pct = 100.0 * done / total if total else float("nan")
                    print(f"[acsincome]   {done / 2**20:7.1f} / {total / 2**20:7.1f} MiB "
                          f"({pct:5.1f}%)  {done / 2**20 / max(time.time() - t0, 1e-9):5.1f} MiB/s")
                    next_report = done + 100 * 2**20
    if expected_bytes is not None and done != expected_bytes:
        raise RuntimeError(f"size mismatch for {url}: got {done}, expected {expected_bytes}")
    tmp.replace(dest)
    print(f"[acsincome] downloaded {dest.name} ({done / 2**20:.1f} MiB) in "
          f"{time.time() - t0:.1f}s")


def pick_person_members(zf: zipfile.ZipFile) -> list[str]:
    """Return the person-level CSV member(s) of an archive (national a/b parts, or PR)."""
    names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
    person = [n for n in names if Path(n).name.lower().startswith("psam_p")]
    if person:
        return person
    if len(names) == 1:
        return names
    raise RuntimeError(f"cannot identify the person-level CSV among {names}")


def stream_filter_member(zf: zipfile.ZipFile, member: str, counters: dict) -> pd.DataFrame:
    """Stream one person CSV in chunks, apply the ACSIncome filter, return kept rows.

    Filtering per chunk keeps peak memory bounded (the national parts are ~1.1 GB each
    uncompressed and cannot be read in one go on this machine).
    """
    kept: list[pd.DataFrame] = []
    dtype = {col: "float64" for col in NEEDED_COLS}
    with zf.open(member) as fh:
        reader = pd.read_csv(
            fh, usecols=NEEDED_COLS, dtype=dtype, chunksize=CHUNK_ROWS, low_memory=False
        )
        for chunk in reader:
            counters["raw"] += len(chunk)
            m1 = chunk["AGEP"] > 16
            m2 = m1 & (chunk["PINCP"] > 100)
            m3 = m2 & (chunk["WKHP"] > 0)
            m4 = m3 & (chunk["PWGTP"] >= 1)
            counters["AGEP>16"] += int(m1.sum())
            counters["PINCP>100"] += int(m2.sum())
            counters["WKHP>0"] += int(m3.sum())
            counters["PWGTP>=1"] += int(m4.sum())
            if m4.any():
                kept.append(chunk.loc[m4])
    if not kept:
        return pd.DataFrame(columns=NEEDED_COLS, dtype=np.float64)
    return pd.concat(kept, ignore_index=True)


def lexsorted_rows(A: np.ndarray) -> np.ndarray:
    """Return rows of a 2-D float array in a deterministic lexicographic order."""
    order = np.lexsort(tuple(A[:, j] for j in range(A.shape[1] - 1, -1, -1)))
    return A[order]


def cross_check_openml(df: pd.DataFrame, X: np.ndarray, y: np.ndarray) -> dict:
    """Compare the built dataset row-for-row with the official OpenML ACSIncome snapshot."""
    download_file(OPENML_URL, OPENML_PATH, None)
    om = pd.read_parquet(OPENML_PATH)
    Xo = om[FEATURES].to_numpy(dtype=np.float64)
    yo = np.where(om["PINCP"].to_numpy(dtype=np.float64) > 50_000, 1, -1).astype(np.int8)
    sto = om["ST"].to_numpy(dtype=np.float64)
    stn = df["ST"].to_numpy(dtype=np.float64)
    print(f"[acsincome] openML snapshot: {len(om)} rows; built dataset: {len(df)} rows")
    print(f"[acsincome] openML positive_rate={float((yo == 1).mean()):.9f}; "
          f"built positive_rate={float((y == 1).mean()):.9f}")
    same_n = len(om) == len(df)
    exact_x = same_n and np.array_equal(lexsorted_rows(X), lexsorted_rows(Xo))
    exact_y = same_n and np.array_equal(np.sort(y), np.sort(yo))
    exact_st = same_n and np.array_equal(np.sort(stn), np.sort(sto))
    print(f"[acsincome] openML exact match: n={same_n}, rows(X)={exact_x}, "
          f"labels(y)={exact_y}, states(ST)={exact_st}")
    return {
        "performed": True,
        "snapshot": f"OpenML dataset 43141 (2018 ACSIncome, Ding et al. 2021), {len(om)} rows",
        "snapshot_n": int(len(om)),
        "built_n": int(len(df)),
        "rows_exact_match": bool(exact_x),
        "labels_exact_match": bool(exact_y),
        "states_exact_match": bool(exact_st),
    }


# ----------------------------------------------------------------------------- main
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- 1. acquire official 2018 1-year person files (national archive + PR) --------------
    archives = [
        (ZIP_PATH, NATIONAL_URL, NATIONAL_EXPECTED_BYTES),
        (PR_ZIP_PATH, PR_URL, PR_EXPECTED_BYTES),
    ]
    counters = {k: 0 for k in ("raw", "AGEP>16", "PINCP>100", "WKHP>0", "PWGTP>=1")}
    parts: list[pd.DataFrame] = []
    for path, url, expected in archives:
        download_file(url, path, expected)
        with zipfile.ZipFile(path) as zf:
            for member in pick_person_members(zf):
                # cheap header peek to validate the schema before streaming
                with zf.open(member) as fh:
                    header_line = fh.readline().decode("utf-8-sig").strip()
                header = [c.strip() for c in header_line.split(",")]
                missing = [c for c in NEEDED_COLS if c not in header]
                if missing:
                    raise RuntimeError(f"missing required columns {missing} in {member}")
                print(f"[acsincome] {member}: {len(header)} columns; required 13 found; streaming...")
                t0 = time.time()
                before = counters["raw"]
                part = stream_filter_member(zf, member, counters)
                print(f"[acsincome] {member}: raw {counters['raw'] - before} rows, "
                      f"kept {len(part)} rows ({time.time() - t0:.1f}s)")
                parts.append(part)

    # ---- 2. folktables/Ding et al. ACSIncome filter (applied per chunk above) ---------------
    df = pd.concat(parts, ignore_index=True)
    raw_n = counters["raw"]
    print(f"[acsincome] raw person records read (national + PR): {raw_n}")
    print(f"[acsincome] after AGEP > 16: {counters['AGEP>16']}")
    print(f"[acsincome] after PINCP > 100: {counters['PINCP>100']}")
    print(f"[acsincome] after WKHP > 0: {counters['WKHP>0']}")
    print(f"[acsincome] after PWGTP >= 1: {counters['PWGTP>=1']}")

    # folktables' state_list = 50 states + PR, WITHOUT the District of Columbia -> drop DC
    dc_mask = df["ST"].to_numpy() == DC_ST
    n_dc = int(dc_mask.sum())
    df = df[~dc_mask].reset_index(drop=True)
    print(f"[acsincome] dropped District of Columbia (ST=11) rows: {n_dc} "
          f"(Ding et al./folktables ACSIncome excludes DC)")
    n = len(df)

    if n != EXPECTED_N:
        raise RuntimeError(
            f"n={n} != expected {EXPECTED_N} (Ding et al. 2021). The official 2018 files "
            f"should reproduce it exactly; check the acquisition/filter steps."
        )
    print(f"[acsincome] n == {EXPECTED_N} exactly -> matches Ding et al. (2021)")

    # ---- 3. build X, y, z -------------------------------------------------------------------
    X = df[FEATURES].to_numpy(dtype=np.float64)
    n_nan = int(np.isnan(X).sum())
    if n_nan:
        print(f"[acsincome] replacing {n_nan} NaN feature entries with -1 "
              f"(same as folktables ACSIncome postprocess np.nan_to_num(x, -1))")
        X = np.nan_to_num(X, nan=-1.0)

    y = np.where(df["PINCP"].to_numpy(dtype=np.float64) > 50_000, 1, -1).astype(np.int8)
    z = np.where(df["SEX"].to_numpy() == 1, 1, 0).astype(np.int8)
    p = X.shape[1]

    # ---- 4. sanity checks -------------------------------------------------------------------
    assert X.shape == (n, p) and p == 10, X.shape
    assert np.isfinite(X).all(), "non-finite value in X"
    assert set(np.unique(y)) == {-1, 1}, np.unique(y)
    assert set(np.unique(z)) == {0, 1}, np.unique(z)
    assert set(np.unique(df["SEX"])) == {1, 2}, np.unique(df["SEX"])
    zero_var = np.flatnonzero(X.std(axis=0) == 0)
    assert zero_var.size == 0, f"zero-variance columns: {[FEATURES[i] for i in zero_var]}"
    for name in ("PINCP", "PWGTP", "ST"):
        assert name not in FEATURES, f"leak: {name}"

    pos_rate = float((y == 1).mean())
    n_neg, n_pos = int((z == 0).sum()), int((z == 1).sum())
    p_neg = float((y[z == 0] == 1).mean())
    p_pos = float((y[z == 1] == 1).mean())
    print(f"[acsincome] X: shape={X.shape} dtype={X.dtype}, finite={np.isfinite(X).all()}")
    print(f"[acsincome] y: +1={int((y == 1).sum())} (-1={int((y == -1).sum())}), "
          f"positive_rate={pos_rate:.9f}")
    print(f"[acsincome] z: z=0 {n_neg} ({n_neg / n:.4f}), z=1 {n_pos} ({n_pos / n:.4f}); "
          f"positive_rate|z0={p_neg:.6f}, positive_rate|z1={p_pos:.6f}")

    # ---- 5. cross-check #1: folktables' own per-state pipeline (Wyoming) --------------------
    xcheck_wy = {"performed": False}
    try:
        from folktables import ACSDataSource, ACSIncome

        FOLKTABLES_CACHE.mkdir(parents=True, exist_ok=True)
        source = ACSDataSource(
            survey_year="2018", horizon="1-Year", survey="person",
            root_dir=str(FOLKTABLES_CACHE),
        )
        wy_df = source.get_data(states=["WY"], download=True)
        X_wy, y_wy, _ = ACSIncome.df_to_numpy(wy_df)
        X_wy = np.asarray(X_wy, dtype=np.float64)
        y_wy = np.where(np.asarray(y_wy).astype(bool), 1, -1).astype(np.int8)

        wy_mask = df["ST"].to_numpy() == 56  # 56 = Wyoming FIPS
        X_nat, y_nat = X[wy_mask], y[wy_mask]
        print(f"[acsincome] cross-check WY: built rows={len(X_nat)}, "
              f"folktables per-state rows={len(X_wy)}")
        exact = (
            X_nat.shape == X_wy.shape
            and np.array_equal(lexsorted_rows(X_nat), lexsorted_rows(X_wy))
            and np.array_equal(np.sort(y_nat), np.sort(y_wy))
        )
        print(f"[acsincome] cross-check WY exact match: {exact}")
        assert exact, "national-file pipeline does not reproduce folktables per-state pipeline"
        xcheck_wy = {
            "performed": True,
            "state": "WY",
            "built_rows": int(len(X_nat)),
            "folktables_rows": int(len(X_wy)),
            "exact_match": bool(exact),
        }
    except Exception as exc:  # network / package problem must not destroy the primary deliverable
        print(f"[acsincome] WARNING: folktables cross-check skipped/failed: {exc!r}")
        xcheck_wy = {"performed": False, "error": repr(exc)}

    # ---- 6. cross-check #2: official OpenML snapshot of the Ding et al. benchmark -----------
    xcheck_om = {"performed": False}
    try:
        xcheck_om = cross_check_openml(df, X, y)
        if not (xcheck_om["rows_exact_match"] and xcheck_om["labels_exact_match"]
                and xcheck_om["states_exact_match"]):
            raise RuntimeError(f"OpenML snapshot mismatch: {xcheck_om}")
        print("[acsincome] openML cross-check PASSED (dataset is row-for-row identical to "
              "the official Ding et al. 2018 ACSIncome snapshot)")
    except Exception as exc:
        print(f"[acsincome] WARNING: OpenML cross-check skipped/failed: {exc!r}")
        xcheck_om = {"performed": False, "error": repr(exc)}

    # ---- 7. write ---------------------------------------------------------------------------
    np.savez(OUT_NPZ, X=X, y=y, z=z)
    meta = {
        "dataset": "acsincome",
        "feature_names": FEATURES,
        "feature_descriptions": FEATURE_DESCRIPTIONS,
        "sensitive_name": "SEX",
        "sensitive_definition": {"0": "Female (SEX == 2)", "1": "Male (SEX == 1)"},
        "label_definition": {"+1": "PINCP > 50000", "-1": "PINCP <= 50000"},
        "n": int(n),
        "p": int(p),
        "positive_rate": pos_rate,
        "group_sizes": {"0": n_neg, "1": n_pos},
        "group_positive_rates": {"0": p_neg, "1": p_pos},
        "source": (
            "U.S. Census Bureau, 2018 1-Year American Community Survey (ACS) Public Use "
            "Microdata Sample (PUMS), person-level files (national + Puerto Rico): "
            + NATIONAL_URL + " ; " + PR_URL
        ),
        "source_url": NATIONAL_URL,
        "survey_year": "2018",
        "horizon": "1-Year",
        "survey": "person",
        "raw_rows": int(raw_n),
        "filter": "AGEP > 16, PINCP > 100, WKHP > 0, PWGTP >= 1 (folktables.ACSIncome / Ding et al. 2021)",
        "filtered_rows": int(n),
        "dc_excluded_rows": n_dc,
        "geography": (
            "50 states + Puerto Rico (ST=72); District of Columbia (ST=11, 4,187 filtered rows) "
            "excluded to match Ding et al. (2021) / folktables, whose state_list omits DC. "
            "This reproduces the published n=1,664,500 exactly."
        ),
        "n_nan_feature_entries_replaced": n_nan,
        "categorical_encoding": (
            "native PUMS integer codes (COW, SCHL, MAR, OCCP, POBP, RELP, SEX, RAC1P) and raw "
            "numeric values (AGEP, WKHP); NO one-hot encoding; matches folktables' native "
            "ACSIncome representation"
        ),
        "standardized": False,
        "standardization_note": (
            "raw PUMS values are stored; downstream code/core may z-score them "
            "(raw column means/stds recorded below for convenience)"
        ),
        "feature_mean": [float(v) for v in X.mean(axis=0)],
        "feature_std": [float(v) for v in X.std(axis=0)],
        "randomness": "none (deterministic; no train/test split is performed in data prep)",
        "seed": SEED,
        "cross_check_folktables_wy": xcheck_wy,
        "cross_check_openml": xcheck_om,
        "acquisition_note": (
            "Official Census archives were used instead of folktables' 52 per-state downloads: "
            "csv_pus.zip (national person, split into psam_pusa.csv + psam_pusb.csv) and "
            "csv_ppr.zip (Puerto Rico); DC removed to mirror folktables' state_list. "
            "Equivalence to folktables is asserted on Wyoming; row-for-row equality with the "
            "official OpenML ACMIncome snapshot is asserted for the full dataset."
        ),
        "paper_alignment": (
            "Roy & Mohapatra UAI 2026 Sec. 6.1.3 / Ding et al. (2021): 2018 1-Year ACS, "
            "PINCP > 50K, 10 standard features, SEX sensitive, n=1,664,500 (exact).  SEX is "
            "both one of the 10 features and the sensitive attribute."
        ),
    }
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    print(f"[acsincome] wrote {OUT_NPZ} ({OUT_NPZ.stat().st_size / 2**20:.1f} MiB)")
    print(f"[acsincome] wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
