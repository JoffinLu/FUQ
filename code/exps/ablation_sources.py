"""Which noise source must a fairness interval resample?

Ablation over the components of the joint bootstrap, under PROTOCOL A (a fresh evaluation set
in every repetition, fixed constraint set D'): for each repetition we form three intervals and
measure their coverage of the population gap phi(theta*):

  * "paper"      : training deviations only (the published online multiplier bootstrap);
  * "eval only"  : evaluation resampling deviations only, centred at the freshly evaluated
                   Delta_hat(Theta_T) (a parametric bootstrap of the evaluation set);
  * "train+eval" : training + evaluation deviations (the joint bootstrap without D' resampling).

If the two sources are of comparable size, neither single-source interval can reach the nominal
level and only the combined one does.  This is the empirical counterpart of the variance budget.

Run:
  python code/exps/ablation_sources.py --dataset synth_di --m 1000
  python code/exps/ablation_sources.py --dataset adult
  python code/exps/ablation_sources.py --dataset acsincome
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

from core.dgp import dgp_di, dgp_dm  # noqa: E402
from core.fairuq import add_intercept, di_constraint_direction, train_di, train_dm  # noqa: E402
from core.optimum import theta_star_di, theta_star_dm  # noqa: E402

ROOT = CODE_DIR.parent
DATA = ROOT / "data" / "processed"
TAB = ROOT / "results" / "tables"

REAL_CFG = {
    "adult":     dict(kind="di", eps=1e-5, n_dprime=1000, m=1000, n_reservoir=8000, kappa=0.1),
    "acsincome": dict(kind="di", eps=0.01, n_dprime=1000, m=1000, n_reservoir=8000, kappa=0.1),
    "compas":    dict(kind="dm", R2=300.0, n_dprime=250, m=400, n_reservoir=1200, kappa=0.1),
}
SYNTH = dict(n_pool=20000, n_dprime=200, eps=0.002, kappa=1e-4)
SYNTH_DM = dict(n_pool=20000, n_dprime=250, R2=500.0, kappa=1e-4, m=100, eta0=0.03)


def run_synth_dm(args):
    """Synthetic DM generator (R^2 = 500): training - divergence with eta0 = 0.1."""
    X, y, z = dgp_dm(SYNTH_DM["n_pool"] + SYNTH_DM["n_dprime"], seed=args.seed)
    perm = np.random.default_rng(args.seed + 1).permutation(len(y))
    i_dp, i_pool = perm[:SYNTH_DM["n_dprime"]], perm[SYNTH_DM["n_dprime"]:]
    Phi = add_intercept(X)
    Phi_pool, y_pool = Phi[i_pool], y[i_pool]
    w_all = z[i_dp].astype(np.float64) - float(z[i_dp].mean())
    sel = (y[i_dp] == -1)
    Phi_m, y_m, w_m = Phi[i_dp][sel], y[i_dp][sel].astype(np.float64), w_all[sel]
    th_star, _ = theta_star_dm(Phi_pool, y_pool, SYNTH_DM["R2"], Phi_m, y_m, w_m,
                               SYNTH_DM["kappa"])
    Xt, yt, zt = dgp_dm(2000000, seed=args.seed + 3)
    phi_pop = abs(float(delta_hat(th_star, add_intercept(Xt), zt, yt, kind="dm")[0]))
    print(f"[synth_dm] m={args.m} phi_pop={phi_pop:.5f}")

    rng = np.random.default_rng(args.seed + 99)
    rows = []
    for rep in range(args.reps):
        avg, _ = train_dm(Phi_pool, y_pool, SYNTH_DM["R2"], Phi_m, y_m, w_m, T=args.T,
                          B=args.B, kappa=SYNTH_DM["kappa"], eta0=SYNTH_DM["eta0"],
                          eta_a=0.501,
                          rng=np.random.default_rng(args.seed + 1000 + rep))
        Xe, ye, ze = dgp_dm(args.m, seed=args.seed + 500000 + rep)
        Phi_e = add_intercept(Xe)
        cen = float(delta_hat(avg[0:1], Phi_e, ze, ye, kind="dm")[0])
        train_dev = delta_hat(avg[1:], Phi_e, ze, ye, kind="dm") - cen
        sigma2 = args.T * float(np.var(train_dev, ddof=1))

        pred = (avg[0] @ Phi_e.T) > 0
        mask = (ye == -1)
        m0, m1 = mask & (ze == 0), mask & (ze == 1)
        idx0, idx1 = np.where(m0)[0], np.where(m1)[0]
        n0, n1 = len(idx0), len(idx1)
        p0, p1 = float(pred[idx0].mean()), float(pred[idx1].mean())
        v2 = p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1
        e0 = pred[idx0][rng.integers(0, n0, size=(args.R, n0))].mean(axis=1) - p0
        e1 = pred[idx1][rng.integers(0, n1, size=(args.R, n1))].mean(axis=1) - p1
        eval_dev = e0 - e1

        lo_p, hi_p = np.quantile(np.abs(cen + train_dev),
                                 [args.alpha / 2, 1 - args.alpha / 2])
        lo_e, hi_e = interval(cen, eval_dev, args.alpha)
        comb = (train_dev[rng.integers(0, args.B, size=4000)]
                + eval_dev[rng.integers(0, args.R, size=4000)])
        lo_j, hi_j = interval(cen, comb, args.alpha)
        rows.append({"rep": rep,
                     "cov_paper": float(lo_p <= phi_pop <= hi_p), "w_paper": hi_p - lo_p,
                     "cov_eval": float(lo_e <= phi_pop <= hi_e), "w_eval": hi_e - lo_e,
                     "cov_je": float(lo_j <= phi_pop <= hi_j), "w_je": hi_j - lo_j,
                     "se_train": float(np.sqrt(sigma2 / args.T)), "se_eval": float(np.sqrt(v2))})
    return phi_pop, pd.DataFrame(rows), dict(SYNTH_DM, m=args.m, kind="dm")


def delta_hat(Theta, Phi_eval, z_eval, y_eval=None, kind="di"):
    pred = (np.atleast_2d(Theta) @ Phi_eval.T) > 0.0
    if kind == "di":
        m0, m1 = z_eval == 0, z_eval == 1
    else:
        mask = (y_eval == -1)
        m0, m1 = mask & (z_eval == 0), mask & (z_eval == 1)
    return pred[:, m0].mean(axis=1) - pred[:, m1].mean(axis=1)


def fold(lo, hi):
    if lo > 0:
        return lo, hi
    if hi < 0:
        return -hi, -lo
    return 0.0, max(-lo, hi)


def interval(cen, dev, alpha):
    ql, qh = np.quantile(dev, [alpha / 2, 1 - alpha / 2])
    return fold(cen + ql, cen + qh)


def run_synth(args):
    X, y, z = dgp_di(SYNTH["n_pool"] + SYNTH["n_dprime"], seed=args.seed)
    perm = np.random.default_rng(args.seed + 1).permutation(len(y))
    i_dp, i_pool = perm[:SYNTH["n_dprime"]], perm[SYNTH["n_dprime"]:]
    Phi = add_intercept(X)
    Phi_pool, y_pool = Phi[i_pool], y[i_pool]
    xt = di_constraint_direction(Phi[i_dp], z[i_dp])
    th_star, _ = theta_star_di(Phi_pool, y_pool, xt, SYNTH["eps"], SYNTH["kappa"])
    Xt, _, zt = dgp_di(2000000, seed=args.seed + 3)
    phi_pop = abs(float(delta_hat(th_star, add_intercept(Xt), zt)[0]))
    print(f"[synth_di] m={args.m} phi_pop={phi_pop:.5f}")

    rng = np.random.default_rng(args.seed + 99)
    rows = []
    for rep in range(args.reps):
        avg, _ = train_di(Phi_pool, y_pool, xt, SYNTH["eps"], T=args.T, B=args.B,
                          kappa=SYNTH["kappa"], eta0=args.eta0, eta_a=0.501,
                          rng=np.random.default_rng(args.seed + 1000 + rep))
        Xe, _, ze = dgp_di(args.m, seed=args.seed + 500000 + rep)
        Phi_e = add_intercept(Xe)
        cen = float(delta_hat(avg[0:1], Phi_e, ze)[0])
        train_dev = delta_hat(avg[1:], Phi_e, ze) - cen
        sigma2 = args.T * float(np.var(train_dev, ddof=1))

        pred = (avg[0] @ Phi_e.T) > 0
        idx0, idx1 = np.where(ze == 0)[0], np.where(ze == 1)[0]
        n0, n1 = len(idx0), len(idx1)
        p0, p1 = float(pred[idx0].mean()), float(pred[idx1].mean())
        v2 = p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1
        e0 = pred[idx0][rng.integers(0, n0, size=(args.R, n0))].mean(axis=1) - p0
        e1 = pred[idx1][rng.integers(0, n1, size=(args.R, n1))].mean(axis=1) - p1
        eval_dev = e0 - e1

        lo_p, hi_p = np.quantile(np.abs(cen + train_dev),
                                          [args.alpha / 2, 1 - args.alpha / 2])
        lo_e, hi_e = interval(cen, eval_dev, args.alpha)
        comb = (train_dev[rng.integers(0, args.B, size=4000)]
                + eval_dev[rng.integers(0, args.R, size=4000)])
        lo_j, hi_j = interval(cen, comb, args.alpha)
        rows.append({"rep": rep,
                     "cov_paper": float(lo_p <= phi_pop <= hi_p), "w_paper": hi_p - lo_p,
                     "cov_eval": float(lo_e <= phi_pop <= hi_e), "w_eval": hi_e - lo_e,
                     "cov_je": float(lo_j <= phi_pop <= hi_j), "w_je": hi_j - lo_j,
                     "se_train": float(np.sqrt(sigma2 / args.T)), "se_eval": float(np.sqrt(v2))})
    return phi_pop, pd.DataFrame(rows), SYNTH


def run_real(args):
    cfg = REAL_CFG[args.dataset]
    d = np.load(DATA / f"{args.dataset}.npz")
    X, y, z = d["X"].astype(np.float64), d["y"].astype(np.int64), d["z"].astype(np.int64)
    rng = np.random.default_rng(args.seed)
    perm = rng.permutation(len(y))
    i_dp = perm[:cfg["n_dprime"]]
    i_res = perm[cfg["n_dprime"]:cfg["n_dprime"] + cfg["n_reservoir"]]
    i_pool = perm[cfg["n_dprime"] + cfg["n_reservoir"]:]
    mu, sd = X[i_pool].mean(0), X[i_pool].std(0)
    sd[sd < 1e-12] = 1.0
    Phi = add_intercept((X - mu) / sd)
    Phi_pool, Phi_res = Phi[i_pool], Phi[i_res]
    y_pool, y_res = y[i_pool], y[i_res]
    z_res = z[i_res]

    kind = cfg["kind"]
    if kind == "di":
        xt = di_constraint_direction(Phi[i_dp], z[i_dp])
        th_star, res = theta_star_di(Phi_pool, y_pool, xt, cfg["eps"], cfg["kappa"])
    else:
        w_all = z[i_dp].astype(np.float64) - float(z[i_dp].mean())
        sel = (y[i_dp] == -1)
        Phi_m, y_m, w_m = Phi[i_dp][sel], y[i_dp][sel].astype(np.float64), w_all[sel]

        th_star, res = theta_star_dm(Phi_pool, y_pool, cfg["R2"],
                                            Phi_m, y_m, w_m, cfg["kappa"])

    idx_all = (np.random.default_rng(args.seed + 5).choice(len(y), size=200000, replace=False)
               if len(y) > 200000 else np.arange(len(y)))
    phi_pop = abs(float(delta_hat(th_star, Phi[idx_all], z[idx_all], y[idx_all], kind)[0]))
    print(f"[{args.dataset}] kind={kind} m={cfg['m']} phi_pop={phi_pop:.5f}")

    rng2 = np.random.default_rng(args.seed + 99)
    residx = np.arange(len(i_res))
    rows = []
    for rep in range(args.reps):
        if kind == "di":
            avg, _ = train_di(Phi_pool, y_pool, xt, cfg["eps"], T=args.T, B=args.B,
                              kappa=cfg["kappa"], eta0=args.eta0, eta_a=0.501,
                              rng=np.random.default_rng(args.seed + 1000 + rep))
        else:
            avg, _ = train_dm(Phi_pool, y_pool, cfg["R2"], Phi_m, y_m, w_m, T=args.T, B=args.B,
                              kappa=cfg["kappa"], eta0=args.eta0, eta_a=0.501,
                              rng=np.random.default_rng(args.seed + 1000 + rep))
        sel = rng2.choice(residx, size=cfg["m"], replace=False)
        Phi_e, z_e, y_e = Phi_res[sel], z_res[sel], y_res[sel]
        cen = float(delta_hat(avg[0:1], Phi_e, z_e, y_e, kind)[0])
        train_dev = delta_hat(avg[1:], Phi_e, z_e, y_e, kind) - cen
        sigma2 = args.T * float(np.var(train_dev, ddof=1))

        pred = (avg[0] @ Phi_e.T) > 0
        if kind == "di":
            m0, m1 = z_e == 0, z_e == 1
        else:
            mask = (y_e == -1)
            m0, m1 = mask & (z_e == 0), mask & (z_e == 1)
        idx0, idx1 = np.where(m0)[0], np.where(m1)[0]
        n0, n1 = len(idx0), len(idx1)
        p0, p1 = float(pred[idx0].mean()), float(pred[idx1].mean())
        v2 = p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1
        e0 = pred[idx0][rng2.integers(0, n0, size=(args.R, n0))].mean(axis=1) - p0
        e1 = pred[idx1][rng2.integers(0, n1, size=(args.R, n1))].mean(axis=1) - p1
        eval_dev = e0 - e1

        lo_p, hi_p = np.quantile(np.abs(cen + train_dev),
                                          [args.alpha / 2, 1 - args.alpha / 2])
        lo_e, hi_e = interval(cen, eval_dev, args.alpha)
        comb = (train_dev[rng2.integers(0, args.B, size=4000)]
                + eval_dev[rng2.integers(0, args.R, size=4000)])
        lo_j, hi_j = interval(cen, comb, args.alpha)
        rows.append({"rep": rep,
                     "cov_paper": float(lo_p <= phi_pop <= hi_p), "w_paper": hi_p - lo_p,
                     "cov_eval": float(lo_e <= phi_pop <= hi_e), "w_eval": hi_e - lo_e,
                     "cov_je": float(lo_j <= phi_pop <= hi_j), "w_je": hi_j - lo_j,
                     "se_train": float(np.sqrt(sigma2 / args.T)), "se_eval": float(np.sqrt(v2))})
    return phi_pop, pd.DataFrame(rows), cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["synth_di", "synth_dm", "adult", "acsincome",
                                          "compas"], required=True)
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--m", type=int, default=1000, help="synth_di only: held-out size")
    ap.add_argument("--T", type=int, default=20000)
    ap.add_argument("--B", type=int, default=100)
    ap.add_argument("--R", type=int, default=300)
    ap.add_argument("--eta0", type=float, default=0.1)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--tag", default=None, help="output tag override (finite-sample grid)")
    args = ap.parse_args()
    if args.dataset in ("adult", "acsincome", "compas"):
        args.T = 30000
    t0 = time.time()
    TAB.mkdir(parents=True, exist_ok=True)
    if args.dataset == "synth_di":
        phi_pop, df, cfg = run_synth(args)
    elif args.dataset == "synth_dm":
        phi_pop, df, cfg = run_synth_dm(args)
    else:
        phi_pop, df, cfg = run_real(args)
    out = {"dataset": args.dataset, "protocol": "A (fresh evaluation set per repetition)",
           "config": {"T": args.T, "B": args.B, "R": args.R, "reps": args.reps,
                      "m": args.m if args.dataset in ("synth_di", "synth_dm") else cfg["m"],
                      "eta0": args.eta0, **cfg},
           "phi_pop": round(phi_pop, 5),
           "coverage_paper": round(float(df.cov_paper.mean()), 3),
           "coverage_eval_only": round(float(df.cov_eval.mean()), 3),
           "coverage_train_eval": round(float(df.cov_je.mean()), 3),
           "width_paper": round(float(df.w_paper.mean()), 5),
           "width_eval_only": round(float(df.w_eval.mean()), 5),
           "width_train_eval": round(float(df.w_je.mean()), 5),
           "se_train": round(float(df.se_train.mean()), 5),
           "se_eval": round(float(df.se_eval.mean()), 5),
           "elapsed_sec": round(time.time() - t0, 1)}
    if args.dataset == "synth_di":
        tag = f"synth_di_m{args.m}"
    elif args.dataset == "synth_dm":
        tag = f"synth_dm_m{args.m}"
    else:
        tag = args.dataset
    if args.tag:
        tag = args.tag
    df.to_csv(TAB / f"ablation_{tag}_per_rep.csv", index=False)
    with open(TAB / f"ablation_{tag}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print("saved ->", TAB / f"ablation_{tag}.json")


if __name__ == "__main__":
    main()
