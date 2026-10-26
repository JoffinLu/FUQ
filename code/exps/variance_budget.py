"""Variance budget: how much of the uncertainty in a reported fairness value comes from
   (T) training stochasticity, (E) evaluation sampling, and (C) constraint-set D' sampling?

Components (signed gap Delta = p0 - p1):
  T : Var(Delta(theta_bar_T) - Delta(theta*))      ~ sigma^2 / T   (from the reproduction CI widths)
  E : Var(Delta_hat_m(theta*) - Delta(theta*))     = v^2 / m       (binomial / delta method)
  C : Var(Delta(theta*(D'_new)) - Delta(theta*(D'))) = 2 s^2_{D'} if both audits are random draws;
      we report s^2_{D'} = Var over resampled D' of Delta(theta*(D'_r)) evaluated on the pool.

The C component is estimated by resampling D' R times and solving the constrained problem directly
(warm-started SLSQP / L-BFGS), which is the expensive-but-exact route; no retraining is needed.

Run: python code/exps/variance_budget.py --dataset adult --R 25
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from core.fairuq import add_intercept, di_constraint_direction, make_splits, phi_hat  # noqa: E402
from core.optimum import theta_star_di, theta_star_dm  # noqa: E402

ROOT = CODE_DIR.parent
DATA = ROOT / "data" / "processed"
TAB = ROOT / "results" / "tables"

CFG = {
    "adult":     dict(kind="di", eps=1e-5, n_dprime=1000, n_tilde=1000, kappa=0.1, T=50000),
    "acsincome": dict(kind="di", eps=0.01, n_dprime=1000, n_tilde=1000, kappa=0.1, T=50000),
    "compas":    dict(kind="dm", R2=300.0, n_dprime=250, n_tilde=400, kappa=0.1, T=50000),
}


def load_split(name, n_dprime, n_tilde, seed=20261026):
    d = np.load(DATA / f"{name}.npz")
    X, y, z = d["X"].astype(np.float64), d["y"].astype(np.int64), d["z"].astype(np.int64)
    i_dp, i_tl, i_pool = make_splits(len(y), n_dprime, n_tilde, np.random.default_rng(seed))
    mu, sd = X[i_pool].mean(axis=0), X[i_pool].std(axis=0)
    sd[sd < 1e-12] = 1.0
    Phi = add_intercept((X - mu) / sd)
    return Phi, y, z, i_dp, i_tl, i_pool


def delta_hat(Theta, Phi_eval, z_eval, y_eval=None, kind="di"):
    pred = (np.atleast_2d(Theta) @ Phi_eval.T) > 0.0
    if kind == "di":
        m0, m1 = z_eval == 0, z_eval == 1
    else:
        base = y_eval == -1
        m0, m1 = base & (z_eval == 0), base & (z_eval == 1)
    return pred[:, m0].mean(axis=1) - pred[:, m1].mean(axis=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=list(CFG), required=True)
    ap.add_argument("--R", type=int, default=25)
    ap.add_argument("--seed", type=int, default=20261026)
    args = ap.parse_args()
    cfg = CFG[args.dataset]
    kind = cfg["kind"]

    Phi, y, z, i_dp, i_tl, i_pool = load_split(args.dataset, cfg["n_dprime"], cfg["n_tilde"], args.seed)
    Phi_pool, y_pool, z_pool = Phi[i_pool], y[i_pool], z[i_pool]
    Phi_tl, y_tl, z_tl = Phi[i_tl], y[i_tl], z[i_tl]

    # ---- observed D' -> theta*, and the two cheap variance components ----
    if kind == "di":
        xt = di_constraint_direction(Phi[i_dp], z[i_dp])
        th, res = theta_star_di(Phi_pool, y_pool, xt, cfg["eps"], cfg["kappa"])
    else:
        w_all = z[i_dp].astype(np.float64) - float(z[i_dp].mean())
        sel = (y[i_dp] == -1)
        Phi_m, y_m, w_m = Phi[i_dp][sel], y[i_dp][sel].astype(np.float64), w_all[sel]
        th, res = theta_star_dm(Phi_pool, y_pool, cfg["R2"], Phi_m, y_m, w_m, cfg["kappa"])
    d_star = float(delta_hat(th, Phi_tl, z_tl, y_tl, kind)[0])
    pred = (th @ Phi_tl.T) > 0
    if kind == "di":
        m0, m1 = z_tl == 0, z_tl == 1
    else:
        base = y_tl == -1
        m0, m1 = base & (z_tl == 0), base & (z_tl == 1)
    p0, p1 = float(pred[m0].mean()), float(pred[m1].mean())
    n0, n1 = int(m0.sum()), int(m1.sum())
    v2 = p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1
    d_pop = float(delta_hat(th, Phi_pool, z_pool, y_pool, kind)[0])

    # training component: read the reproduction CI width for the same dataset
    summary_csv = TAB / f"real_{args.dataset}_summary_k01.csv"
    import pandas as pd
    summ = pd.read_csv(summary_csv)
    width_T = float(summ.iloc[-1]["ci_width_mean"])
    se_train = width_T / (2 * 1.959963984540054)

    # ---- constraint-set component: resample D' and re-solve theta*(D') ----
    rng = np.random.default_rng(args.seed + 7)
    n_c = cfg["n_dprime"]
    d_vals = []
    t0 = time.time()
    th_prev = th
    for r in range(args.R):
        idx = rng.choice(i_pool, size=n_c, replace=False)
        if kind == "di":
            xt_r = di_constraint_direction(Phi[idx], z[idx])
            th_r, rr = theta_star_di(Phi_pool, y_pool, xt_r, cfg["eps"], cfg["kappa"])
        else:
            z_r = z[idx]
            w_r = z_r.astype(np.float64) - float(z_r.mean())
            sel_r = (y[idx] == -1)
            th_r, rr = theta_star_dm(Phi_pool, y_pool, cfg["R2"],
                                     Phi[idx][sel_r], y[idx][sel_r].astype(np.float64), w_r[sel_r],
                                     cfg["kappa"])
        d_vals.append(float(delta_hat(th_r, Phi_pool, z_pool, y_pool, kind)[0]))
        if r == 0:
            print(f"  first D' resample solved in {time.time() - t0:.1f}s (success={rr.success})")
    d_vals = np.array(d_vals)
    s2_D = float(np.var(d_vals, ddof=1))
    mean_D = float(d_vals.mean())

    var_T = float(se_train ** 2)          # per-audit training variance of the reported gap
    var_E = float(v2)                     # evaluation variance (already includes 1/m)
    total = var_T + var_E + s2_D
    out = {"dataset": args.dataset, "kind": kind, "R": args.R,
           "delta_star_eval": round(d_star, 5), "delta_star_pool": round(d_pop, 5),
           "theta_star_norm": round(float(np.linalg.norm(th)), 3), "optimizer_success": bool(res.success),
           "se_train": round(se_train, 5), "se_eval": round(float(np.sqrt(v2)), 5),
           "sd_Dprime": round(float(np.sqrt(s2_D)), 5), "mean_delta_over_Dprime": round(mean_D, 5),
           "var_train": round(var_T, 8), "var_eval": round(var_E, 8), "var_Dprime": round(s2_D, 8),
           "share_train": round(var_T / total, 3) if total > 0 else None,
           "share_eval": round(var_E / total, 3) if total > 0 else None,
           "share_Dprime": round(s2_D / total, 3) if total > 0 else None,
           "total_se": round(float(np.sqrt(total)), 5),
           "elapsed_sec": round(time.time() - t0, 1)}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    TAB.mkdir(parents=True, exist_ok=True)
    with open(TAB / f"variance_budget_{args.dataset}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"saved -> {TAB / f'variance_budget_{args.dataset}.json'}")


if __name__ == "__main__":
    main()
