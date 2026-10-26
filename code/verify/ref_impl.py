"""Independent reference implementation, rebuilt from SPEC.md only.

Project: fuq-fairness (Roy & Mohapatra, "Fairness Uncertainty Quantification:
A Constrained Stochastic Optimization Perspective", UAI 2026).

Author: theory-check (independent verifier).  This module deliberately does NOT
import anything from ``code/core/`` -- it is the independent oracle used to
check the Lead's implementation.

Implemented (SPEC section in parentheses)
-----------------------------------------
* slab projection onto Theta = {theta : |xt~^T theta| <= eps}         (Sec. 3)
* DI-aware stochastic dual averaging (SDA), averaged iterate           (Sec. 3)
* DM-aware penalised-SGD objective/gradient (gamma, grad gamma)        (Sec. 4)
* online multiplier bootstrap, V ~ Unif[1-sqrt3, 1+sqrt3]              (Sec. 5)
* synthetic DI / DM data-generating processes                          (Sec. 6)
* MIS interval score                                                   (Sec. 7)

Conventions
-----------
* features phi(x) = [1, x_1, ..., x_p]  (intercept FIRST), d = p + 1.
* theta_1 = 0 (u_0 = 0), theta_k = Pi_Theta(-u_{k-1}),
  u_k = u_{k-1} + eta_k * grad_loss(theta_k; W_k), eta_k = 0.01 * k**(-0.501).
* theta_bar_T = (1/T) sum_{k=1..T} theta_k.

Built-in smoke test:  ``python ref_impl.py``
"""
from __future__ import annotations

import math

import numpy as np

KAPPA = 1e-4          # ridge coefficient (SPEC Sec. 3)
ETA_C = 0.01          # step-size constant (SPEC Sec. 3)
ETA_ALPHA = 0.501     # step-size exponent (SPEC Sec. 3)
ALPHA_CI = 0.05       # nominal miscoverage (SPEC Sec. 6)


# ---------------------------------------------------------------------------
# 1. slab projection  (SPEC Sec. 3)
# ---------------------------------------------------------------------------
def slab_project(v, xt, eps):
    """Euclidean projection of v onto Theta = {theta : |xt^T theta| <= eps}.

    P(v) = v - alpha*xt, with
        alpha = (xt^T v - eps) / ||xt||^2   if xt^T v >  eps
        alpha = (xt^T v + eps) / ||xt||^2   if xt^T v < -eps
        alpha = 0                           otherwise.
    """
    v = np.asarray(v, dtype=np.float64)
    xt = np.asarray(xt, dtype=np.float64)
    xtv = float(xt @ v)
    nrm2 = float(xt @ xt)
    if xtv > eps:
        alpha = (xtv - eps) / nrm2
    elif xtv < -eps:
        alpha = (xtv + eps) / nrm2
    else:
        alpha = 0.0
    return v - alpha * xt


def slab_project_batch(V, xt, eps):
    """Row-wise slab projection.  V : (B, d) -> (B, d)."""
    V = np.asarray(V, dtype=np.float64)
    xt = np.asarray(xt, dtype=np.float64)
    xtv = V @ xt                          # (B,)
    nrm2 = float(xt @ xt)
    alpha = np.zeros_like(xtv)
    hi = xtv > eps
    lo = xtv < -eps
    alpha[hi] = (xtv[hi] - eps) / nrm2
    alpha[lo] = (xtv[lo] + eps) / nrm2
    return V - alpha[:, None] * xt[None, :]


# ---------------------------------------------------------------------------
# 2. features and synthetic DGPs  (SPEC Sec. 6)
# ---------------------------------------------------------------------------
def phi_features(X):
    """phi(x) = [1, x] -> shape (n, p+1); intercept FIRST."""
    X = np.atleast_2d(np.asarray(X, dtype=np.float64))
    return np.column_stack([np.ones(X.shape[0]), X])


