"""Multilevel logistic regression fitted by full maximum likelihood with adaptive Gauss-Hermite quadrature.

The model of Moineddin, Matheson and Glazier (2007), equation (2), in general form:

    logit P(y_ij = 1) = X_ij beta + Z_ij b_j,    b_j ~ N(0, D),

with q = 1 or 2 random effects per group (an intercept, a slope, or both). The fit follows what the paper
says of SAS PROC NLMIXED (Methods): full maximum likelihood, normal random effects, adaptive Gaussian
quadrature with the number of points chosen automatically at the starting values, a dual quasi-Newton
(BFGS) optimizer started at the given values, at most 200 iterations.

The variance parameters are the variances and the covariance themselves, unconstrained, as in an NLMIXED
statement ``random u0 u1 ~ normal([0, 0], [s0, c01, s1])``: a trial point whose D is not positive definite
has no likelihood, and the line search steps back from it. When the maximum lies on the boundary (a
variance at zero) the optimizer cannot meet its gradient criteria and the fit ends without converging.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# NLMIXED's search sequence for the number of quadrature points per dimension (QPOINTS not given)
QPOINT_SEQUENCE = (1, 3, 5, 7, 9, 11, 21, 31)
QTOL = 1e-4          # NLMIXED QTOL default
ABSGCONV = 1e-5      # NLMIXED default absolute gradient criterion
GCONV = 1e-8         # NLMIXED default relative gradient criterion
MAXITER = 200        # paper: "the maximum number of iterations was 200"
MAXFUNC = 500        # NLMIXED MAXFUNC default for quasi-Newton
ABSXCONV = 1e-8      # paper: "the absolute value for parameter convergence criterion was 10^-8"
_LOG2PI = math.log(2.0 * math.pi)


@dataclass
class GroupedData:
    """Data padded to groups x max group size; ``mask`` marks real observations."""

    y: np.ndarray       # (J, m)
    X: np.ndarray       # (J, m, p) fixed-effect design
    Z: np.ndarray       # (J, m, q) random-effect design
    mask: np.ndarray    # (J, m) 1.0 for an observation, 0.0 for padding
    fixed_names: list = field(default_factory=list)
    random_names: list = field(default_factory=list)

    @property
    def p(self):
        return self.X.shape[2]

    @property
    def q(self):
        return self.Z.shape[2]

    @property
    def n_obs(self):
        return int(self.mask.sum())


def group_data(y, X, Z, groups, fixed_names=None, random_names=None) -> GroupedData:
    """Pad long-format data (one row per observation) into a GroupedData.

    y: (N,) 0/1 outcome; X: (N, p) fixed-effect design; Z: (N, q) random-effect design; groups: (N,) labels.
    """
    y = np.asarray(y, float)
    X = np.atleast_2d(np.asarray(X, float))
    Z = np.asarray(Z, float)
    if Z.ndim == 1:
        Z = Z[:, None]
    if X.shape[0] != y.size:
        X = X.T
    groups = np.asarray(groups)
    if not (X.shape[0] == Z.shape[0] == groups.size == y.size):
        raise ValueError("y, X, Z and groups must have one row per observation")
    if not np.all((y == 0) | (y == 1)):
        raise ValueError("y must be 0 or 1")
    if Z.shape[1] not in (1, 2):
        raise ValueError("only 1 or 2 random effects per group are supported")
    labels, inv = np.unique(groups, return_inverse=True)
    J = labels.size
    counts = np.bincount(inv, minlength=J)
    m = counts.max()
    order = np.argsort(inv, kind="stable")
    pos = np.empty(y.size, int)
    starts = np.concatenate([[0], np.cumsum(counts)[:-1]])
    pos[order] = np.arange(y.size) - np.repeat(starts, counts)
    Yp = np.zeros((J, m))
    Xp = np.zeros((J, m, X.shape[1]))
    Zp = np.zeros((J, m, Z.shape[1]))
    Mp = np.zeros((J, m))
    Yp[inv, pos] = y
    Xp[inv, pos] = X
    Zp[inv, pos] = Z
    Mp[inv, pos] = 1.0
    return GroupedData(Yp, Xp, Zp, Mp,
                       list(fixed_names or [f"b{i}" for i in range(X.shape[1])]),
                       list(random_names or [f"u{i}" for i in range(Z.shape[1])]))


# ---------------------------------------------------------------- variance parameters

def n_cov_params(q, cov):
    return 3 if (q == 2 and cov) else q


def cov_param_names(random_names, cov):
    q = len(random_names)
    if q == 1:
        return [f"var({random_names[0]})"]
    if cov:
        return [f"var({random_names[0]})", f"cov({random_names[0]};{random_names[1]})", f"var({random_names[1]})"]
    return [f"var({random_names[0]})", f"var({random_names[1]})"]


def build_D(theta_d, q, cov):
    """D from the variance parameters: [s] (q=1), [s0, s1] (q=2, independent) or [s0, c01, s1]."""
    if q == 1:
        return np.array([[theta_d[0]]])
    if cov:
        return np.array([[theta_d[0], theta_d[1]], [theta_d[1], theta_d[2]]])
    return np.diag(theta_d[:2])


def _chol(D):
    """Cholesky factor of D, or None when D is not positive definite."""
    if D.shape[0] == 1:
        return np.sqrt(D) if D[0, 0] > 0 else None
    if not (D[0, 0] > 0 and D[0, 0] * D[1, 1] - D[0, 1] ** 2 > 0):
        return None
    return _chol_small(D)


def _mm(A, B):
    """Small matrix product with NumPy's own loops (no BLAS), so results do not depend on the CPU's kernels."""
    return np.einsum("ij,jk->ik", A, B)


def _mv(A, v):
    return np.einsum("ij,j->i", A, v)


def _dot(a, b):
    return float(np.einsum("i,i->", a, b))


def _inv_small(H):
    """Inverse of a stack of 1x1 or 2x2 symmetric matrices (closed form, no LAPACK)."""
    if H.shape[-1] == 1:
        return 1.0 / H
    a, b, d = H[..., 0, 0], H[..., 0, 1], H[..., 1, 1]
    det = a * d - b * b
    out = np.empty_like(H)
    out[..., 0, 0] = d / det
    out[..., 1, 1] = a / det
    out[..., 0, 1] = out[..., 1, 0] = -b / det
    return out


def _chol_small(A):
    """Lower Cholesky factor of a stack of 1x1 or 2x2 positive definite matrices (closed form)."""
    if A.shape[-1] == 1:
        return np.sqrt(A)
    l11 = np.sqrt(A[..., 0, 0])
    l21 = A[..., 1, 0] / l11
    l22 = np.sqrt(A[..., 1, 1] - l21 * l21)
    L = np.zeros_like(A)
    L[..., 0, 0], L[..., 1, 0], L[..., 1, 1] = l11, l21, l22
    return L


# ---------------------------------------------------------------- quadrature

def gh_nodes(Q, q):
    """Tensor Gauss-Hermite nodes t (K, q) and log weights for the weight function exp(-t't)."""
    t1, w1 = np.polynomial.hermite.hermgauss(Q)
    grids = np.meshgrid(*([t1] * q), indexing="ij")
    t = np.stack([g.ravel() for g in grids], axis=1)
    lw = sum(np.log(w1)[idx.ravel()] for idx in np.meshgrid(*([np.arange(Q)] * q), indexing="ij"))
    return t, np.asarray(lw)


def _log1pexp(x):
    return np.logaddexp(0.0, x)


def _expit(x):
    """1 / (1 + exp(-x)); exp overflows to inf for x below about -709, which gives the right 0."""
    with np.errstate(over="ignore"):
        return 1.0 / (1.0 + np.exp(-x))


def _modes(data, beta, D, b0=None, tol=1e-10, maxit=100):
    """Posterior modes of b_j and the negative Hessian there, for every group at once (Newton, step halving)."""
    J, q = data.y.shape[0], data.q
    Dinv = _inv_small(D)
    eta0 = np.einsum("jmp,p->jm", data.X, beta)                                           # (J, m)
    b = np.zeros((J, q)) if b0 is None else b0.copy()

    def obj(b):
        lin = eta0 + np.einsum("jmq,jq->jm", data.Z, b)
        ll = (data.mask * (data.y * lin - _log1pexp(lin))).sum(1)
        return ll - 0.5 * np.einsum("jq,qr,jr->j", b, Dinv, b)

    f = obj(b)
    for _ in range(maxit):
        lin = eta0 + np.einsum("jmq,jq->jm", data.Z, b)
        pr = _expit(lin)
        r = data.mask * (data.y - pr)
        g = np.einsum("jm,jmq->jq", r, data.Z) - np.einsum("jq,qr->jr", b, Dinv)
        w = data.mask * pr * (1.0 - pr)
        H = np.einsum("jm,jmq,jmr->jqr", w, data.Z, data.Z) + Dinv
        step = np.einsum("jqr,jr->jq", _inv_small(H), g)
        alpha = np.ones(J)
        for _h in range(30):
            bn = b + alpha[:, None] * step
            fn = obj(bn)
            bad = fn < f - 1e-12 * (1 + np.abs(f))
            if not bad.any():
                break
            alpha = np.where(bad, alpha * 0.5, alpha)
        b, f = bn, fn
        if np.max(np.abs(alpha[:, None] * step)) < tol:
            break
    lin = eta0 + np.einsum("jmq,jq->jm", data.Z, b)
    pr = _expit(lin)
    w = data.mask * pr * (1.0 - pr)
    H = np.einsum("jm,jmq,jmr->jqr", w, data.Z, data.Z) + Dinv
    return b, H


@dataclass
class Grid:
    """Adaptive quadrature nodes b_jk (J, K, q) and their log weights (J, K), fixed between adaptations."""

    nodes: np.ndarray
    logw: np.ndarray
    modes: np.ndarray
    Q: int


def adapt(data, beta, D, Q, b0=None) -> Grid:
    t, lwt = gh_nodes(Q, data.q)
    mu, H = _modes(data, beta, D, b0)
    L = _chol_small(_inv_small(H))                                  # (J, q, q)
    nodes = mu[:, None, :] + math.sqrt(2.0) * np.einsum("jqr,kr->jkq", L, t)
    logdetL = np.log(np.diagonal(L, axis1=1, axis2=2)).sum(1)       # (J,)
    logw = lwt[None, :] + (t * t).sum(1)[None, :] + 0.5 * data.q * math.log(2.0) + logdetL[:, None]
    return Grid(nodes, logw, mu, Q)


def _node_terms(data, beta, D, grid):
    """Log integrand at each node (J, K) and the quantities its gradient needs."""
    C = _chol(D)
    if C is None:
        return None
    eta0 = np.einsum("jmp,p->jm", data.X, beta)                                           # (J, m)
    lin = eta0[:, :, None] + np.einsum("jmq,jkq->jmk", data.Z, grid.nodes)
    ll = (data.mask[:, :, None] * (data.y[:, :, None] * lin - _log1pexp(lin))).sum(1)   # (J, K)
    Dinv = _inv_small(D)
    logdet = 2.0 * np.log(np.diag(C)).sum()
    quad = np.einsum("jkq,qr,jkr->jk", grid.nodes, Dinv, grid.nodes)
    lphi = -0.5 * (data.q * _LOG2PI + logdet + quad)
    return lin, ll + lphi + grid.logw, Dinv


def loglik_grid(theta, data, cov, grid, with_grad=False):
    """Log-likelihood on fixed nodes (and its exact gradient for those nodes). None if D is not PD."""
    p, q = data.p, data.q
    beta = theta[:p]
    D = build_D(theta[p:], q, cov)
    terms = _node_terms(data, beta, D, grid)
    if terms is None:
        return (None, None) if with_grad else None
    lin, a, Dinv = terms
    amax = a.max(1, keepdims=True)
    s = np.exp(a - amax)
    tot = s.sum(1, keepdims=True)
    ll = float((amax[:, 0] + np.log(tot[:, 0])).sum())
    if not with_grad:
        return ll
    pi = s / tot                                                   # (J, K)
    pr = _expit(lin)                                # (J, m, K)
    r = (data.mask[:, :, None] * (data.y[:, :, None] - pr) * pi[:, None, :]).sum(2)   # (J, m)
    g_beta = np.einsum("jm,jmp->p", r, data.X)
    S = np.einsum("jk,jkq,jkr->qr", pi, grid.nodes, grid.nodes)
    J = data.y.shape[0]
    G = 0.5 * (_mm(_mm(Dinv, S), Dinv) - J * Dinv)
    if q == 1:
        g_d = [G[0, 0]]
    elif cov:
        g_d = [G[0, 0], 2.0 * G[0, 1], G[1, 1]]
    else:
        g_d = [G[0, 0], G[1, 1]]
    return ll, np.concatenate([g_beta, g_d])


def loglik(theta, data, cov=False, Q=None):
    """Adaptive Gauss-Hermite log-likelihood at theta (nodes centred and scaled at theta's modes)."""
    theta = np.asarray(theta, float)
    p, q = data.p, data.q
    D = build_D(theta[p:], q, cov)
    if _chol(D) is None:
        return None
    if Q is None:
        Q = select_qpoints(theta, data, cov)
    return loglik_grid(theta, data, cov, adapt(data, theta[:p], D, Q))


def select_qpoints(theta0, data, cov=False, qtol=QTOL, sequence=QPOINT_SEQUENCE, pick="second"):
    """NLMIXED's automatic choice: evaluate the log-likelihood at the starting values with 1, 3, 5, ...
    points per dimension until two successive values differ by less than qtol (relative). ``pick`` says
    which of the two is used: "second" (the larger, default) or "first"."""
    theta0 = np.asarray(theta0, float)
    p, q = data.p, data.q
    D = build_D(theta0[p:], q, cov)
    if _chol(D) is None:
        raise ValueError("starting values give a covariance matrix that is not positive definite")
    prev, prevQ = None, None
    for Q in sequence:
        ll = loglik_grid(theta0, data, cov, adapt(data, theta0[:p], D, Q))
        if prev is not None and abs(ll - prev) / max(abs(ll), 1e-300) < qtol:
            return Q if pick == "second" else prevQ
        prev, prevQ = ll, Q
    return sequence[-1]


# ---------------------------------------------------------------- fit

@dataclass
class Fit:
    names: list
    estimate: np.ndarray
    se: np.ndarray
    converged: bool
    status: str
    iterations: int
    function_calls: int
    loglik: float
    qpoints: int
    hessian_pd: bool
    max_abs_gradient: float
    cov: bool

    def as_dict(self):
        return {"names": list(self.names), "estimate": [float(v) for v in self.estimate],
                "se": [None if not np.isfinite(v) else float(v) for v in self.se],
                "converged": bool(self.converged), "status": self.status, "iterations": int(self.iterations),
                "function_calls": int(self.function_calls), "loglik": float(self.loglik),
                "qpoints": int(self.qpoints), "hessian_pd": bool(self.hessian_pd),
                "max_abs_gradient": float(self.max_abs_gradient), "cov": bool(self.cov)}


def _fd_hessian(theta, data, cov, grid):
    """Hessian of the fixed-node log-likelihood by central differences of its exact gradient."""
    k = theta.size
    H = np.full((k, k), np.nan)
    for i in range(k):
        h = 1e-5 * max(1.0, abs(theta[i]))
        tp, tm = theta.copy(), theta.copy()
        tp[i] += h
        tm[i] -= h
        _, gp = loglik_grid(tp, data, cov, grid, True)
        _, gm = loglik_grid(tm, data, cov, grid, True)
        if gp is None or gm is None:
            return None
        H[:, i] = (gp - gm) / (2 * h)
    return 0.5 * (H + H.T)


def fit(data: GroupedData, start, cov=False, qpoints=None, maxiter=MAXITER, maxfunc=MAXFUNC,
        absgconv=ABSGCONV, gconv=GCONV, absxconv=None, qpick="second") -> Fit:
    """Fit the model by maximum likelihood from ``start`` = [beta..., variance parameters...].

    The variance parameters are [var] (one random effect), [var0, var1] (two, independent) or
    [var0, cov01, var1] (two, ``cov=True``). ``qpoints`` fixes the points per dimension; by default they are
    chosen at the starting values as NLMIXED does. Convergence: max |gradient| <= absgconv, or the relative
    gradient g'H^-1 g / |loglik| <= gconv, or (when ``absxconv`` is given) the largest change of a parameter
    in an iteration <= absxconv, within maxiter iterations and maxfunc function calls.
    """
    theta = np.asarray(start, float).copy()
    p, q = data.p, data.q
    k = theta.size
    if k != p + n_cov_params(q, cov):
        raise ValueError(f"start needs {p + n_cov_params(q, cov)} values, got {k}")
    names = list(data.fixed_names) + cov_param_names(data.random_names, cov)
    Q = qpoints or select_qpoints(theta, data, cov, pick=qpick)

    nfun = 0
    grid = adapt(data, theta[:p], build_D(theta[p:], q, cov), Q)
    f, g = loglik_grid(theta, data, cov, grid, True)
    nfun += 1
    # Initial inverse Hessian: from finite differences when it is negative definite, else scaled identity.
    Hn = _fd_hessian(theta, data, cov, grid)
    Binv = None
    if Hn is not None and np.all(np.isfinite(Hn)):
        try:
            np.linalg.cholesky(-Hn)
            Binv = np.linalg.inv(-Hn)
        except np.linalg.LinAlgError:
            Binv = None
    if Binv is None:
        Binv = np.eye(k) / max(1.0, np.abs(g).max())
    status, it = "maxiter", 0
    modes = grid.modes
    for it in range(1, maxiter + 1):
        # Convergence at the current point (gradient of the maximized function, so -g for the minimum)
        if np.max(np.abs(g)) <= absgconv:
            status = "absgconv"
            break
        if abs(_dot(g, _mv(Binv, g))) / max(abs(f), 1e-6) <= gconv:
            status = "gconv"
            break
        d = _mv(Binv, g)                                           # ascent direction
        slope = _dot(g, d)
        if slope <= 0:
            Binv = np.eye(k) / max(1.0, np.abs(g).max())
            d = _mv(Binv, g)
            slope = _dot(g, d)
        alpha, accepted = 1.0, False
        for _ in range(40):
            tn = theta + alpha * d
            fn = loglik_grid(tn, data, cov, grid)
            nfun += 1
            if fn is not None and np.isfinite(fn) and fn >= f + 1e-4 * alpha * slope:
                accepted = True
                break
            alpha *= 0.5
            if nfun >= maxfunc:
                break
        if not accepted:
            status = "linesearch" if nfun < maxfunc else "maxfunc"
            break
        # Re-adapt the nodes at the new point, then take value and gradient there
        Dn = build_D(tn[p:], q, cov)
        grid = adapt(data, tn[:p], Dn, Q, modes)
        modes = grid.modes
        fn, gn = loglik_grid(tn, data, cov, grid, True)
        nfun += 1
        s, yv = tn - theta, -(gn - g)                              # BFGS on the negative log-likelihood
        sy = _dot(s, yv)
        if sy > 1e-12 * np.linalg.norm(s) * np.linalg.norm(yv):
            rho = 1.0 / sy
            V = np.eye(k) - rho * np.outer(s, yv)
            Binv = _mm(_mm(V, Binv), V.T) + rho * np.outer(s, s)
        xchange = float(np.max(np.abs(tn - theta)))
        theta, f, g = tn, fn, gn
        if absxconv is not None and xchange <= absxconv:
            status = "absxconv"
            break
        if nfun >= maxfunc:
            status = "maxfunc"
            break
    else:
        it = maxiter
    converged = status in ("absgconv", "gconv", "absxconv")
    Hn = _fd_hessian(theta, data, cov, grid)
    se = np.full(k, np.nan)
    hpd = False
    if Hn is not None and np.all(np.isfinite(Hn)):
        try:
            np.linalg.cholesky(-Hn)
            hpd = True
            se = np.sqrt(np.diag(np.linalg.inv(-Hn)))
        except np.linalg.LinAlgError:
            hpd = False
            try:
                v = np.diag(np.linalg.inv(-Hn))
                se = np.where(v > 0, np.sqrt(np.abs(v)), np.nan)
            except np.linalg.LinAlgError:
                pass
    return Fit(names, theta, se, converged, status, it, nfun, f, Q, hpd, float(np.max(np.abs(g))), cov)
