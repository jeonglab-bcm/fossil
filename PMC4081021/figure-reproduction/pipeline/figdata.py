"""What each data panel of Figs 2 to 6 plots, computed the way the authors' plotting scripts
compute it (conversion_reaction/*/plots_for_paper.m and plotODEMix_paper.m;
NGF_induced_Erk_phosphorylation/pathway_model_A/plots_for_paper.m, plotODEMix_1_paper.m,
plotODEMix_2_paper.m; plots_for_paper__model_comparison.m).

Each panel is a dict: axis limits and scales, and a list of layers
  {"kind": "line"|"fill"|"markers"|"rect", "rgb": MATLAB colour, "lw": MATLAB line width,
   "x": ..., "y": ...}
in data units. `fits` selects whose optima are drawn: the authors' saved optima ("saved") or
our refit ("refit", from output/refit/*.json).
"""

import json
import os

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.stats import chi2, lognorm, norm

from odemm import simulate, subpop_distribution, _weights
from saved import load_model, to_D

GREEN = (0, 0.8, 0)
PURPLE = (0.6, 0, 0.6)
RED = (1, 0, 0)
BLUE = (0, 0, 1)
GREY = (0.7, 0.7, 0.7)
BLACK = (0, 0, 0)
ALPHA = [0.99, 0.95, 0.9, 0.8]


# --------------------------------------------------------------------------- MATLAB helpers

def matlab_hist(y, centers):
    """hist(y, centers): bins are bounded by the midpoints between centres; the first and last
    bins extend to -inf and +inf."""
    edges = np.r_[-np.inf, (centers[1:] + centers[:-1]) / 2, np.inf]
    return np.histogram(y, edges)[0].astype(float)


def staircase(edges_x, h):
    """x = y_hist(round(0.5:0.5:n)), y = [0; h(round(0.5:0.5:n-1)); 0] (MATLAB round)."""
    n = len(edges_x)
    ix = np.floor(np.arange(0.5, n + 0.25, 0.5) + 0.5).astype(int) - 1
    ih = np.floor(np.arange(0.5, len(h) + 0.25, 0.5) + 0.5).astype(int) - 1
    return edges_x[ix], np.r_[0.0, h[ih], 0.0]


def confidence_intervals(p, alpha):
    """getConfidenceIntervals.m, profile-likelihood intervals (CI.PL) for all parameters."""
    par = np.asarray(p.MS.MAP.par, float)
    thr = np.exp(-chi2.ppf(alpha, 1) / 2)
    P = np.atleast_1d(p.P)
    ci = np.full((len(par), 2), np.nan)
    for i in range(len(par)):
        if i >= len(P) or np.size(P[i].par) == 0:
            continue
        pp = np.atleast_2d(P[i].par)[i]
        R = np.atleast_1d(P[i].R).astype(float)
        ind = np.flatnonzero(pp <= par[i])
        j = np.flatnonzero(R[ind] <= thr)
        if len(j):
            j = j[-1]
            ci[i, 0] = np.interp(thr, R[ind[[j, j + 1]]][::-1], pp[ind[[j, j + 1]]][::-1]) \
                if R[ind[j]] > R[ind[j + 1]] else np.interp(thr, R[ind[[j, j + 1]]], pp[ind[[j, j + 1]]])
        else:
            ci[i, 0] = -np.inf
        ind = np.flatnonzero(pp >= par[i])
        j = np.flatnonzero(R[ind] <= thr)
        if len(j):
            j = j[0]
            a, b = ind[j - 1], ind[j]
            xr, yr = np.array([R[a], R[b]]), np.array([pp[a], pp[b]])
            o = np.argsort(xr)
            ci[i, 1] = np.interp(thr, xr[o], yr[o])
        else:
            ci[i, 1] = np.inf
    return ci



