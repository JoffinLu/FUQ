"""Core implementation: online multiplier bootstrap for fairness UQ.

Reproduction of Roy & Mohapatra (UAI 2026),
"Fairness Uncertainty Quantification: A Constrained Stochastic Optimization Perspective".

Implements (see ../SPEC.md sections 3-5):
  * Algorithm 1  : DI-aware weighted stochastic dual averaging (slab projection)
  * Algorithm 1' : DM-aware penalised SGD
  * Algorithm 2  : online multiplier bootstrap, B perturbed trajectories on one data stream

All arrays use the design matrix Phi = [X, 1] (intercept appended), so theta in R^d.

Conventions
-----------
y in {-1, +1}, z in {0, 1}, h(x; theta) = sign(theta^T phi(x)).
phi_DI(theta) = |P(h=1|z=0) - P(h=1|z=1)|
phi_DM(theta) = |P(h=1|y=-1,z=0) - P(h=1|y=-1,z=1)|
"""
from __future__ import annotations

import numpy as np
from scipy.special import expit
from scipy.stats import wasserstein_distance

SQRT3 = np.sqrt(3.0)


# --------------------------------------------------------------------------------------
# data helpers
# --------------------------------------------------------------------------------------
def add_intercept(X: np.ndarray) -> np.ndarray:
    """Append a constant column so that theta^T phi(x) includes an intercept."""
    X = np.asarray(X, dtype=np.float64)
    return np.hstack([X, np.ones((X.shape[0], 1), dtype=np.float64)])


def make_splits(n: int, n_dprime: int, n_tilde: int, rng: np.random.Generator):
    """Fixed split: (constraint set D', evaluation set D~, training pool)."""
    perm = rng.permutation(n)
    idx_dp = perm[:n_dprime]
    idx_tl = perm[n_dprime:n_dprime + n_tilde]
    idx_pool = perm[n_dprime + n_tilde:]
    return idx_dp, idx_tl, idx_pool


# --------------------------------------------------------------------------------------
# DI: constraint geometry + projection
# --------------------------------------------------------------------------------------
def di_constraint_direction(Phi_dp: np.ndarray, z_dp: np.ndarray) -> np.ndarray:
    """x_tilde = mean_{i in D'} (z_i - zbar) phi(x_i)."""
    w = z_dp.astype(np.float64) - float(z_dp.mean())
    return (w[:, None] * Phi_dp).mean(axis=0)


def slab_projection(V: np.ndarray, xt: np.ndarray, eps: float) -> np.ndarray:
    """Euclidean projection of each row of V onto {theta : |xt^T theta| <= eps}.

    V : (M, d) ; xt : (d,) ; returns (M, d).
    """
    V = np.atleast_2d(V)
    a = V @ xt
    nrm2 = float(xt @ xt)
    out = V.copy()
    active = np.abs(a) > eps
    if np.any(active):
        aa = a[active]
        adj = (aa - np.sign(aa) * eps) / nrm2
        out[active] = V[active] - adj[:, None] * xt[None, :]
    return out


# --------------------------------------------------------------------------------------
# losses and gradients
# --------------------------------------------------------------------------------------
def ce_grad(Theta: np.ndarray, phi: np.ndarray, y: float, kappa: float) -> np.ndarray:
    """Gradient of CE loss + kappa/2 ||theta||^2 for each row of Theta at the same sample.

    Theta : (M, d) ; phi : (d,) ; y : scalar. Returns (M, d).
    grad = -y * phi / (1 + exp(y * theta^T phi)) + kappa * theta
    """
    s = y * (Theta @ phi)                       # (M,)
    coef = -y * expit(-s)                       # (M,)  == -y / (1 + e^{s}), stable
    return coef[:, None] * phi[None, :] + kappa * Theta


def ce_loss(Theta: np.ndarray, Phi: np.ndarray, y: np.ndarray, kappa: float) -> np.ndarray:
    """CE loss + kappa/2 ||theta||^2 averaged over samples. Returns (M,)."""
    s = y[:, None] * (Phi @ Theta.T)            # (n, M)
    return np.logaddexp(0.0, -s).mean(axis=0) + 0.5 * kappa * (Theta * Theta).sum(axis=1)


