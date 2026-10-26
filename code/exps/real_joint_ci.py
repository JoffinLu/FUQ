"""Protocol-A joint bootstrap on the REAL datasets (Adult / ACSIncome DI, COMPAS DM).

Split (per dataset):
  D'        : fixed constraint set (n_c from the paper's Table 1)
  reservoir : rows kept aside for evaluation; each repetition draws a fresh D~ of size m
  pool      : remaining rows -> training stream (with replacement)

Target: the population gap Delta(theta*) evaluated on ALL rows of the dataset (very accurate).

Compare: paper CI (percentile of |Delta_hat(theta_bar^b_T)|) vs joint bootstrap
         (training deviation + evaluation resampling deviation).

Run:
  python code/exps/real_joint_ci.py --dataset adult
  python code/exps/real_joint_ci.py --dataset acsincome
  python code/exps/real_joint_ci.py --dataset compas
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

from core.fairuq import add_intercept, di_constraint_direction, train_di, train_dm  # noqa: E402
from core.optimum import theta_star_di, theta_star_dm  # noqa: E402

ROOT = CODE_DIR.parent
DATA = ROOT / "data" / "processed"
TAB = ROOT / "results" / "tables"

CFG = {
    "adult":     dict(kind="di", eps=1e-5, n_dprime=1000, m=1000, n_reservoir=8000, kappa=0.1),
    "acsincome": dict(kind="di", eps=0.01, n_dprime=1000, m=1000, n_reservoir=8000, kappa=0.1),
    "compas":    dict(kind="dm", R2=300.0, n_dprime=250, m=400, n_reservoir=1200, kappa=0.1),
}


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=list(CFG), required=True)
    ap.add_argument("--reps", type=int, default=60)
    ap.add_argument("--T", type=int, default=30000)
    ap.add_argument("--B", type=int, default=100)
    ap.add_argument("--R", type=int, default=300)
    ap.add_argument("--eta0", type=float, default=0.1)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=20261026)
    args = ap.parse_args()
    cfg = CFG[args.dataset]
    kind = cfg["kind"]
    t0 = time.time()

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
    Phi_pool, y_pool = Phi[i_pool], y[i_pool]
    Phi_res, z_res, y_res = Phi[i_res], z[i_res], y[i_res]

    if kind == "di":
        xt = di_constraint_direction(Phi[i_dp], z[i_dp])
        th_star, res = theta_star_di(Phi_pool, y_pool, xt, cfg["eps"], cfg["kappa"])
    else:
        w_all = z[i_dp].astype(np.float64) - float(z[i_dp].mean())
        sel = (y[i_dp] == -1)
        Phi_m, y_m, w_m = Phi[i_dp][sel], y[i_dp][sel].astype(np.float64), w_all[sel]
        th_star, res = theta_star_dm(Phi_pool, y_pool, cfg["R2"], Phi_m, y_m, w_m, cfg["kappa"])

    # population target; for the 1.66M-row dataset evaluate on a 200k subsample
    if len(y) > 200000:
        idx_all = np.random.default_rng(args.seed + 5).choice(len(y), size=200000, replace=False)
    else:
        idx_all = np.arange(len(y))
    d_pop = float(delta_hat(th_star, Phi[idx_all], z[idx_all], y[idx_all], kind)[0])
    phi_pop = abs(d_pop)
    d_res = float(delta_hat(th_star, Phi_res, z_res, y_res, kind)[0])
    print(f"[{args.dataset}] kind={kind} pool={len(y_pool)} reservoir={len(i_res)} "
          f"|D'|={cfg['n_dprime']} m={cfg['m']} T={args.T} B={args.B}")
    print(f"[theta*] ||th||={np.linalg.norm(th_star):.3f} success={res.success} "
          f"Delta(pop)={d_pop:.5f} |Delta(reservoir)|={abs(d_res):.5f} phi_pop={phi_pop:.5f}")

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
        d_main = float(delta_hat(avg[0:1], Phi_e, z_e, y_e, kind)[0])
        d_boot = delta_hat(avg[1:], Phi_e, z_e, y_e, kind)
        train_dev = d_boot - d_main
        sigma2 = args.T * float(np.var(d_boot, ddof=1))

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
        R = args.R
        e0 = pred[idx0][rng2.integers(0, n0, size=(R, n0))].mean(axis=1) - p0
        e1 = pred[idx1][rng2.integers(0, n1, size=(R, n1))].mean(axis=1) - p1
        eval_dev = e0 - e1

        lo_b, hi_b = np.quantile(np.abs(d_boot), [args.alpha / 2, 1 - args.alpha / 2])
        comb = train_dev[rng2.integers(0, args.B, size=4000)] + eval_dev[rng2.integers(0, R, size=4000)]
        ql, qh = np.quantile(comb, [args.alpha / 2, 1 - args.alpha / 2])
        lo_j, hi_j = fold(d_main + ql, d_main + qh)
        rows.append({"rep": rep, "d_main": d_main,
                     "cov_paper": float(lo_b <= phi_pop <= hi_b),
                     "cov_joint": float(lo_j <= phi_pop <= hi_j),
                     "w_paper": hi_b - lo_b, "w_joint": hi_j - lo_j,
                     "se_train": np.sqrt(sigma2 / args.T), "se_eval": np.sqrt(v2)})

    df = pd.DataFrame(rows)
    out = {"dataset": args.dataset, "kind": kind,
           "protocol": "A (fresh evaluation set per repetition)",
           "config": {**cfg, "reps": args.reps, "T": args.T, "B": args.B, "R": args.R,
                      "eta0": args.eta0},
           "phi_pop": round(phi_pop, 5), "delta_pop": round(d_pop, 5),
           "theta_star_norm": round(float(np.linalg.norm(th_star)), 3),
           "coverage_paper": round(float(df.cov_paper.mean()), 3),
           "coverage_joint": round(float(df.cov_joint.mean()), 3),
           "width_paper": round(float(df.w_paper.mean()), 5),
           "width_joint": round(float(df.w_joint.mean()), 5),
           "width_ratio": round(float((df.w_joint / df.w_paper).mean()), 3),
           "se_train_mean": round(float(df.se_train.mean()), 5),
           "se_eval_mean": round(float(df.se_eval.mean()), 5),
           "elapsed_sec": round(time.time() - t0, 1)}
    TAB.mkdir(parents=True, exist_ok=True)
    df.to_csv(TAB / f"real_joint_ci_{args.dataset}_per_rep.csv", index=False)
    with open(TAB / f"real_joint_ci_{args.dataset}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"saved -> {TAB / f'real_joint_ci_{args.dataset}.json'}")


if __name__ == "__main__":
    main()