class Fit:
    """A model with its parameters: the authors' saved optimum or our refit."""

    def __init__(self, sources, study, model, fits="saved", refit_dir=None):
        self.spec, self.m = load_model(sources, study, model)
        self.p = self.m["parameters"]
        self.D = to_D(self.m["D"])
        self.xi = np.asarray(self.p.MS.MAP.par, float)
        if fits == "refit":
            r = json.load(open(os.path.join(refit_dir, f"{study}__{model}.json")))
            self.xi = np.asarray(r["best_xi"], float)
        self.w = _weights(self.spec, self.xi)

    def sim(self, s, T, u):
        return simulate(self.spec, self.xi, s, T, u)

    def dist(self, e, s, xstate, k):
        return subpop_distribution(self.spec, self.xi, e, s, xstate, k)

    def sigma_vec(self, e, s):
        return 10.0 ** self.xi[self.spec.readout[(s, e)].sigma_idx]


def _pdf(dist, y, mu, sigma):
    if dist == "logn":
        return lognorm.pdf(y, s=sigma, scale=np.exp(mu))
    return norm.pdf(y, mu, sigma)


# --------------------------------------------------------------------------- Fig. 2

def fig2(sources, scenario, fits="saved", refit_dir=None):
    """Fig. 2B-D (scenario 1) or 2E-G (scenario 2). Model M_H2,2 (2logn_mean_k1a)."""
    study = f"cr{scenario}"
    F = Fit(sources, study, "2logn_mean_k1a", fits, refit_dir)
    D = F.D[0]
    panels = {}
    # subpopulation colours: scenario 1 draws fitted subpopulation 1 purple, scenario 2 green
    c1, c2 = (PURPLE, GREEN) if scenario == 1 else (GREEN, PURPLE)

    # --- B / E: trajectories (sample_trajectories.eps)
    xi_true = np.array([np.log10(0.5), np.log10(1.5), np.log10(0.75), np.log10(0.1), 0.5])
    sig_true = 0.04 if scenario == 1 else 0.1
    t = np.linspace(0, 1.05, 15)
    tt = np.r_[-0.05, t]
    X1 = F.sim(0, t, 1.0)[:, 0]
    X2 = F.sim(1, t, 1.0)[:, 0]
    X = F.w[0] * X1 + F.w[1] * X2
    # mean of sample trajectories: the authors average 500 random cells; we use the exact
    # expectation over the true parameter distribution (Gauss-Hermite in log10 space)
    gh, gw = np.polynomial.hermite_e.hermegauss(15)
    gw = gw / gw.sum()

    def expected(ix):
        acc = np.zeros_like(t)
        for a, wa in zip(gh, gw):
            for b, wb in zip(gh, gw):
                for c, wc in zip(gh, gw):
                    th = 10 ** (xi_true[ix] + sig_true * np.array([a, b, c]))
                    acc += wa * wb * wc * _sim_cr(th, t)
        return acc
    M1 = expected([0, 1, 2])   # true subpopulation 1 (k1 = 0.75), drawn green
    M2 = expected([0, 1, 3])   # true subpopulation 2 (k1 = 0.1), drawn purple
    # 20 sample trajectories per subpopulation, drawn from the true parameter distribution as
    # in plots_for_paper.m (random; MATLAB's draws cannot be repeated, so these are not scored)
    rng = np.random.default_rng(0)
    traj = {0: [], 1: []}
    while min(len(v) for v in traj.values()) < 20:
        s = 0 if rng.random() < xi_true[4] else 1
        ix = [0, 1, 2] if s == 0 else [0, 1, 3]
        th = 10 ** (xi_true[ix] + sig_true * rng.standard_normal(3))
        traj[s].append(_sim_cr(th, t))
    layers = []
    for j in range(20):
        for s, c in [(0, (0.7, 1.0, 0.7)), (1, (1.0, 0.7, 1.0))]:
            layers.append({"kind": "line", "rgb": c, "lw": 0.5, "x": tt,
                           "y": np.r_[traj[s][j][0], traj[s][j]], "compare": False})
    layers += [
        {"kind": "line", "rgb": GREEN, "lw": 1.5, "style": "--", "x": tt, "y": np.r_[M1[0], M1],
         "note": "mean of sample trajectories (exact expectation; the authors average 500 random cells)"},
        {"kind": "line", "rgb": PURPLE, "lw": 1.5, "style": "--", "x": tt, "y": np.r_[M2[0], M2],
         "note": "mean of sample trajectories (exact expectation)"},
    ]
    # sample_trajectories.eps (both scenarios; the scenario-2 script also writes a
    # sample_trajectories_data.eps without these two curves, which is not the published panel)
    layers += [{"kind": "line", "rgb": c1, "lw": 1.5, "x": tt, "y": np.r_[X1[0], X1]},
               {"kind": "line", "rgb": c2, "lw": 1.5, "x": tt, "y": np.r_[X2[0], X2]}]
    layers += [{"kind": "line", "rgb": RED, "lw": 1.5, "x": tt, "y": np.r_[X[0], X]},
               {"kind": "markers", "rgb": BLACK, "size": 8, "x": D["t"],
                "y": np.nanmean(D["y"], axis=1)}]
    panels["B" if scenario == 1 else "E"] = {"xlim": (-0.05, 1.05), "ylim": (0, 0.7),
                                             "layers": layers}

    # --- C / F: histograms (model_data_comparison.eps)
    bins, points = (100, 600) if scenario == 1 else (50, 200)
    z_hist = np.linspace(-1, 0, bins + 1)
    y_hist = 10 ** z_hist
    dz = z_hist[1] - z_hist[0]
    y_grid = 10 ** np.linspace(-1, 0, points + 1)
    Xk = [F.sim(s, D["t"], D["u"])[:, 0] for s in range(2)]
    hp = {}
    for k in range(len(D["t"])):
        y = D["y"][k][~np.isnan(D["y"][k])]
        h = matlab_hist(y, y_hist)[:-1]
        h = h / h.sum()
        sx, sy = staircase(y_hist, h)
        ps = []
        for s in range(2):
            mu, sg = F.dist(0, s, Xk[s][k], k)
            ps.append(F.w[s] * _pdf("logn", y_grid, mu, sg) * y_grid * dz * np.log(10))
        hp[k] = {"xlim": (0.1, 1), "ylim": (0, 0.1), "xlog": True, "t": float(D["t"][k]),
                 "layers": [{"kind": "fill", "rgb": GREY, "x": sx, "y": sy},
                            {"kind": "line", "rgb": c1, "lw": 1, "x": y_grid, "y": ps[0]},
                            {"kind": "line", "rgb": c2, "lw": 1, "x": y_grid, "y": ps[1]},
                            {"kind": "line", "rgb": RED, "lw": 1, "x": y_grid,
                             "y": ps[0] + ps[1]}]}
    panels["C" if scenario == 1 else "F"] = hp

    # --- D / G: parameter uncertainty (parameter_uncertainties.eps)
    xg = np.linspace(-1.5, 1, 1000 if scenario == 1 else 100)
    sd = sig_true if scenario == 1 else 0.1
    xs = 10 ** xg[np.r_[0, np.arange(len(xg)), len(xg) - 1]]
    pdf = lambda c: np.r_[0, norm.pdf(xg, c, sd), 0]   # noqa: E731
    cis = {a: confidence_intervals(F.p, a) if fits == "saved" else None for a in ALPHA}
    top = {
        "k1": {"ylim": (0, 6 if scenario == 1 else 2.2),
               "fills": [(GREEN, 0.5 * pdf(xi_true[2])), (PURPLE, 0.5 * pdf(xi_true[3]))]},
        "k2": {"ylim": (0, 12 if scenario == 1 else 4.4),
               "fills": [(GREEN, pdf(xi_true[0])), (PURPLE, 0.5 * pdf(xi_true[0]))]},
        "k3": {"ylim": (0, 12 if scenario == 1 else 4.4),
               "fills": [(GREEN, pdf(xi_true[1])), (PURPLE, 0.5 * pdf(xi_true[1]))]},
    }
    dpan = {}
    for name, spec in top.items():
        dpan[name + "_density"] = {"xlim": (10 ** -1.5, 10), "ylim": spec["ylim"], "xlog": True,
                                   "layers": [{"kind": "fill", "rgb": c, "x": xs, "y": yv}
                                              for c, yv in spec["fills"]]}
    # w1: Poisson sampling density of the number of subpopulation-1 cells among 1000
    from scipy.stats import poisson
    n = np.arange(1001)
    dpan["w1_density"] = {"xlim": (0, 1), "ylim": (0, 0.00003),
                          "layers": [{"kind": "line", "rgb": BLACK, "lw": 0.5, "x": n / 1000,
                                      "y": poisson.pmf(n, 0.5 * 1000) / 1000}]}
    col_2 = [(1, 0.90, 0.90), (1, 0.75, 0.75), (1, 0.60, 0.60), (1, 0.45, 0.45), (1, 0.10, 0.10)]
    for name, i, log in [("k1_s1", 2, True), ("k1_s2", 3, True), ("k2", 0, True),
                         ("k3", 1, True), ("w1", 4, False)]:
        layers = []
        if cis[ALPHA[0]] is not None:
            for j, a in enumerate(ALPHA):
                lo, hi = cis[a][i]
                hgt = 0.1 + (j + 1) * 0.05
                layers.append({"kind": "rect", "rgb": col_2[j], "x": (lo, hi) if not log else
                               (10 ** lo, 10 ** hi), "y": (-hgt, hgt)})
        mp = F.xi[i]
        eps = 1e-2 if log else 0.5e-2
        layers.append({"kind": "rect", "rgb": col_2[-1],
                       "x": (10 ** (mp - eps), 10 ** (mp + eps)) if log else (mp - eps, mp + eps),
                       "y": (-0.4, 0.4)})
        dpan[name + "_estimate"] = {"xlim": (10 ** -1.5, 10) if log else (0, 1),
                                    "ylim": (-0.5, 0.5), "xlog": log, "layers": layers}
    panels["D" if scenario == 1 else "G"] = dpan
    return panels


