"""A5 -- verify the MIS (mean interval score) implementation, SPEC Sec. 7.

        MIS_N(l,u;alpha) = (u-l)
                         + 2/(N alpha) * sum_i (s_i-u) 1[s_i > u]
                         + 2/(N alpha) * sum_i (l-s_i) 1[s_i < l]

Hand-computed examples (N=3, alpha=0.1 => 2/(N alpha) = 6.6666...):
  E1  s=[1, 2, 10],  [l,u]=[0,3]:
        (u-l) = 3;  above: s=10 -> (10-3)=7 -> 6.6667*7 = 46.6667; below: 0
        MIS = 3 + 46.6667 = 49.6667
  E2  s=[-1, 2, 10], [l,u]=[0,3]:
        above: 7 -> 46.6667; below: (0-(-1))=1 -> 6.6667
        MIS = 3 + 46.6667 + 6.6667 = 56.3333
  E3  s=[-1, 0.5, 2], [l,u]=[0,3]:
        above: 0; below: 1 -> 6.6667
        MIS = 3 + 6.6667 = 9.6667
  E4  s=[1, 2, 4], [l,u]=[3,3.5]:  (u-l)=0.5; above: (4-3.5)=0.5;
      below: (3-1)=2 and (3-2)=1
        MIS = 0.5 + 6.6667*(0.5+2+1) = 0.5 + 23.3333 = 23.8333
  E5  all inside  s=[1,2], [l,u]=[0,3]: MIS = 3 (only the width term).

Analytic expectation check: s ~ U[0,1], [l,u]=[0.1,0.9], alpha=0.1:
  E[(s-u)_+] = int_{0.9}^1 (s-0.9) ds = 0.005 ; same for below
  E[MIS] = 0.8 + 2/(1*0.1)*(0.005+0.005) = 0.8 + 0.2 = 1.0
Monotonicity check: the score must prefer a wider interval on the same sample.

Run:  python verify_mis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ref_impl import mis  # noqa: E402

RESULTS = {}


def mis_reference(l, u, s, alpha):
    """Deliberately naive scalar reference implementation (independent code)."""
    s = list(map(float, s))
    n = len(s)
    total = float(u - l)
    for si in s:
        if si > u:
            total += 2.0 / (n * alpha) * (si - u)
        if si < l:
            total += 2.0 / (n * alpha) * (l - si)
    return total


def main():
    alpha = 0.1
    cases = [
        # name, l, u, s, expected hand value
        ("E1_above", 0.0, 3.0, [1.0, 2.0, 10.0], 3.0 + 6.666666666666667 * 7.0),
        ("E2_above_below", 0.0, 3.0, [-1.0, 2.0, 10.0],
         3.0 + 6.666666666666667 * 7.0 + 6.666666666666667 * 1.0),
        ("E3_below", 0.0, 3.0, [-1.0, 0.5, 2.0], 3.0 + 6.666666666666667 * 1.0),
        ("E4_degenerate_width", 3.0, 3.5, [1.0, 2.0, 4.0],
         0.5 + 6.666666666666667 * 3.5),
        ("E5_inside", 0.0, 3.0, [1.0, 2.0], 3.0),
    ]
    rows = []
    all_ok = True
    for name, l, u, s, exp in cases:
        got = mis(l, u, s, alpha)
        ref = mis_reference(l, u, s, alpha)
        ok = abs(got - exp) <= 1e-12 and abs(got - ref) <= 1e-12
        all_ok &= ok
        rows.append(dict(case=name, l=l, u=u, s=s, expected=exp, got=got,
                         naive_impl=ref, abs_err=abs(got - exp), ok=bool(ok)))
        print(f"  {name:18s} expected={exp:.10f}  got={got:.10f}  "
              f"|err|={abs(got-exp):.1e}  {'PASS' if ok else 'FAIL'}")

    # analytic expectation via large MC
    rng = np.random.default_rng(20261026)
    N = 1_000_000
    s = rng.random(N)
    mc = mis(0.1, 0.9, s, alpha)
    exp_mc = 1.0
    se = 0.0
    # MC standard error of MIS estimator (delta method on the two tail means):
    # the sample MIS estimate has variance 2*Var((s-u)_+)/(N alpha^2)+...
    # we just use a generous tolerance 3e-3 (< 0.3% relative).
    ok_mc = abs(mc - exp_mc) < 3e-3
    all_ok &= ok_mc
    print(f"  analytic E[MIS]    expected={exp_mc:.6f}  got={mc:.6f}  "
          f"|err|={abs(mc-exp_mc):.2e}  {'PASS' if ok_mc else 'FAIL'}")

    # monotonicity: wider interval must have a lower MIS on the same sample
    s3 = np.array([1.0, 2.0, 10.0])
    narrow = mis(0.0, 3.0, s3, alpha)
    wide = mis(-1.0, 4.0, s3, alpha)
    ok_mono = wide < narrow
    all_ok &= ok_mono
    print(f"  monotone width     narrow=[0,3] -> {narrow:.4f} ; "
          f"wide=[-1,4] -> {wide:.4f} ; wider better: {ok_mono}")

    RESULTS.update(alpha=alpha, cases=rows,
                   mc_analytic=dict(n=N, expected=exp_mc, got=float(mc),
                                    abs_err=abs(mc-exp_mc)),
                   monotone_width=dict(narrow=float(narrow), wide=float(wide),
                                       ok=bool(ok_mono)),
                   overall="PASS" if all_ok else "FAIL")
    print(f"  => {RESULTS['overall']}")

    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    (out / "verify_mis.json").write_text(json.dumps(RESULTS, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