SIGMA1_DI = np.array([[0.4, 0.2], [0.2, 0.3]], dtype=np.float64)
SIGMA2_DI = np.array([[0.6, 0.1], [0.1, 0.4]], dtype=np.float64)
ROT_PI_3 = np.array(
    [[math.cos(math.pi / 3.0), -math.sin(math.pi / 3.0)],
     [math.sin(math.pi / 3.0), math.cos(math.pi / 3.0)]],
    dtype=np.float64,
)
MU_DI = np.array([1.5, 1.5], dtype=np.float64)


def _mvn_logpdf(z, mean, cov):
    """log N(z; mean, cov) for z of shape (..., 2); cov (2,2)."""
    z = np.asarray(z, dtype=np.float64)
    cov = np.asarray(cov, dtype=np.float64)
    diff = z - mean
    sign, logdet = np.linalg.slogdet(cov)
    inv = np.linalg.inv(cov)
    quad = np.einsum("...i,ij,...j->...", diff, inv, diff)
    d = z.shape[-1]
    return -0.5 * (d * math.log(2.0 * math.pi) + logdet + quad)


def make_di_dgp(n, rng):
    """Synthetic DI DGP of SPEC Sec. 6 (Zafar et al. 2019 style).

    x|y=+1 ~ N((1.5,1.5), Sigma1), x|y=-1 ~ N((-1.5,-1.5), Sigma2),
    P(z=1|x) = f1(x') / (f1(x') + f_{-1}(x')),  x' = Rot(pi/3) x,
    y uniform on {-1, +1}.

    Returns
    -------
    X : (n, 2) float64
    y : (n,) int8 in {-1, +1}
    z : (n,) int8 in {0, 1}
    """
    rng = np.random.default_rng(rng) if not isinstance(rng, np.random.Generator) else rng
    n = int(n)
    y = rng.choice(np.array([-1, 1], dtype=np.int64), size=n)
    x = np.empty((n, 2), dtype=np.float64)
    m1 = y == 1
    n1 = int(m1.sum())
    x[m1] = rng.multivariate_normal(MU_DI, SIGMA1_DI, size=n1)
    x[~m1] = rng.multivariate_normal(-MU_DI, SIGMA2_DI, size=n - n1)
    xp = x @ ROT_PI_3.T
    lf1 = _mvn_logpdf(xp, MU_DI, SIGMA1_DI)
    lf2 = _mvn_logpdf(xp, -MU_DI, SIGMA2_DI)
    # P(z=1) = f1 / (f1 + f_{-1}) = sigmoid(lf1 - lf2)
    p1 = 1.0 / (1.0 + np.exp(-(lf1 - lf2)))
    z = (rng.random(n) < p1).astype(np.int64)
    y = y.astype(np.int64)
    return x, y, z


SIGMA1_DM = np.array([[3.0, 1.0], [1.0, 3.0]], dtype=np.float64)


def make_dm_dgp(n, rng):
    """Synthetic DM DGP of SPEC Sec. 6 (Zafar style).

    rho(x|z=0,y=+1) = rho(x|z=1,y=+1) = N((2,2), Sigma1)
    rho(x|z=0,y=-1) = N((1,1), Sigma1)
    rho(x|z=1,y=-1) = N((-2,-2), Sigma1)
    y uniform on {-1,+1} (then z is implied by the conditional above).

    Returns X (n,2), y (n,), z (n,).
    """
    rng = np.random.default_rng(rng) if not isinstance(rng, np.random.Generator) else rng
    n = int(n)
    y = rng.choice(np.array([-1, 1], dtype=np.int64), size=n)
    z = rng.integers(0, 2, size=n)
    x = np.empty((n, 2), dtype=np.float64)
    for yy, zz, mu in (
        (1, 0, np.array([2.0, 2.0])),
        (1, 1, np.array([2.0, 2.0])),
        (-1, 0, np.array([1.0, 1.0])),
        (-1, 1, np.array([-2.0, -2.0])),
    ):
        m = (y == yy) & (z == zz)
        nm = int(m.sum())
        if nm:
            x[m] = rng.multivariate_normal(mu, SIGMA1_DM, size=nm)
    return x, y.astype(np.int64), z.astype(np.int64)