def _sim_cr(th, t):
    a = th[0] + th[2]
    lam = a + th[1]
    x0 = th[0] / (th[0] + th[1])
    return a / lam + (x0 - a / lam) * np.exp(-lam * t)


# --------------------------------------------------------------------------- Figs. 3 and 4

def _mean_curves(F, median):
    """Kinetic and dose-response mean pErk per subpopulation (plots_for_paper.m)."""
    D = F.D
    t = np.linspace(D[0]["t"][0], D[0]["t"][-1], 100)
    u = np.r_[0, 10 ** np.linspace(-3.1, 1.1, 21)]
    K, DR = [], []
    for s in range(F.spec.n_subpop):
        X = F.sim(s, t, D[0]["u"])[:, 1]
        if median:
            sk = 10 ** PchipInterpolator(D[0]["t"], np.log10(F.sigma_vec(0, s)))(t)
            K.append(X * np.exp(sk ** 2 / 2))       # MEDIAN*exp(sigma^2/2), MEDIAN = x
        else:
            K.append(X)
        row = []
        sig_d = PchipInterpolator(D[1]["u"], np.log10(F.sigma_vec(1, s)))
        for ud in u:
            # the authors reuse t = linspace(0, 60, 100): the curve is the state at 60 min
            x = F.sim(s, t, ud)[-1, 1]
            row.append(x * np.exp((10 ** sig_d(ud)) ** 2 / 2) if median else x)
        DR.append(np.array(row))
    return t, u, K, DR