def dm_penalty_grad(Theta: np.ndarray, Phi_m: np.ndarray, y_m: np.ndarray,
                    w_m: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Gradient of gamma(theta; D'_-) = (mean_i w_i * min(0, y_i phi_i^T theta))^2.

    w_i = z_i - zbar (zbar over the full constraint set D').
    Returns (grad (M, d), s (M,)) with s the inner mean before squaring.
    """
    U = (Phi_m @ Theta.T) * y_m[:, None]        # (n_m, M) = y_i phi_i^T theta
    neg = (U < 0.0)
    s = (w_m[:, None] * np.minimum(U, 0.0)).mean(axis=0)          # (M,)
    A = w_m[:, None] * y_m[:, None] * Phi_m                       # (n_m, d)
    inner = (neg.astype(np.float64).T @ A) / Phi_m.shape[0]        # (M, d)
    return 2.0 * s[:, None] * inner, s


# --------------------------------------------------------------------------------------
# training (Algorithm 1 / 1')
# --------------------------------------------------------------------------------------
def train_di(Phi_pool: np.ndarray, y_pool: np.ndarray, xt: np.ndarray, eps: float,
             T: int, B: int, kappa: float, eta0: float, eta_a: float,
             rng: np.random.Generator, snapshot_ks: np.ndarray | None = None):
    """Algorithm 1 + Algorithm 2 for DI.  Row 0 of every array is the unperturbed run.

    Returns
    -------
    avg   : (B+1, d) running average theta_bar_T for each trajectory
    snaps : dict k -> (B+1, d) theta_bar_k at requested iterations (main row only stored
            when snapshot_main_only=True; here we store the full matrix for flexibility)
    """
    M = B + 1
    d = Phi_pool.shape[1]
    Theta = np.zeros((M, d))
    U = np.zeros((M, d))
    avg = np.zeros((M, d))

    eta = eta0 * np.power(np.arange(1, T + 1, dtype=np.float64), -eta_a)
    stream = rng.integers(0, len(y_pool), size=T)
    # multipliers: row 0 fixed at 1 (unperturbed), rows 1..B i.i.d. Uniform[1-sqrt3, 1+sqrt3]
    Vs = rng.uniform(1.0 - SQRT3, 1.0 + SQRT3, size=(T, B))
    v = np.empty(M)

    snaps: dict[int, np.ndarray] = {}
    for k in range(1, T + 1):
        # theta_k = Pi_Theta(-u_{k-1})
        theta = slab_projection(-U, xt, eps)
        v[0] = 1.0
        v[1:] = Vs[k - 1]
        i = stream[k - 1]
        grad = ce_grad(theta, Phi_pool[i], float(y_pool[i]), kappa)
        U += eta[k - 1] * v[:, None] * grad
        avg += (theta - avg) / k
        if snapshot_ks is not None and k in snapshot_ks:
            snaps[k] = avg.copy()
    return avg, snaps


def train_dm(Phi_pool: np.ndarray, y_pool: np.ndarray, R2: float,
             Phi_m: np.ndarray, y_m: np.ndarray, w_m: np.ndarray,
             T: int, B: int, kappa: float, eta0: float, eta_a: float,
             rng: np.random.Generator, snapshot_ks: np.ndarray | None = None):
    """Algorithm 1' + Algorithm 2 for DM (penalised SGD, Polyak-Ruppert averaging)."""
    M = B + 1
    d = Phi_pool.shape[1]
    Theta = np.zeros((M, d))
    avg = np.zeros((M, d))

    eta = eta0 * np.power(np.arange(1, T + 1, dtype=np.float64), -eta_a)
    stream = rng.integers(0, len(y_pool), size=T)
    Vs = rng.uniform(1.0 - SQRT3, 1.0 + SQRT3, size=(T, B))
    v = np.empty(M)

    snaps: dict[int, np.ndarray] = {}
    for k in range(1, T + 1):
        grad_ce = ce_grad(Theta, Phi_pool[stream[k - 1]], float(y_pool[stream[k - 1]]), kappa)
        grad_pen, _ = dm_penalty_grad(Theta, Phi_m, y_m, w_m)
        v[0] = 1.0
        v[1:] = Vs[k - 1]
        Theta = Theta - eta[k - 1] * v[:, None] * (grad_ce + R2 * grad_pen)
        avg += (Theta - avg) / k
        if snapshot_ks is not None and k in snapshot_ks:
            snaps[k] = avg.copy()
    return avg, snaps


# --------------------------------------------------------------------------------------
# fairness functionals on a held-out evaluation set
# --------------------------------------------------------------------------------------
def phi_hat(Theta: np.ndarray, Phi_eval: np.ndarray, z_eval: np.ndarray,
            y_eval: np.ndarray | None = None, kind: str = "di") -> np.ndarray:
    """hat phi(theta) for each row of Theta, evaluated on the held-out set.

    kind='di': |P(h=1|z=0) - P(h=1|z=1)|
    kind='dm': |P(h=1|z=0,y=-1) - P(h=1|z=1,y=-1)|
    """
    Theta = np.atleast_2d(Theta)
    pred = (Theta @ Phi_eval.T) > 0.0                         # (M, m)
    if kind == "di":
        mask0 = (z_eval == 0)
        mask1 = (z_eval == 1)
    elif kind == "dm":
        base = (y_eval == -1)
        mask0 = base & (z_eval == 0)
        mask1 = base & (z_eval == 1)
    else:
        raise ValueError(kind)
    p0 = pred[:, mask0].mean(axis=1)
    p1 = pred[:, mask1].mean(axis=1)
    return np.abs(p0 - p1)


# --------------------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------------------
def mis(s: np.ndarray, lo: float, hi: float, alpha: float) -> float:
    """Mean interval score (lower is better); SPEC section 7."""
    s = np.asarray(s, dtype=np.float64)
    N = s.size
    return float((hi - lo)
                 + 2.0 / (N * alpha) * np.maximum(s - hi, 0.0).sum()
                 + 2.0 / (N * alpha) * np.maximum(lo - s, 0.0).sum())


def mean_mis(s: np.ndarray, intervals: np.ndarray, alpha: float) -> float:
    """Average MIS of a collection of intervals against the sample s (paper-style score)."""
    return float(np.mean([mis(s, lo, hi, alpha) for lo, hi in intervals]))


def theoretical_density_curve(sigma: float, centre: float, k: int, grid_size: int = 4001):
    """Return (quantiles-free) normal CDF grid helper -- not used in main pipeline."""
    from scipy.stats import norm
    xs = np.linspace(centre - 6 * sigma, centre + 6 * sigma, grid_size)
    return xs, norm.cdf(xs, loc=centre, scale=sigma)


def w2_to_normal(sample: np.ndarray, centre: float, sigma: float) -> float:
    """1-D Wasserstein-2 distance between the empirical sample and N(centre, sigma^2).

    Computed exactly by integrating |F_emp^{-1}(u) - F_norm^{-1}(u)|^2 du on a fine
    grid of quantile levels (equivalent to scipy.stats.wasserstein_distance against
    the theoretical quantile function).
    """
    from scipy.stats import norm
    sample = np.sort(np.asarray(sample, dtype=np.float64))
    if sigma <= 0:
        return float(np.abs(sample - centre).mean())
    N = sample.size
    u = (np.arange(N, dtype=np.float64) + 0.5) / N
    # empirical quantile function on u; theoretical normal quantile on u
    q_emp = sample
    q_theo = norm.ppf(u) * sigma + centre
    return float(np.sqrt(np.mean((q_emp - q_theo) ** 2)))


def w2_empirical_vs_normal(sample: np.ndarray, centre: float, sigma: float) -> float:
    """Alternative W2 via scipy on a dense theoretical sample (cross-check)."""
    from scipy.stats import norm
    if sigma <= 0:
        return float(np.abs(np.mean(sample) - centre))
    theo = norm.ppf((np.arange(10000) + 0.5) / 10000) * sigma + centre
    return float(wasserstein_distance(sample, theo))
