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
import viz_style as vs  # noqa: E402

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

    vs.apply_style()
    fig, axes = plt.subplots(2, 2, figsize=(vs.TEXT_WIDTH_IN, 4.55), sharex=True)
    fig.subplots_adjust(left=0.095, right=0.985, top=0.955, bottom=0.115,
                        wspace=0.30, hspace=0.30)
    ks = summ["k"].values

    # (a) W2 to theoretical normal
    sigma2 = T * float(np.var(df[df.k == T]["phi_main"].values, ddof=1))
    w2 = []
    for k in ks:
        phis = df[df.k == k]["phi_main"].values
        w2.append(w2_empirical_vs_normal(phis, phi_pop, np.sqrt(max(sigma2 / k, 1e-15))))
    ax = axes[0, 0]
    ax.plot(ks, w2, "o-", ms=vs.plt.rcParams["lines.markersize"], lw=1.2, color=vs.OURS)
    ax.set_xscale("log"); ax.set_yscale("log")
    vs.log_axis(ax)
    ax.set_ylabel(r"$W_2$ to asymptotic law")
    vs.panel_label(ax, "a")

    # (b) MIS
    ax = axes[0, 1]
    ax.plot(ks, summ["mis"], "s-", ms=vs.plt.rcParams["lines.markersize"], lw=1.2, color=vs.HELD)
    ax.set_xscale("log"); ax.set_yscale("log")
    vs.log_axis(ax)
    ax.set_ylabel("mean interval score")
    vs.panel_label(ax, "b")

    # (c) coverage, two targets
    ax = axes[1, 0]
    ax.plot(ks, summ["cov_hold"], "o-", ms=vs.plt.rcParams["lines.markersize"], lw=1.2,
            color=vs.HELD, label="held-out estimand $\\hat\\phi(\\theta^*)$")
    ax.plot(ks, summ["cov_pop"], "s--", ms=vs.plt.rcParams["lines.markersize"], lw=1.2,
            color=vs.POP, label="population $\\phi(\\theta^*)$")
    ax.axhline(1 - alpha, color=vs.REF, ls=(0, (1, 1.6)), lw=1.0, label="nominal $1-\\alpha$")
    ax.set_xscale("log"); ax.set_xlabel("iterations $k$"); ax.set_ylabel("coverage")
    ax.set_ylim(-0.03, 1.05)
    ax.legend(loc="lower center", labelspacing=0.25, handletextpad=0.5)
    vs.panel_label(ax, "c")

    # (d) width vs spread of phi across reps
    ax = axes[1, 1]
    ax.plot(ks, summ["width"], "o-", ms=vs.plt.rcParams["lines.markersize"], lw=1.2,
            color=vs.OURS, label="mean interval width")
    ax.plot(ks, 4 * summ["phi_sd"], "s--", ms=vs.plt.rcParams["lines.markersize"], lw=1.2,
            color=vs.EVAL, label="4 x sd of $\\phi(\\bar\\theta_k)$")
    ax.set_xscale("log")
    ax.set_xlabel("iterations $k$"); ax.set_ylabel("width")
    hi = max(float(summ["width"].max()), float((4 * summ["phi_sd"]).max())) * 1.08
    ax.set_ylim(0.0, hi)
    ax.legend(loc="upper right", labelspacing=0.25, handletextpad=0.5)
    vs.panel_label(ax, "d")

    for ax in axes[0]:
        ax.tick_params(labelbottom=False)
    FIG.mkdir(parents=True, exist_ok=True)
    vs.finish(fig, FIG / f"repro_{tag}.pdf", FIG / f"repro_{tag}.png",
              align=True, align_json=FIG / f"repro_{tag}.alignment.json")
    print(f"[fig] {FIG / ('repro_' + tag + '.pdf')}")

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
