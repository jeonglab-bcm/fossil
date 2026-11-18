"""Transcriptional ODE models, likelihood, Metropolis MCMC and thermodynamic integration.

A rebuild of the inference part of Ocone et al. (2015), whose code is lost, from the main text
(Eqs 1-3) and the supplement (Eqs 4-6, sections 1.5-1.6).

Model strings follow the supplement's notation: ``A+`` (activating input), ``D-`` (inhibiting),
``and(A+,D-)``, ``or(A+,D-)``, ``and(or(A+,B-),D-)``, ``or(and(A+,B-),D-)``.  They are written
as a sum of terms, each a product of factors, each a sum of Hill functions:

* a leaf or ``and(...)`` of leaves and ``or(leaves)``: one term, one synthesis rate (Eqs 2, 4);
* ``or(...)`` of leaves only: one term with one factor (Eq. 3, one synthesis rate);
* ``or(...)`` with an ``and(...)`` child: one term per child, each with its own rate (Eq. 5).

Parameters: [alpha_1..alpha_T, lambda, kappa_1, h_1, ..., kappa_L, h_L] in the order the inputs
appear in the string, as in supplementary Tables 8 and 9.
"""
import math
import re

import numpy as np
from numba import njit

# ---------------------------------------------------------------- model parsing


def _parse(s):
    s = s.replace(" ", "")
    pos = 0

    def node():
        nonlocal pos
        m = re.match(r"(and|or)\(", s[pos:])
        if m:
            op = m.group(1)
            pos += len(m.group(0))
            kids = [node()]
            while s[pos] == ",":
                pos += 1
                kids.append(node())
            assert s[pos] == ")", s
            pos += 1
            return (op, kids)
        m = re.match(r"([A-Za-z0-9.]+)([+-])", s[pos:])
        assert m, f"bad model string {s!r} at {pos}"
        pos += len(m.group(0))
        return ("leaf", m.group(1), 1 if m.group(2) == "+" else -1)

    tree = node()
    assert pos == len(s), s
    return tree


def _factor(n):
    """A factor is a leaf or an or() of leaves: list of (name, sign)."""
    if n[0] == "leaf":
        return [(n[1], n[2])]
    if n[0] == "or" and all(k[0] == "leaf" for k in n[1]):
        return [(k[1], k[2]) for k in n[1]]
    raise ValueError(f"unsupported factor {n}")


def _term(n):
    """A term is a product of factors."""
    if n[0] == "and":
        out = []
        for k in n[1]:
            out.extend(_term(k) if k[0] == "and" else [_factor(k)])
        return out
    return [_factor(n)]


class Model:
    def __init__(self, spec):
        self.spec = spec
        tree = _parse(spec)
        if tree[0] == "or" and any(k[0] != "leaf" for k in tree[1]):
            terms = [_term(k) for k in tree[1]]
        else:
            terms = [_term(tree)]
        self.terms = terms
        self.leaves = [lf for t in terms for f in t for lf in f]
        self.inputs = []
        for name, _ in self.leaves:
            if name not in self.inputs:
                self.inputs.append(name)
        T = len(terms)
        L = len(self.leaves)
        self.n_terms, self.n_leaves = T, L
        self.n_params = T + 1 + 2 * L
        self.names = ([f"alpha{i + 1}" if T > 1 else "alpha" for i in range(T)] + ["lambda"]
                      + [p for name, sg in self.leaves for p in (f"kappa_{name}", f"h_{name}")])
        # flat arrays for the compiled code
        fac_term, leaf_fac, leaf_in, leaf_sign = [], [], [], []
        fi = 0
        for ti, t in enumerate(terms):
            for f in t:
                fac_term.append(ti)
                for name, sg in f:
                    leaf_fac.append(fi)
                    leaf_in.append(self.inputs.index(name))
                    leaf_sign.append(sg)
                fi += 1
        self.fac_term = np.array(fac_term, np.int64)
        self.leaf_fac = np.array(leaf_fac, np.int64)
        self.leaf_in = np.array(leaf_in, np.int64)
        self.leaf_sign = np.array(leaf_sign, np.int64)

    def bounds(self):
        """Upper bounds of the uniform priors (supp. section 1.5.2.1)."""
        ub = [2000.0] * self.n_terms + [50.0] + [2000.0, 30.0] * self.n_leaves
        return np.zeros(self.n_params), np.array(ub)

    def __repr__(self):
        return f"Model({self.spec})"


