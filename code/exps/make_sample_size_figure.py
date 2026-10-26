"""Sample-size planning figure and the minimum certifiable gap.

From the protocol-A runs we have se_train at T and se_eval at m, hence
  sigma_Delta ~ se_train * sqrt(T),      v ~ se_eval * sqrt(m).
For a target 95% half-width w the feasible set is
  sigma_Delta^2 / T + v^2 / m  <=  (w / 1.96)^2 ,
and the best achievable half-width at a given budget is hw(T,m) = 1.96 sqrt(sigma^2/T + v^2/m).

Outputs:
  results/figures/sample_size.{png,pdf}  -- feasible region (T, m) for three datasets
  results/tables/min_detectable_gap.csv  -- hw at the audit budget vs the reported gap
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
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
import viz_style as vs  # noqa: E402

TAB = ROOT / "results" / "tables"
FIG = ROOT / "results" / "figures"
ZT = 1.959963984540054

SETS = ["adult", "acsincome", "compas"]
LABELS = {"adult": "Adult (DI)", "acsincome": "ACSIncome (DI)", "compas": "COMPAS (DM)"}


def main():
    est = {}
    for s in SETS:
        j = json.load(open(TAB / f"real_joint_ci_{s}.json", encoding="utf-8"))
        T = j["config"]["T"]
        m = j["config"]["m"]
        sigma = j["se_train_mean"] * np.sqrt(T)
        v = j["se_eval_mean"] * np.sqrt(m)
        hw = ZT * np.sqrt(sigma ** 2 / T + v ** 2 / m)
        est[s] = {"T": T, "m": m, "sigma": sigma, "v": v, "phi": j["phi_pop"],
                  "half_width": hw, "ratio": hw / j["phi_pop"]}

    rows = []
    for s in SETS:
        e = est[s]
        rows.append({"dataset": s, "phi_pop": round(e["phi"], 5), "T": e["T"], "m": e["m"],
                     "sigma_Delta": round(e["sigma"], 4), "v": round(e["v"], 4),
                     "best_half_width": round(e["half_width"], 4),
                     "half_width_over_gap": round(e["ratio"], 2)})
    df = pd.DataFrame(rows)
    df.to_csv(TAB / "min_detectable_gap.csv", index=False)
    print(df.to_string(index=False))

    vs.apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(vs.TEXT_WIDTH_IN, 2.95))
    fig.subplots_adjust(left=0.085, right=0.99, top=0.86, bottom=0.245, wspace=0.24)
    curve_styles = [(0.02, vs.OURS, "-"), (0.05, vs.EVAL, "--"), (0.10, vs.BASE, ":")]
    for i, (ax, s) in enumerate(zip(axes, SETS)):
        e = est[s]
        sigma, v = e["sigma"], e["v"]
        T = np.logspace(3, 6.5, 300)
        for w, color, style in curve_styles:
            inside = sigma ** 2 / T < (w / ZT) ** 2
            m_need = np.where(inside,
                              v ** 2 / np.maximum((w / ZT) ** 2 - sigma ** 2 / T, 1e-12),
                              np.nan)
            ax.plot(T, m_need, style, lw=1.3, color=color)
        ax.scatter([e["T"]], [e["m"]], marker="*", s=90, color=vs.POP, zorder=5)
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("training iterations $T$")
        if i == 0:
            ax.set_ylabel("evaluation size $m$")
        ax.grid(True, which="major")
        ax.set_title(LABELS[s], fontsize=8, fontweight="bold", pad=4)
        vs.panel_label(ax, "abc"[i], y=1.02)

    handles = [
        Line2D([], [], color=vs.OURS, ls="-", lw=1.3, label="half-width 0.02"),
        Line2D([], [], color=vs.EVAL, ls="--", lw=1.3, label="half-width 0.05"),
        Line2D([], [], color=vs.BASE, ls=":", lw=1.3, label="half-width 0.10"),
        Line2D([], [], color=vs.POP, marker="*", ls="none", ms=8, label="audit budget"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.005),
               handletextpad=0.4, columnspacing=1.6)
    FIG.mkdir(parents=True, exist_ok=True)
    vs.finish(fig, FIG / "sample_size.pdf", FIG / "sample_size.png",
              align=True, align_json=FIG / "sample_size.alignment.json")
    print(f"[fig] {FIG / 'sample_size.pdf'}")


if __name__ == "__main__":
    main()
