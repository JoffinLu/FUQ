
"""Empirical convergence-rate check for Theorem 1 / Corollary 1 (synthetic DI).

The averaged iterate theta_bar_T satisfies sqrt(T)(Delta_hat_m(theta_bar_T) - Delta(theta*)) => N(0, sigma^2 + lambda v^2)
(Theorem 1), so the training bias should decay like T^{-1/2}.  This script runs a
T-grid of independent replications on the paper's synthetic DI generator with a fixed
constraint set D' (protocol A: fresh evaluation set of size m=100 per replication) and
fits the log-log slope of E|Delta_hat - Delta(theta*)| against T.

It also extracts the W2(k) decay from results/tables/synth_di_summary_paperdgp.csv and
fits its log-log slope against k.

Outputs: results/tables/rate_check_synth_di.csv / .json
"""
import argparse, json, time
import numpy as np
import pandas as pd
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "code" / "core"))
from dgp import dgp_di
from fairuq import add_intercept, make_splits, di_constraint_direction, train_di, phi_hat
from optimum import theta_star_di


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--Tgrid", type=str, default="1000,3000,10000,30000,100000")
    ap.add_argument("--reps", type=int, default=40)
    ap.add_argument("--B", type=int, default=100)
    ap.add_argument("--eta0", type=float, default=0.1)
    ap.add_argument("--eta_a", type=float, default=0.501)
    ap.add_argument("--kappa", type=float, default=1e-4)
    ap.add_argument("--eps", type=float, default=0.002)
    ap.add_argument("--n_dprime", type=int, default=200)
    ap.add_argument("--m", type=int, default=100)
    ap.add_argument("--n_pool", type=int, default=20000)
    ap.add_argument("--n_star_pool", type=int, default=200000)
    ap.add_argument("--n_true", type=int, default=2000000)
    ap.add_argument("--seed", type=int, default=20261026)
    args = ap.parse_args()
    Tgrid = [int(t) for t in args.Tgrid.split(",")]
    rng = np.random.default_rng(args.seed)
    out = root / "results" / "tables"
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    # ---- fixed constraint set D' and population truth ----
    X, y, z = dgp_di(args.n_dprime + 11, seed=args.seed + 100)
    Phi_all = add_intercept(X)
    idx_dp, _, _ = make_splits(len(y), args.n_dprime, 10, np.random.default_rng(args.seed + 101))
    Phi_dp, y_dp, z_dp = Phi_all[idx_dp], y[idx_dp], z[idx_dp]
    xt = di_constraint_direction(Phi_dp, z_dp)
    # theta* on a large pool (the population risk minimiser over Theta(D'))
    Xs, ys, zs = dgp_di(args.n_star_pool, seed=args.seed + 102)
    theta_star = theta_star_di(add_intercept(Xs), ys, xt, args.eps, kappa=args.kappa)[0]
    Xt, yt, zt = dgp_di(args.n_true, seed=args.seed + 103)
    Phi_true, z_true = add_intercept(Xt), zt
    delta_star = float(phi_hat(theta_star[None, :], Phi_true, z_true, kind="di")[0])
    print(f"[truth] |theta*| = {np.linalg.norm(theta_star):.4f} | Delta(theta*) = {delta_star:.5f}", flush=True)

    rows = []
    for T in Tgrid:
        biases, train_biases, train_signed, dists = [], [], [], []
        for r in range(args.reps):
            Xr, yr, zr = dgp_di(args.n_pool + args.m, seed=args.seed + 1000 * T + r)
            Phi = add_intercept(Xr)
            Phi_pool, y_pool = Phi[: args.n_pool], yr[: args.n_pool]
            Phi_eval, y_eval, z_eval = Phi[args.n_pool :], yr[args.n_pool :], zr[args.n_pool :]
            res = train_di(Phi_pool, y_pool, xt, args.eps, T=T, B=args.B, kappa=args.kappa,
                           eta0=args.eta0, eta_a=args.eta_a, rng=np.random.default_rng(args.seed + 7 * T + r))
            theta_bar = res["avg"][0] if isinstance(res, dict) and "avg" in res else res[0][0]
            delta_hat = float(phi_hat(np.atleast_2d(theta_bar), Phi_eval, z_eval, kind="di")[0])
            biases.append(abs(delta_hat - delta_star))
            # training-only deviation, evaluated on the large independent sample
            delta_train = float(phi_hat(np.atleast_2d(theta_bar), Phi_true, z_true, kind="di")[0])
            train_biases.append(abs(delta_train - delta_star))
            train_signed.append(delta_train - delta_star)
            dists.append(float(np.linalg.norm(theta_bar - theta_star)))
        rows.append(dict(T=T, mean_abs_bias_m100=float(np.mean(biases)), sd_abs_bias_m100=float(np.std(biases)),
                         mean_abs_train_bias=float(np.mean(train_biases)),
                         mean_signed_train_bias=float(np.mean(train_signed)),
                         sd_abs_train_bias=float(np.std(train_biases)),
                         mean_dist_to_star=float(np.mean(dists)), sd_dist_to_star=float(np.std(dists)),
                         elapsed_sec=round(time.time() - t0, 1)))
        print(rows[-1], flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(out / "rate_check_synth_di.csv", index=False)
    lt = np.log(df["T"].to_numpy())
    def _slope(col):
        lb = np.log(df[col].to_numpy())
        return float(np.linalg.lstsq(np.vstack([lt, np.ones_like(lt)]).T, lb, rcond=None)[0][0])
    slope_bias = _slope("mean_abs_bias_m100")
    slope_train_bias = _slope("mean_abs_train_bias")
    slope_dist = _slope("mean_dist_to_star")
    slope_signed = _slope("mean_signed_train_bias")

    w2 = pd.read_csv(out / "synth_di_summary_paperdgp.csv")
    w2 = w2[w2["k"] >= 200]
    lk = np.log(w2["k"].to_numpy()); lw = np.log(w2["w2_to_normal"].to_numpy())
    slope_w2 = float(np.linalg.lstsq(np.vstack([lk, np.ones_like(lk)]).T, lw, rcond=None)[0][0])

    summary = dict(reps=args.reps, B=args.B, Tgrid=Tgrid, delta_star=delta_star,
                   theta_star_norm=float(np.linalg.norm(theta_star)),
                   slope_abs_bias_m100_vs_T=round(slope_bias, 3),
                   slope_train_bias_vs_T=round(slope_train_bias, 3),
                   slope_signed_train_bias_vs_T=round(slope_signed, 3),
                   slope_norm_distance_vs_T=round(slope_dist, 3),
                   slope_w2_vs_k=round(slope_w2, 3), rows=rows)
    (out / "rate_check_synth_di.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"slope |bias|(m=100) vs T = {slope_bias:.3f} | slope |train bias| vs T = {slope_train_bias:.3f} "
          f"(theory -0.5) | slope ||theta_bar - theta*|| vs T = {slope_dist:.3f} (theory -0.5) "
          f"| slope signed train bias = {slope_signed:.3f} | slope W2 vs k = {slope_w2:.3f}", flush=True)
    print(f"done in {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
