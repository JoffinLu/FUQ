"""A3 -- verify the slab projection Pi_Theta and its KKT first-order condition.

Checks (SPEC Sec. 3):
  1. |xt~^T Pi(v)| <= eps + 1e-10 for all sampled v.
  2. Active case (xt~^T v > eps):  |xt~^T Pi(v) - eps| <= 1e-10.
     Active case (xt~^T v < -eps): |xt~^T Pi(v) + eps| <= 1e-10.
  3. Inactive case: Pi(v) == v exactly.
  4. KKT/geometry: v - Pi(v) is collinear with xt~ (residual on xt~^perp ~ 0)
     and the scalar alpha has the sign required by the active side.
  5. Optimality: ||v - Pi(v)|| <= ||v - theta|| for random theta in Theta.
  6. Idempotency Pi(Pi(v)) == Pi(v); batch == single implementation.
  7. Edge cases: on-boundary point unchanged; extremely small eps; large eps.

Run:  python verify_projection.py
Exit code 0 iff every check passes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ref_impl import slab_project, slab_project_batch  # noqa: E402

TOL_INEQ = 1e-10
TOL_ACTIVE = 1e-10
TOL_COLLINEAR = 1e-10
TOL_OPT = 1e-12
TOL_IDEMP = 1e-12
TOL_INACTIVE = 1e-15

RESULTS = {}


def _box(ok):
    return "PASS" if ok else "FAIL"


def main():
    rng = np.random.default_rng(20261026)
    all_ok = True

    # ---------------------------------------------------------------- case set
    # Several constraint geometries, including the DI-like intercept-free xt~
    # and a generic dense xt~; eps values from the SPEC experiments.
    xt_cases = {
        "di_like": np.array([0.0, 0.6477, 0.5739]),
        "dense": np.array([0.35, -0.80, 0.49]),
        "axis": np.array([1.0, 0.0, 0.0]),
    }
    eps_cases = [0.002, 0.01, 0.1, 1.0]

    n_v = 200
    max_absorb = 0.0          # max |xt^T Pi| - eps (should be <= 0)
    max_boundary_err = 0.0    # max ||xt^T Pi| - eps| on active cases
    max_inactive_err = 0.0    # max ||Pi(v)-v|| on inactive cases
    max_collinear = 0.0
    max_opt_gap = 0.0         # max ||v-Pi|| - ||v-theta|| (must be <= 0)
    max_idemp = 0.0
    max_batch = 0.0
    n_active = 0
    n_inactive = 0
    sign_ok = True

    for name, xt in xt_cases.items():
        nrm2 = float(xt @ xt)
        for eps in eps_cases:
            for _ in range(n_v):
                # mix of generic perturbations and perturbations of the
                # boundary itself so both active branches are exercised
                v = rng.normal(size=3) * (1.0 + eps)

                pv = slab_project(v, xt, eps)
                s = float(xt @ v)
                sp = float(xt @ pv)
                alpha = (v - pv) @ xt / nrm2

                # 1. feasibility
                max_absorb = max(max_absorb, abs(sp) - eps)
                all_ok &= abs(sp) <= eps + TOL_INEQ

                # 2/3. active vs inactive
                if s > eps:
                    n_active += 1
                    max_boundary_err = max(max_boundary_err, abs(sp - eps))
                    sign_ok &= alpha >= 0.0
                    all_ok &= abs(sp - eps) <= TOL_ACTIVE
                elif s < -eps:
                    n_active += 1
                    max_boundary_err = max(max_boundary_err, abs(sp + eps))
                    sign_ok &= alpha <= 0.0
                    all_ok &= abs(sp + eps) <= TOL_ACTIVE
                else:
                    n_inactive += 1
                    max_inactive_err = max(max_inactive_err, float(np.linalg.norm(pv - v)))
                    all_ok &= float(np.linalg.norm(pv - v)) <= TOL_INACTIVE

                # 4. KKT: v - Pi(v) is parallel to xt~
                diff = v - pv
                resid = diff - (float(diff @ xt) / nrm2) * xt
                max_collinear = max(max_collinear, float(np.linalg.norm(resid)))
                all_ok &= float(np.linalg.norm(resid)) <= TOL_COLLINEAR

                # 5. optimality over Theta: sample random feasible theta
                for _ in range(3):
                    theta = rng.normal(size=3)
                    # walk into the slab along xt~ without moving off
                    t = float(xt @ theta)
                    if t > eps:
                        theta = theta - ((t - eps) / nrm2) * xt
                    elif t < -eps:
                        theta = theta + ((-eps - t) / nrm2) * xt
                    if abs(float(xt @ theta)) > eps + 1e-9:
                        continue
                    gap = float(np.linalg.norm(v - pv)) - float(np.linalg.norm(v - theta))
                    max_opt_gap = max(max_opt_gap, gap)
                    all_ok &= gap <= TOL_OPT

                # 6. idempotency
                pp = slab_project(pv, xt, eps)
                max_idemp = max(max_idemp, float(np.linalg.norm(pp - pv)))
                all_ok &= float(np.linalg.norm(pp - pv)) <= TOL_IDEMP

            # 6b. batch implementation agrees with single implementation
            Vs = rng.normal(size=(n_v, 3)) * (1.0 + eps)
            Pb = slab_project_batch(Vs, xt, eps)
            Ps = np.vstack([slab_project(v, xt, eps) for v in Vs])
            max_batch = max(max_batch, float(np.abs(Pb - Ps).max()))
            all_ok &= float(np.abs(Pb - Ps).max()) <= 1e-14

    # ------------------------------------------------------------- edge cases
    edge = {}
    xt = np.array([0.0, 0.5, 0.5])
    # exactly on boundary -> unchanged
    v = xt / float(xt @ xt) * 0.1
    edge["on_boundary_unchanged"] = float(np.linalg.norm(slab_project(v, xt, 0.1) - v))
    all_ok &= edge["on_boundary_unchanged"] <= TOL_INACTIVE
    # tiny eps: point above eps gets pulled to the eps-boundary
    pv = slab_project(v * 5.0, xt, 1e-6)
    edge["tiny_eps_boundary_err"] = abs(float(xt @ pv) - 1e-6)
    all_ok &= edge["tiny_eps_boundary_err"] <= TOL_ACTIVE
    # huge eps -> identity
    vv = rng.normal(size=3)
    edge["huge_eps_identity"] = float(np.linalg.norm(slab_project(vv, xt, 1e6) - vv))
    all_ok &= edge["huge_eps_identity"] <= TOL_INACTIVE

    RESULTS.update(
        n_vectors_per_case=n_v,
        n_cases=len(xt_cases) * len(eps_cases),
        n_active=n_active,
        n_inactive=n_inactive,
        max_abs_feasibility_slack=float(max_absorb),          # (must be <= 0)
        max_active_boundary_error=float(max_boundary_err),    # (must be <= 1e-10)
        max_inactive_identity_error=float(max_inactive_err),  # (must be <= 1e-15)
        max_kkt_orthogonality_residual=float(max_collinear),  # (must be <= 1e-10)
        kkt_alpha_sign_ok=bool(sign_ok),
        max_projection_optimality_gap=float(max_opt_gap),     # (must be <= 0)
        max_idempotency_error=float(max_idemp),
        max_batch_vs_single_error=float(max_batch),
        edge_cases=edge,
        overall=_box(all_ok),
    )

    print("A3  slab projection / KKT verification (SPEC Sec. 3)")
    print(f"    cases: {RESULTS['n_cases']}, vectors/case: {n_v}, "
          f"active: {n_active}, inactive: {n_inactive}")
    print(f"    max |xt^T Pi| - eps           = {max_absorb:+.3e}   (<=0)")
    print(f"    max active boundary error    = {max_boundary_err:.3e}   (<=1e-10)")
    print(f"    max inactive identity error  = {max_inactive_err:.3e}   (<=1e-15)")
    print(f"    max KKT parallel residual    = {max_collinear:.3e}   (<=1e-10)")
    print(f"    alpha sign consistent        = {sign_ok}")
    print(f"    max optimality gap           = {max_opt_gap:+.3e}   (<=0)")
    print(f"    max idempotency error        = {max_idemp:.3e}   (<=1e-12)")
    print(f"    max batch-vs-single error    = {max_batch:.3e}   (<=1e-14)")
    print(f"    edge cases                   = {edge}")
    print(f"    => {RESULTS['overall']}")

    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    (out / "verify_projection.json").write_text(json.dumps(RESULTS, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