def _data_points(D):
    out = []
    for e in range(2):
        Ey = D[e]["Ey"]
        m = np.nanmean(Ey, axis=1)
        sd = np.nanstd(Ey, axis=1, ddof=1)
        out.append((m, sd))
    return out


def fig34(sources, which, fits="saved", refit_dir=None):
    """Fig. 3 (which='H1': 1logn_mean red, 1logn_median blue) or Fig. 4 ('H3':
    2logn_mean_TrkA0, 2logn_median_TrkA0), pathway model A."""
    names = {"H1": ("1logn_mean", "1logn_median"),
             "H3": ("2logn_mean_TrkA0", "2logn_median_TrkA0")}[which]
    Fs = [Fit(sources, "ngfA", n, fits, refit_dir) for n in names]
    D = Fs[0].D
    pts = _data_points(D)
    ylim = (0, 4) if which == "H1" else (0, 6)
    panels = {"B": {}, "C": {}, "D": {}}
    main = [RED, BLUE]
    subc = [[(1.0, 0.5, 0.5), (0.5, 0.0, 0.0)], [(0.5, 0.5, 1.0), (0.0, 0.0, 0.5)]]
    for mi, F in enumerate(Fs):
        t, u, K, DR = _mean_curves(F, median=(mi == 1))
        ti = np.r_[-3, t, t[-1] + 3]
        ext = lambda v: np.r_[v[0], v, v[-1]]   # noqa: E731
        kin, dose = [], []
        if which == "H3":
            for s in range(2):
                kin.append({"kind": "line", "rgb": subc[mi][s], "lw": 1, "x": ti, "y": ext(K[s])})
                dose.append({"kind": "line", "rgb": subc[mi][s], "lw": 1,
                             "x": 10 ** np.linspace(-3.1, 1.1, 21), "y": DR[s][1:]})
                dose.append({"kind": "line", "rgb": subc[mi][s], "lw": 1,
                             "x": np.array([1e-4 / 1.5, 1e-4 * 1.5]), "y": DR[s][0] * np.ones(2)})
            Kt = F.w[0] * K[0] + F.w[1] * K[1]
            Dt = F.w[0] * DR[0] + F.w[1] * DR[1]
        else:
            Kt, Dt = K[0], DR[0]
        kin.append({"kind": "line", "rgb": main[mi], "lw": 2, "x": ti, "y": ext(Kt)})
        dose.append({"kind": "line", "rgb": main[mi], "lw": 2,
                     "x": 10 ** np.linspace(-3.1, 1.1, 21), "y": Dt[1:]})
        dose.append({"kind": "line", "rgb": main[mi], "lw": 2,
                     "x": np.array([1e-4 / 1.5, 1e-4 * 1.5]), "y": Dt[0] * np.ones(2)})
        for lay, (m, sd), xs in [(kin, pts[0], D[0]["t"]), (dose, pts[1], 10.0 ** np.arange(-4, 2))]:
            lay.append({"kind": "markers", "rgb": BLACK, "size": 3, "open": True, "x": xs, "y": m})
            lay.append({"kind": "errorbar", "rgb": BLACK, "lw": 1, "x": xs, "y": m, "err": sd})
        if which == "H1" and mi == 0:
            # legend drawn with plot() inside the top dose-response panel
            dose += [{"kind": "markers", "rgb": BLACK, "size": 3, "open": True, "x": [0.001], "y": [3.5]},
                     {"kind": "line", "rgb": RED, "lw": 2, "x": [0.001 / 3, 0.003], "y": [3.0, 3.0]},
                     {"kind": "line", "rgb": BLUE, "lw": 2, "x": [0.001 / 3, 0.003], "y": [2.5, 2.5]}]
        panels["B"][f"kinetic_{mi}"] = {"xlim": (-3, 63), "ylim": ylim, "layers": kin}
        panels["B"][f"dose_{mi}"] = {"xlim": (1e-4 / 1.5, 10 ** 1.1), "ylim": ylim, "xlog": True,
                                     "layers": dose}

    # --- C: histograms (log x 0.1..100, 200 bins, model 200 points, z_max 0.06)
    z_hist = np.linspace(-1, 2, 201)
    y_hist = 10 ** z_hist
    dz = z_hist[1] - z_hist[0]
    y_grid = 10 ** np.linspace(-1, 2, 201)
    for e, De in enumerate(D):
        n_rows = De["y"].shape[0]
        for k in range(n_rows):
            y = De["y"][k][~np.isnan(De["y"][k])]
            h = matlab_hist(y, y_hist)[:-1]
            h = h / h.sum()
            sx, sy = staircase(y_hist, h)
            layers = [{"kind": "fill", "rgb": GREY, "x": sx, "y": sy}]
            for mi, F in enumerate(Fs):
                ps = []
                for s in range(F.spec.n_subpop):
                    if De["type"] == "kinetic":
                        xs = F.sim(s, De["t"], De["u"])[k, 1]
                    else:
                        xs = F.sim(s, De["t"], De["u"][k])[-1, 1]
                    mu, sg = F.dist(e, s, xs, k)
                    ps.append(F.w[s] * _pdf("logn", y_grid, mu, sg) * y_grid * dz * np.log(10))
                if which == "H3":
                    for s in range(2):
                        layers.append({"kind": "line", "rgb": subc[mi][s], "lw": 0.5,
                                       "x": y_grid, "y": ps[s]})
                layers.append({"kind": "line", "rgb": main[mi], "lw": 1, "x": y_grid,
                               "y": sum(ps)})
            key = ("kinetic" if e == 0 else "dose") + f"_{k}"
            panels["C"][key] = {"xlim": (0.1, 100), "ylim": (0, 0.06), "xlog": True,
                                "layers": layers}

    # --- D: parameter uncertainty
    col = [[(1, 0.90, 0.90), (1, 0.75, 0.75), (1, 0.60, 0.60), (1, 0.45, 0.45), (1, 0.10, 0.10)],
           [(0.90, 0.90, 1), (0.75, 0.75, 1), (0.60, 0.60, 1), (0.45, 0.45, 1), (0.10, 0.10, 1)]]
    order = [0, 1, 2, 3, 5, 4] if which == "H1" else [0, 1, 2, 3, 6, 4, 5]
    delta = 0.5
    layers = []
    for i, oi in enumerate(order, start=1):
        for mi, F in enumerate(Fs):
            yc = i * (-2 - delta) - mi
            if fits == "saved":
                for j, a in enumerate(ALPHA):
                    ci = confidence_intervals(F.p, a)[oi]
                    if which == "H1":
                        ci = np.clip(ci, -2.5, 1.5)
                    hgt = 0.1 + (j + 1) * 0.05
                    layers.append({"kind": "rect", "rgb": col[mi][j], "x": tuple(10.0 ** ci),
                                   "y": (yc - hgt, yc + hgt)})
            layers.append({"kind": "rect", "rgb": col[mi][-1],
                           "x": (10 ** (F.xi[oi] - 1e-2), 10 ** (F.xi[oi] + 1e-2)),
                           "y": (yc - 0.4, yc + 0.4)})
    n = len(order)
    panels["D"]["rates"] = {"xlim": (10 ** -2.5, 10 ** 1.5), "xlog": True,
                            "ylim": (n * (-2 - delta) - 1 - 0.5 - delta / 2,
                                     1 * (-2 - delta) + 0.5 + delta / 2), "layers": layers}
    if which == "H3":
        layers = []
        for mi, F in enumerate(Fs):
            yc = (-2 - delta) - mi
            if fits == "saved":
                for j, a in enumerate(ALPHA):
                    ci = confidence_intervals(F.p, a)[7]
                    hgt = 0.1 + (j + 1) * 0.05
                    layers.append({"kind": "rect", "rgb": col[mi][j], "x": tuple(ci),
                                   "y": (yc - hgt, yc + hgt)})
            layers.append({"kind": "rect", "rgb": col[mi][-1],
                           "x": (F.xi[7] - 2e-3, F.xi[7] + 2e-3), "y": (yc - 0.4, yc + 0.4)})
        panels["D"]["w1"] = {"xlim": (0, 1), "ylim": (-2 - delta - 1 - 0.5 - delta / 2,
                                                     -2 - delta + 0.5 + delta / 2),
                             "layers": layers}
    panels["weights"] = [F.w for F in Fs]
    return panels


