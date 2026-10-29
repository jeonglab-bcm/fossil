"""ODE constrained mixture models (ODE-MMs) of Hasenauer et al. 2014, ported to Python.

The authors' MATLAB code (Text S1, ODEMM_implementation_v01) defines each model in a
fitting script: a pathway model (`M.model`), and for every subpopulation s and experiment e
the map from the parameter vector xi to the kinetic rates (`M.theta{s}`), the distribution
parameters (`M.mu{s,e}`, `M.sigma{s,e}`), the weight (`M.w{s}`) and the distribution type.
`parse_fitting_script` reads those definitions from the .m file, and `log_likelihood` follows
`logLikelihood.m`.

Pathway models:
  conversion   simConversionReaction.m   dx/dt = (th1 + th3 u) - (th1 + th3 u + th2) x
  ngf_A        ODEmodel.m                TrkA:NGF and pErk (2 states)
  ngf_B        model_NGF_Erk__M2_syms.m  Ras/Raf/Mek/Erk cascade (5 states)
  ngf_C        model_NGF_Erk__M3_syms.m  cascade with negative feedback from pErk to Ras
"""

import re
from dataclasses import dataclass, field

import numpy as np
from scipy.integrate import solve_ivp

LOG10 = np.log(10.0)


# --------------------------------------------------------------------------- pathway models

def sim_conversion(T, th, u):
    """simConversionReaction.m: closed-form solution of the linear ODE (the original uses
    CVODES at rtol = atol = 1e-7). Returns x with shape (len(T), 1)."""
    T = np.atleast_1d(np.asarray(T, float))
    a = th[0] + th[2] * u
    lam = a + th[1]
    x0 = th[0] / (th[0] + th[1])
    xinf = a / lam
    return (xinf + (x0 - xinf) * np.exp(-lam * T))[:, None]


def _rhs_A(t, x, th, u):
    return [th[0] * u * (th[4] - x[0]) - th[1] * x[0],
            (th[2] + x[0]) * (th[5] - x[1]) - th[3] * x[1]]


def _jac_A(t, x, th, u):
    return [[-(th[0] * u + th[1]), 0.0],
            [th[5] - x[1], -(th[2] + th[3] + x[0])]]


def _x0_A(th):
    return np.array([0.0, th[2] * th[5] / (th[2] + th[3])])


def _rhs_BC(t, x, p, u, feedback):
    k1, k2, k4, k5, k7, k9, k11, TrkA0, Ras0, Raf0, Mek0, Erk0 = p[:12]
    act = x[0]
    if feedback:
        sK, n = p[12], p[13]
        r = max(x[4], 0.0) / sK
        act = x[0] / (1.0 + r ** n) if r < 1e3 or n < 100 else 0.0
    return [k1 * u * (TrkA0 - x[0]) - k2 * x[0],
            (act + k4) * (Ras0 - x[1]) - k5 * x[1],
            x[1] * (Raf0 - x[2]) - k7 * x[2],
            x[2] * (Mek0 - x[3]) - k9 * x[3],
            x[3] * (Erk0 - x[4]) - k11 * x[4]]


def _x0_BC(p):
    k1, k2, k4, k5, k7, k9, k11, TrkA0, Ras0, Raf0, Mek0, Erk0 = p[:12]
    x2 = k4 * Ras0 / (k4 + k5)
    x3 = x2 * Raf0 / (x2 + k7)
    x4 = x3 * Mek0 / (x3 + k9)
    x5 = x4 * Erk0 / (x4 + k11)
    return np.array([0.0, x2, x3, x4, x5])


def _integrate(rhs, x0, T, args, jac=None, rtol=1e-10, atol=1e-12):
    T = np.atleast_1d(np.asarray(T, float))
    out = np.empty((len(T), len(x0)))
    k0 = 0
    while k0 < len(T) and T[k0] == 0:
        out[k0] = x0
        k0 += 1
    if k0 < len(T):
        sol = solve_ivp(rhs, (0.0, T[-1]), x0, method="LSODA", t_eval=T[k0:], args=args,
                        jac=jac, rtol=rtol, atol=atol)
        if not sol.success:
            raise RuntimeError(sol.message)
        out[k0:] = sol.y.T
    return out