# ---------------------------------------------------------------- compiled core


@njit(cache=True)
def _rate(theta, xin, fac_term, leaf_fac, leaf_in, leaf_sign, n_terms):
    nf = fac_term.shape[0]
    fac = np.zeros(nf)
    for l in range(leaf_in.shape[0]):
        x = xin[leaf_in[l]]
        if x < 1e-12:
            x = 1e-12
        k = theta[n_terms + 1 + 2 * l]
        h = theta[n_terms + 2 + 2 * l]
        if k < 1e-300:
            k = 1e-300
        z = h * (math.log(x) - math.log(k))
        if z > 700.0:
            z = 700.0
        elif z < -700.0:
            z = -700.0
        act = 1.0 / (1.0 + math.exp(-z))
        fac[leaf_fac[l]] += act if leaf_sign[l] > 0 else 1.0 - act
    terms = np.ones(n_terms)
    for f in range(nf):
        terms[fac_term[f]] *= fac[f]
    r = 0.0
    for t in range(n_terms):
        r += theta[t] * terms[t]
    return r


@njit(cache=True)
def solve(theta, X, dt, y0, fac_term, leaf_fac, leaf_in, leaf_sign, n_terms):
    """Classical RK4 on a uniform grid. X holds the inputs at half steps: X[2i] at t_i,
    X[2i+1] at t_i + dt/2. Returns y at the grid points."""
    n = (X.shape[0] - 1) // 2 + 1
    lam = theta[n_terms]
    # keep lambda * h below 1 for stability: substeps with the production rate interpolated
    # quadratically through its values at the start, middle and end of the step
    m = 1
    if lam * dt > 1.0:
        m = int(math.ceil(lam * dt))
    h = dt / m
    y = np.empty(n)
    y[0] = y0
    for i in range(n - 1):
        a = _rate(theta, X[2 * i], fac_term, leaf_fac, leaf_in, leaf_sign, n_terms)
        b = _rate(theta, X[2 * i + 1], fac_term, leaf_fac, leaf_in, leaf_sign, n_terms)
        c = _rate(theta, X[2 * i + 2], fac_term, leaf_fac, leaf_in, leaf_sign, n_terms)
        yi = y[i]
        if m == 1:
            k1 = a - lam * yi
            k2 = b - lam * (yi + 0.5 * dt * k1)
            k3 = b - lam * (yi + 0.5 * dt * k2)
            k4 = c - lam * (yi + dt * k3)
            yi = yi + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        else:
            for j in range(m):
                u0 = j / m
                u1 = (j + 0.5) / m
                u2 = (j + 1.0) / m
                r0 = a * (2 * u0 - 1) * (u0 - 1) + b * 4 * u0 * (1 - u0) + c * u0 * (2 * u0 - 1)
                r1 = a * (2 * u1 - 1) * (u1 - 1) + b * 4 * u1 * (1 - u1) + c * u1 * (2 * u1 - 1)
                r2 = a * (2 * u2 - 1) * (u2 - 1) + b * 4 * u2 * (1 - u2) + c * u2 * (2 * u2 - 1)
                k1 = r0 - lam * yi
                k2 = r1 - lam * (yi + 0.5 * h * k1)
                k3 = r1 - lam * (yi + 0.5 * h * k2)
                k4 = r2 - lam * (yi + h * k3)
                yi = yi + h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        y[i + 1] = yi
    return y


@njit(cache=True)
def loglik(theta, Xs, xoff, dts, y0s, oidx, ow, oval, osig, ooff,
           fac_term, leaf_fac, leaf_in, leaf_sign, n_terms):
    """Gaussian log-likelihood (supp. Eq. 6) summed over all series."""
    ll = 0.0
    for s in range(dts.shape[0]):
        X = Xs[xoff[s]:xoff[s + 1]]
        y = solve(theta, X, dts[s], y0s[s], fac_term, leaf_fac, leaf_in, leaf_sign, n_terms)
        sig = osig[s]
        for j in range(ooff[s], ooff[s + 1]):
            i = oidx[j]
            w = ow[j]
            yp = y[i] * (1 - w) + (y[i + 1] * w if w > 0 else 0.0)
            r = oval[j] - yp
            ll += -0.5 * r * r / (sig * sig) - math.log(sig) - 0.9189385332046727
    return ll


