"""A4 -- verify the bootstrap multiplier distribution.

SPEC Sec. 5: V ~ Unif[1 - sqrt3, 1 + sqrt3] (mean 1, variance 1).

Checks on a 1e6 sample:
  * |sample mean - 1| < 1e-2          (MC s.e. of the mean = 1/sqrt(1e6) = 1e-3)
  * |sample variance - 1| < 1e-2      (MC s.e. of variance ~ sqrt(2/1e6) ~ 1.4e-3)
  * all draws inside [1-sqrt3, 1+sqrt3]
  * KS test vs Unif[1-sqrt3, 1+sqrt3] (must not reject)
  * exact analytic moments of the sampler's declared support:
        E[V]=(lo+hi)/2=1, Var(V)=(hi-lo)^2/12 = 1.

Run:  python verify_multiplier.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ref_impl import sample_multipliers  # noqa: E402

RESULTS = {}
TOL = 1e-2
N = 1_000_000


def main():
    lo = 1.0 - math.sqrt(3.0)
    hi = 1.0 + math.sqrt(3.0)
    rng = np.random.default_rng(20261026)
    V = sample_multipliers(rng, size=N)

    mean_hat = float(V.mean())
    var_hat = float(V.var(ddof=1))
    mn, mx = float(V.min()), float(V.max())
    ks = stats.kstest((V - lo) / (hi - lo), "uniform")

    checks = {
        "support_ok": bool(mn >= lo - 1e-15 and mx <= hi + 1e-15),
        "mean_ok": bool(abs(mean_hat - 1.0) < TOL),
        "variance_ok": bool(abs(var_hat - 1.0) < TOL),
        "ks_not_rejected_1pct": bool(ks.pvalue > 0.01),
    }
    all_ok = all(checks.values())

    RESULTS.update(
        n=int(N),
        support=[lo, hi],
        analytic_mean=1.0,
        analytic_variance=(hi - lo) ** 2 / 12.0,
        sample_mean=mean_hat,
        sample_variance=var_hat,
        mean_abs_error=abs(mean_hat - 1.0),
        variance_abs_error=abs(var_hat - 1.0),
        min_draw=mn,
        max_draw=mx,
        ks_statistic=float(ks.statistic),
        ks_pvalue=float(ks.pvalue),
        checks=checks,
        overall="PASS" if all_ok else "FAIL",
    )

    print("A4  multiplier distribution V ~ Unif[1-sqrt3, 1+sqrt3] (SPEC Sec. 5)")
    print(f"    support                = [{lo:.6f}, {hi:.6f}]  (width {hi-lo:.6f})")
    print(f"    analytic mean, var     = 1, 1")
    print(f"    sample   mean          = {mean_hat:.6f}  (|err|={abs(mean_hat-1):.2e} < 1e-2)")
    print(f"    sample   var (ddof=1)  = {var_hat:.6f}  (|err|={abs(var_hat-1):.2e} < 1e-2)")
    print(f"    min / max draw         = {mn:.6f} / {mx:.6f}")
    print(f"    KS vs Unif: D={ks.statistic:.4f}, p={ks.pvalue:.4f}")
    print(f"    => {RESULTS['overall']}")

    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    (out / "verify_multiplier.json").write_text(json.dumps(RESULTS, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
