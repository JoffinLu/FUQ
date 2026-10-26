"""Reproduction: synthetic DM data (paper Figure 5, Table 1 row 'Synthetic (DM)').

DGP: SPEC section 6.2.1 (Zafar et al. style).
Protocol: fixed (D', D~); repetitions resample only the training stream.
Params: R^2=500, B=100, |D~|=100, |D'|=250, 100 reps, T=20000, kappa=1e-4, eta0=0.1 (see SPEC).
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

from core.dgp import dgp_dm  # noqa: E402
from core.fairuq import add_intercept, make_splits, mis, phi_hat, train_dm, w2_empirical_vs_normal  # noqa: E402
from core.optimum import theta_star_dm  # noqa: E402

ROOT = CODE_DIR.parent
RAW = ROOT / "results" / "raw"
TAB = ROOT / "results" / "tables"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--T", type=int, default=20000)
    ap.add_argument("--B", type=int, default=100)
    ap.add_argument("--n-pool", type=int, default=20000, dest="n_pool")
    ap.add_argument("--n-dprime", type=int, default=250, dest="n_dprime")
    ap.add_argument("--n-tilde", type=int, default=100, dest="n_tilde")
    ap.add_argument("--R2", type=float, default=500.0)
    ap.add_argument("--n-true", type=int, default=2000000, dest="n_true")
    ap.add_argument("--kappa", type=float, default=1e-4)
    ap.add_argument("--eta0", type=float, default=0.1)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--tag", type=str, default="paperdgp")
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    X, y, z = dgp_dm(args.n_pool + args.n_dprime + args.n_tilde, seed=args.seed)
    i_dp, i_tl, i_pool = make_splits(len(y), args.n_dprime, args.n_tilde,
                                     np.random.default_rng(args.seed + 1))
    Phi = add_intercept(X)
    Phi_pool, y_pool = Phi[i_pool], y[i_pool]
    Phi_tl, y_tl, z_tl = Phi[i_tl], y[i_tl], z[i_tl]

    w_all = z[i_dp].astype(np.float64) - float(z[i_dp].mean())
    sel = (y[i_dp] == -1)
    Phi_m, y_m, w_m = Phi[i_dp][sel], y[i_dp][sel].astype(np.float64), w_all[sel]
    print(f"[data] n={len(y)} pool={len(y_pool)} |D'|={args.n_dprime} |D'_-|={sel.sum()} |D~|={args.n_tilde}")

    th_star, res = theta_star_dm(Phi_pool, y_pool, args.R2, Phi_m, y_m, w_m, args.kappa)
    phi_hold = float(phi_hat(th_star, Phi_tl, z_tl, y_tl, kind="dm")[0])
    Xt, yt, zt = dgp_dm(args.n_true, seed=args.seed + 3)
    phi_true = float(phi_hat(th_star, add_intercept(Xt), zt, yt, kind="dm")[0])
    print(f"[theta*] success={res.success} ||th*||={np.linalg.norm(th_star):.4f} "
          f"pool_acc={float((((Phi_pool @ th_star) > 0) == (y_pool > 0)).mean()):.4f} "
          f"| phi*(D~)={phi_hold:.5f}  phi*(truth)={phi_true:.5f}")

    ks = np.unique(np.round(np.logspace(0, np.log10(args.T), 40)).astype(int))
    snapshots = set(int(k) for k in ks)
    rows, per_rep = [], {int(k): [] for k in ks}
    for rep in range(args.reps):
        avg, snaps = train_dm(Phi_pool, y_pool, args.R2, Phi_m, y_m, w_m, T=args.T, B=args.B,
                              kappa=args.kappa, eta0=args.eta0, eta_a=0.501,
                              rng=np.random.default_rng(args.seed + 1000 + rep),
                              snapshot_ks=snapshots)
        for k in ks:
            k = int(k)
            phis = phi_hat(snaps[k], Phi_tl, z_tl, y_tl, kind="dm")
            lo, hi = np.quantile(phis[1:], [args.alpha / 2, 1 - args.alpha / 2])
            per_rep[k].append(float(phis[0]))
            rows.append({"rep": rep, "k": k, "phi_main": float(phis[0]),
                         "ci_lo": float(lo), "ci_hi": float(hi)})

    df = pd.DataFrame(rows)
    out_csv = RAW / f"synth_dm_per_rep_{args.tag}.csv"
    df.to_csv(out_csv, index=False)

    summary = []
    for k in ks:
        k = int(k)
        sub = df[df["k"] == k]
        phis = np.array(per_rep[k])
        cov_hold = float(np.mean((sub["ci_lo"] <= phi_hold) & (phi_hold <= sub["ci_hi"])))
        cov_pop = float(np.mean((sub["ci_lo"] <= phi_true) & (phi_true <= sub["ci_hi"])))
        mis_v = [mis(phis, a, b, args.alpha) for a, b in zip(sub["ci_lo"], sub["ci_hi"])]
        sigma2 = args.T * float(np.var(phis, ddof=1))
        summary.append({"k": k, "phi_mean": float(phis.mean()), "phi_sd": float(phis.std(ddof=1)),
                        "ci_width_mean": float((sub["ci_hi"] - sub["ci_lo"]).mean()),
                        "coverage_hold": cov_hold, "coverage_pop": cov_pop,
                        "mis": float(np.mean(mis_v)),
                        "w2_to_normal": w2_empirical_vs_normal(phis, phi_true, np.sqrt(max(sigma2 / k, 1e-15)))})
    summ = pd.DataFrame(summary)
    summ.to_csv(TAB / f"synth_dm_summary_{args.tag}.csv", index=False)
    meta = {"config": vars(args), "phi_star_hold": phi_hold, "phi_star_true": phi_true,
            "theta_star": th_star.tolist(), "theta_star_norm": float(np.linalg.norm(th_star)),
            "optimizer_success": bool(res.success),
            "coverage_hold_T": float(summ.iloc[-1]["coverage_hold"]),
            "coverage_pop_T": float(summ.iloc[-1]["coverage_pop"]),
            "ci_width_T": float(summ.iloc[-1]["ci_width_mean"]),
            "mis_T": float(summ.iloc[-1]["mis"]), "w2_T": float(summ.iloc[-1]["w2_to_normal"]),
            "mis_first": float(summ.iloc[0]["mis"]),
            "elapsed_sec": round(time.time() - t0, 1)}
    with open(TAB / f"synth_dm_meta_{args.tag}.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print("\n=== head/tail ===")
    print(summ.head(2).to_string(index=False))
    print(summ.tail(2).to_string(index=False))
    print(f"\ncoverage@T held-out={meta['coverage_hold_T']:.2f} population={meta['coverage_pop_T']:.2f} "
          f"| width={meta['ci_width_T']:.4f} | MIS {meta['mis_first']:.3f}->{meta['mis_T']:.3f} "
          f"| W2={meta['w2_T']:.4f}")
    print(f"elapsed {meta['elapsed_sec']}s -> {out_csv}")


if __name__ == "__main__":
    main()
