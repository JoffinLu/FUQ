"""Check that every headline number in manuscript/main.tex matches the result files.

Fails (exit code 1) if any expected string is missing.  This is the automated part of the
submission checklist item "numbers in the manuscript match results/tables/*".
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "results" / "tables"
TEX = (ROOT / "manuscript" / "main.tex").read_text(encoding="utf-8")

expected = []  # (label, string that must appear)


def add(label, s):
    expected.append((label, s))


# ---- Table 1: reproduction summary ------------------------------------------------
repro = pd.read_csv(TAB / "repro_summary.csv")
for _, r in repro.iterrows():
    add(f"repro phi {r.experiment}", f"{r.phi_star:.4f}")
    add(f"repro cov_pop {r.experiment}", f"{r.coverage_pop_T:.2f}")
    add(f"repro width {r.experiment}", f"{r.ci_width_T:.3f}")

# ---- Table 2: protocol-A coverage -------------------------------------------------
jb = json.load(open(TAB / "joint_bootstrap_v3b_fresh_eval.json", encoding="utf-8"))["results"]
for r in jb:
    add(f"synthetic m={r['m_tilde']} paper cov", f"{r['cov_paper']:.2f}")
    add(f"synthetic m={r['m_tilde']} joint cov", f"{r['cov_jb']:.2f}")
    add(f"synthetic m={r['m_tilde']} ratio", f"{r['width_jb'] / r['width_paper']:.2f}")
for ds in ("adult", "acsincome", "compas"):
    j = json.load(open(TAB / f"real_joint_ci_{ds}.json", encoding="utf-8"))
    add(f"{ds} paper cov", f"{j['coverage_paper']:.2f}")
    add(f"{ds} joint cov", f"{j['coverage_joint']:.2f}")
    add(f"{ds} ratio", f"{j['width_ratio']:.2f}")
    add(f"{ds} width paper", f"{j['width_paper']:.3f}")
    add(f"{ds} width joint", f"{j['width_joint']:.3f}")

# ---- Table 3: variance budget -----------------------------------------------------
for ds in ("adult", "acsincome", "compas"):
    b = json.load(open(TAB / f"variance_budget_{ds}.json", encoding="utf-8"))
    add(f"{ds} se_train", f"{b['se_train']:.4f}")
    add(f"{ds} se_eval", f"{b['se_eval']:.4f}")
    add(f"{ds} sd_Dprime", f"{b['sd_Dprime']:.4f}")
    add(f"{ds} share_train", f"{100 * b['share_train']:.1f}")
    add(f"{ds} share_eval", f"{100 * b['share_eval']:.1f}")
    add(f"{ds} share_Dprime", f"{100 * b['share_Dprime']:.1f}")

# ---- Table 4: sensitivity ---------------------------------------------------------
sens = pd.read_csv(TAB / "sensitivity_adult.csv")
for _, r in sens.iterrows():
    add(f"kappa {r.kappa} norm", f"{r.theta_star_norm:.2f}")
    add(f"kappa {r.kappa} bias", f"{r.bias_median:.2f}")
    add(f"kappa {r.kappa} cov", f"{r.coverage_pop:.2f}")
    add(f"kappa {r.kappa} width", f"{r.ci_width:.4f}")

# ---- empirical convergence rates --------------------------------------------------
rate = json.load(open(TAB / "rate_check_synth_di.json", encoding="utf-8"))
add("rate slope norm distance", f"{abs(rate['slope_norm_distance_vs_T']):.2f}")
add("rate slope signed bias", f"{abs(rate['slope_signed_train_bias_vs_T']):.2f}")

# ---- Table 5: source ablation -----------------------------------------------------
for tag in ("synth_di_m100", "synth_di_m1000", "synth_dm_m100", "synth_dm_m1000",
            "adult", "acsincome", "compas"):
    a = json.load(open(TAB / f"ablation_{tag}.json", encoding="utf-8"))
    add(f"ablation {tag} cov paper", f"{a['coverage_paper']:.2f}")
    add(f"ablation {tag} cov eval", f"{a['coverage_eval_only']:.2f}")
    add(f"ablation {tag} cov joint", f"{a['coverage_train_eval']:.2f}")
    add(f"ablation {tag} w paper", f"{a['width_paper']:.3f}")
    add(f"ablation {tag} w eval", f"{a['width_eval_only']:.3f}")
    add(f"ablation {tag} w joint", f"{a['width_train_eval']:.3f}")

# ---- minimum certifiable gap ------------------------------------------------------
mdg = pd.read_csv(TAB / "min_detectable_gap.csv")
for _, r in mdg.iterrows():
    add(f"{r.dataset} half width", f"{r.best_half_width:.3f}")
    add(f"{r.dataset} gap", f"{r.phi_pop:.3f}")

missing = [(lab, s) for lab, s in expected if s not in TEX]
print(f"checked {len(expected)} numeric strings; missing {len(missing)}")
for lab, s in missing:
    print(f"  MISSING [{lab}] -> '{s}'")
sys.exit(1 if missing else 0)