# --------------------------------------------------------------------------- Fig. 5

FIG5_MODELS = ["1norm", "1logn_mean", "1logn_median", "2norm_Erk0", "2logn_mean_Erk0",
               "2logn_median_Erk0", "2norm_TrkA0", "2logn_mean_TrkA0", "2logn_median_TrkA0"]


def fig5(sources, fits="saved", refit_dir=None):
    """BIC of the 9 models x 3 pathway models (B) and w_1 of M_H3,3 (C)."""
    bic = np.zeros((9, 3))
    w = []
    for j, st in enumerate(["ngfA", "ngfB", "ngfC"]):
        for i, mname in enumerate(FIG5_MODELS):
            if fits == "saved":
                _, m = load_model(sources, st, mname)
                bic[i, j] = float(m["parameters"].MS.MAP.BIC)
            else:
                bic[i, j] = json.load(open(os.path.join(refit_dir, f"{st}__{mname}.json")))["best_BIC"]
        F = Fit(sources, st, "2logn_median_TrkA0", fits, refit_dir)
        w.append(F.w)
    return {"BIC": bic, "w_H33": w}


# --------------------------------------------------------------------------- Fig. 6

def fig6(sources, n_init=1, seed=0):
    """Correlation analysis (plots_for_paper.m, 'correlation_analysis'): the first 1500 cells
    of each condition, Pearson correlation of log10 Erk and log10 pErk, and a two-component
    Gaussian mixture (gmdistribution.fit) of the stimulated cells in log10 space."""
    from saved import code_root
    import scipy.io as sio
    from scipy.stats import pearsonr
    path = os.path.join(code_root(sources), "NGF_induced_Erk_phosphorylation", "pathway_model_A",
                        "project", "data", "correlation_data.mat")
    Dc = sio.loadmat(path, squeeze_me=True, struct_as_record=False)["D_corr"]
    I = slice(0, 1500)
    ctrl = np.log10(Dc.y_control[I, :2])
    stim = np.log10(Dc.y_stimulated[I, :2])
    r_c, p_c = pearsonr(ctrl[:, 0], ctrl[:, 1])
    r_s, p_s = pearsonr(stim[:, 0], stim[:, 1])
    gm = gmm2(stim, n_init=n_init, seed=seed)
    order = np.argsort(gm["mu"][:, 1])
    gm = {k: (v[order] if k in ("mu", "Sigma", "p") else v) for k, v in gm.items()}
    from scipy.stats import multivariate_normal as mvn
    P1 = mvn.pdf(stim, gm["mu"][0], gm["Sigma"][0]) * gm["p"][0]
    P2 = mvn.pdf(stim, gm["mu"][1], gm["Sigma"][1]) * gm["p"][0]   # sic: PComponents(1)
    ind1, ind2 = np.flatnonzero(P1 > P2), np.flatnonzero(P2 > P1)
    return {"control": ctrl, "stimulated": stim, "rho_control": r_c, "p_control": p_c,
            "rho_stimulated": r_s, "p_stimulated": p_s, "gm": gm, "ind1": ind1, "ind2": ind2,
            "n_control_total": int(len(Dc.y_control)), "n_stim_total": int(len(Dc.y_stimulated))}


