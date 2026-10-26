"""00_all.py -- build every processed dataset (idempotent).

Adult and COMPAS raw files are read from data/raw/ (override with the FUQ_RAW_DIR
environment variable); the ACSIncome files are downloaded into data/raw/acs_pums
on first use.  Scripts are skipped when their processed output already exists.

Usage:
    python code/data_prep/00_all.py            # build what is missing
    python code/data_prep/00_all.py --force    # rebuild everything
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT = PROJECT_ROOT / "data" / "processed"

STEPS = [
    ("01_adult.py", OUT / "adult.npz"),
    ("02_compas.py", OUT / "compas.npz"),
    ("03_acsincome.py", OUT / "acsincome.npz"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="rebuild even if the output exists")
    args = ap.parse_args()
    for script, target in STEPS:
        if target.exists() and not args.force:
            print(f"[data_prep] skip {script}: {target.name} exists")
            continue
        print(f"[data_prep] run {script}", flush=True)
        result = subprocess.run([sys.executable, str(Path(__file__).parent / script)], cwd=PROJECT_ROOT)
        if result.returncode != 0:
            print(f"[data_prep] FAILED: {script}")
            return result.returncode
    print("[data_prep] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
