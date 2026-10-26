"""Reproduction experiment: synthetic DI data (paper Figures 1, 2 + Table 1 row 1).

Protocol (SPEC.md sections 6, 8):
  * one fixed (D', D~) split; repetitions resample only the training stream;
  * Algorithm 1 (SDA) + Algorithm 2 (online multiplier bootstrap), B perturbed paths;
  * snapshot theta_bar_k over a log grid of k, evaluate phi_hat on D~ for all paths;
  * CI = [q_{alpha/2}, q_{1-alpha/2}] of {phi_hat(theta_bar^b_k)};
  * truth phi(theta*) evaluated on a large independent DGP sample.

Outputs
  results/raw/synth_di_per_rep.csv   long format: rep, k, phi_main, ci_lo, ci_hi
  results/tables/synth_di_summary.csv
  results/tables/synth_di_meta.json
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

from core.dgp import dgp_di                                    # noqa: E402
from core.fairuq import (add_intercept, di_constraint_direction, mis,  # noqa: E402
                         make_splits, phi_hat, slab_projection, train_di,
                         w2_empirical_vs_normal)

ROOT = CODE_DIR.parent
RAW = ROOT / "results" / "raw"
TAB = ROOT / "results" / "tables"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=100)
    p.add_argument("--T", type=int, default=8000)
    p.add_argument("--B", type=int, default=100)
    p.add_argument("--T-star", type=int, default=100000, dest="T_star")
    p.add_argument("--n-pool", type=int, default=20000, dest="n_pool")
    p.add_argument("--n-dprime", type=int, default=200, dest="n_dprime")
    p.add_argument("--n-tilde", type=int, default=100, dest="n_tilde")
    p.add_argument("--n-true", type=int, default=2000000, dest="n_true")
    p.add_argument("--eps", type=float, default=0.002)
    p.add_argument("--kappa", type=float, default=1e-4)
    p.add_argument("--eta0", type=float, default=0.01)
    p.add_argument("--eta-a", type=float, default=0.501, dest="eta_a")
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--seed", type=int, default=20261026)
    p.add_argument("--tag", type=str, default="main")
    p.add_argument("--smoke", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    if args.smoke:
        args.reps = min(args.reps, 3)
        args.T = min(args.T, 400)
        args.B = min(args.B, 20)
        args.T_star = 5000
        args.n_pool = 2000
        args.n_true = 50000
        args.tag = "smoke"

    RAW.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    # ---------------- data: one fixed dataset + fixed split ----------------
    n_total = args.n_pool + args.n_dprime + args.n_tilde
    X, y, z = dgp_di(n_total, seed=args.seed)
    rng_split = np.random.default_rng(args.seed + 1)
    idx_dp, idx_tl, idx_pool = make_splits(len(y), args.n_dprime, args.n_tilde, rng_split)

    Phi = add_intercept(X)
    Phi_pool, y_pool = Phi[idx_pool], y[idx_pool]
    Phi_dp, z_dp = Phi[idx_dp], z[idx_dp]
    Phi_tl, z_tl, y_tl = Phi[idx_tl], z[idx_tl], y[idx_tl]

    xt = di_constraint_direction(Phi_dp, z_dp)
    print(f"[data] n_total={n_total} pool={len(y_pool)} |D'|={len(z_dp)} |D~|={len(z_tl)} "
          f"| ||xt||={np.linalg.norm(xt):.4f}")

    # ---------------- global optimum theta* (long run, unperturbed) ----------------
    rng_star = np.random.default_rng(args.seed + 2)
    avg_star, _ = train_di(Phi_pool, y_pool, xt, args.eps, T=args.T_star, B=0,
                           kappa=args.kappa, eta0=args.eta0, eta_a=args.eta_a,
                           rng=rng_star, snapshot_ks=None)
    theta_star = avg_star[0]
    phi_star_eval = float(phi_hat(theta_star, Phi_tl, z_tl, kind="di")[0])

    # truth on a large independent DGP sample (noise ~ 1/sqrt(n_true))
    Xt, yt, zt = dgp_di(args.n_true, seed=args.seed + 3)
    Phi_true = add_intercept(Xt)
    phi_star_true = float(phi_hat(theta_star, Phi_true, zt, kind="di")[0])
    print(f"[theta*] phi on D~ = {phi_star_eval:.5f} | phi on truth({args.n_true}) = {phi_star_true:.5f}")

    # ---------------- repetition grid ----------------
    ks = np.unique(np.round(np.logspace(0, np.log10(args.T), 40)).astype(int))
    snapshots = set(int(k) for k in ks)

    rows = []
    per_rep_phi = {int(k): [] for k in ks}
    ci_at_T = []
    dist_to_star = []

    for rep in range(args.reps):
        rng = np.random.default_rng(args.seed + 1000 + rep)
        avg, snaps = train_di(Phi_pool, y_pool, xt, args.eps, T=args.T, B=args.B,
                              kappa=args.kappa, eta0=args.eta0, eta_a=args.eta_a,
                              rng=rng, snapshot_ks=snapshots)
        dist_to_star.append(float(np.linalg.norm(avg[0] - theta_star)))
        for k in ks:
            phis = phi_hat(snaps[int(k)], Phi_tl, z_tl, kind="di")   # (B+1,)
            lo, hi = np.quantile(phis[1:], [args.alpha / 2, 1 - args.alpha / 2])
            per_rep_phi[int(k)].append(float(phis[0]))
            rows.append({"rep": rep, "k": int(k), "phi_main": float(phis[0]),
                         "ci_lo": float(lo), "ci_hi": float(hi),
                         "phi_boot_mean": float(phis[1:].mean())})
        ci_at_T.append((rows[-1]["ci_lo"], rows[-1]["ci_hi"]))

    df = pd.DataFrame(rows)
    out_csv = RAW / f"synth_di_per_rep_{args.tag}.csv"
    df.to_csv(out_csv, index=False)

    # ---------------- summary metrics ----------------
    summary = []
    for k in ks:
        k = int(k)
        sub = df[df["k"] == k]
        phis = np.array(per_rep_phi[k])
        covered = float(np.mean((sub["ci_lo"].values <= phi_star_true) &
                                (sub["ci_hi"].values >= phi_star_true)))
        # MIS of each rep's interval against the cross-rep sample of phi values
        mis_vals = [mis(phis, lo, hi, args.alpha)
                    for lo, hi in zip(sub["ci_lo"].values, sub["ci_hi"].values)]
        sigma2 = args.T * float(np.var(phis, ddof=1))     # sigma^2/k model at k=T
        w2 = w2_empirical_vs_normal(phis, phi_star_true, np.sqrt(max(sigma2 / k, 1e-12)))
        summary.append({"k": k, "phi_mean": float(phis.mean()),
                        "phi_sd": float(phis.std(ddof=1)),
                        "ci_width_mean": float((sub["ci_hi"] - sub["ci_lo"]).mean()),
                        "coverage": covered, "mis": float(np.mean(mis_vals)),
                        "w2_to_normal": w2})
    summ = pd.DataFrame(summary)
    summ.to_csv(TAB / f"synth_di_summary_{args.tag}.csv", index=False)

    meta = {
        "args": vars(args),
        "phi_star_true": phi_star_true,
        "phi_star_eval_Dtilde": phi_star_eval,
        "theta_star": theta_star.tolist(),
        "xt_norm": float(np.linalg.norm(xt)),
        "dist_to_star_median": float(np.median(dist_to_star)),
        "coverage_at_T": float(summ.iloc[-1]["coverage"]),
        "mis_at_T": float(summ.iloc[-1]["mis"]),
        "w2_at_T": float(summ.iloc[-1]["w2_to_normal"]),
        "elapsed_sec": time.time() - t0,
    }
    with open(TAB / f"synth_di_meta_{args.tag}.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print("\n=== summary (head/tail) ===")
    print(summ.head(3).to_string(index=False))
    print(summ.tail(3).to_string(index=False))
    print(f"\ncoverage at T: {meta['coverage_at_T']:.3f} | MIS at T: {meta['mis_at_T']:.4f} "
          f"| W2 at T: {meta['w2_at_T']:.4f}")
    print(f"theta_bar_T vs theta*: median ||diff|| = {meta['dist_to_star_median']:.2e}")
    print(f"saved -> {out_csv} , {TAB/f'synth_di_summary_{args.tag}.csv'} , meta json")
    print(f"elapsed: {meta['elapsed_sec']:.1f}s")


if __name__ == "__main__":
    main()
