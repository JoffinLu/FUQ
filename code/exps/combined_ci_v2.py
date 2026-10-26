"""Extension method v2: joint bootstrap CI for POPULATION fairness.

Errors of the reported gap:
    Delta_hat_m(theta_bar_T) - Delta(theta*)  =  [Delta(theta_bar_T)-Delta(theta*)]
                                              +  [Delta_hat_m(theta_bar_T)-Delta(theta_bar_T)]
The first term is the training noise (paper's online multiplier bootstrap); the second is the
evaluation noise (resampling of the held-out set).  They are independent by construction.

Joint bootstrap:
    D*_{b,r} = [Delta_hat_m(theta_bar^b) - Delta_hat_m(theta_bar_T)]   (training)
             + [Delta_hat_{m,r}(theta_bar_T) - Delta_hat_m(theta_bar_T)] (evaluation resample)
    CI for Delta: Delta_hat_m + quantiles(D*), then fold |.| -> interval for phi.

Compared here (100 repetitions, synthetic DI):
  * paper      : percentile interval of {|Delta_hat(theta_bar^b)|}
  * analytic   : Delta_hat +/- z sqrt(sigma_train^2/T + v_eval^2), folded
  * joint-boot : Delta_hat + quantiles(D*) (this method)
  * oracle     : z-quantiles with the true (large-repetition) sigma and analytic v
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
    Theta = np.atleast_2d(Theta)
    pred = (Theta @ Phi_eval.T) > 0.0
    return pred[:, z_eval == 0].mean(axis=1) - pred[:, z_eval == 1].mean(axis=1)


def fold(lo, hi):
    if lo > 0:
        return lo, hi
    if hi < 0:
        return -hi, -lo
    return 0.0, max(-lo, hi)


def run_case(m_tilde, reps, T, B, seed, alpha=0.05, kappa=1e-4, eps=0.002, R=400):
    n_pool, n_dp = 20000, 200
    X, y, z = dgp_di(n_pool + n_dp + m_tilde, seed=seed)
    i_dp, i_tl, i_pool = make_splits(len(y), n_dp, m_tilde, np.random.default_rng(seed + 1))
    Phi = add_intercept(X)
    Phi_pool, y_pool = Phi[i_pool], y[i_pool]
    Phi_tl, z_tl = Phi[i_tl], z[i_tl]
    xt = di_constraint_direction(Phi[i_dp], z[i_dp])

    th_star, _ = theta_star_di(Phi_pool, y_pool, xt, eps, kappa)
    Xt, _, zt = dgp_di(2000000, seed=seed + 3)
    Phi_true = add_intercept(Xt)
    d_pop = float(delta_hat(th_star, Phi_true, zt)[0])
    phi_pop = abs(d_pop)
    phi_hold = abs(float(delta_hat(th_star, Phi_tl, z_tl)[0]))

    # analytic evaluation variance at theta*
    pred_star = (th_star @ Phi_tl.T) > 0
    p0s, p1s = pred_star[z_tl == 0].mean(), pred_star[z_tl == 1].mean()
    n0, n1 = (z_tl == 0).sum(), (z_tl == 1).sum()
    v2_star = p0s * (1 - p0s) / n0 + p1s * (1 - p1s) / n1

    idx0 = np.where(z_tl == 0)[0]
    idx1 = np.where(z_tl == 1)[0]
    rng = np.random.default_rng(seed + 99)

    rows = []
    d_mains = []
    for rep in range(reps):
        avg, _ = train_di(Phi_pool, y_pool, xt, eps, T=T, B=B, kappa=kappa,
                          eta0=0.1, eta_a=0.501, rng=np.random.default_rng(seed + 1000 + rep))
        d_main = float(delta_hat(avg[0:1], Phi_tl, z_tl)[0])
        d_boot = delta_hat(avg[1:], Phi_tl, z_tl)
        d_mains.append(d_main)
        train_dev = d_boot - d_main
        sigma2 = T * float(np.var(d_boot, ddof=1))

        # evaluation resampling at theta_bar_T (same predictions as d_main)
        pred = (avg[0] @ Phi_tl.T) > 0
        p0, p1 = float(pred[idx0].mean()), float(pred[idx1].mean())
        v2 = p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1
        e0 = pred[idx0][rng.integers(0, n0, size=(R, n0))].mean(axis=1) - p0
        e1 = pred[idx1][rng.integers(0, n1, size=(R, n1))].mean(axis=1) - p1
        eval_dev = e0 - e1

        # paper: percentile of |Delta_boot|
        lo_b, hi_b = np.quantile(np.abs(d_boot), [alpha / 2, 1 - alpha / 2])
        # analytic combined, folded
        se_c = np.sqrt(sigma2 / T + v2)
        lo_a, hi_a = fold(d_main - ZT * se_c, d_main + ZT * se_c)
        # joint bootstrap, folded
        comb = (train_dev[rng.integers(0, B, size=4000)]
                + eval_dev[rng.integers(0, R, size=4000)])
        ql, qh = np.quantile(comb, [alpha / 2, 1 - alpha / 2])
        lo_j, hi_j = fold(d_main + ql, d_main + qh)
        # oracle (true sigma from across-rep spread is not available per-rep; use analytic v only)
        se_o = np.sqrt(sigma2 / T + v2_star)
        lo_o, hi_o = fold(d_main - ZT * se_o, d_main + ZT * se_o)

        rows.append({
            "rep": rep, "d_main": d_main,
            "cov_paper_pop": float(lo_b <= phi_pop <= hi_b), "cov_paper_hold": float(lo_b <= phi_hold <= hi_b),
            "cov_ana_pop": float(lo_a <= phi_pop <= hi_a), "cov_ana_hold": float(lo_a <= phi_hold <= hi_a),
            "cov_jb_pop": float(lo_j <= phi_pop <= hi_j), "cov_jb_hold": float(lo_j <= phi_hold <= hi_j),
            "cov_oracle_pop": float(lo_o <= phi_pop <= hi_o),
            "w_paper": hi_b - lo_b, "w_ana": hi_a - lo_a, "w_jb": hi_j - lo_j, "w_oracle": hi_o - lo_o,
            "se_train": np.sqrt(sigma2 / T), "se_eval": np.sqrt(v2), "se_eval_star": np.sqrt(v2_star),
        })
    df = pd.DataFrame(rows)
    sigma2_true = T * float(np.var(df.d_main.values, ddof=1))
    out = {"m_tilde": m_tilde, "reps": reps, "T": T, "B": B,
           "phi_pop": round(phi_pop, 5), "phi_hold": round(phi_hold, 5),
           "sigma2_train": round(sigma2_true, 5),
           "v2_eval_at_star": round(float(v2_star), 6),
           "cov_paper_pop": round(float(df.cov_paper_pop.mean()), 3),
           "cov_paper_hold": round(float(df.cov_paper_hold.mean()), 3),
           "cov_ana_pop": round(float(df.cov_ana_pop.mean()), 3),
           "cov_jb_pop": round(float(df.cov_jb_pop.mean()), 3),
           "cov_jb_hold": round(float(df.cov_jb_hold.mean()), 3),
           "cov_oracle_pop": round(float(df.cov_oracle_pop.mean()), 3),
           "width_paper": round(float(df.w_paper.mean()), 5),
           "width_ana": round(float(df.w_ana.mean()), 5),
           "width_jb": round(float(df.w_jb.mean()), 5),
           "width_oracle": round(float(df.w_oracle.mean()), 5),
           "se_train_mean": round(float(df.se_train.mean()), 5),
           "se_eval_mean": round(float(df.se_eval.mean()), 5)}
    return out, df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--T", type=int, default=20000)
    ap.add_argument("--B", type=int, default=100)
    ap.add_argument("--R", type=int, default=400)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--out", type=str, default="joint_bootstrap_v2.json")
    args = ap.parse_args()
    TAB.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    results = []
    for m_tilde in (100, 1000):
        res, df = run_case(m_tilde, args.reps, args.T, args.B, args.seed, R=args.R)
        df.to_csv(TAB / f"joint_bootstrap_v2_m{m_tilde}.csv", index=False)
        results.append(res)
        print(json.dumps(res, ensure_ascii=False))
    payload = {"config": vars(args), "results": results, "elapsed_sec": round(time.time() - t0, 1)}
    with open(TAB / args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("\n=== coverage for POPULATION fairness (nominal 0.95) ===")
    print(f"{'m':>6} {'paper':>7} {'analytic':>9} {'joint-boot':>11} {'oracle':>7} | widths paper/ana/jb/oracle")
    for r in results:
        print(f"{r['m_tilde']:>6} {r['cov_paper_pop']:>7.2f} {r['cov_ana_pop']:>9.2f} "
              f"{r['cov_jb_pop']:>11.2f} {r['cov_oracle_pop']:>7.2f} | "
              f"{r['width_paper']:.4f}/{r['width_ana']:.4f}/{r['width_jb']:.4f}/{r['width_oracle']:.4f}")
    print(f"elapsed {payload['elapsed_sec']}s -> {TAB / args.out}")


if __name__ == "__main__":
    main()