def sim_ngf_A(T, th, u):
    return _integrate(_rhs_A, _x0_A(th), T, (th, u), jac=_jac_A)


def sim_ngf_B(T, th, u):
    return _integrate(_rhs_BC, _x0_BC(th), T, (th, u, False))


def sim_ngf_C(T, th, u):
    return _integrate(_rhs_BC, _x0_BC(th), T, (th, u, True))


SIMULATORS = {"conversion": sim_conversion, "ngf_A": sim_ngf_A, "ngf_B": sim_ngf_B,
              "ngf_C": sim_ngf_C}


# --------------------------------------------------------------------------- model definitions

def _matlab_index(expr):
    """'[1:5,7]' or '1:3' or '5' -> zero-based list."""
    out = []
    for part in expr.strip("[] ").split(","):
        part = part.strip()
        if ":" in part:
            a, b = part.split(":")
            out.extend(range(int(a) - 1, int(b)))
        elif part:
            out.append(int(part) - 1)
    return out


@dataclass
class Readout:
    state: int                   # column of x that is measured
    log: bool                    # mu = log(x) (log-normal) or x (normal)
    sigma_idx: list              # xi index per time point (kinetic) or per dose (dose response)
    mean_shift: bool             # mu = log(x) - sigma^2/2, i.e. the ODE describes the mean


@dataclass
class ModelSpec:
    name: str
    pathway: str
    n_subpop: int
    theta_idx: list = field(default_factory=list)   # per subpopulation
    weight: list = field(default_factory=list)      # per subpopulation: ('const',1) / ('xi',k) / ('1-xi',k)
    dist: list = field(default_factory=list)        # per subpopulation: 'norm' / 'logn'
    readout: dict = field(default_factory=dict)     # (s, e) -> Readout


def _join_continuations(text):
    text = re.sub(r"%[^\n]*", "", text)
    return re.sub(r"\.\.\.\s*\n\s*", " ", text)


def parse_fitting_script(path, pathway, doses=(0, 0.001, 0.01, 0.1, 1, 10)):
    """Read the model definition of one fitting__*.m script."""
    src = _join_continuations(open(path, encoding="latin-1").read())
    name = re.search(r"model_name\s*=\s*'([^']+)'", src).group(1)
    n_sub = int(re.search(r"M\.N_subpop\s*=\s*(\d+)", src).group(1))
    spec = ModelSpec(name=name, pathway=pathway, n_subpop=n_sub)
    for s in range(1, n_sub + 1):
        th = re.search(rf"M\.theta\{{{s}\}}\s*=\s*@\(xi\)\s*10\.\^xi\((\[[^\]]*\]|[^)]*)\)", src)
        spec.theta_idx.append(_matlab_index(th.group(1)))
        w = re.search(rf"M\.w\{{{s}\}}\s*=\s*@\(xi\)\s*([^;]+);", src).group(1).replace(" ", "")
        if w == "1":
            spec.weight.append(("const", 1.0))
        elif w.startswith("1-xi("):
            spec.weight.append(("1-xi", int(w[5:-1]) - 1))
        elif w.startswith("xi("):
            spec.weight.append(("xi", int(w[3:-1]) - 1))
        else:
            raise ValueError(f"{path}: weight {w}")
        spec.dist.append(re.search(rf"M\.distribution\{{{s}\}}\s*=\s*'(\w+)'", src).group(1))
        for e in (1, 2):
            mu = re.search(rf"M\.mu\{{{s},{e}\}}\s*=\s*@\(t,x,xi,d\)\s*([^;]+);", src)
            sg = re.search(rf"M\.sigma\{{{s},{e}\}}\s*=\s*@\(t,x,xi,d\)\s*([^;]+);", src)
            if mu is None:
                continue
            mu, sg = mu.group(1).replace(" ", ""), sg.group(1).replace(" ", "")
            m = re.match(r"^10\.\^xi\(([\d:]+)\)$", sg)
            if m:
                sigma_idx = _matlab_index(m.group(1))
            else:
                pairs = re.findall(r"\(d==([\d.]+)\)\*10\.\^xi\((\d+)\)", sg)
                by_dose = {float(d): int(i) - 1 for d, i in pairs}
                sigma_idx = [by_dose[float(d)] for d in doses]
            base = re.match(r"^(log\()?x(\(:,(\d)\))?\)?", mu)
            state = int(base.group(3)) - 1 if base.group(3) else 0
            shift = "10.^(2*xi" in mu
            if shift:   # check that the shift uses the same parameters as sigma
                if "(d==" in mu:
                    pairs = re.findall(r"\(d==([\d.]+)\)\*10\.\^\(2\*xi\((\d+)\)\)", mu)
                    shift_idx = [{float(d): int(i) - 1 for d, i in pairs}[float(d)] for d in doses]
                else:
                    shift_idx = _matlab_index(re.search(r"10\.\^\(2\*xi\(([\d:]+)\)\)", mu).group(1))
                assert shift_idx == sigma_idx, (path, s, e)
            spec.readout[(s - 1, e - 1)] = Readout(state=state, log=mu.startswith("log("),
                                                   sigma_idx=sigma_idx, mean_shift=shift)
    return spec


