"""One-command driver for the reproduction and the paper experiments.

Usage
-----
    python code/reproduce_all.py --scale light     # pipeline sanity check, minutes
    python code/reproduce_all.py --scale full      # all reported experiments, ~2 h CPU
    python code/reproduce_all.py --scale full --dry-run
    python code/reproduce_all.py --only figures    # one stage

Every command is exactly one line of the documented reproduction (supplement, Section 9).
The light scale writes tagged outputs (`_light` / smoke tags) and does not touch the
reported tables, so it is safe to run after the paper numbers were produced.  The full
scale passes the exact settings of the reported runs, so it regenerates the canonical
files in results/tables/ (deterministic seeds).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
EXPS = ROOT / "code" / "exps"

LIGHT = [
    ("data", [PY, str(ROOT / "code" / "data_prep" / "00_all.py")]),
    ("exp", [PY, str(EXPS / "run_synth_di.py"),
             "--reps", "3", "--T", "1000", "--n-pool", "5000", "--n-true", "20000", "--tag", "light"]),
    ("exp", [PY, str(EXPS / "run_synth_dm.py"),
             "--reps", "3", "--T", "1000", "--n-pool", "5000", "--n-true", "20000", "--tag", "light"]),
    ("exp", [PY, str(EXPS / "run_real.py"), "--dataset", "adult",
             "--reps", "2", "--T", "1000", "--B", "20", "--smoke", "--tag", "light"]),
    ("check", [PY, str(ROOT / "manuscript" / "check_numbers.py")]),
]

# Settings of the runs reported in the paper (see Table 2, Table 3, Table 5 and the supplement).
FULL = [
    ("data", [PY, str(ROOT / "code" / "data_prep" / "00_all.py")]),

    # --- reproduction of the baseline (Table 2): exact settings of Section 6
    ("exp", [PY, str(EXPS / "run_synth_di.py"),
             "--reps", "100", "--T", "20000", "--B", "100", "--T-star", "200000",
             "--n-pool", "20000", "--n-dprime", "200", "--n-tilde", "100",
             "--n-true", "400000", "--eps", "0.002", "--kappa", "0.0001",
             "--eta0", "0.1", "--tag", "paperdgp"]),
    ("exp", [PY, str(EXPS / "run_synth_dm.py"),
             "--reps", "100", "--T", "20000", "--B", "100", "--n-pool", "20000",
             "--n-dprime", "250", "--n-tilde", "100", "--R2", "500",
             "--n-true", "2000000", "--kappa", "0.0001", "--eta0", "0.03", "--tag", "paperdgp"]),
    ("exp", [PY, str(EXPS / "run_real.py"), "--dataset", "adult",
             "--reps", "100", "--T", "50000", "--B", "200", "--kappa", "0.1", "--eta0", "0.1", "--tag", "k01"]),
    ("exp", [PY, str(EXPS / "run_real.py"), "--dataset", "acsincome",
             "--reps", "150", "--T", "50000", "--B", "100", "--kappa", "0.1", "--eta0", "0.1", "--tag", "k01"]),
    ("exp", [PY, str(EXPS / "run_real.py"), "--dataset", "compas",
             "--reps", "150", "--T", "50000", "--B", "200", "--kappa", "0.1", "--eta0", "0.1", "--tag", "k01"]),

    # --- protocol A with a fresh evaluation set (Table 3)
    ("exp", [PY, str(EXPS / "combined_ci_v3_fresh_eval.py"),
             "--reps", "100", "--T", "20000", "--B", "100", "--R", "400",
             "--out", "joint_bootstrap_v3b_fresh_eval.json"]),
    ("exp", [PY, str(EXPS / "real_joint_ci.py"), "--dataset", "adult",
             "--reps", "60", "--T", "30000", "--B", "100", "--R", "300", "--eta0", "0.1"]),
    ("exp", [PY, str(EXPS / "real_joint_ci.py"), "--dataset", "acsincome",
             "--reps", "60", "--T", "30000", "--B", "100", "--R", "300", "--eta0", "0.1"]),
    ("exp", [PY, str(EXPS / "real_joint_ci.py"), "--dataset", "compas",
             "--reps", "60", "--T", "30000", "--B", "100", "--R", "300", "--eta0", "0.1"]),

    # --- variance budget (Table 4), tolerance sensitivity (Table 5), rate check (supplement)
    ("analysis", [PY, str(EXPS / "variance_budget.py"), "--dataset", "adult", "--R", "25"]),
    ("analysis", [PY, str(EXPS / "variance_budget.py"), "--dataset", "acsincome", "--R", "25"]),
    ("analysis", [PY, str(EXPS / "variance_budget.py"), "--dataset", "compas", "--R", "25"]),
    ("analysis", [PY, str(EXPS / "sensitivity_adult.py"), "--reps", "20"]),
    ("analysis", [PY, str(EXPS / "rate_check.py"), "--reps", "40"]),

    # --- source ablation (Table 6 and supplement): training only vs evaluation only vs both
    ("analysis", [PY, str(EXPS / "ablation_sources.py"), "--dataset", "synth_di", "--m", "100"]),
    ("analysis", [PY, str(EXPS / "ablation_sources.py"), "--dataset", "synth_di", "--m", "1000"]),
    ("analysis", [PY, str(EXPS / "ablation_sources.py"), "--dataset", "synth_dm", "--m", "100"]),
    ("analysis", [PY, str(EXPS / "ablation_sources.py"), "--dataset", "synth_dm", "--m", "1000"]),
    ("analysis", [PY, str(EXPS / "ablation_sources.py"), "--dataset", "adult",
                  "--reps", "60", "--T", "30000", "--B", "100", "--R", "300"]),
    ("analysis", [PY, str(EXPS / "ablation_sources.py"), "--dataset", "acsincome",
                  "--reps", "60", "--T", "30000", "--B", "100", "--R", "300"]),
    ("analysis", [PY, str(EXPS / "ablation_sources.py"), "--dataset", "compas",
                  "--reps", "60", "--T", "30000", "--B", "100", "--R", "300"]),

    # --- figures and final consistency checks
    ("figures", [PY, str(EXPS / "make_figures.py")]),
    ("figures", [PY, str(EXPS / "make_extension_figures.py")]),
    ("figures", [PY, str(EXPS / "make_sample_size_figure.py")]),
    ("check", [PY, str(ROOT / "manuscript" / "check_numbers.py")]),
    ("check", [PY, str(ROOT / "manuscript" / "check_refs.py")]),
]


def run(steps, dry: bool) -> int:
    for stage, command in steps:
        label = " ".join([Path(command[1]).name, *command[2:]])
        if dry:
            print(f"[{stage}] {label}")
            continue
        print(f"[{stage}] {label}", flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode != 0:
            print(f"FAILED (exit {result.returncode}) in stage {stage}: {label}")
            return result.returncode
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scale", choices=["light", "full"], default="light")
    parser.add_argument("--only", choices=["data", "exp", "analysis", "figures", "check"], default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    plan = LIGHT if args.scale == "light" else FULL
    if args.only:
        plan = [step for step in plan if step[0] == args.only]
    code = run(plan, args.dry_run)
    print("done" if code == 0 else "failed")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
