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
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
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

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.1))
    for ax, s in zip(axes, SETS):
        e = est[s]
        sigma, v = e["sigma"], e["v"]
        T = np.logspace(3, 6.5, 300)
        for w, style in [(0.02, "-"), (0.05, "--"), (0.10, ":")]:
            inside = sigma ** 2 / T < (w / ZT) ** 2
            m_need = np.where(inside,
                              v ** 2 / np.maximum((w / ZT) ** 2 - sigma ** 2 / T, 1e-12),
                              np.nan)
            ax.plot(T, m_need, style, lw=1.4, label=f"half-width {w:.2f}")
        ax.scatter([e["T"]], [e["m"]], marker="*", s=180, color="#d62728", zorder=5,
                   label="audit budget")
        ax.axhline(e["m"], color="gray", lw=0.8, ls="-.")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("training iterations T"); ax.set_ylabel("evaluation size m")
        ax.set_title(f"{LABELS[s]}  (reported gap {e['phi']:.3f});\n"
                     f"best half-width at budget {e['half_width']:.3f}")
        ax.legend(fontsize=7); ax.grid(alpha=.3, which="both")
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"sample_size.{ext}", dpi=300)
    plt.close(fig)
    print(f"[fig] {FIG / 'sample_size.png'}")


if __name__ == "__main__":
    main()
