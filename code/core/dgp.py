"""Synthetic data generating processes from Roy & Mohapatra (UAI 2026), SPEC.md section 6.

Both DGPs are the ones studied in Zafar et al. (2019) and reused by the paper.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import multivariate_normal


def dgp_di(n: int, seed: int):
    """Synthetic DI data (SPEC 6.1.1).

    rho(x|y=1)  = N(( 1.5,  1.5), Sigma1)
    rho(x|y=-1) = N((-1.5, -1.5), Sigma2)
    P(z=1) = f_1(x') / (f_1(x') + f_{-1}(x')),  x' = R(pi/3) x

    Returns X (n,2), y (n,), z (n,).
    """
    rng = np.random.default_rng(seed)
    S1 = np.array([[0.4, 0.2], [0.2, 0.3]])
    S2 = np.array([[0.6, 0.1], [0.1, 0.4]])
    mu1, mu2 = np.array([1.5, 1.5]), np.array([-1.5, -1.5])

    y = rng.choice(np.array([-1, 1]), size=n)
    X = np.empty((n, 2), dtype=np.float64)
    pos = (y == 1)
    X[pos] = rng.multivariate_normal(mu1, S1, size=int(pos.sum()))
    X[~pos] = rng.multivariate_normal(mu2, S2, size=int((~pos).sum()))

    R = np.array([[np.cos(np.pi / 3), -np.sin(np.pi / 3)],
                  [np.sin(np.pi / 3), np.cos(np.pi / 3)]])
    xp = X @ R.T
    f1 = multivariate_normal(mean=mu1, cov=S1).pdf(xp)
    f2 = multivariate_normal(mean=mu2, cov=S2).pdf(xp)
    pz = f1 / (f1 + f2 + 1e-300)
    z = (rng.random(n) < pz).astype(np.int64)
    return X, y.astype(np.int64), z


def dgp_dm(n: int, seed: int):
    """Synthetic DM data (SPEC 6.2.1).

    rho(x|z=0,y= 1) = rho(x|z=1,y= 1) = N(( 2, 2), S1)
    rho(x|z=0,y=-1)                   = N(( 1, 1), S1)
    rho(x|z=1,y=-1)                   = N((-2,-2), S1)
    with S1 = [[3,1],[1,3]]; y uniform, z uniform and independent of y a priori.

    Returns X (n,2), y (n,), z (n,).
    """
    rng = np.random.default_rng(seed)
    S1 = np.array([[3.0, 1.0], [1.0, 3.0]])
    y = rng.choice(np.array([-1, 1]), size=n)
    z = rng.integers(0, 2, size=n)

    X = np.empty((n, 2), dtype=np.float64)
    groups = {
        (0, 1): np.array([2.0, 2.0]),
        (1, 1): np.array([2.0, 2.0]),
        (0, -1): np.array([1.0, 1.0]),
        (1, -1): np.array([-2.0, -2.0]),
    }
    for (zz, yy), mu in groups.items():
        m = (z == zz) & (y == yy)
        X[m] = rng.multivariate_normal(mu, S1, size=int(m.sum()))
    return X, y.astype(np.int64), z