@njit(cache=True)
def _logprior(theta, ub, lam_idx, lam_mu, lam_sd):
    """Log prior density in log-parameter space (includes the Jacobian sum(log theta)).
    Uniform U(0, ub) on every parameter, or a Gaussian on lambda if lam_sd > 0."""
    lp = 0.0
    for i in range(theta.shape[0]):
        if theta[i] <= 0 or theta[i] >= ub[i]:
            return -np.inf
        lp += math.log(theta[i])
    if lam_sd > 0:
        z = (theta[lam_idx] - lam_mu) / lam_sd
        lp += -0.5 * z * z
    return lp


@njit(cache=True)
def chain(logth0, prop_sd, n_iter, thin, temp, seed, ub, lam_idx, lam_mu, lam_sd,
          Xs, xoff, dts, y0s, oidx, ow, oval, osig, ooff,
          fac_term, leaf_fac, leaf_in, leaf_sign, n_terms):
    """Metropolis random walk on log parameters (supp. section 1.5.2.1), targeting
    p(theta) * L(theta)^temp. Returns thinned samples, their log-likelihoods, acceptance."""
    np.random.seed(seed)
    P = logth0.shape[0]
    cur = logth0.copy()
    th = np.exp(cur)
    cll = loglik(th, Xs, xoff, dts, y0s, oidx, ow, oval, osig, ooff,
                 fac_term, leaf_fac, leaf_in, leaf_sign, n_terms)
    clp = _logprior(th, ub, lam_idx, lam_mu, lam_sd)
    ns = n_iter // thin
    S = np.empty((ns, P))
    LL = np.empty(ns)
    acc = 0
    best = cur.copy()
    bestpost = -np.inf
    for it in range(n_iter):
        prop = cur + prop_sd * np.random.standard_normal(P)
        pth = np.exp(prop)
        plp = _logprior(pth, ub, lam_idx, lam_mu, lam_sd)
        if plp > -np.inf:
            pll = loglik(pth, Xs, xoff, dts, y0s, oidx, ow, oval, osig, ooff,
                         fac_term, leaf_fac, leaf_in, leaf_sign, n_terms)
            a = temp * (pll - cll) + plp - clp
            if a >= 0 or math.log(np.random.random()) < a:
                cur = prop
                cll = pll
                clp = plp
                acc += 1
        if temp * cll + clp > bestpost:
            bestpost = temp * cll + clp
            best = cur.copy()
        if (it + 1) % thin == 0:
            S[it // thin] = cur
            LL[it // thin] = cll
    return S, LL, acc / n_iter, best, bestpost


# ---------------------------------------------------------------- data packing


class Series:
    """One pseudo time series of a target gene with emulated inputs.

    t, y: observations (pseudo times, target values). emus: {gene: callable t -> values}, the
    emulators of the inputs. y0: initial value. sigma: likelihood standard deviation."""

    def __init__(self, t, y, emus, y0, sigma, dt=0.25, t0=0.0, t1=None):
        self.t = np.asarray(t, float)
        self.y = np.asarray(y, float)
        self.emus = emus
        self.y0 = float(y0)
        self.sigma = float(sigma)
        self.dt = dt
        self.t0 = t0
        self.t1 = float(self.t.max()) if t1 is None else t1


class Problem:
    """A target gene, a model, and the series it is fitted to."""

    def __init__(self, model, series, lam_prior=None):
        self.model = model
        self.series = series
        self.lam_prior = lam_prior  # (mu, sd) or None
        Xs, xoff, dts, y0s, oidx, ow, oval, osig, ooff = [], [0], [], [], [], [], [], [], [0]
        self.grids = []
        for s in series:
            n = int(math.ceil((s.t1 - s.t0) / s.dt)) + 1
            half = s.t0 + np.arange(2 * n - 1) * s.dt / 2
            X = np.column_stack([np.asarray(s.emus[g](half), float) for g in model.inputs])
            Xs.append(X)
            xoff.append(xoff[-1] + len(X))
            grid = s.t0 + np.arange(n) * s.dt
            self.grids.append(grid)
            pos = np.clip((s.t - s.t0) / s.dt, 0, n - 1 - 1e-9)
            i = np.floor(pos).astype(np.int64)
            oidx.extend(i)
            ow.extend(pos - i)
            oval.extend(s.y)
            ooff.append(ooff[-1] + len(s.y))
            dts.append(s.dt)
            y0s.append(s.y0)
            osig.append(s.sigma)
        self.Xs = np.ascontiguousarray(np.vstack(Xs))
        self.xoff = np.array(xoff, np.int64)
        self.dts = np.array(dts)
        self.y0s = np.array(y0s)
        self.oidx = np.array(oidx, np.int64)
        self.ow = np.array(ow)
        self.oval = np.array(oval)
        self.osig = np.array(osig)
        self.ooff = np.array(ooff, np.int64)
        self.n_obs = len(self.oval)

    def args(self):
        m = self.model
        return (self.Xs, self.xoff, self.dts, self.y0s, self.oidx, self.ow, self.oval, self.osig,
                self.ooff, m.fac_term, m.leaf_fac, m.leaf_in, m.leaf_sign, m.n_terms)

    def loglik(self, theta):
        return loglik(np.asarray(theta, float), *self.args())

    def trajectories(self, theta):
        m = self.model
        out = []
        for s, x0, x1, g in zip(range(len(self.series)), self.xoff[:-1], self.xoff[1:], self.grids):
            y = solve(np.asarray(theta, float), self.Xs[x0:x1], self.dts[s], self.y0s[s],
                      m.fac_term, m.leaf_fac, m.leaf_in, m.leaf_sign, m.n_terms)
            out.append((g, y))
        return out

    def prior_args(self):
        lo, ub = self.model.bounds()
        lam_idx = self.model.n_terms
        if self.lam_prior:
            return ub, lam_idx, float(self.lam_prior[0]), float(self.lam_prior[1])
        return ub, lam_idx, 0.0, 0.0


# ---------------------------------------------------------------- samplers


def _start(problem, rng, n_try=4000):
    """Best of n_try draws from the prior (log-uniform over [1e-2, ub) for a usable start)."""
    lo, ub = problem.model.bounds()
    lub = np.log(ub)
    best, bll = None, -np.inf
    for _ in range(n_try):
        lt = rng.uniform(np.log(1e-2), lub - 1e-6)
        if problem.lam_prior:
            lt[problem.model.n_terms] = np.log(max(problem.lam_prior[0], 1e-6))
        ll = problem.loglik(np.exp(lt))
        if ll > bll:
            best, bll = lt, ll
    return best


def global_optimum(problem, seed, maxiter=300):
    """Differential evolution on log parameters (log posterior), to start the chains in the main
    mode: the posteriors of these models have several modes and a random start can stay in a poor
    one."""
    from scipy.optimize import differential_evolution

    ub, lam_idx, mu, sd = problem.prior_args()
    lo = np.full(len(ub), np.log(1e-3))
    hi = np.log(ub) - 1e-6

    def neg(lt):
        th = np.exp(lt)
        lp = _logprior(th, ub, lam_idx, mu, sd)
        if not np.isfinite(lp):
            return 1e300
        v = -(problem.loglik(th) + lp)
        return v if np.isfinite(v) else 1e300

    r = differential_evolution(neg, list(zip(lo, hi)), seed=seed, maxiter=maxiter, popsize=20,
                               tol=1e-8, polish=True, init="sobol")
    return r.x


def run_mcmc(problem, seed, temp=1.0, n_adapt=6000, n_burn=4000, n_sample=20000, thin=10,
             start=None, n_starts=3):
    """Adaptive warm-up (proposal scale tuned to ~25% acceptance), burn-in, sampling.
    With start=None, chains are warmed up from the differential-evolution optimum and from the
    best prior draws, and the one with the highest posterior is kept."""
    rng = np.random.default_rng(seed)
    ub, lam_idx, mu, sd = problem.prior_args()
    P = problem.model.n_params
    args = problem.args()
    if start is not None:
        starts = [start]
    else:
        starts = [global_optimum(problem, int(rng.integers(2**31)))]
        starts += [_start(problem, rng) for _ in range(n_starts - 1)]
    best = None
    for si, s0 in enumerate(starts):
        cur = np.array(s0, float)
        psd = np.full(P, 0.05)
        sub = 0
        for blk in range(n_adapt // 500):
            S, LL, acc, b, bp = chain(cur, psd, 500, 500, temp, int(rng.integers(2**31)), ub,
                                      lam_idx, mu, sd, *args)
            cur = S[-1]
            if acc < 0.15:
                psd *= 0.6
            elif acc > 0.35:
                psd *= 1.5
            sub += 1
        S, LL, acc, b, bp = chain(cur, psd, n_burn, n_burn, temp, int(rng.integers(2**31)), ub,
                                  lam_idx, mu, sd, *args)
        cur = S[-1]
        if best is None or bp > best[0]:
            best = (bp, cur, psd)
    _, cur, psd = best
    S, LL, acc, b, bp = chain(cur, psd, n_sample, thin, temp, int(rng.integers(2**31)), ub,
                              lam_idx, mu, sd, *args)
    return {"logtheta": S, "loglik": LL, "accept": acc, "map_logtheta": b, "map_logpost": bp,
            "prop_sd": psd}


def map_estimate(problem, mc):
    """Polish the best sample with Nelder-Mead on log parameters (maximum a posteriori)."""
    from scipy.optimize import minimize

    ub, lam_idx, mu, sd = problem.prior_args()

    def neg(lt):
        th = np.exp(lt)
        if np.any(th >= ub):
            return 1e300
        lp = 0.0
        if sd > 0:
            lp = -0.5 * ((th[lam_idx] - mu) / sd) ** 2
        return -(problem.loglik(th) + lp)

    x0 = mc["map_logtheta"]
    r = minimize(neg, x0, method="Nelder-Mead",
                 options={"maxiter": 4000 * len(x0), "xatol": 1e-7, "fatol": 1e-7})
    th = np.exp(r.x if r.fun <= neg(x0) else x0)
    return th, problem.loglik(th)


def info_criteria(loglik_max, n_params, n_obs):
    """AIC and BIC as defined in the supplement (section 1.6): larger is better."""
    return loglik_max - n_params, loglik_max - 0.5 * n_params * math.log(n_obs)


def thermodynamic_integration(problem, seed, n_temps=30, power=5, n_burn=3000, n_sample=6000,
                              thin=10, n_prior=4000):
    """log p(D|M) by power posteriors and the trapezoidal rule (supp. section 1.6.1).
    Ladder t_i = (i/n)^power (Calderhead and Girolami 2009). Chains run from t = 1 down to the
    smallest temperature, each starting at the previous chain's last state."""
    rng = np.random.default_rng(seed)
    temps = (np.arange(n_temps + 1) / n_temps) ** power
    E = np.empty(n_temps + 1)
    sdE = np.empty(n_temps + 1)
    # t = 0: the prior itself
    lo, ub = problem.model.bounds()
    lls = []
    for _ in range(n_prior):
        th = rng.uniform(0, ub)
        if problem.lam_prior:
            th[problem.model.n_terms] = abs(rng.normal(*problem.lam_prior))
        lls.append(problem.loglik(th))
    lls = np.array(lls)
    E[0], sdE[0] = lls.mean(), lls.std()
    top = run_mcmc(problem, int(rng.integers(2**31)), temp=1.0, n_adapt=6000, n_burn=n_burn,
                   n_sample=n_sample, thin=thin)
    E[-1], sdE[-1] = top["loglik"].mean(), top["loglik"].std()
    cur = top["logtheta"][-1]
    for i in range(n_temps - 1, 0, -1):
        mc = run_mcmc(problem, int(rng.integers(2**31)), temp=temps[i], n_adapt=3000,
                      n_burn=n_burn, n_sample=n_sample, thin=thin, start=cur)
        E[i], sdE[i] = mc["loglik"].mean(), mc["loglik"].std()
        cur = mc["logtheta"][-1]
    logZ = float(np.sum(np.diff(temps) * (E[:-1] + E[1:]) / 2))
    return {"log_evidence": logZ, "temps": temps.tolist(), "E": E.tolist(), "sdE": sdE.tolist()}
