"""Build reproduction figures and the combined summary table.

For each experiment (synthetic DI, Adult DI, ACSIncome DI, COMPAS DM) produce a 2x2 figure
mirroring the layout of the paper's Figures 2-6:
  (a) W2(density_k, theoretical N(phi*, sigma^2/k)) vs k
  (b) MIS of the bootstrap CI vs k
  (c) empirical coverage of CI for the held-out estimand and for the population estimand
  (d) CI width vs k together with the spread of phi(theta_bar_k) across repetitions

Usage:  python code/exps/make_figures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))
ROOT = CODE_DIR.parent
sys.path.insert(0, str(ROOT / "code"))
from core.fairuq import mis, w2_empirical_vs_normal  # noqa: E402

RAW = ROOT / "results" / "raw"
TAB = ROOT / "results" / "tables"
FIG = ROOT / "results" / "figures"

EXPERIMENTS = [
    # (tag, per-rep csv, meta json, kind, label)
    ("synth_di", "synth_di_per_rep_paperdgp.csv", "synth_di_meta_paperdgp.json", "di",
     "Synthetic (DI)"),
    ("synth_dm", "synth_dm_per_rep_paperdgp.csv", "synth_dm_meta_paperdgp.json", "dm",
     "Synthetic (DM)"),
    ("adult", "real_adult_per_rep_k01.csv", "real_adult_meta_k01.json", "di", "Adult (DI)"),
    ("acsincome", "real_acsincome_per_rep_k01.csv", "real_acsincome_meta_k01.json", "di",
     "ACSIncome (DI)"),
    ("compas", "real_compas_per_rep_k01.csv", "real_compas_meta_k01.json", "dm", "COMPAS (DM)"),
]


def targets(meta, name):
    if name == "synth_di":
        return float(meta["phi_star_eval_Dtilde"]), float(meta["phi_star_true"])
    if name == "synth_dm":
        return float(meta["phi_star_hold"]), float(meta["phi_star_true"])
    return float(meta["phi_hold"]), float(meta["phi_pop"])


def panel_data(df, meta, name, alpha=0.05):
    phi_hold, phi_pop = targets(meta, name)
    out = []
    for k, sub in df.groupby("k"):
        phis = sub["phi_main"].values
        lo, hi = sub["ci_lo"].values, sub["ci_hi"].values
        sigma2 = max(len(phis) * 0, 0)
        out.append({
            "k": int(k), "phi_mean": float(phis.mean()), "phi_sd": float(phis.std(ddof=1)),
            "width": float((hi - lo).mean()),
            "cov_hold": float(np.mean((lo <= phi_hold) & (phi_hold <= hi))),
            "cov_pop": float(np.mean((lo <= phi_pop) & (phi_pop <= hi))),
            "mis": float(np.mean([mis(phis, a, b, alpha) for a, b in zip(lo, hi)])),
        })
    return pd.DataFrame(out).sort_values("k"), phi_hold, phi_pop


def make_figure(tag, rep_csv, meta_json, kind, label, alpha=0.05):
    df = pd.read_csv(RAW / rep_csv)
    meta = json.load(open(TAB / meta_json, encoding="utf-8"))
    summ, phi_hold, phi_pop = panel_data(df, meta, tag, alpha)
    T = int(df["k"].max())

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.6))
    ks = summ["k"].values

    # (a) W2 to theoretical normal
    sigma2 = T * float(np.var(df[df.k == T]["phi_main"].values, ddof=1))
    w2 = []
    for k in ks:
        phis = df[df.k == k]["phi_main"].values
        w2.append(w2_empirical_vs_normal(phis, phi_pop, np.sqrt(max(sigma2 / k, 1e-15))))
    ax = axes[0, 0]
    ax.plot(ks, w2, "o-", ms=3, lw=1.2, color="#1f77b4")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("iterations k"); ax.set_ylabel(r"$W_2(\hat P_k,\ \mathcal{N}(\phi^*,\sigma^2/k))$")
    ax.set_title("(a) convergence to asymptotic law"); ax.grid(alpha=.3, which="both")

    # (b) MIS
    ax = axes[0, 1]
    ax.plot(ks, summ["mis"], "s-", ms=3, lw=1.2, color="#d62728")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("iterations k"); ax.set_ylabel("MIS (lower is better)")
    ax.set_title("(b) mean interval score"); ax.grid(alpha=.3, which="both")

    # (c) coverage, two targets
    ax = axes[1, 0]
    ax.plot(ks, summ["cov_hold"], "o-", ms=3, lw=1.2, label="held-out estimand $\\hat\\phi(\\theta^*)$")
    ax.plot(ks, summ["cov_pop"], "s--", ms=3, lw=1.2, label="population $\\phi(\\theta^*)$")
    ax.axhline(1 - alpha, color="k", ls=":", lw=1, label="nominal $1-\\alpha$")
    ax.set_xscale("log"); ax.set_xlabel("iterations k"); ax.set_ylabel("coverage")
    ax.set_ylim(-0.02, 1.02); ax.legend(fontsize=8, loc="lower left")
    ax.set_title("(c) empirical coverage"); ax.grid(alpha=.3)

    # (d) width vs spread of phi across reps
    ax = axes[1, 1]
    ax.plot(ks, summ["width"], "o-", ms=3, lw=1.2, label="mean CI width")
    ax.plot(ks, 4 * summ["phi_sd"], "s--", ms=3, lw=1.2, label="4 x sd of $\\phi(\\bar\\theta_k)$")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("iterations k"); ax.set_ylabel("width")
    ax.legend(fontsize=8); ax.set_title("(d) interval width vs sampling spread"); ax.grid(alpha=.3, which="both")

    fig.suptitle(f"Reproduction — {label}  (T={T}, B={meta.get('cfg', {}).get('B', meta.get('args', {}).get('B'))}, "
                 f"reps={int(df['rep'].max()) + 1})", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    FIG.mkdir(parents=True, exist_ok=True)
    out = FIG / f"repro_{tag}.png"
    fig.savefig(out, dpi=300)
    fig.savefig(FIG / f"repro_{tag}.pdf")
    plt.close(fig)
    print(f"[fig] {out}")

    last = summ.iloc[-1]
    return {"experiment": label, "T": T, "reps": int(df["rep"].max()) + 1,
            "phi_star": round(phi_pop, 5),
            "coverage_hold_T": round(float(last.cov_hold), 3),
            "coverage_pop_T": round(float(last.cov_pop), 3),
            "ci_width_T": round(float(last.width), 5),
            "mis_T": round(float(last.mis), 5),
            "w2_T": round(float(w2[-1]), 5)}


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    rows = []
    for tag, rep_csv, meta_json, kind, label in EXPERIMENTS:
        if not (RAW / rep_csv).exists():
            print(f"[skip] {rep_csv} not found")
            continue
        rows.append(make_figure(tag, rep_csv, meta_json, kind, label))
    if rows:
        out = TAB / "repro_summary.csv"
        pd.DataFrame(rows).to_csv(out, index=False)
        print("\n=== combined reproduction summary ===")
        print(pd.DataFrame(rows).to_string(index=False))
        print(f"saved -> {out}")


if __name__ == "__main__":
    main()
