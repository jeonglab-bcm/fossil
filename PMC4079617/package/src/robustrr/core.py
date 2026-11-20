"""Relative risks by robust Poisson and log-binomial regression.

Every fit is batched: ``X`` has shape (n, p) or (R, n, p) and ``y`` (n,) or (R, n), so the R data sets of a
simulation are fitted together. Column 0 of ``X`` is the intercept.

Robust Poisson (Zou 2004): the Poisson log-linear model fitted by maximum likelihood, with the sandwich
(robust) variance; SAS PROC GENMOD with a REPEATED statement and one record per subject gives the same
estimate and the HC0 sandwich used here.

Log-binomial: the binomial model with a log link, fitted by maximum likelihood inside the parameter space
(every fitted probability below 1). When the maximum lies on the boundary (a fitted probability reaches 1), the
plain fit does not converge, and the COPY method takes over (Deddens, Petersen and Lei 2003; Petersen and
Deddens 2009, the revised macro): the original data with weight C and the data with the outcome reversed
(Y -> 1 - Y) with weight 1, fitted as one weighted log-binomial model. C = 1,000,000 by default, as in Chen et al.

Both likelihoods are maximized by Newton's method with a backtracking line search. The log-binomial
log-likelihood is concave in the coefficients, so Newton's method finds its maximum when it is interior, and
the COPY likelihood is strictly concave with its maximum always interior.
"""

from __future__ import annotations

import numpy as np

DEFAULT_COPIES = 1_000_000
_TOL = 1e-12          # Newton decrement (half of g' H^-1 g) at which a fit has converged
_MAXIT = 100          # Newton iterations
_MAXHALF = 60         # step halvings per iteration
_BOUNDARY = 1e-6      # a plain log-binomial fit whose largest fitted probability exceeds 1 - _BOUNDARY is on the boundary


def _batch(X, y):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    single = X.ndim == 2
    if single:
        X, y = X[None], y[None]
    if X.ndim != 3 or y.shape != X.shape[:2]:
        raise ValueError(f"X must be (n, p) or (R, n, p) and y (n,) or (R, n); got {X.shape} and {y.shape}")
    if not np.all((y == 0) | (y == 1)):
        raise ValueError("the outcome must be 0 or 1")
    return X, y, single


def _solve(A, g):
    return np.linalg.solve(A, g[..., None])[..., 0]


def _poisson_ll(eta, y):
    return (y * eta - np.exp(eta)).sum(-1)


def poisson_coef(X, y, maxit=_MAXIT):
    """Poisson maximum likelihood coefficients (log link). Returns (coef, converged)."""
    X, y, single = _batch(X, y)
    R, n, p = X.shape
    b = np.zeros((R, p))
    b[:, 0] = np.log(np.maximum(y.mean(1), 1e-300))
    eta = _xb(X, b)
    ll = _poisson_ll(eta, y)
    conv = np.zeros(R, bool)
    for _ in range(maxit):
        act = np.flatnonzero(~conv)
        if act.size == 0:
            break
        Xa, ya, ba = X[act], y[act], b[act]
        mu = np.exp(_xb(Xa, ba))
        g = np.einsum("rnp,rn->rp", Xa, ya - mu)
        A = np.einsum("rni,rn,rnj->rij", Xa, mu, Xa)
        d = _solve(A, g)
        dec = 0.5 * np.einsum("rp,rp->r", g, d)
        step = np.ones(act.size)
        lla = ll[act]
        newb, newll = ba.copy(), lla.copy()
        todo = np.ones(act.size, bool)
        for _h in range(_MAXHALF):
            cand = ba + step[:, None] * d
            lc = _poisson_ll(_xb(Xa, cand), ya)
            ok = todo & (lc >= lla + 1e-4 * step * 2 * dec - 1e-9 * np.abs(lla))
            newb[ok], newll[ok] = cand[ok], lc[ok]
            todo &= ~ok
            if not todo.any():
                break
            step[todo] /= 2
        b[act], ll[act] = newb, newll
        conv[act] = dec < _TOL
    return (b[0], bool(conv[0])) if single else (b, conv)


