"""Calibration for real-data experiments: how do accuracy / fairness gap vary with the
paper's hyper-parameters (epsilon for DI, R^2 for DM) under our preprocessing?

Motivation: on the synthetic DGP the paper's epsilon produces a near-degenerate constrained
optimum (accuracy ~0.62). Before running hundreds of repetitions we need to know what the
corresponding regime looks like on Adult / ACSIncome / COMPAS.

Run:  python code/exps/diag_real_calibration.py --dataset adult
      python code/exps/diag_real_calibration.py --dataset compas
      python code/exps/diag_real_calibration.py --dataset acsincome
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from core.fairuq import (add_intercept, di_constraint_direction, dm_penalty_grad,  # noqa: E402
                         make_splits, phi_hat, train_di, train_dm)

ROOT = CODE_DIR.parent
DATA = ROOT / "data" / "processed"


def load(name: str, n_dprime: int, n_tilde: int, seed: int = 20261026):
    d = np.load(DATA / f"{name}.npz")
    X, y, z = d["X"].astype(np.float64), d["y"].astype(np.int64), d["z"].astype(np.int64)
    rng = np.random.default_rng(seed)
    i_dp, i_tl, i_pool = make_splits(len(y), n_dprime, n_tilde, rng)
    # standardise features with pool statistics (no label leakage; needed for conditioning)
    mu = X[i_pool].mean(axis=0)
    sd = X[i_pool].std(axis=0)
    sd[sd < 1e-12] = 1.0
    Xs = (X - mu) / sd
    Phi = add_intercept(Xs)
    return Phi, y, z, i_dp, i_tl, i_pool


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["adult", "compas", "acsincome"], required=True)
    ap.add_argument("--T", type=int, default=100000)
    ap.add_argument("--eta0", type=float, default=0.1)
    ap.add_argument("--kappa", type=float, default=1e-4)
    ap.add_argument("--seed", type=int, default=20261026)
    args = ap.parse_args()

    if args.dataset == "adult":
        n_dp, n_tl, eps_list = 1000, 1000, [1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.0]
    elif args.dataset == "acsincome":
        n_dp, n_tl, eps_list = 1000, 1000, [1e-3, 1e-2, 1e-1, 1.0]
    else:
        n_dp, n_tl, eps_list = 250, 400, []

    Phi, y, z, i_dp, i_tl, i_pool = load(args.dataset, n_dp, n_tl, args.seed)
    Phi_pool, y_pool = Phi[i_pool], y[i_pool]
    Phi_tl, z_tl, y_tl = Phi[i_tl], z[i_tl], y[i_tl]
    print(f"[{args.dataset}] n={len(y)} d={Phi.shape[1]} pool={len(y_pool)} "
          f"|D'|={len(i_dp)} |D~|={len(i_tl)}")

    def acc(theta, Phi_eval=Phi_tl, y_eval=y_tl):
        return float((((Phi_eval @ theta) > 0) == (y_eval > 0)).mean())

    if args.dataset in ("adult", "acsincome"):
        Phi_dp, z_dp = Phi[i_dp], z[i_dp]
        xt = di_constraint_direction(Phi_dp, z_dp)
        print(f"  ||xt||={np.linalg.norm(xt):.4g}")
        for eps in eps_list:
            t0 = time.time()
            avg, _ = train_di(Phi_pool, y_pool, xt, eps, T=args.T, B=0, kappa=args.kappa,
                              eta0=args.eta0, eta_a=0.501,
                              rng=np.random.default_rng(args.seed + 1), snapshot_ks=None)
            th = avg[0]
            print(f"  eps={eps:<8g} |x~^T th|={abs(xt @ th):.3e}  ||th||={np.linalg.norm(th):6.3f}  "
                  f"acc={acc(th):.4f}  DI(eval)={float(phi_hat(th, Phi_tl, z_tl, kind='di')[0]):.4f}  "
                  f"({time.time() - t0:.1f}s)")
    else:
        Phi_dp, z_dp = Phi[i_dp], z[i_dp]
        w_all = z_dp.astype(np.float64) - float(z_dp.mean())
        sel = (y[i_dp] == -1)
        Phi_m = Phi_dp[sel]
        y_m = y[i_dp][sel].astype(np.float64)
        w_m = w_all[sel]
        print(f"  |D'_-|={len(y_m)}")
        for R2 in [0.0, 30.0, 100.0, 300.0, 1000.0, 10000.0]:
            t0 = time.time()
            avg, _ = train_dm(Phi_pool, y_pool, R2, Phi_m, y_m, w_m, T=args.T, B=0,
                              kappa=args.kappa, eta0=args.eta0, eta_a=0.501,
                              rng=np.random.default_rng(args.seed + 1), snapshot_ks=None)
            th = avg[0]
            print(f"  R2={R2:<8g} ||th||={np.linalg.norm(th):6.3f}  acc={acc(th):.4f}  "
                  f"DM(eval)={float(phi_hat(th, Phi_tl, z_tl, y_tl, kind='dm')[0]):.4f}  "
                  f"({time.time() - t0:.1f}s)")


if __name__ == "__main__":
    main()
