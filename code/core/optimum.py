"""Global optima of the fairness-aware training objectives, computed by direct optimisation.

Used as the "truth" theta* for coverage assessment on real data (the paper assumes theta*
exists but never computes it).  DI: linearly constrained convex problem -> SLSQP.
DM: unconstrained penalised convex problem -> L-BFGS.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


def _ce_and_grad(Phi: np.ndarray, y: np.ndarray, theta: np.ndarray, kappa: float):
    s = y * (Phi @ theta)
    f = float(np.logaddexp(0.0, -s).mean() + 0.5 * kappa * (theta @ theta))
    g = ((-y * expit(-s))[:, None] * Phi).mean(axis=0) + kappa * theta
    return f, g


def theta_star_di(Phi_pool, y_pool, xt, eps, kappa=1e-4, maxiter=2000):
    """argmin E[CE] + kappa/2 ||theta||^2  s.t.  |xt^T theta| <= eps."""
    d = Phi_pool.shape[1]

    def f(th):
        return _ce_and_grad(Phi_pool, y_pool, th, kappa)[0]

    def g(th):
        return _ce_and_grad(Phi_pool, y_pool, th, kappa)[1]

    cons = [
        {"type": "ineq", "fun": lambda t: eps - float(xt @ t), "jac": lambda t: -xt},
        {"type": "ineq", "fun": lambda t: eps + float(xt @ t), "jac": lambda t: xt},
    ]
    r = minimize(f, np.zeros(d), jac=g, constraints=cons, method="SLSQP",
                 options={"maxiter": maxiter, "ftol": 1e-12})
    return r.x, r


def _gamma_and_grad(Phi_m, y_m, w_m, theta):
    U = y_m * (Phi_m @ theta)                  # (n_m,)
    s = float((w_m * np.minimum(U, 0.0)).mean())
    neg = (U < 0.0).astype(np.float64)
    A = w_m[:, None] * y_m[:, None] * Phi_m
    inner = (neg[:, None] * A).mean(axis=0)
    return s * s, 2.0 * s * inner


def theta_star_dm(Phi_pool, y_pool, R2, Phi_m, y_m, w_m, kappa=1e-4, maxiter=5000):
    """argmin E[CE] + kappa/2||theta||^2 + R^2 * gamma(theta; D'_-)."""
    d = Phi_pool.shape[1]

    def fg(th):
        f1, g1 = _ce_and_grad(Phi_pool, y_pool, th, kappa)
        g2, gg = _gamma_and_grad(Phi_m, y_m, w_m, th)
        return f1 + R2 * g2, g1 + R2 * gg

    r = minimize(lambda t: fg(t), np.zeros(d), jac=True, method="L-BFGS-B",
                 options={"maxiter": maxiter, "ftol": 1e-14, "gtol": 1e-10})
    return r.x, r
