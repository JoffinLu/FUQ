"""Fast invariants for the core fairness-UQ primitives (no external data needed).

These checks are deliberately cheap (< 10 s on one CPU) so a reviewer can run them
before the full reproduction:

    python code/tests/test_invariants.py        # prints "ALL TESTS PASSED", exit 0

They cover the mathematical identities the paper relies on:
  * the slab projection and its KKT conditions                (Lemma A.1 / Eq. projection)
  * the multiplier distribution V ~ Unif[1-sqrt3, 1+sqrt3]      (Algorithm 2)
  * the DI constraint direction x_tilde (def. of Theta(D'))
  * the DI/DM fairness functionals phi(theta)
  * finite-difference agreement of ce_grad and dm_penalty_grad
  * determinism of the training loops under a fixed seed
  * reproducibility of the data generators under a fixed seed
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from core.dgp import dgp_di, dgp_dm  # noqa: E402
from core.fairuq import (  # noqa: E402
    SQRT3,
    add_intercept,
    ce_grad,
    ce_loss,
    di_constraint_direction,
    dm_penalty_grad,
    phi_hat,
    slab_projection,
    train_di,
    train_dm,
)

RNG = np.random.default_rng(20261026)
N_TESTS = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global N_TESTS
    N_TESTS += 1
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        raise AssertionError(name)


def test_projection() -> None:
    d, eps = 4, 0.1
    xt = RNG.normal(size=d)
    V = RNG.normal(scale=2.0, size=(300, d))
    out = slab_projection(V, xt, eps)
    slack = float(np.abs(out @ xt).max()) - eps
    check("slab_projection feasibility", slack <= 1e-9, f"max slack {slack:.2e}")
    inside = np.abs(V @ xt) <= eps
    check("slab_projection keeps feasible rows", np.array_equal(out[inside], V[inside]))
    active = ~inside
    diff = V[active] - out[active]                       # = adj * xt, parallel to xt
    res = diff - (diff @ xt / (xt @ xt))[:, None] * xt[None, :]
    check("slab_projection KKT (difference || xt)", float(np.abs(res).max()) <= 1e-9,
          f"||res|| {np.abs(res).max():.2e}")
    check("slab_projection boundary", np.allclose(np.abs(out[active] @ xt), eps, atol=1e-9))


def test_multiplier_moments() -> None:
    V = RNG.uniform(1.0 - SQRT3, 1.0 + SQRT3, size=300_000)
    check("E[V] = 1", abs(V.mean() - 1.0) < 0.01, f"{V.mean():.4f}")
    check("Var[V] = 1", abs(V.var() - 1.0) < 0.02, f"{V.var():.4f}")


def test_di_direction() -> None:
    n, d = 300, 3
    Phi = RNG.normal(size=(n, d))
    z = RNG.integers(0, 2, size=n)
    xt = di_constraint_direction(Phi, z)
    manual = sum((z[i] - z.mean()) * Phi[i] for i in range(n)) / n
    check("di_constraint_direction", np.allclose(xt, manual, atol=1e-12))


def test_phi_hat() -> None:
    n, d = 400, 3
    Phi = RNG.normal(size=(n, d))
    theta = RNG.normal(size=(3, d))
    z = RNG.integers(0, 2, size=n)
    y = RNG.choice([-1.0, 1.0], size=n)
    pred = (theta @ Phi.T) > 0
    p0 = pred[:, z == 0].mean(axis=1)
    p1 = pred[:, z == 1].mean(axis=1)
    check("phi_hat DI", np.allclose(phi_hat(theta, Phi, z, kind="di"), np.abs(p0 - p1), atol=1e-12))
    base = y == -1
    p0m = pred[:, base & (z == 0)].mean(axis=1)
    p1m = pred[:, base & (z == 1)].mean(axis=1)
    check("phi_hat DM", np.allclose(phi_hat(theta, Phi, z, y, kind="dm"), np.abs(p0m - p1m), atol=1e-12))


def test_ce_grad_fd() -> None:
    d = 4
    theta = RNG.normal(size=(2, d))
    phi = RNG.normal(size=d)
    y, kappa, eps = 1.0, 0.1, 1e-6
    g = ce_grad(theta, phi, y, kappa)
    g_fd = np.zeros_like(theta)
    for j in range(d):
        e = np.zeros(d)
        e[j] = eps
        g_fd[:, j] = (ce_loss(theta + e[None, :], phi[None, :], np.array([y]), kappa)
                      - ce_loss(theta - e[None, :], phi[None, :], np.array([y]), kappa)) / (2 * eps)
    check("ce_grad finite differences", np.allclose(g, g_fd, atol=1e-6),
          f"max err {np.abs(g - g_fd).max():.2e}")


def test_dm_grad_fd() -> None:
    n, d = 25, 3
    Phi = RNG.normal(size=(n, d))
    y = RNG.choice([-1.0, 1.0], size=n)
    z = RNG.integers(0, 2, size=n)
    w = z.astype(float) - z.mean()
    theta = RNG.normal(size=(2, d))
    g, _ = dm_penalty_grad(theta, Phi, y, w)

    def gamma_row(t: np.ndarray) -> float:
        u = (Phi @ t) * y
        s = float((w * np.minimum(u, 0.0)).mean())
        return s * s

    eps = 1e-6
    g_fd = np.zeros_like(theta)
    for r in range(theta.shape[0]):
        for j in range(d):
            e = np.zeros(d)
            e[j] = eps
            g_fd[r, j] = (gamma_row(theta[r] + e) - gamma_row(theta[r] - e)) / (2 * eps)
    check("dm_penalty_grad finite differences", np.allclose(g, g_fd, atol=1e-5),
          f"max err {np.abs(g - g_fd).max():.2e}")


def test_training_determinism() -> None:
    Phi, y, z = dgp_di(800, seed=7)
    xt = di_constraint_direction(Phi[:100], z[:100])

    def run_di(seed: int):
        return train_di(Phi, y, xt=xt, eps=0.05, T=150, B=4, kappa=0.01,
                        eta0=0.1, eta_a=0.501, rng=np.random.default_rng(seed))

    a1, _ = run_di(11)
    a2, _ = run_di(11)
    check("train_di determinism", np.array_equal(a1, a2))
    R2 = 50.0
    m = 100
    Phi_m, y_m, z_m = dgp_dm(2 * m, seed=8)
    w_m = z_m.astype(float) - z_m.mean()

    def run_dm(seed: int):
        return train_dm(Phi, y, R2, Phi_m[:m], y_m[:m], w_m[:m], T=150, B=4,
                        kappa=0.01, eta0=0.03, eta_a=0.501, rng=np.random.default_rng(seed))

    b1, _ = run_dm(12)
    b2, _ = run_dm(12)
    check("train_dm determinism", np.array_equal(b1, b2))


def test_generators() -> None:
    X1, y1, z1 = dgp_di(500, seed=1)
    X2, y2, z2 = dgp_di(500, seed=1)
    check("dgp_di reproducible", np.array_equal(X1, X2) and np.array_equal(y1, y2) and np.array_equal(z1, z2))
    check("dgp_di shapes/labels", X1.shape[0] == 500 and set(np.unique(y1)) <= {-1.0, 1.0}
          and set(np.unique(z1)) <= {0, 1}, f"X{X1.shape} y{np.unique(y1)[:2]} z{np.unique(z1)}")
    Xd, yd, zd = dgp_dm(600, seed=2)
    check("dgp_dm shapes", Xd.shape[0] == 600 and set(np.unique(yd)) <= {-1.0, 1.0}, f"X{Xd.shape}")


def main() -> int:
    t0 = time.time()
    test_projection()
    test_multiplier_moments()
    test_di_direction()
    test_phi_hat()
    test_ce_grad_fd()
    test_dm_grad_fd()
    test_training_determinism()
    test_generators()
    print(f"\nALL TESTS PASSED ({N_TESTS} checks, {time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
