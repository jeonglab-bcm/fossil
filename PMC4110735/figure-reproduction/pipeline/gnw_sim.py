"""A Python port of GeneNetWeaver's DREAM4 time-series simulation (GNW 3.1, Schaffter, Marbach et al.).

GNW is MIT-licensed Java. This port follows its source for the model and the protocol, reading the kinetic
parameters from the network SBML files shipped in GNW's lib/gnw-networks.jar:

- mRNA x and protein y of each gene: dx/dt = max * f(y) - delta * x, dy/dt = maxTranslation * x - deltaProtein * y
  (HillGene.java); f is the thermodynamic module model of RegulatoryModule.java and HillGene.java.
- DREAM4 time series (BenchmarkGeneratorDream4.java, TimeSeriesExperiment.java): start from the wild-type
  steady state, apply a strong multifactorial perturbation (each gene with probability 0.33 gets a new basal
  activation drawn from U(0, 1)) for the first half (t = 0 to 500), remove it, sample every 50 time units
  to t = 1000 (21 points).
- Chemical Langevin noise (GeneNetworkSDE.java): diffusion 0.05 * sqrt(production + degradation).
- Microarray noise of Tu et al. 2002 (Experiment.java): x * exp(w), w ~ N(0, 0.001 + 0.689 / (1 + x / 0.01)),
  then every value divided by the largest value of the network's data (normalizeAfterAddingNoise).

Not a copy of GNW: the integrator is Euler-Maruyama with step 0.1 (GNW uses Milstein-Stratonovich with
step 1), and the random numbers are NumPy's. The authors' own simulated matrices were not released, so any
simulation stands in for them.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import numpy as np

NS = {"s": "http://www.sbml.org/sbml/level2"}


@dataclass
class Module:
    complex: bool
    nact: int
    ndeact: int
    inputs: list = field(default_factory=list)  # gene indices, activators first
    k: list = field(default_factory=list)
    n: list = field(default_factory=list)


@dataclass
class Gene:
    name: str
    max: float = 0.0
    delta: float = 0.0
    max_tl: float = 0.0
    delta_p: float = 0.0
    alpha: list = field(default_factory=list)
    modules: list = field(default_factory=list)


def read_sbml(path):
    root = ET.parse(path).getroot()
    species = [s.get("id") for s in root.iter("{%s}species" % NS["s"]) if s.get("id") != "_void_"]
    index = {g: i for i, g in enumerate(species)}
    genes = {g: Gene(g) for g in species}
    for rx in root.iter("{%s}reaction" % NS["s"]):
        rid = rx.get("id")
        params = {p.get("id"): float(p.get("value")) for p in rx.iter("{%s}parameter" % NS["s"])}
        if rid.endswith("_degradation"):
            genes[rid[: -len("_degradation")]].delta = params["delta"]
            continue
        g = genes[rid[: -len("_synthesis")]]
        g.max = params["max"]
        g.delta_p = params["deltaProtein"]
        g.max_tl = params["maxTranslation"]
        mods = [m.get("species") for m in rx.iter("{%s}modifierSpeciesReference" % NS["s"])]
        nmod = 1
        while f"numActivators_{nmod}" in params:
            nmod += 1
        nmod -= 1
        g.alpha = [params[f"a_{i}"] for i in range(2 ** nmod)]
        pos, kin = 0, 1
        for m in range(1, nmod + 1):
            na, nd = int(params[f"numActivators_{m}"]), int(params[f"numDeactivators_{m}"])
            mod = Module(params[f"bindsAsComplex_{m}"] > 0.5, na, nd)
            for _ in range(na + nd):
                mod.inputs.append(index[mods[pos]])
                mod.k.append(params[f"k_{kin}"])
                mod.n.append(params[f"n_{kin}"])
                pos += 1
                kin += 1
            g.modules.append(mod)
        assert pos == len(mods), (rid, pos, mods)
    return species, [genes[s] for s in species]


def gold_standard(genes, names):
    """Directed regulator -> target matrix from the modifiers (self-regulation left out, as GNW's evaluation)."""
    idx = {g: i for i, g in enumerate(names)}
    G = np.zeros((len(names), len(names)), dtype=int)
    for t, g in enumerate(genes):
        for m in g.modules:
            for i in m.inputs:
                if i != t:
                    G[i, t] = 1
    return G


class Model:
    def __init__(self, genes):
        self.genes = genes
        self.N = len(genes)
        self.max = np.array([g.max for g in genes])
        self.delta = np.array([g.delta for g in genes])
        self.max_tl = np.array([g.max_tl for g in genes])
        self.delta_p = np.array([g.delta_p for g in genes])
        self.alpha_wt = [np.array(g.alpha, dtype=float) for g in genes]
        self.alpha = [a.copy() for a in self.alpha_wt]
        # state-occupancy bit patterns per gene
        self.bits = []
        for g in genes:
            nm = len(g.modules)
            states = np.arange(2 ** nm)
            self.bits.append(np.array([[(s >> j) & 1 for j in range(nm)] for s in states], dtype=float).reshape(2 ** nm, nm))

    def perturb(self, delta_basal):
        self.alpha = []
        for a_wt, d in zip(self.alpha_wt, delta_basal):
            a = a_wt.copy()
            if a[0] + d > 1:
                d = 1 - a[0]
            elif a[0] + d < 0:
                d = -a[0]
            self.alpha.append(np.clip(a + d, 0, 1))

    def restore(self):
        self.alpha = [a.copy() for a in self.alpha_wt]

    def production(self, y):
        f = np.empty(self.N)
        for gi, g in enumerate(self.genes):
            if not g.modules:
                f[gi] = self.alpha[gi][0]
                continue
            m = np.empty(len(g.modules))
            for j, mod in enumerate(g.modules):
                xi = (np.maximum(y[mod.inputs], 0) / np.array(mod.k)) ** np.array(mod.n)
                act = np.prod(xi[: mod.nact]) if mod.nact else 1.0
                if mod.complex:
                    den = 1 + act
                    if mod.ndeact:
                        den += act * np.prod(xi[mod.nact:])
                else:
                    den = np.prod(xi + 1)
                m[j] = act / den
            B = self.bits[gi]
            p = np.prod(np.where(B == 1, m, 1 - m), axis=1)
            f[gi] = float(self.alpha[gi] @ p)
        return self.max * f

    def drift_terms(self, xy):
        x, y = xy[: self.N], xy[self.N:]
        V = np.r_[self.production(y), self.max_tl * x]
        D = np.r_[self.delta * x, self.delta_p * y]
        return V, D

    def steady_state(self, t=20000.0, dt=1.0):
        xy = np.zeros(2 * self.N)
        for _ in range(int(t / dt)):
            V, D = self.drift_terms(xy)
            new = np.maximum(xy + dt * (V - D), 0)
            if np.max(np.abs(new - xy)) < 1e-12:
                xy = new
                break
            xy = new
        return xy


def simulate_dream4(path, n_series, seed, maxt=1000.0, sample_dt=50.0, h=0.1, noise_sde=0.05, p_perturb=0.33):
    names, genes = read_sbml(path)
    model = Model(genes)
    rng = np.random.default_rng(seed)
    wt = model.steady_state()
    series = []
    halftime = maxt / 2
    nsteps_sample = int(round(sample_dt / h))
    for _ in range(n_series):
        delta = np.where(rng.uniform(size=model.N) < p_perturb, rng.uniform(size=model.N) - np.array([a[0] for a in model.alpha_wt]), 0.0)
        model.perturb(delta)
        xy = wt.copy()
        pts = [xy[: model.N].copy()]
        t = 0.0
        for s in range(int(round(maxt / sample_dt))):
            for _ in range(nsteps_sample):
                if t >= halftime - 1e-9 and model.alpha is not model.alpha_wt and not getattr(model, "_restored", False):
                    model.restore()
                    model._restored = True
                V, D = model.drift_terms(xy)
                dW = rng.normal(size=xy.size) * np.sqrt(h)
                xy = np.maximum(xy + h * (V - D) + noise_sde * np.sqrt(np.maximum(V + D, 0)) * dW, 0)
                t += h
            pts.append(xy[: model.N].copy())
        model._restored = False
        model.restore()
        series.append(np.array(pts).T)  # genes x 21
    X = np.concatenate(series, axis=1)
    # microarray noise (Tu et al. 2002), then normalise by the maximum
    var = 0.001 + (0.69 - 0.001) / (1 + X / 0.01)
    Xn = np.where(X > 0, X * np.exp(rng.normal(size=X.shape) * np.sqrt(var)), 0.0)
    Xn = Xn / Xn.max()
    return names, Xn, [X.shape[1] // n_series] * n_series, gold_standard(genes, names), wt[: model.N] / Xn.max() * 1.0


if __name__ == "__main__":
    path, n_series, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    names, X, seg, G, wt = simulate_dream4(path, n_series, seed)
    np.savez_compressed(out, names=np.array(names), X=X, segments=np.array(seg), gold=G)
    print(out, X.shape, int(G.sum()))
