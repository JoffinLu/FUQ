"""v3: coverage under PROTOCOL A (a fresh evaluation set in every repetition).

Why this matters
----------------
In the paper's own simulation protocol the held-out set D~ is FIXED across repetitions, so the
evaluation error acts as a constant bias rather than random noise.  Under that protocol any
sufficiently wide interval covers trivially, and the paper's narrow interval fails because its
width cannot absorb the bias.  A fair assessment of an interval's frequentist validity must
average over the evaluation sampling as well: draw a FRESH D~ per repetition.

Protocol A: theta* and phi(theta*) are fixed (they depend only on D'); every repetition draws
  - a fresh training stream (training noise),
  - a fresh evaluation set D~_r of size m (evaluation noise).
Then report coverage of phi(theta*) and the widths of
  * paper CI       : percentile of |Delta_hat(theta_bar^b)|
  * joint bootstrap: Delta_hat + quantiles of [training deviation + evaluation resampling deviation]
  * oracle-ish     : +/- z sqrt(sigma^2/T + v^2) with sigma estimated from across-rep spread
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

from core.dgp import dgp_di  # noqa: E402
from core.fairuq import add_intercept, di_constraint_direction, make_splits, train_di  # noqa: E402
from core.optimum import theta_star_di  # noqa: E402

ROOT = CODE_DIR.parent
TAB = ROOT / "results" / "tables"
ZT = 1.959963984540054


def delta_hat(Theta, Phi_eval, z_eval):
    Th = np.atleast_2d(Theta)
    pred = (Th @ Phi_eval.T) > 0.0
    return pred[:, z_eval == 0].mean(axis=1) - pred[:, z_eval == 1].mean(axis=1)


def fold(lo, hi):
    if lo > 0:
        return lo, hi
    if hi < 0:
        return -hi, -lo
    return 0.0, max(-lo, hi)


def run_case(m_tilde, reps, T, B, fresh_eval, seed, alpha=0.05, kappa=1e-4, eps=0.002, R=400):
    # FIXED constraint set D' across all m values so that theta* and phi(theta*) do not change;
    # the evaluation set is drawn fresh from the DGP in every repetition (protocol A).
    n_pool, n_dp = 20000, 200
    X, y, z = dgp_di(n_pool + n_dp, seed=seed)
    perm = np.random.default_rng(seed + 1).permutation(len(y))
    i_dp, i_pool = perm[:n_dp], perm[n_dp:]
    Phi = add_intercept(X)
    Phi_pool, y_pool = Phi[i_pool], y[i_pool]
    xt = di_constraint_direction(Phi[i_dp], z[i_dp])
    th_star, _ = theta_star_di(Phi_pool, y_pool, xt, eps, kappa)

    Xt, _, zt = dgp_di(2000000, seed=seed + 3)
    phi_pop = abs(float(delta_hat(th_star, add_intercept(Xt), zt)[0]))

    rng = np.random.default_rng(seed + 99)
    rows, d_mains = [], []
    for rep in range(reps):
        avg, _ = train_di(Phi_pool, y_pool, xt, eps, T=T, B=B, kappa=kappa,
                          eta0=0.1, eta_a=0.501,
                          rng=np.random.default_rng(seed + 1000 + rep))
        if fresh_eval:
            Xe, _, ze = dgp_di(m_tilde, seed=seed + 500000 + rep)
            Phi_e = add_intercept(Xe)
        else:
            Phi_e, ze = Phi_tl, z_tl

        d_main = float(delta_hat(avg[0:1], Phi_e, ze)[0])
        d_boot = delta_hat(avg[1:], Phi_e, ze)
        d_mains.append(d_main)
        train_dev = d_boot - d_main
        sigma2 = T * float(np.var(d_boot, ddof=1))

        pred = (avg[0] @ Phi_e.T) > 0
        idx0, idx1 = np.where(ze == 0)[0], np.where(ze == 1)[0]
        n0, n1 = len(idx0), len(idx1)
        p0, p1 = float(pred[idx0].mean()), float(pred[idx1].mean())
        v2 = p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1
        e0 = pred[idx0][rng.integers(0, n0, size=(R, n0))].mean(axis=1) - p0
        e1 = pred[idx1][rng.integers(0, n1, size=(R, n1))].mean(axis=1) - p1
        eval_dev = e0 - e1

        lo_b, hi_b = np.quantile(np.abs(d_boot), [alpha / 2, 1 - alpha / 2])
        comb = (train_dev[rng.integers(0, B, size=4000)]
                + eval_dev[rng.integers(0, R, size=4000)])
        ql, qh = np.quantile(comb, [alpha / 2, 1 - alpha / 2])
        lo_j, hi_j = fold(d_main + ql, d_main + qh)
        se_o = np.sqrt(sigma2 / T + v2)
        lo_o, hi_o = fold(d_main - ZT * se_o, d_main + ZT * se_o)
        lo_a, hi_a = fold(d_main - ZT * np.sqrt(sigma2 / T + v2), d_main + ZT * np.sqrt(sigma2 / T + v2))

        rows.append({"rep": rep, "d_main": d_main,
                     "cov_paper_pop": float(lo_b <= phi_pop <= hi_b),
                     "cov_jb_pop": float(lo_j <= phi_pop <= hi_j),
                     "cov_ana_pop": float(lo_a <= phi_pop <= hi_a),
                     "w_paper": hi_b - lo_b, "w_jb": hi_j - lo_j, "w_ana": hi_a - lo_a,
                     "se_train": np.sqrt(sigma2 / T), "se_eval": np.sqrt(v2)})
    df = pd.DataFrame(rows)
    return {"m_tilde": m_tilde, "fresh_eval": bool(fresh_eval), "reps": reps, "T": T, "B": B,
            "phi_pop": round(phi_pop, 5),
            "sigma2_train_across_reps": round(T * float(np.var(df.d_main, ddof=1)), 4),
            "cov_paper": round(float(df.cov_paper_pop.mean()), 3),
            "cov_jb": round(float(df.cov_jb_pop.mean()), 3),
            "cov_ana": round(float(df.cov_ana_pop.mean()), 3),
            "width_paper": round(float(df.w_paper.mean()), 5),
            "width_jb": round(float(df.w_jb.mean()), 5),
            "width_ana": round(float(df.w_ana.mean()), 5),
            "se_train": round(float(df.se_train.mean()), 5),
            "se_eval": round(float(df.se_eval.mean()), 5)}, df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--T", type=int, default=20000)
    ap.add_argument("--B", type=int, default=100)
    ap.add_argument("--R", type=int, default=400)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--out", type=str, default="joint_bootstrap_v3_fresh_eval.json")
    args = ap.parse_args()
    TAB.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    results = []
    for m_tilde in (100, 1000, 5000):
        res, df = run_case(m_tilde, args.reps, args.T, args.B, True, args.seed, R=args.R)
        df.to_csv(TAB / f"joint_bootstrap_v3_m{m_tilde}.csv", index=False)
        results.append(res)
        print(json.dumps(res, ensure_ascii=False))
    payload = {"config": vars(args), "protocol": "fresh evaluation set per repetition",
               "results": results, "elapsed_sec": round(time.time() - t0, 1)}
    with open(TAB / args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("\n=== Protocol A: coverage of population phi(theta*) (nominal 0.95) ===")
    print(f"{'m':>6} {'paper':>7} {'joint':>7} {'analytic':>9} | widths paper/joint/analytic | se_train/se_eval")
    for r in results:
        print(f"{r['m_tilde']:>6} {r['cov_paper']:>7.2f} {r['cov_jb']:>7.2f} {r['cov_ana']:>9.2f} | "
              f"{r['width_paper']:.4f}/{r['width_jb']:.4f}/{r['width_ana']:.4f} | "
              f"{r['se_train']:.4f}/{r['se_eval']:.4f}")
    print(f"elapsed {payload['elapsed_sec']}s -> {TAB / args.out}")


if __name__ == "__main__":
    main()