def _lb_ll(eta, a, w):
    """sum a*eta + w*log(1 - exp(eta)); -inf outside eta < 0."""
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        t = a * eta + w * np.log(-np.expm1(eta))
    t = np.where(eta < 0, t, -np.inf)
    t = np.where((w == 0) & (eta <= 0), a * eta, t)  # a record with no (1 - mu) term may sit on the boundary
    return t.sum(-1)


def _lb_newton(X, a, w, b, maxit=_MAXIT, stop_above=None):
    """Maximize sum a*eta + w*log(1 - mu), eta = X b, from a feasible b. Returns (b, converged, iterations, score).

    Each Newton step starts at the largest step that keeps every eta below 0 (times 0.99), then halves until the
    Armijo condition holds. stop_above: stop a data set (not converged) once a fitted probability exceeds it.
    """
    R = X.shape[0]
    eta = _xb(X, b)
    ll = _lb_ll(eta, a, w)
    conv = np.zeros(R, bool)
    done = np.zeros(R, bool)
    its = np.zeros(R, int)
    for _ in range(maxit):
        act = np.flatnonzero(~done)
        if act.size == 0:
            break
        Xa, aa, wa, ba = X[act], a[act], w[act], b[act]
        eta = _xb(Xa, ba)
        mu = np.exp(eta)
        om = -np.expm1(eta)                       # 1 - mu
        pos = wa > 0                              # records with no (1 - mu) term may sit at mu = 1
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.where(pos, wa * mu / om, 0.0)
            h = np.where(pos, wa * mu / om**2, 0.0)   # -d2/deta2
        g = np.einsum("rnp,rn->rp", Xa, aa - r)
        A = np.matmul(Xa.transpose(0, 2, 1) * h[:, None, :], Xa)
        try:
            d = _solve(A, g)
        except np.linalg.LinAlgError:
            d = _solve(A + 1e-10 * np.eye(A.shape[-1]), g)
        dec = 0.5 * np.einsum("rp,rp->r", g, d)
        deta = _xb(Xa, d)
        with np.errstate(divide="ignore", invalid="ignore"):
            lim = np.where(deta > 0, -eta / deta, np.inf).min(1)
        step = np.minimum(1.0, 0.99 * lim)
        lla = ll[act]
        newb, newll = ba.copy(), lla.copy()
        todo = np.ones(act.size, bool)
        for _h in range(_MAXHALF):
            cand = ba + step[:, None] * d
            lc = _lb_ll(eta + step[:, None] * deta, aa, wa)
            ok = todo & np.isfinite(lc) & (lc >= lla + 1e-4 * step * 2 * dec - 1e-12 * np.abs(lla))
            newb[ok], newll[ok] = cand[ok], lc[ok]
            todo &= ~ok
            if not todo.any():
                break
            step[todo] /= 2
        b[act], ll[act] = newb, newll
        its[act] += 1
        c = dec < _TOL
        conv[act] = c
        stop = c | todo                           # converged, or no step improves the likelihood any more
        if stop_above is not None:
            stop |= np.exp(_xb(Xa, newb).max(1)) > stop_above
        done[act] = stop
    eta = _xb(X, b)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(w > 0, w * np.exp(eta) / -np.expm1(eta), 0.0)
    g = np.einsum("rnp,rn->rp", X, a - r)
    return b, conv, its, g


def _xb(X, b):
    return np.matmul(X, b[..., None])[..., 0]


def _feasible_start(X, y):
    """A start inside the parameter space: the intercept-only fit, log(mean y), every other coefficient 0."""
    R, n, p = X.shape
    b = np.zeros((R, p))
    b[:, 0] = np.log(np.clip(y.mean(1), 1e-12, 1 - 1e-9))
    return b


