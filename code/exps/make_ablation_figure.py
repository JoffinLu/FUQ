"""Figure for the source ablation (protocol A, joint vs single-source bootstrap).

(a) coverage of the population gap phi(theta*) for the three intervals
(b) interval width, averaged over repetitions

Reads results/tables/ablation_{synth_di_m100,synth_di_m1000,synth_dm_m100,
synth_dm_m1000,adult,acsincome,compas}.json and writes
results/figures/ablation_coverage.{pdf,png}.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
import viz_style as vs  # noqa: E402

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
    ("coverage_paper", "width_paper", "training only", vs.BASE),
    ("coverage_eval_only", "width_eval_only", "evaluation only", vs.EVAL),
    ("coverage_train_eval", "width_train_eval", "joint (this paper)", vs.OURS),
]


def main():
    rows = []
    for tag, label in SETTINGS:
        with open(TAB / f"ablation_{tag}.json", encoding="utf-8") as fh:
            rows.append((label, json.load(fh)))

    vs.apply_style()
    x = np.arange(len(rows))
    w = 0.26
    fig, axes = plt.subplots(2, 1, figsize=(vs.TEXT_WIDTH_IN, 3.65), sharex=True)
    fig.subplots_adjust(left=0.095, right=0.99, top=0.93, bottom=0.235, hspace=0.16)

    ax = axes[0]
    for j, (cov_key, _, name, color) in enumerate(VARIANTS):
        vals = [r[cov_key] for _, r in rows]
        ax.bar(x + (j - 1) * w, vals, w, label=name, color=color, edgecolor="none")
    ax.axhline(0.95, color=vs.REF, ls=(0, (1, 1.6)), lw=1.0, label="nominal 0.95")
    ax.set_ylabel("coverage of $\\phi(\\theta^*)$")
    ax.set_ylim(0.0, 1.08)
    ax.grid(True, axis="y", which="major")
    ax.tick_params(labelbottom=False)

    ax = axes[1]
    for j, (_, width_key, name, color) in enumerate(VARIANTS):
        vals = [r[width_key] for _, r in rows]
        ax.bar(x + (j - 1) * w, vals, w, label=name, color=color, edgecolor="none")
    ax.set_xticks(x)
    ax.set_xticklabels([lab for lab, _ in rows], fontsize=7)
    ax.set_ylabel("95% interval width")
    ax.set_ylim(0.0, 0.30)
    ax.grid(True, axis="y", which="major")

    # Panel letters live in the figure margin: inside the axes they would be
    # crossed by the horizontal grid lines (flagged by the collision audit).
    p_top = axes[0].get_position()
    p_bot = axes[1].get_position()
    fig.text(0.02, p_top.y1 + 0.02, "a", fontsize=9, fontweight="bold",
             color="#272727", ha="left", va="center")
    fig.text(0.02, 0.5 * (p_top.y0 + p_bot.y1), "b", fontsize=9, fontweight="bold",
             color="#272727", ha="left", va="center")

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=vs.BASE, label="training only"),
        plt.Rectangle((0, 0), 1, 1, color=vs.EVAL, label="evaluation only"),
        plt.Rectangle((0, 0), 1, 1, color=vs.OURS, label="joint (this paper)"),
        vs.nominal_handle(),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.005),
               handletextpad=0.4, columnspacing=1.6)

    FIG.mkdir(parents=True, exist_ok=True)
    vs.finish(fig, FIG / "ablation_coverage.pdf", FIG / "ablation_coverage.png",
              align=True, align_json=FIG / "ablation_coverage.alignment.json")

    print("wrote results/figures/ablation_coverage.{pdf,png}")
    for lab, r in rows:
        print(f"{lab:18s} cov {r['coverage_paper']:.2f} {r['coverage_eval_only']:.2f} "
              f"{r['coverage_train_eval']:.2f} | width {r['width_paper']:.3f} "
              f"{r['width_eval_only']:.3f} {r['width_train_eval']:.3f}")


if __name__ == "__main__":
    main()