# ---------------------------------------------------------------------------
# 3. constraint vector x~  (SPEC Sec. 3)
# ---------------------------------------------------------------------------
def di_constraint_vector(Phi, z):
    """xt~ = (1/n_c) sum_i (z_i - zbar) phi(x_i)   (SPEC Sec. 3)."""
    Phi = np.asarray(Phi, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    zbar = float(z.mean())
    return ((z - zbar)[:, None] * Phi).mean(axis=0)


# ---------------------------------------------------------------------------
# 4. losses / gradients
# ---------------------------------------------------------------------------
def _softplus(x):
    """log(1 + exp(x)), numerically stable."""
    return np.logaddexp(0.0, x)


def ce_loss(theta, Phi, y, kappa=KAPPA):
    """(1/n) sum_i log(1+exp(-y_i phi_i^T theta)) + kappa/2 ||theta||^2."""
    theta = np.asarray(theta, dtype=np.float64)
    Phi = np.asarray(Phi, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = y * (Phi @ theta)
    return float(np.mean(_softplus(-z))) + 0.5 * kappa * float(theta @ theta)


def ce_sample_grad(theta, phi_x, y, kappa=KAPPA):
    """Single-sample CE gradient: -y phi(x) / (1+exp(y theta^T phi(x))) + kappa theta."""
    theta = np.asarray(theta, dtype=np.float64)
    phi_x = np.asarray(phi_x, dtype=np.float64)
    z = float(y * (phi_x @ theta))
    # 1/(1+exp(z)) evaluated stably
    if z >= 0.0:
        sig = math.exp(-z) / (1.0 + math.exp(-z))
    else:
        sig = 1.0 / (1.0 + math.exp(z))
    return (-float(y) * sig) * phi_x + kappa * theta


def ce_mean_grad(theta, Phi, y, kappa=KAPPA):
    """Full-batch (sample-average) CE gradient."""
    theta = np.asarray(theta, dtype=np.float64)
    Phi = np.asarray(Phi, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = y * (Phi @ theta)
    # -y * sigmoid(-z) = -y / (1 + exp(z))
    sig_neg = 0.5 * (1.0 - np.tanh(0.5 * z))  # sigmoid(-z) = 1/(1+e^z)
    G = (Phi * (-y * sig_neg)[:, None]).mean(axis=0)
    return G + kappa * theta


# ---------------------------------------------------------------------------
# 5. DM penalty gamma and its gradient  (SPEC Sec. 4)
# ---------------------------------------------------------------------------
def dm_terms(theta, Phi, y, z, ):
    """Return (s, grad_gamma) for the DM penalty of SPEC Sec. 4.

    D' is the constraint set (all given rows), D'_- = {i in D' : y_i = -1},
    n_c^- = |D'_-|, zbar is computed over all of D' (not only D'_-):

        s(theta)      = 1/n_c^- sum_{i in D'_-} (z_i - zbar) min(0, y_i phi_i^T theta)
        grad_gamma(th)= 2 s(theta) * 1/n_c^- sum_{i in D'_-: y_i phi_i^T theta < 0}
                                            (z_i - zbar) y_i phi_i

    The DM objective is  F(theta) = ell(theta) + R^2 * gamma(theta)  with
    gamma = s(theta)^2.
    """
    theta = np.asarray(theta, dtype=np.float64)
    Phi = np.asarray(Phi, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    zbar = float(z.mean())                       # over all of D'
    neg = y == -1.0
    Phi_n = Phi[neg]
    y_n = y[neg]
    zc_n = (z[neg] - zbar)
    nneg = int(neg.sum())
    if nneg == 0:
        return 0.0, np.zeros_like(theta)
    margins = y_n * (Phi_n @ theta)              # y_i phi_i^T theta
    active = margins < 0.0
    s = float(np.dot(zc_n, np.minimum(margins, 0.0)) / nneg)
    if active.any():
        g = (zc_n[active] * y_n[active])[:, None] * Phi_n[active]
        grad = 2.0 * s * g.sum(axis=0) / nneg
    else:
        grad = np.zeros_like(theta)
    return s, grad


def dm_penalty(theta, Phi, y, z):
    s, _ = dm_terms(theta, Phi, y, z)
    return s * s


def dm_objective(theta, Phi, y, z, kappa=KAPPA, R2=1.0):
    """F(theta) = ell(theta) + R^2 gamma(theta)."""
    return ce_loss(theta, Phi, y, kappa) + R2 * dm_penalty(theta, Phi, y, z)


def dm_objective_grad(theta, Phi, y, z, kappa=KAPPA, R2=1.0):
    _, g = dm_terms(theta, Phi, y, z)
    return ce_mean_grad(theta, Phi, y, kappa) + R2 * g


# ---------------------------------------------------------------------------
# 6. step sizes, multipliers, averaging  (SPEC Sec. 3, 5)
# ---------------------------------------------------------------------------
def eta_spec(k, c=ETA_C, alpha=ETA_ALPHA):
    """eta_k = 0.01 * k**(-0.501), k >= 1."""
    return c * float(k) ** (-alpha)


def eta_array(T, c=ETA_C, alpha=ETA_ALPHA):
    k = np.arange(1, T + 1, dtype=np.float64)
    return c * k ** (-alpha)


def sample_multipliers(rng, size):
    """V ~ Unif[1-sqrt3, 1+sqrt3] (mean 1, variance 1)."""
    rng = np.random.default_rng(rng) if not isinstance(rng, np.random.Generator) else rng
    lo = 1.0 - math.sqrt(3.0)
    hi = 1.0 + math.sqrt(3.0)
    return rng.uniform(lo, hi, size=size)


# ---------------------------------------------------------------------------
# 7. DI-aware SDA  (SPEC Sec. 3) and online multiplier bootstrap (Sec. 5)
# ---------------------------------------------------------------------------
def sda_di(Phi_stream, y_stream, xt, eps, kappa=KAPPA, theta0=None, u0=None,
           eta_fn=eta_spec, T=None):
    """Single-trajectory DI-aware SDA (SPEC Algorithm 1).

    Parameters
    ----------
    Phi_stream : (T, d) feature rows phi(x_k) of the i.i.d. stream W_k
    y_stream   : (T,)   labels of the stream
    xt, eps    : constraint vector x~ and radius epsilon of Theta
    theta0     : initial theta (default 0, unused: theta_1 = Pi(-u_0))
    u0         : initial dual (default 0)
    eta_fn     : callable k -> eta_k

    Returns
    -------
    theta_bar : (d,) averaged iterate (1/T) sum_{k=1..T} theta_k
    theta_path : (T, d) all iterates theta_k  (only if T is not huge; caller may
                 prefer a memoryless version via ``return_path=False``)
    """
    Phi_stream = np.asarray(Phi_stream, dtype=np.float64)
    y_stream = np.asarray(y_stream, dtype=np.float64)
    d = Phi_stream.shape[1]
    T = int(Phi_stream.shape[0] if T is None else T)
    u = np.zeros(d) if u0 is None else np.asarray(u0, dtype=np.float64).copy()
    avg = np.zeros(d)
    for k in range(1, T + 1):
        theta = slab_project(-u, xt, eps)
        avg += theta
        phi_x = Phi_stream[k - 1]
        z = float(y_stream[k - 1] * (phi_x @ theta))
        if z >= 0.0:
            sig = math.exp(-z) / (1.0 + math.exp(-z))
        else:
            sig = 1.0 / (1.0 + math.exp(z))
        g = (-float(y_stream[k - 1]) * sig) * phi_x + kappa * theta
        u = u + eta_fn(k) * g
    return avg / T


def sda_di_path(Phi_stream, y_stream, xt, eps, kappa=KAPPA, u0=None, eta_fn=eta_spec):
    """Like ``sda_di`` but also returns the full theta path (memory O(T*d))."""
    Phi_stream = np.asarray(Phi_stream, dtype=np.float64)
    y_stream = np.asarray(y_stream, dtype=np.float64)
    T, d = Phi_stream.shape
    u = np.zeros(d) if u0 is None else np.asarray(u0, dtype=np.float64).copy()
    path = np.empty((T, d))
    for k in range(1, T + 1):
        theta = slab_project(-u, xt, eps)
        path[k - 1] = theta
        phi_x = Phi_stream[k - 1]
        z = float(y_stream[k - 1] * (phi_x @ theta))
        if z >= 0.0:
            sig = math.exp(-z) / (1.0 + math.exp(-z))
        else:
            sig = 1.0 / (1.0 + math.exp(z))
        g = (-float(y_stream[k - 1]) * sig) * phi_x + kappa * theta
        u = u + eta_fn(k) * g
    return path


def sda_di_bootstrap(Phi_stream, y_stream, xt, eps, V_stream, kappa=KAPPA,
                     u0=None, eta_fn=eta_spec):
    """Online multiplier bootstrap for DI, all B trajectories sharing one stream.

    SPEC Algorithm 2:
        theta^b_k = Pi_Theta(-u^b_{k-1}),
        u^b_k     = u^b_{k-1} + eta_k * V^b_k * grad ell(theta^b_k; W_k),
    with the SAME W_k for all b (vectorised implementation required).

    Parameters
    ----------
    Phi_stream : (T, d)
    y_stream   : (T,)
    V_stream   : (T, B) multipliers, V^b_k ~ Unif[1-sqrt3, 1+sqrt3]
    u0         : (B, d) or (d,) or None (zeros)

    Returns
    -------
    theta_bar_B : (B, d)  average (1/T) sum_k theta^b_k for each b.
    """
    Phi_stream = np.asarray(Phi_stream, dtype=np.float64)
    y_stream = np.asarray(y_stream, dtype=np.float64)
    V_stream = np.asarray(V_stream, dtype=np.float64)
    T, d = Phi_stream.shape
    B = V_stream.shape[1]
    if u0 is None:
        U = np.zeros((B, d))
    else:
        U = np.zeros((B, d)) + np.asarray(u0, dtype=np.float64)
    avg = np.zeros((B, d))
    for k in range(1, T + 1):
        Theta = slab_project_batch(-U, xt, eps)          # (B,d)
        avg += Theta
        phi_x = Phi_stream[k - 1]
        y = y_stream[k - 1]
        z = y * (Theta @ phi_x)                          # (B,)
        # sigmoid(-z) = 1/(1+exp(z)) stably, elementwise
        sig_neg = 0.5 * (1.0 - np.tanh(0.5 * z))
        G = (-y * sig_neg)[:, None] * phi_x[None, :] + kappa * Theta
        U = U + eta_fn(k) * V_stream[k - 1][:, None] * G
    return avg / T


def sda_di_shared_run(Phi_stream, y_stream, xt, eps, B, rng, kappa=KAPPA,
                      eta_fn=eta_spec):
    """Convenience: main trajectory + B bootstrap trajectories on one stream.

    The multipliers are drawn inside as V_stream = sample_multipliers(rng, (T,B)).
    Returns (theta_bar_main (d,), theta_bar_boot (B, d), V_stream (T,B)).
    """
    Phi_stream = np.asarray(Phi_stream, dtype=np.float64)
    T = Phi_stream.shape[0]
    V_stream = sample_multipliers(rng, size=(T, B))
    theta_main = sda_di(Phi_stream, y_stream, xt, eps, kappa=kappa, eta_fn=eta_fn)
    theta_boot = sda_di_bootstrap(Phi_stream, y_stream, xt, eps, V_stream,
                                  kappa=kappa, eta_fn=eta_fn)
    return theta_main, theta_boot, V_stream


# ---------------------------------------------------------------------------
# 8. bootstrap CI and MIS  (SPEC Sec. 5, 7)
# ---------------------------------------------------------------------------
def bootstrap_ci(values, alpha=ALPHA_CI):
    """(1-alpha) percentile CI = [q_{alpha/2}, q_{1-alpha/2}] of ``values``."""
    values = np.asarray(values, dtype=np.float64)
    lo = float(np.quantile(values, alpha / 2.0))
    hi = float(np.quantile(values, 1.0 - alpha / 2.0))
    return lo, hi


def mis(l, u, s, alpha):
    """Mean interval score (SPEC Sec. 7), lower score = better.

    MIS = (u-l) + 2/(N alpha) sum_i (s_i-u) 1[s_i>u]
                + 2/(N alpha) sum_i (l-s_i) 1[s_i<l].
    """
    s = np.asarray(s, dtype=np.float64)
    l = float(l)
    u = float(u)
    n = s.size
    above = np.maximum(s - u, 0.0)
    below = np.maximum(l - s, 0.0)
    return float(u - l) + float(2.0 * above.sum() / (n * alpha)) \
        + float(2.0 * below.sum() / (n * alpha))


# ---------------------------------------------------------------------------
# 9. small utilities
# ---------------------------------------------------------------------------
def rel_err(a, b, eps_floor=1e-300):
    """||a-b|| / max(||b||, eps_floor)."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return float(np.linalg.norm(a - b) / max(np.linalg.norm(b), eps_floor))


def fd_grad(fun, theta, h=1e-6):
    """Central finite-difference gradient of scalar fun at theta."""
    theta = np.asarray(theta, dtype=np.float64)
    d = theta.size
    g = np.zeros(d)
    for i in range(d):
        e = np.zeros(d)
        e[i] = h
        g[i] = (fun(theta + e) - fun(theta - e)) / (2.0 * h)
    return g


# ---------------------------------------------------------------------------
# 10. built-in smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    rng = np.random.default_rng(0)
    xt = np.array([0.8, 0.6, 0.0])
    eps = 0.1
    v = rng.normal(size=3) * 2.0
    pv = slab_project(v, xt, eps)
    print(f"[projection] xt^T v = {xt @ v:+.6f}  -> xt^T P v = {xt @ pv:+.6f}"
          f"  (eps={eps})  |xt^T Pv|<=eps+1e-10: {abs(xt @ pv) <= eps + 1e-10}")

    X, y, z = make_di_dgp(200, rng)
    Phi = phi_features(X)
    xt_di = di_constraint_vector(Phi, z)
    print(f"[DGP DI] n=200, y mean={y.mean():+.3f}, z mean={z.mean():+.3f}, "
          f"xt~ = {np.array2string(xt_di, precision=5)}")

    Xd, yd, zd = make_dm_dgp(200, rng)
    Phid = phi_features(Xd)
    th = rng.normal(size=3) * 0.5
    s, g = dm_terms(th, Phid, yd, zd)
    gfd = fd_grad(lambda t: dm_penalty(t, Phid, yd, zd), th)
    print(f"[DM] s={s:+.6e}  ||grad_gamma - FD|| = "
          f"{np.linalg.norm(g - gfd):.3e}")

    V = sample_multipliers(rng, size=20)
    print(f"[multipliers] sample mean={V.mean():+.4f} var={V.var(ddof=1):.4f}")

    print("[MIS] mis(l=0,u=3,s=[1,2,10],alpha=0.1) =",
          mis(0.0, 3.0, [1.0, 2.0, 10.0], 0.1))
    print("smoke test done.")
