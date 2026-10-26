"""Prototype of the extension: combined CI that accounts for training + evaluation noise.

For each repetition:
  1. run the paper's online multiplier bootstrap -> B perturbed trajectories (training noise);
  2. estimate sigma^2_train = T * Var_b(Delta_hat^b)      (asymptotic training variance);
  3. estimate eval variance v^2 = p0(1-p0)/n0 + p1(1-p1)/n1  (delta method on the held-out set);
  4. combined CI for the SIGNED gap Delta: Delta_hat +/- z * sqrt(sigma^2_train/T + v^2);
  5. fold to phi = |Delta| and compare coverage with the paper's percentile CI.

Targets: population phi(theta*) evaluated on a large independent DGP sample, and the held-out
estimand phi_hat(theta*) on the same D~ (to reproduce the paper's own coverage claim).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from core.dgp import dgp_di  # noqa: E402
from core.fairuq import (add_intercept, di_constraint_direction, make_splits,  # noqa: E402
                         train_di)
from core.optimum import theta_star_di  # noqa: E402

ROOT = CODE_DIR.parent
TAB = ROOT / "results" / "tables"


def delta_hat(Theta, Phi_eval, z_eval):
    """Signed DI gap p0 - p1 for each row of Theta."""
    Theta = np.atleast_2d(Theta)
    pred = (Theta @ Phi_eval.T) > 0.0
    m0 = z_eval == 0
    m1 = z_eval == 1
    return pred[:, m0].mean(axis=1) - pred[:, m1].mean(axis=1)


def fold_interval(lo, hi):
    """Map a CI for signed Delta onto a CI for |Delta|."""
    if lo > 0:
        return lo, hi
    if hi < 0:
        return -hi, -lo
    return 0.0, max(-lo, hi)


def paper_interval(delta_boot, alpha):
    s = np.abs(delta_boot)
    return float(np.quantile(s, alpha / 2)), float(np.quantile(s, 1 - alpha / 2))


def run_case(m_tilde, reps, T, B, seed, alpha=0.05, kappa=1e-4, eps=0.002):
    rng = np.random.default_rng(seed)
    n_pool, n_dp = 20000, 200
    X, y, z = dgp_di(n_pool + n_dp + m_tilde, seed=seed)
    i_dp, i_tl, i_pool = make_splits(len(y), n_dp, m_tilde, np.random.default_rng(seed + 1))
    Phi = add_intercept(X)
    Phi_pool, y_pool = Phi[i_pool], y[i_pool]
    Phi_tl, z_tl = Phi[i_tl], z[i_tl]
    xt = di_constraint_direction(Phi[i_dp], z[i_dp])

    th_star, _ = theta_star_di(Phi_pool, y_pool, xt, eps, kappa)
    Xt, yt, zt = dgp_di(2000000, seed=seed + 3)
    Phi_true = add_intercept(Xt)
    d_pop = float(delta_hat(th_star, Phi_true, zt)[0])
    phi_pop = abs(d_pop)
    phi_hold = abs(float(delta_hat(th_star, Phi_tl, z_tl)[0]))

    zt_ = 1.959963984540054
    rows = []
    for rep in range(reps):
        avg, _ = train_di(Phi_pool, y_pool, xt, eps, T=T, B=B, kappa=kappa,
                          eta0=0.1, eta_a=0.501, rng=np.random.default_rng(seed + 1000 + rep))
        d_main = float(delta_hat(avg[0:1], Phi_tl, z_tl)[0])
        d_boot = delta_hat(avg[1:], Phi_tl, z_tl)
        sigma2 = T * float(np.var(d_boot, ddof=1))

        pred = (avg[0] @ Phi_tl.T) > 0
        p0 = float(pred[z_tl == 0].mean())
        p1 = float(pred[z_tl == 1].mean())
        n0, n1 = int((z_tl == 0).sum()), int((z_tl == 1).sum())
        v2 = p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1

        se_paper = np.sqrt(sigma2 / T)
        lo_p, hi_p = d_main - zt_ * se_paper, d_main + zt_ * se_paper
        lo_p, hi_p = fold_interval(lo_p, hi_p)

        se_comb = np.sqrt(sigma2 / T + v2)
        lo_c, hi_c = fold_interval(d_main - zt_ * se_comb, d_main + zt_ * se_comb)

        lo_b, hi_b = paper_interval(d_boot, alpha)  # the paper's own percentile interval

        rows.append({"rep": rep,
                     "cov_paper_pop": float(lo_b <= phi_pop <= hi_b),
                     "cov_paper_hold": float(lo_b <= phi_hold <= hi_b),
                     "cov_comb_pop": float(lo_c <= phi_pop <= hi_c),
                     "cov_comb_hold": float(lo_c <= phi_hold <= hi_c),
                     "width_paper": hi_b - lo_b, "width_comb": hi_c - lo_c,
                     "se_train": se_paper, "se_eval": np.sqrt(v2), "abs_bias": abs(d_main - d_pop)})
    import pandas as pd
    df = pd.DataFrame(rows)
    return {
        "m_tilde": m_tilde, "reps": reps, "T": T, "B": B,
        "phi_pop": phi_pop, "phi_hold": phi_hold,
        "cov_paper_pop": round(float(df.cov_paper_pop.mean()), 3),
        "cov_paper_hold": round(float(df.cov_paper_hold.mean()), 3),
        "cov_comb_pop": round(float(df.cov_comb_pop.mean()), 3),
        "cov_comb_hold": round(float(df.cov_comb_hold.mean()), 3),
        "width_paper": round(float(df.width_paper.mean()), 5),
        "width_comb": round(float(df.width_comb.mean()), 5),
        "se_train_mean": round(float(df.se_train.mean()), 5),
        "se_eval_mean": round(float(df.se_eval.mean()), 5),
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--T", type=int, default=20000)
    ap.add_argument("--B", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--out", type=str, default="combined_ci_synth_di.json")
    args = ap.parse_args()

    TAB.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    results = []
    for m_tilde in (100, 1000):
        res = run_case(m_tilde, args.reps, args.T, args.B, args.seed)
        results.append(res)
        print(json.dumps(res, ensure_ascii=False))
    payload = {"config": vars(args), "results": results, "elapsed_sec": round(time.time() - t0, 1)}
    with open(TAB / args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("\n=== combined vs paper CI ===")
    for r in results:
        print(f"m={r['m_tilde']:5d} | coverage pop: paper {r['cov_paper_pop']:.2f} -> combined {r['cov_comb_pop']:.2f}"
              f" | coverage hold: paper {r['cov_paper_hold']:.2f} -> combined {r['cov_comb_hold']:.2f}"
              f" | width paper {r['width_paper']:.4f} vs comb {r['width_comb']:.4f}"
              f" | se_train {r['se_train_mean']:.4f} se_eval {r['se_eval_mean']:.4f}")
    print(f"elapsed {payload['elapsed_sec']}s -> {TAB / args.out}")


if __name__ == "__main__":
    main()