# --------------------------------------------------------------------------- likelihood

def _weights(spec, xi):
    w = []
    for kind, k in spec.weight:
        w.append(1.0 if kind == "const" else (xi[k] if kind == "xi" else 1.0 - xi[k]))
    return w


def _density(dist, y, logy, mu, sigma):
    if dist == "logn":
        z = (logy - mu) / sigma
        return np.exp(-0.5 * z * z) / (y * sigma * np.sqrt(2 * np.pi))
    z = (y - mu) / sigma
    return np.exp(-0.5 * z * z) / (sigma * np.sqrt(2 * np.pi))


def subpop_distribution(spec, xi, e, s, x, k):
    """mu and sigma of subpopulation s for experiment e at time/dose index k, given the
    simulated state value x (already the measured column)."""
    ro = spec.readout[(s, e)]
    sigma = 10.0 ** xi[ro.sigma_idx[k]]
    if ro.log:
        mu = np.log(x) - (sigma ** 2 / 2 if ro.mean_shift else 0.0)
    else:
        mu = x
    return mu, sigma


def simulate(spec, xi, s, T, u):
    th = 10.0 ** np.asarray(xi)[spec.theta_idx[s]]
    return SIMULATORS[spec.pathway](T, th, u)


def log_likelihood(spec, xi, D, per_condition=False):
    """logLikelihood.m (without gradient). D is a list of experiments with fields
    type ('kinetic'/'dose response'), t, u and y (rows: time points or doses; NaN padded)."""
    xi = np.asarray(xi, float)
    w = _weights(spec, xi)
    total, parts = 0.0, []
    for e, De in enumerate(D):
        rows = []
        if De["type"] == "kinetic":
            X = [simulate(spec, xi, s, De["t"], De["u"]) for s in range(spec.n_subpop)]
            for k in range(len(np.atleast_1d(De["t"]))):
                rows.append((k, [X[s][k, spec.readout[(s, e)].state] for s in range(spec.n_subpop)]))
        else:
            for d, ud in enumerate(np.atleast_1d(De["u"])):
                xs = [simulate(spec, xi, s, De["t"], ud)[-1, spec.readout[(s, e)].state]
                      for s in range(spec.n_subpop)]
                rows.append((d, xs))
        for k, xs in rows:
            y = De["y"][k]
            y = y[~np.isnan(y)]
            logy = np.log(y)
            p = np.zeros_like(y)
            for s in range(spec.n_subpop):
                mu, sigma = subpop_distribution(spec, xi, e, s, xs[s], k)
                p += w[s] * _density(spec.dist[s], y, logy, mu, sigma)
            ll = float(np.sum(np.log(p)))
            parts.append(ll)
            total += ll
    if not np.isfinite(total):
        total = -np.inf
    return (total, parts) if per_condition else total


def n_data(D):
    return int(sum(np.sum(~np.isnan(De["y"])) for De in D))


def bic(logL, n_par, D):
    return -2 * logL + np.log(n_data(D)) * n_par