def gmm2(X, n_init=1, seed=0, iters=100, tol=1e-6):
    """gmdistribution.fit(X, 2) as in MATLAB R2013a: start from two randomly chosen data
    points as means, diagonal covariances holding each column's variance and equal weights;
    EM stops after 100 iterations or when the log-likelihood changes by less than 1e-6 of its
    value. This stops before full convergence: 289 of 300 random starts give the published
    68.0 / 32.0 %, the fully converged mixture gives 68.1 / 31.9 %."""
    rng = np.random.default_rng(seed)
    from scipy.stats import multivariate_normal as mvn
    best = None
    n = len(X)
    for _ in range(n_init):
        mu = X[rng.choice(n, 2, replace=False)].copy()
        S = np.array([np.diag(X.var(0, ddof=1))] * 2)
        p = np.array([0.5, 0.5])
        ll_old = None
        for it in range(iters):
            dens = np.stack([p[k] * mvn.pdf(X, mu[k], S[k]) for k in range(2)], 1)
            tot = dens.sum(1)
            ll = np.log(tot).sum()
            if ll_old is not None and abs(ll - ll_old) < tol * abs(ll):
                break
            ll_old = ll
            r = dens / tot[:, None]
            nk = r.sum(0)
            p = nk / n
            mu = (r.T @ X) / nk[:, None]
            S = np.array([((X - mu[k]).T * r[:, k]) @ (X - mu[k]) / nk[k] for k in range(2)])
        if best is None or ll > best["logL"]:
            best = {"mu": mu, "Sigma": S, "p": p, "logL": ll, "iterations": it}
    return best
