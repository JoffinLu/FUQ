"""Figures for the extension paper.

(a) protocol-A coverage vs |D~| (paper vs joint bootstrap), from joint_bootstrap_v3b_fresh_eval.json
(b) width ratio (joint / paper) vs |D~|
(c) three-source variance shares on Adult / ACSIncome / COMPAS, from variance_budget_*.json
(d) standard errors of the three components (log scale)
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


def main():
    jb = json.load(open(TAB / "joint_bootstrap_v3b_fresh_eval.json", encoding="utf-8"))["results"]
    ms = [r["m_tilde"] for r in jb]
    cov_p = [r["cov_paper"] for r in jb]
    cov_j = [r["cov_jb"] for r in jb]
    ratio = [r["width_jb"] / r["width_paper"] for r in jb]

    buds = {}
    for name in ("adult", "acsincome", "compas"):
        buds[name] = json.load(open(TAB / f"variance_budget_{name}.json", encoding="utf-8"))

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.4))

    ax = axes[0, 0]
    ax.plot(ms, cov_p, "o-", label="paper CI", color="#d62728")
    ax.plot(ms, cov_j, "s-", label="joint bootstrap", color="#1f77b4")
    ax.axhline(0.95, color="k", ls=":", lw=1, label="nominal 0.95")
    ax.set_xscale("log"); ax.set_xlabel("held-out size m"); ax.set_ylabel("coverage of $\\phi(\\theta^*)$")
    ax.set_ylim(0.4, 1.03); ax.legend(fontsize=8, loc="lower right")
    ax.set_title("(a) protocol-A coverage vs m"); ax.grid(alpha=.3)

    ax = axes[0, 1]
    ax.plot(ms, ratio, "o-", color="#2ca02c")
    ax.axhline(1.0, color="k", ls=":", lw=1)
    ax.set_xscale("log"); ax.set_xlabel("held-out size m"); ax.set_ylabel("width(joint) / width(paper)")
    ax.set_title("(b) price of valid inference"); ax.grid(alpha=.3)

    labels = {"adult": "Adult (DI)", "acsincome": "ACSIncome (DI)", "compas": "COMPAS (DM)"}
    shares = np.array([[buds[k]["share_train"], buds[k]["share_eval"], buds[k]["share_Dprime"]]
                       for k in buds])
    ax = axes[1, 0]
    bottom = np.zeros(len(buds))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    names = ["training", "evaluation", "constraint set $D'$"]
    for j, (c, nm) in enumerate(zip(colors, names)):
        ax.bar([labels[k] for k in buds], shares[:, j], bottom=bottom, color=c, label=nm)
        bottom += shares[:, j]
    ax.set_ylabel("share of total variance"); ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, loc="upper right", ncols=3)
    ax.set_title("(c) variance budget"); ax.grid(alpha=.3, axis="y")

    ax = axes[1, 1]
    x = np.arange(len(buds))
    w = 0.26
    ax.bar(x - w, [buds[k]["se_train"] for k in buds], w, label="training", color=colors[0])
    ax.bar(x, [buds[k]["se_eval"] for k in buds], w, label="evaluation", color=colors[1])
    ax.bar(x + w, [buds[k]["sd_Dprime"] for k in buds], w, label="constraint $D'$", color=colors[2])
    ax.set_xticks(x); ax.set_xticklabels([labels[k] for k in buds])
    ax.set_yscale("log"); ax.set_ylabel("standard error (log)")
    ax.legend(fontsize=8); ax.set_title("(d) component sizes"); ax.grid(alpha=.3, axis="y")

    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"extension_main.{ext}", dpi=300)
    plt.close(fig)
    print(f"[fig] {FIG / 'extension_main.png'}")


if __name__ == "__main__":
    main()