def log_binomial_coef(X, y, copy=True, copies=DEFAULT_COPIES, maxit=_MAXIT):
    """Log-binomial coefficients, with the COPY method when the plain fit does not converge.

    Returns (coef, info) where info holds, per data set: ``method`` ("mle" or "copy"), ``converged`` (the
    fit reported, plain or COPY), ``plain_converged``, ``max_fitted`` (largest fitted probability of the
    reported fit, on the original data) and ``iterations``.

    The plain fit has converged when Newton's method stops at an interior point: its largest fitted
    probability is below 1 - 1e-6 and the score is zero there. Otherwise the maximum is on the boundary and,
    with ``copy=True``, the COPY fit (weights C on the data, 1 on the reversed data) is returned instead.
    """
    X, y, single = _batch(X, y)
    if copies <= 0:
        raise ValueError("copies must be positive")
    b0 = _feasible_start(X, y)
    b, conv, its, g = _lb_newton(X, y, 1 - y, b0.copy(), maxit, stop_above=1 - _BOUNDARY)
    eta = _xb(X, b)
    maxmu = np.exp(eta.max(1))
    scale = np.sqrt((X**2).sum(1)).max(1)
    score_ok = np.abs(g).max(1) <= 1e-6 * np.maximum(scale, 1)
    plain_ok = conv & (maxmu < 1 - _BOUNDARY) & score_ok
    method = np.where(plain_ok, "mle", "copy")
    coef = b.copy()
    converged = plain_ok.copy()
    iters = its.copy()
    todo = np.flatnonzero(~plain_ok)
    if copy and todo.size:
        Xc, yc = X[todo], y[todo]
        inv = 1.0 / copies                        # weights C and 1, divided by C
        a = yc + (1 - yc) * inv                   # coefficient of eta: C*y + (1 - y)
        w = (1 - yc) + yc * inv                   # coefficient of log(1 - mu): C*(1 - y) + y
        start = b[todo].copy()
        etas = _xb(Xc, start)
        start[:, 0] -= np.maximum(etas.max(1) + 1e-3, 0)   # strictly inside
        bc, cc, itc, _ = _lb_newton(Xc, a, w, start, maxit)
        coef[todo], converged[todo], iters[todo] = bc, cc, iters[todo] + itc
    if not copy:
        method = np.where(plain_ok, "mle", "none")
    info = {"method": method, "converged": converged, "plain_converged": plain_ok,
            "max_fitted": np.exp(_xb(X, coef).max(1)), "iterations": iters}
    if single:
        return coef[0], {k: (v[0].item() if hasattr(v[0], "item") else v[0]) for k, v in info.items()}
    return coef, info


def robust_poisson(X, y):
    """Robust Poisson fit of one data set: coefficients, sandwich (HC0) covariance and convergence."""
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    if X.ndim != 2:
        raise ValueError("robust_poisson fits one data set: X must be (n, p)")
    coef, conv = poisson_coef(X, y)
    mu = np.exp(X @ coef)
    bread = np.linalg.inv((X * mu[:, None]).T @ X)
    meat = (X * ((y - mu) ** 2)[:, None]).T @ X
    return {"coef": coef, "cov": bread @ meat @ bread, "converged": conv}


def log_binomial(X, y, copy=True, copies=DEFAULT_COPIES):
    """Log-binomial fit of one data set: coefficients, model-based covariance, method and convergence.

    The covariance is the inverse expected information of the original data, sum mu/(1 - mu) x x', at the
    reported coefficients (for a COPY fit, the information of the weighted data divided by C, which is the
    same up to a factor 1 + 1/C).
    """
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    if X.ndim != 2:
        raise ValueError("log_binomial fits one data set: X must be (n, p)")
    coef, info = log_binomial_coef(X, y, copy=copy, copies=copies)
    mu = np.exp(X @ coef)
    W = mu / -np.expm1(np.minimum(X @ coef, -1e-300))
    cov = np.linalg.inv((X * W[:, None]).T @ X)
    return {"coef": coef, "cov": cov, **info}
