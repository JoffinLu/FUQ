"""Reproduction experiments on real data: Adult / ACSIncome (DI) and COMPAS (DM).

Paper Table 1:
  Adult     : eps=1e-5,  B=200, |D~|=1000, |D'|=1000, 200 reps
  ACSIncome : eps=0.01,  B=100, |D~|=1000, |D'|=1000, 200 reps
  COMPAS    : R^2=300,   B=200, |D~|=400,  |D'|=250,  200 reps

Protocol: one fixed split (D', D~); repetitions resample only the training stream.
theta* is obtained by direct optimisation on the training pool; two targets are reported:
  * held-out estimand  phi_hat(theta*) on D~   (what the paper's bootstrap actually covers)
  * population estimand phi(theta*) on the full training pool (n ~ 28k / 1.66M / 4.6k)
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

from core.fairuq import (add_intercept, di_constraint_direction, make_splits,  # noqa: E402
                         mis, phi_hat, train_di, train_dm, w2_empirical_vs_normal)
from core.optimum import theta_star_di, theta_star_dm  # noqa: E402

ROOT = CODE_DIR.parent
DATA = ROOT / "data" / "processed"
RAW = ROOT / "results" / "raw"
TAB = ROOT / "results" / "tables"

PAPER = {
    "adult":     dict(kind="di", eps=1e-5, B=200, n_tilde=1000, n_dprime=1000, reps=200),
    "acsincome": dict(kind="di", eps=0.01, B=100, n_tilde=1000, n_dprime=1000, reps=200),
    "compas":    dict(kind="dm", R2=300.0, B=200, n_tilde=400, n_dprime=250, reps=200),
}


def load_split(name, n_dprime, n_tilde, seed=20261026):
    d = np.load(DATA / f"{name}.npz")
    X = d["X"].astype(np.float64)
    y = d["y"].astype(np.int64)
    z = d["z"].astype(np.int64)
    rng = np.random.default_rng(seed)
    i_dp, i_tl, i_pool = make_splits(len(y), n_dprime, n_tilde, rng)
    mu = X[i_pool].mean(axis=0)
    sd = X[i_pool].std(axis=0)
    sd[sd < 1e-12] = 1.0
    Phi = add_intercept((X - mu) / sd)
    return Phi, y, z, i_dp, i_tl, i_pool


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=list(PAPER), required=True)
    ap.add_argument("--reps", type=int, default=None)
    ap.add_argument("--T", type=int, default=20000)
    ap.add_argument("--B", type=int, default=None)
    ap.add_argument("--kappa", type=float, default=1e-4)
    ap.add_argument("--eta0", type=float, default=0.1)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--tag", type=str, default="paper")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    cfg = PAPER[args.dataset]
    kind = cfg["kind"]
    reps = args.reps if args.reps is not None else cfg["reps"]
    B = args.B if args.B is not None else cfg["B"]
    T = args.T
    if args.smoke:
        reps, B, T = min(reps, 3), min(B, 20), min(T, 2000)
        args.tag = "smoke"

    RAW.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    Phi, y, z, i_dp, i_tl, i_pool = load_split(args.dataset, cfg["n_dprime"], cfg["n_tilde"], args.seed)
    Phi_pool, y_pool, z_pool = Phi[i_pool], y[i_pool], z[i_pool]
    Phi_tl, y_tl, z_tl = Phi[i_tl], y[i_tl], z[i_tl]
    print(f"[{args.dataset}] kind={kind} n={len(y)} d={Phi.shape[1]} pool={len(y_pool)} "
          f"|D'|={cfg['n_dprime']} |D~|={cfg['n_tilde']} T={T} B={B} reps={reps}")

    # ---------------- theta* and the two estimands ----------------
    if kind == "di":
        xt = di_constraint_direction(Phi[i_dp], z[i_dp])
        th_star, res = theta_star_di(Phi_pool, y_pool, xt, cfg["eps"], args.kappa)
        print(f"  theta*: success={res.success} ||th*||={np.linalg.norm(th_star):.4f} "
              f"|xt^T th*|={abs(xt @ th_star):.3e} pool_acc={float((((Phi_pool @ th_star) > 0) == (y_pool > 0)).mean()):.4f}")
        phi_hold = float(phi_hat(th_star, Phi_tl, z_tl, kind="di")[0])
        phi_pop = float(phi_hat(th_star, Phi_pool, z_pool, kind="di")[0])
    else:
        w_all = z[i_dp].astype(np.float64) - float(z[i_dp].mean())
        sel = (y[i_dp] == -1)
        Phi_m, y_m, w_m = Phi[i_dp][sel], y[i_dp][sel].astype(np.float64), w_all[sel]
        th_star, res = theta_star_dm(Phi_pool, y_pool, cfg["R2"], Phi_m, y_m, w_m, args.kappa)
        print(f"  theta*: success={res.success} ||th*||={np.linalg.norm(th_star):.4f} "
              f"pool_acc={float((((Phi_pool @ th_star) > 0) == (y_pool > 0)).mean()):.4f}")
        phi_hold = float(phi_hat(th_star, Phi_tl, z_tl, y_tl, kind="dm")[0])
        phi_pop = float(phi_hat(th_star, Phi_pool, z_pool, y_pool, kind="dm")[0])
    print(f"  phi*(held-out D~)={phi_hold:.5f}   phi*(pool)={phi_pop:.5f}")

    ks = np.unique(np.round(np.logspace(0, np.log10(T), 40)).astype(int))
    snapshots = set(int(k) for k in ks)

    rows = []
    per_rep = {int(k): [] for k in ks}
    for rep in range(reps):
        rng = np.random.default_rng(args.seed + 1000 + rep)
        if kind == "di":
            avg, snaps = train_di(Phi_pool, y_pool, xt, cfg["eps"], T=T, B=B, kappa=args.kappa,
                                  eta0=args.eta0, eta_a=0.501, rng=rng, snapshot_ks=snapshots)
        else:
            avg, snaps = train_dm(Phi_pool, y_pool, cfg["R2"], Phi_m, y_m, w_m, T=T, B=B,
                                  kappa=args.kappa, eta0=args.eta0, eta_a=0.501, rng=rng,
                                  snapshot_ks=snapshots)
        for k in ks:
            k = int(k)
            if kind == "di":
                phis = phi_hat(snaps[k], Phi_tl, z_tl, kind="di")
            else:
                phis = phi_hat(snaps[k], Phi_tl, z_tl, y_tl, kind="dm")
            lo, hi = np.quantile(phis[1:], [args.alpha / 2, 1 - args.alpha / 2])
            per_rep[k].append(float(phis[0]))
            rows.append({"rep": rep, "k": k, "phi_main": float(phis[0]),
                         "ci_lo": float(lo), "ci_hi": float(hi)})

    df = pd.DataFrame(rows)
    out_csv = RAW / f"real_{args.dataset}_per_rep_{args.tag}.csv"
    df.to_csv(out_csv, index=False)

    summary = []
    for k in ks:
        k = int(k)
        sub = df[df["k"] == k]
        phis = np.array(per_rep[k])
        cov_hold = float(np.mean((sub["ci_lo"].values <= phi_hold) & (phi_hold <= sub["ci_hi"].values)))
        cov_pop = float(np.mean((sub["ci_lo"].values <= phi_pop) & (phi_pop <= sub["ci_hi"].values)))
        mis_vals = [mis(phis, lo, hi, args.alpha) for lo, hi in zip(sub["ci_lo"], sub["ci_hi"])]
        sigma2 = T * float(np.var(phis, ddof=1))
        w2 = w2_empirical_vs_normal(phis, phi_pop, np.sqrt(max(sigma2 / k, 1e-12)))
        summary.append({"k": k, "phi_mean": float(phis.mean()), "phi_sd": float(phis.std(ddof=1)),
                        "ci_width_mean": float((sub["ci_hi"] - sub["ci_lo"]).mean()),
                        "coverage_hold": cov_hold, "coverage_pop": cov_pop,
                        "mis": float(np.mean(mis_vals)), "w2_to_normal": w2})
    summ = pd.DataFrame(summary)
    summ.to_csv(TAB / f"real_{args.dataset}_summary_{args.tag}.csv", index=False)

    meta = {"dataset": args.dataset, "kind": kind, "cfg": cfg, "args": vars(args),
            "phi_hold": phi_hold, "phi_pop": phi_pop,
            "theta_star": th_star.tolist(), "optimizer_success": bool(res.success),
            "coverage_hold_T": float(summ.iloc[-1]["coverage_hold"]),
            "coverage_pop_T": float(summ.iloc[-1]["coverage_pop"]),
            "ci_width_T": float(summ.iloc[-1]["ci_width_mean"]),
            "mis_T": float(summ.iloc[-1]["mis"]),
            "w2_T": float(summ.iloc[-1]["w2_to_normal"]),
            "elapsed_sec": time.time() - t0}
    with open(TAB / f"real_{args.dataset}_meta_{args.tag}.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print("\n=== head/tail ===")
    print(summ.head(2).to_string(index=False))
    print(summ.tail(2).to_string(index=False))
    print(f"\ncoverage@T  held-out={meta['coverage_hold_T']:.2f}  population={meta['coverage_pop_T']:.2f} "
          f"| width={meta['ci_width_T']:.4f} | MIS={meta['mis_T']:.4f} | W2={meta['w2_T']:.4f}")
    print(f"elapsed {meta['elapsed_sec']:.1f}s -> {out_csv}")


if __name__ == "__main__":
    main()
