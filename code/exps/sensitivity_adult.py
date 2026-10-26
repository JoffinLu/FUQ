"""Sensitivity of the paper's CI to the optimisation bias (the "bias floor").

For a fixed data split and a FIXED held-out set (protocol B, as in the original simulation design),
vary the regularisation strength kappa and the number of iterations T.  Report:
  * ||theta_bar_T - theta*||   (optimisation bias)
  * coverage of the population phi(theta*)   (protocol B)
  * CI width
A converged averaged iterate is a prerequisite for any variance-based interval; when the bias is
larger than the interval half-width the coverage collapses regardless of the bootstrap.

Run: python code/exps/sensitivity_adult.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from core.fairuq import add_intercept, di_constraint_direction, make_splits, phi_hat, train_di  # noqa: E402
from core.optimum import theta_star_di  # noqa: E402

ROOT = CODE_DIR.parent
DATA = ROOT / "data" / "processed"
TAB = ROOT / "results" / "tables"

ZT = 1.959963984540054


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="adult")
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--B", type=int, default=100)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=20261026)
    args = ap.parse_args()

    d = np.load(DATA / f"{args.dataset}.npz")
    X, y, z = d["X"].astype(np.float64), d["y"].astype(np.int64), d["z"].astype(np.int64)
    i_dp, i_tl, i_pool = make_splits(len(y), 1000, 1000, np.random.default_rng(args.seed))
    mu, sd = X[i_pool].mean(0), X[i_pool].std(0)
    sd[sd < 1e-12] = 1.0
    Phi = add_intercept((X - mu) / sd)
    Phi_pool, y_pool = Phi[i_pool], y[i_pool]
    Phi_tl, z_tl = Phi[i_tl], z[i_tl]
    xt = di_constraint_direction(Phi[i_dp], z[i_dp])

    # population target: full dataset evaluated at theta*(kappa) -- per kappa below
    idx_all = np.arange(len(y))

    grid = [(1e-4, 20000), (1e-2, 20000), (0.1, 20000), (1.0, 20000)]
    rows = []
    rng_global = np.random.default_rng(args.seed + 3)
    for kappa, T in grid:
        th_star, res = theta_star_di(Phi_pool, y_pool, xt, 1e-5, kappa)
        pred_star = (th_star @ Phi[idx_all].T) > 0
        phi_pop = abs(pred_star[z == 0].mean() - pred_star[z == 1].mean())
        covs, widths, dists, phis = [], [], [], []
        for rep in range(args.reps):
            avg, _ = train_di(Phi_pool, y_pool, xt, 1e-5, T=T, B=args.B, kappa=kappa,
                              eta0=0.1, eta_a=0.501,
                              rng=np.random.default_rng(args.seed + 1000 + rep + 7919 * rep))
            th = avg[0]
            dists.append(float(np.linalg.norm(th - th_star)))
            phis_main = phi_hat(avg, Phi_tl, z_tl, kind="di")
            lo, hi = np.quantile(phis_main[1:], [args.alpha / 2, 1 - args.alpha / 2])
            covs.append(float(lo <= phi_pop <= hi))
            widths.append(float(hi - lo))
        rows.append({"kappa": kappa, "T": T, "theta_star_norm": round(float(np.linalg.norm(th_star)), 3),
                     "bias_median": round(float(np.median(dists)), 4),
                     "coverage_pop": round(float(np.mean(covs)), 3),
                     "ci_width": round(float(np.mean(widths)), 5),
                     "phi_pop": round(float(phi_pop), 5)})
        print(rows[-1])

    df = pd.DataFrame(rows)
    TAB.mkdir(parents=True, exist_ok=True)
    df.to_csv(TAB / f"sensitivity_{args.dataset}.csv", index=False)
    with open(TAB / f"sensitivity_{args.dataset}.json", "w", encoding="utf-8") as f:
        json.dump({"config": vars(args), "rows": rows}, f, indent=2, ensure_ascii=False)
    print(df.to_string(index=False))
    print(f"saved -> {TAB / f'sensitivity_{args.dataset}.csv'}")


if __name__ == "__main__":
    main()
