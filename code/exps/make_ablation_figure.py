"""Figure for the source ablation (protocol A, joint vs single-source bootstrap).

(a) coverage of the population gap phi(theta*) for the three intervals
(b) interval width, averaged over repetitions

Reads results/tables/ablation_{synth_di_m100,synth_di_m1000,synth_dm_m100,
synth_dm_m1000,adult,acsincome,compas}.json and writes
results/figures/ablation_coverage.{pdf,png}.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TAB = ROOT / "results" / "tables"
FIG = ROOT / "results" / "figures"

SETTINGS = [
    ("synth_di_m100", "S-DI\nm=100"),
    ("synth_di_m1000", "S-DI\nm=1000"),
    ("synth_dm_m100", "S-DM\nm=100"),
    ("synth_dm_m1000", "S-DM\nm=1000"),
    ("adult", "Adult\nm=1000"),
    ("acsincome", "ACSIncome\nm=1000"),
    ("compas", "COMPAS\nm=400"),
]
VARIANTS = [
    ("coverage_paper", "width_paper", "training only", "#d62728"),
    ("coverage_eval_only", "width_eval_only", "evaluation only", "#ff7f0e"),
    ("coverage_train_eval", "width_train_eval", "joint (this paper)", "#1f77b4"),
]


def main():
    rows = []
    for tag, label in SETTINGS:
        with open(TAB / f"ablation_{tag}.json", encoding="utf-8") as fh:
            rows.append((label, json.load(fh)))

    x = np.arange(len(rows))
    w = 0.26
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.0))

    ax = axes[0]
    for j, (cov_key, _, name, color) in enumerate(VARIANTS):
        vals = [r[cov_key] for _, r in rows]
        ax.bar(x + (j - 1) * w, vals, w, label=name, color=color)
    ax.axhline(0.95, color="k", ls=":", lw=1, label="nominal 0.95")
    ax.set_xticks(x)
    ax.set_xticklabels([lab for lab, _ in rows], fontsize=7.5, linespacing=1.1)
    ax.set_ylabel("coverage of $\\phi(\\theta^*)$")
    ax.set_ylim(0.0, 1.06)
    ax.set_title("(a) coverage under protocol (A)")
    ax.grid(alpha=0.3, axis="y")
    ax.legend(fontsize=7.5, loc="lower left", framealpha=0.9)

    ax = axes[1]
    for j, (_, width_key, name, color) in enumerate(VARIANTS):
        vals = [r[width_key] for _, r in rows]
        ax.bar(x + (j - 1) * w, vals, w, label=name, color=color)
    ax.set_xticks(x)
    ax.set_xticklabels([lab for lab, _ in rows], fontsize=7.5, linespacing=1.1)
    ax.set_ylabel("95% interval width")
    ax.set_title("(b) price of valid inference")
    ax.grid(alpha=0.3, axis="y")
    ax.legend(fontsize=7.5, loc="upper left", framealpha=0.9)

    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"ablation_coverage.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("wrote results/figures/ablation_coverage.{pdf,png}")
    for lab, r in rows:
        print(f"{lab:18s} cov {r['coverage_paper']:.2f} {r['coverage_eval_only']:.2f} "
              f"{r['coverage_train_eval']:.2f} | width {r['width_paper']:.3f} "
              f"{r['width_eval_only']:.3f} {r['width_train_eval']:.3f}")


if __name__ == "__main__":
    main()
