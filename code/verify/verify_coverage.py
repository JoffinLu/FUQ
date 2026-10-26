"""A6 -- coverage calibration of the SPEC Sec. 5 online multiplier bootstrap.

Toy model (fully analytic)
--------------------------
theta in R^2, loss

    ell(theta) = E[(a^T theta - b)^2]/2 + (kappa/2)||theta||^2,
    a ~ N(0, s^2 I_2),   b = a^T theta_0,

so the population gradient is  grad ell(theta) = A(theta-theta_0) + kappa theta
with A = E[a a^T] = s^2 I, Hessian H = (s^2+kappa) I = h I.
Constraint:  Theta = {theta : |xt^T theta| <= eps},  xt = (0.8, 0.6), ||xt||=1.

Analytic quantities
    theta_u   = s^2/h * theta_0                        (unconstrained min)
    theta*    = theta_u - (xt^T theta_u - eps) xt      (active upper boundary)
For the averaged SDA, with tangent projector P = I - xt xt^T, B = P H P = h P,
S = P Cov(xi(theta*)) P = s^4 P   (xi = (aa^T-A)(theta-theta_0)), hence

    Sigma = B^{-1} S B^{-1} = (s^2/h)^2 P,       (covariance of sqrt(T)(thbar-th*))
    Var(phi(thbar_T)) ~ sigma^2 / T  for a unit linear functional phi.

Fairness functional (two targets, as requested by the Lead)
------------------------------------------------------------
(a) held-out estimator target: the fairnes functional is estimated on an
    evaluation set D~ of size m:  Delta_hat(theta) = dhat^T theta, where
    dhat = c + tau * mean_{i<=m} xi_i  (xi_i ~ N(0,I_2)), i.e. dhat is a
    noisy sample estimate of the population coefficient c (c = (-0.6, 0.8),
    c^T xt = 0, unit).  The paper's CI is built from the SAME D~ for all
    bootstrap trajectories, so its natural target is phi_hat(theta*) =
    |dhat^T theta*|.
(b) population target: phi(theta*) = |c^T theta*|, which additionally contains
    the evaluation-set sampling error (dhat-c)^T theta* that the training-stream
    bootstrap does NOT capture.

Both coverages are reported.  With tau = 0 the two coincide and the experiment
is the clean calibration of the multiplier bootstrap itself.

The experiment repeats nrep times:
  * one main SDA trajectory thbar_T (frozen at T) and B online-multiplier
    bootstrap trajectories (SPEC Algorithm 2), all sharing the SAME W_k stream
    (vectorised, SPEC Sec. 5):   th^b_k = Pi(-u^b_{k-1}),
                                 u^b_k  = u^b_{k-1} + eta_k V^b_k grad ell(th^b_k;W_k)
  * CI = [q_{alpha/2}, q_{1-alpha/2}] of {phi_hat(thbar^b_T)}_{b=1..B}.

Run:
    python verify_coverage.py --pilot          # 30 reps, fast smoke
    python verify_coverage.py                  # 300 reps clean + 300 reps eval-noise
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ref_impl import KAPPA, eta_array, slab_project_batch  # noqa: E402

# ---------------------------------------------------------------------------
# analytic toy constants
# ---------------------------------------------------------------------------
S2 = 25.0                       # a ~ N(0, S2 I_2)
HESS = S2 + KAPPA               # h
THETA0 = np.array([1.0, 0.5])
XT = np.array([0.8, 0.6])       # ||XT|| = 1 (constraint normal)
EPS = 0.1
C = np.array([-0.6, 0.8])       # unit, orthogonal to XT
PA = np.eye(2) - np.outer(XT, XT)


def analytic():
    theta_u = (S2 / HESS) * THETA0
    s = float(XT @ theta_u)
    assert s > EPS, "constraint is not active with these toy constants"
    theta_star = theta_u - (s - EPS) * XT          # ||XT||=1
    phi_star = abs(float(C @ theta_star))
    sigma2 = (S2 / HESS) ** 2                       # c^T Sigma c
    Sigma = (S2 / HESS) ** 2 * PA
    return dict(theta_u=theta_u, theta_star=theta_star, phi_star=phi_star,
                sigma2=sigma2, sigma=math.sqrt(sigma2), Sigma=Sigma)


def pop_loss(theta, kappa=KAPPA):
    d = theta - THETA0
    return 0.5 * S2 * float(d @ d) + 0.5 * kappa * float(theta @ theta)


def pop_grad(theta, kappa=KAPPA):
    return S2 * (theta - THETA0) + kappa * theta


def solve_pop_slsqp():
    cons = [
        {"type": "ineq", "fun": lambda t: EPS - float(XT @ t),
         "jac": lambda t: -XT},
        {"type": "ineq", "fun": lambda t: EPS + float(XT @ t),
         "jac": lambda t: XT},
    ]
    res = minimize(pop_loss, np.zeros(2), jac=pop_grad, method="SLSQP",
                   constraints=cons, options={"ftol": 1e-16, "maxiter": 1000})
    return res.x


# ---------------------------------------------------------------------------
# one replication: main + B shared-stream bootstrap trajectories
# ---------------------------------------------------------------------------
def run_shared(stream_a, stream_b, V, xt=XT, eps=EPS, kappa=KAPPA, eta=None):
    """All (1+B) trajectories share one data stream (SPEC Algorithm 2).

    Column 0 is the main trajectory (V=1, i.e. Algorithm 1); columns 1..B are
    the bootstrap trajectories.  Returns theta_bar (1+B, 2).
    """
    T, d = stream_a.shape
    if eta is None:
        eta = eta_array(T)
    B = V.shape[1]
    U = np.zeros((B, d))
    avg = np.zeros((B, d))
    for k in range(T):
        Theta = slab_project_batch(-U, xt, eps)
        avg += Theta
        a = stream_a[k]
        b = stream_b[k]
        G = (Theta @ a - b)[:, None] * a[None, :] + kappa * Theta
        U += eta[k] * V[k][:, None] * G
    return avg / T


# ---------------------------------------------------------------------------
# scenario: clean (tau=0) or with evaluation-set noise (tau>0)
# ---------------------------------------------------------------------------
def run_scenario(nrep, T, B, seed, alpha, tau, m_eval, theta_star, phi_star,
                 sigma):
    rng_master = np.random.default_rng(seed)
    eta = eta_array(T)
    lo_q, hi_q = alpha / 2.0, 1.0 - alpha / 2.0
    V_lo, V_hi = 1.0 - math.sqrt(3.0), 1.0 + math.sqrt(3.0)
    halfwidth_oracle = stats.norm.ppf(1.0 - alpha / 2.0) * sigma / math.sqrt(T)

    rec = dict(
        phi_hat_main=np.empty(nrep), phi_hat_star=np.empty(nrep),
        eval_bias=np.empty(nrep), ci_lo=np.empty(nrep), ci_hi=np.empty(nrep),
        boot_sd=np.empty(nrep), boot_median=np.empty(nrep),
        theta_main=np.empty((nrep, 2)),
        covered_a=np.zeros(nrep, dtype=bool),
        covered_b=np.zeros(nrep, dtype=bool),
        oracle_covered_a=np.zeros(nrep, dtype=bool),
        oracle_covered_b=np.zeros(nrep, dtype=bool),
        sigma_hat=np.empty(nrep), sign_flip=np.zeros(nrep, dtype=bool),
    )
    t0 = time.time()
    for r in range(nrep):
        rng = np.random.default_rng(seed + 1 + r)
        a = math.sqrt(S2) * rng.standard_normal((T, 2))
        b = a @ THETA0
        # evaluation set D~ (independent of the training stream); dhat is its
        # estimated linear-functional coefficient vector
        if tau > 0.0:
            dhat = C + tau * rng.standard_normal((m_eval, 2)).mean(axis=0)
        else:
            dhat = C.copy()
        sigma_hat = math.sqrt(max(float(dhat @ analytic()["Sigma"] @ dhat), 0.0))
        V = rng.uniform(V_lo, V_hi, size=(T, B + 1))
        V[:, 0] = 1.0
        Th = run_shared(a, b, V, eta=eta)
        th_main = Th[0]
        th_boot = Th[1:]
        rec["theta_main"][r] = th_main

        phi_main = abs(float(dhat @ th_main))
        phi_star_hat = abs(float(dhat @ theta_star))
        phi_boot = np.abs(th_boot @ dhat)
        lo, hi = np.quantile(phi_boot, [lo_q, hi_q])
        rec["phi_hat_main"][r] = phi_main
        rec["phi_hat_star"][r] = phi_star_hat
        rec["eval_bias"][r] = phi_star_hat - phi_star
        rec["ci_lo"][r], rec["ci_hi"][r] = lo, hi
        rec["boot_sd"][r] = float(phi_boot.std(ddof=1))
        rec["boot_median"][r] = float(np.median(phi_boot))
        rec["sigma_hat"][r] = sigma_hat
        rec["sign_flip"][r] = bool(np.sign(float(dhat @ theta_star))
                                   != np.sign(float(C @ theta_star)))
        # (a) held-out estimator target: phi_hat(theta*) (same D~)
        rec["covered_a"][r] = bool(lo <= phi_star_hat <= hi)
        # (b) population target
        rec["covered_b"][r] = bool(lo <= phi_star <= hi)
        # oracle CIs (analytic width, centred on phi_hat(thbar_T))
        hw_hat = stats.norm.ppf(1.0 - alpha / 2.0) * sigma_hat / math.sqrt(T)
        rec["oracle_covered_a"][r] = bool(
            abs(phi_main - phi_star_hat) <= hw_hat)
        rec["oracle_covered_b"][r] = bool(
            abs(phi_main - phi_star) <= hw_hat)
        if (r + 1) % max(1, nrep // 5) == 0:
            print(f"      rep {r+1}/{nrep} ({time.time()-t0:.1f}s)")
    rec["seconds"] = time.time() - t0
    rec["T"], rec["B"], rec["nrep"] = T, B, nrep
    rec["tau"], rec["m_eval"] = tau, m_eval
    return rec


# ---------------------------------------------------------------------------
def summarise(rec, alpha, theta_star, phi_star, sigma):
    n = rec["nrep"]
    out = dict(tau=rec["tau"], m_eval=rec["m_eval"], nrep=n, T=rec["T"],
               B=rec["B"], seconds=rec["seconds"])
    for key in ("covered_a", "covered_b", "oracle_covered_a",
                "oracle_covered_b"):
        p = float(rec[key].mean())
        out[key] = dict(value=p, mc_se=math.sqrt(p * (1 - p) / n),
                        wilson=list(map(float, stats.binomtest(
                            int(rec[key].sum()), n).proportion_ci(
                                0.95, method="wilson"))))
    c, cse = out["covered_a"]["value"], out["covered_a"]["mc_se"]
    out["coverage_a_sigma_units"] = (c - (1 - alpha)) / cse if cse else 0.0
    c2, cse2 = out["covered_b"]["value"], out["covered_b"]["mc_se"]
    out["coverage_b_sigma_units"] = (c2 - (1 - alpha)) / cse2 if cse2 else 0.0

    phi_main = rec["phi_hat_main"]
    eval_bias = rec["eval_bias"]
    halfwidth = (rec["ci_hi"] - rec["ci_lo"]) / 2.0
    halfwidth = np.asarray(halfwidth)
    sigma_T = sigma / math.sqrt(rec["T"])
    out.update(
        phi_hat_main_mean=float(phi_main.mean()),
        phi_hat_main_sd=float(phi_main.std(ddof=1)),
        eval_bias_mean=float(eval_bias.mean()),
        eval_bias_sd=float(eval_bias.std(ddof=1)),
        eval_bias_sd_over_sigma_T=float(eval_bias.std(ddof=1) / sigma_T),
        eval_bias_over_halfwidth=float(
            np.mean(np.abs(eval_bias) / halfwidth)),
        halfwidth_mean=float(halfwidth.mean()),
        oracle_halfwidth=float(stats.norm.ppf(1 - alpha / 2) * sigma_T),
        width_ratio=float(halfwidth.mean()
                          / (stats.norm.ppf(1 - alpha / 2) * sigma_T)),
        boot_sd_mean=float(rec["boot_sd"].mean()),
        boot_sd_over_sigma_T=float(rec["boot_sd"].mean() / sigma_T),
        boot_center_bias=float((rec["boot_median"] - phi_main).mean()),
        sigma_hat_mean=float(rec["sigma_hat"].mean()),
        sign_flip_fraction=float(rec["sign_flip"].mean()),
        # normal-theory attribution of coverage:
        # coverage_b for one rep ~ P(|b_eval + Z sigma_T| <= halfwidth)
        pred_cov_b=float(np.mean(
            stats.norm.cdf((halfwidth - eval_bias) / sigma_T)
            - stats.norm.cdf((-halfwidth - eval_bias) / sigma_T))),
        pred_cov_a=float(np.mean(
            stats.norm.cdf(halfwidth / sigma_T)
            - stats.norm.cdf(-halfwidth / sigma_T))),
        theta_main_bias=list(map(float, rec["theta_main"].mean(axis=0)
                                 - theta_star)),
    )
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--nrep", type=int, default=300)
    ap.add_argument("--T", type=int, default=5000)
    ap.add_argument("--B", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--tau", type=float, default=2.0,
                    help="evaluation-set noise scale; 0 = clean (no D~ noise)")
    ap.add_argument("--m-eval", type=int, default=100,
                    help="evaluation-set size (first entry of --m-eval-list)")
    ap.add_argument("--m-eval-list", type=str, default="100,1000,10000",
                    help="evaluation-set sizes to sweep in the noisy scenario")
    ap.add_argument("--nrep-list", type=str, default="300,150,100",
                    help="replications per entry of --m-eval-list")
    ap.add_argument("--skip-clean", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--json-out", type=str, default="verify_coverage.json")
    args = ap.parse_args(argv)
    if args.pilot:
        args.nrep = min(args.nrep, 30)
        args.B = min(args.B, 100)

    A = analytic()
    theta_star, phi_star, sigma, Sigma = (A["theta_star"], A["phi_star"],
                                          A["sigma"], A["Sigma"])
    T, B, alpha = args.T, args.B, args.alpha

    th_slsqp = solve_pop_slsqp()
    slsqp_rel = float(np.linalg.norm(th_slsqp - theta_star)
                      / np.linalg.norm(theta_star))
    print("A6  online multiplier bootstrap coverage calibration (SPEC Sec. 5)")
    print(f"    toy: theta in R^2, a~N(0,{S2:g}I), b=a^T theta0, "
          f"theta0={THETA0}, kappa={KAPPA}")
    print(f"    constraint |xt^T theta|<={EPS}, xt={XT}, c={C} (c^T xt=0)")
    print(f"    analytic theta* = {np.array2string(theta_star, precision=8)}  "
          f"phi_pop(theta*) = {phi_star:.8f}")
    print(f"    analytic sigma_Delta = {sigma:.8f}; "
          f"sigma/sqrt(T) = {sigma/math.sqrt(T):.6f}; oracle 95% halfwidth = "
          f"{stats.norm.ppf(0.975)*sigma/math.sqrt(T):.6f}")
    print(f"    SLSQP check on population objective: rel err = {slsqp_rel:.2e} "
          f"-> {'PASS' if slsqp_rel < 1e-8 else 'FAIL'}")
    print(f"    T={T}, B={B}, alpha={alpha}")

    clean = None
    if not args.skip_clean:
        print(f"\n  == scenario CLEAN (tau=0: no evaluation-set noise; "
              f"(a)==(b)) : nrep={args.nrep} ==")
        rec0 = run_scenario(args.nrep, T, B, args.seed, alpha, 0.0,
                            args.m_eval, theta_star, phi_star, sigma)
        clean = summarise(rec0, alpha, theta_star, phi_star, sigma)
        print(f"    coverage (a==b) = {clean['covered_a']['value']:.4f} "
              f"(MC se {clean['covered_a']['mc_se']:.4f}, "
              f"{clean['coverage_a_sigma_units']:+.2f} MC se from 0.95)")
        print(f"    oracle coverage = {clean['oracle_covered_a']['value']:.4f}")
        print(f"    width ratio (bootstrap/oracle) = {clean['width_ratio']:.4f};"
              f"  bootstrap sd / (sigma/sqrt(T)) = "
              f"{clean['boot_sd_over_sigma_T']:.4f}")
        print(f"    eval-set sampling sd at this m: n/a (clean)")

    print(f"\n  == scenario WITH EVALUATION-SET NOISE (tau={args.tau}) ==")
    m_list = [int(s) for s in args.m_eval_list.split(",")]
    nrep_list = [int(s) for s in args.nrep_list.split(",")]
    if args.pilot:
        nrep_list = [min(n, 30) for n in nrep_list]
    eval_scenarios = []
    for jj, m_eval in enumerate(m_list):
        nrep_j = nrep_list[min(jj, len(nrep_list) - 1)]
        print(f"\n  -- D~ of size m={m_eval}, nrep={nrep_j} --")
        rec1 = run_scenario(nrep_j, T, B, args.seed + 500_000 + jj, alpha,
                            args.tau, m_eval, theta_star, phi_star, sigma)
        ev = summarise(rec1, alpha, theta_star, phi_star, sigma)
        eval_scenarios.append(ev)
        print(f"    coverage (a) held-out-estimator target phi_hat(theta*) = "
              f"{ev['covered_a']['value']:.4f} (MC se "
              f"{ev['covered_a']['mc_se']:.4f}, "
              f"{ev['coverage_a_sigma_units']:+.2f} MC se)")
        print(f"    coverage (b) population target phi(theta*)          = "
              f"{ev['covered_b']['value']:.4f} (MC se "
              f"{ev['covered_b']['mc_se']:.4f}, "
              f"{ev['coverage_b_sigma_units']:+.2f} MC se)")
        print(f"    oracle coverage: (a)={ev['oracle_covered_a']['value']:.4f}, "
              f"(b)={ev['oracle_covered_b']['value']:.4f}")
        print(f"    eval bias: mean {ev['eval_bias_mean']:+.5f}, sd "
              f"{ev['eval_bias_sd']:.5f} = "
              f"{ev['eval_bias_sd_over_sigma_T']:.2f} x sigma/sqrt(T), "
              f"|bias|/halfwidth = {ev['eval_bias_over_halfwidth']:.2f}")
        print(f"    bootstrap halfwidth {ev['halfwidth_mean']:.5f} vs oracle "
              f"{ev['oracle_halfwidth']:.5f} (ratio {ev['width_ratio']:.4f})")
        print(f"    sign-flip fraction of dhat^T theta*: "
              f"{ev['sign_flip_fraction']:.4f}")
        print(f"    normal-theory predicted coverage: (a) {ev['pred_cov_a']:.4f},"
              f" (b) {ev['pred_cov_b']:.4f}")
    ev = eval_scenarios[0]
    print(f"\n    => (b)-target gap is an evaluation-set sampling effect: the "
          f"bootstrap conditions on D~ and cannot capture (dhat-c)^T theta*; "
          f"the gap shrinks as m grows (see sweep above).")

    checks = {}
    if clean is not None:
        checks["clean_theta_star_slsqp"] = slsqp_rel < 1e-8
        c = clean["covered_a"]["value"]
        checks["clean_coverage_near_95"] = abs(c - (1 - alpha)) <= \
            3 * clean["covered_a"]["mc_se"] + 0.005
        checks["clean_width_ratio_close_1"] = abs(clean["width_ratio"] - 1) < 0.12
        checks["clean_boot_sd_close"] = abs(clean["boot_sd_over_sigma_T"] - 1) < 0.10
    c_a = ev["covered_a"]["value"]
    checks["eval_a_coverage_near_95"] = abs(c_a - (1 - alpha)) <= \
        3 * ev["covered_a"]["mc_se"] + 0.005
    checks["eval_b_coverage_below_a"] = ev["covered_b"]["value"] < c_a
    checks["eval_b_increases_with_m"] = bool(
        len(eval_scenarios) < 2
        or eval_scenarios[-1]["covered_b"]["value"]
        > eval_scenarios[0]["covered_b"]["value"])
    verdict = "PASS" if all(checks.values()) else "FAIL"
    print("\n  ---- checks ----")
    for k_, v_ in checks.items():
        print(f"    {k_:32s}: {'PASS' if v_ else 'FAIL'}")
    print(f"  => A6 {verdict}")

    out = dict(config=vars(args),
               analytic=dict(theta_u=list(map(float, A["theta_u"])),
                             theta_star=list(map(float, theta_star)),
                             phi_star=float(phi_star),
                             sigma_Delta=float(sigma),
                             Sigma=list(map(list, Sigma))),
               slsqp_rel_err=slsqp_rel, clean=clean,
               eval_scenarios=eval_scenarios,
               checks=checks, verdict=verdict)
    outdir = Path(__file__).resolve().parent / "results"
    outdir.mkdir(exist_ok=True)
    (outdir / args.json_out).write_text(json.dumps(out, indent=2))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
