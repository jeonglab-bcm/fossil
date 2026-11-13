"""Bayesian reconstruction of transmission trees from genetic and epidemiological data.

A reimplementation, from the paper's text and Text S1, of the method of

    Morelli MJ, Thebaud G, Chadoeuf J, King DP, Haydon DT, Soubeyrand S.
    A Bayesian inference framework to reconstruct transmission trees using
    epidemiological and genetic data. PLoS Comput Biol 8(11):e1002768 (2012).
    doi:10.1371/journal.pcbi.1002768

The authors' R code was never released, so every function here is reconstructed
from the equations in the paper and in Text S1. Equation numbers in the
docstrings refer to the main text unless marked "S1".

The model jointly infers, for an outbreak over ``I`` premises:

* the transmission tree ``J`` (``J[i]`` is the source of premise ``i``;
  ``-1`` marks the one premise infected by an external source),
* infection times ``Tinf``, latency durations ``L`` and
  infectiousness-to-detection durations ``D``,
* the parameters ``theta = (alpha1, alpha2, beta1, beta2)``,

given the observed detection times ``Tobs``, removal times ``Tend``, clinical
lesion-age assessments ``Dobs``, premise locations ``X`` (in km) and one
consensus genome per premise (as a pairwise Hamming-distance matrix ``M``).

The genetic term is the *pseudo*-likelihood of Eq. 5: it depends only on the
Hamming distances and on divergence times read off the current tree, so the
transmitted (unobserved) sequences are never augmented.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from importlib import resources
from pathlib import Path

import numpy as np

__all__ = [
    "Data",
    "MCMCConfig",
    "Posterior",
    "run_mcmc",
    "simulate_outbreak",
    "hamming_matrix",
    "read_fasta",
    "read_epi_table",
    "lonlat_to_km",
    "divergence_premise",
    "genetic_log_pseudo_likelihood",
    "log4_substitution",
    "example_path",
]

LOG_EPS = -1e12  # stand-in for log(0); an impossible state gets a huge negative log-density.


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
@dataclass
class Data:
    """Observed data for one outbreak, plus the fixed constants of the model.

    Distances are in km; times in days. ``M`` is the integer matrix of pairwise
    Hamming distances between the observed consensus sequences.
    """

    names: list[str]
    X: np.ndarray            # (I, 2) premise coordinates in km
    Tobs: np.ndarray         # (I,) detection times
    Tend: np.ndarray         # (I,) removal (culling) times
    Dobs: np.ndarray         # (I,) clinical lesion-age assessments
    M: np.ndarray            # (I, I) Hamming distances
    s: float                 # sequence length
    m: float                 # substitution rate per nt per day
    t0: float = -5.0         # earliest possible infection time
    d: float = 0.5           # uncertainty of Dobs:  V(D_i) = d^2 Dobs_i
    prior_mean: tuple = (100.0, 100.0, 100.0, 100.0)  # a1,a2,b1,b2 (Eq. 9)
    logC: np.ndarray = field(default=None, repr=False)  # cached log C(s, M_ij)
    dist: np.ndarray = field(default=None, repr=False)   # cached distance matrix

    def __post_init__(self):
        self.X = np.asarray(self.X, float)
        self.Tobs = np.asarray(self.Tobs, float)
        self.Tend = np.asarray(self.Tend, float)
        self.Dobs = np.asarray(self.Dobs, float)
        self.M = np.asarray(self.M, float)
        I = len(self.names)
        if I < 2:
            raise ValueError("need at least two premises to infer a transmission")
        for arr, nm in ((self.Tobs, "Tobs"), (self.Tend, "Tend"), (self.Dobs, "Dobs")):
            if arr.shape != (I,):
                raise ValueError(f"{nm} must have one value per premise ({I})")
        if self.X.shape != (I, 2):
            raise ValueError(f"X must be ({I}, 2)")
        if self.M.shape != (I, I):
            raise ValueError(f"M must be the ({I}, {I}) Hamming matrix, got {self.M.shape}")
        if self.logC is None:
            lg = math.lgamma
            s = self.s
            self.logC = np.array(
                [[lg(s + 1.0) - lg(mij + 1.0) - lg(s - mij + 1.0) for mij in row]
                 for row in self.M])
        if self.dist is None:
            diff = self.X[:, None, :] - self.X[None, :, :]
            self.dist = np.sqrt((diff * diff).sum(-1))

    @property
    def I(self) -> int:
        return len(self.names)


@dataclass
class State:
    """One point of the Markov chain (Sec. "MCMC algorithm", Text S1)."""

    J: np.ndarray        # (I,) source index, -1 = external
    Tinf: np.ndarray     # (I,) infection times
    L: np.ndarray        # (I,) latency durations
    D: np.ndarray        # (I,) infectiousness-to-detection durations
    alpha: np.ndarray    # (2,) (alpha1, alpha2)
    beta: np.ndarray     # (2,) (beta1, beta2)

    def copy(self) -> "State":
        return State(self.J.copy(), self.Tinf.copy(), self.L.copy(),
                     self.D.copy(), self.alpha.copy(), self.beta.copy())


# --------------------------------------------------------------------------- #
# Genetic model (Eqs. 2, 5; Text S1 Eq. 1)
# --------------------------------------------------------------------------- #
def log4_substitution(m: float, delta: np.ndarray) -> np.ndarray:
    """Return ``log[(3/4)(1 - exp(-4 m delta/3))]`` elementwise, the per-site
    probability of a difference under Jukes-Cantor (Eq. 2). ``delta`` may be 0."""
    delta = np.asarray(delta, dtype=float)
    x = 0.75 * (1.0 - np.exp(-4.0 * m * delta / 3.0))
    return x


def log_binom_coeff(s: float, M: np.ndarray) -> np.ndarray:
    """log C(s, M) using lgamma, for integer ``M`` and real sequence length ``s``."""
    M = np.asarray(M, dtype=float)
    return (math.lgamma(s + 1.0)
            - np.array([math.lgamma(mi + 1.0) for mi in M.ravel()]).reshape(M.shape)
            - np.vectorize(lambda mi: math.lgamma(s - mi + 1.0))(M))


def log_Pms(M: np.ndarray, delta: np.ndarray, m: float, s: float) -> np.ndarray:
    """log P_{m,s}(M | delta): probability of ``M`` substitutions over evolutionary
    duration ``delta`` (Eq. 2), vectorised over equal-shaped ``M`` and ``delta``.

    P = C(s,M) p^M (1-p)^(s-M), with p = (3/4)(1 - exp(-4 m delta/3)).
    """
    M = np.asarray(M, dtype=float)
    delta = np.asarray(delta, dtype=float)
    p = 0.75 * (1.0 - np.exp(-4.0 * m * np.abs(delta) / 3.0))
    p = np.clip(p, 1e-300, 1.0 - 1e-15)
    logp = np.log(p)
    log1mp = np.log1p(-p)
    out = log_binom_coeff(s, M) + M * logp + (s - M) * log1mp
    return out


def _path_to_root(i: int, J: np.ndarray) -> list[int]:
    """Premises from ``i`` up to the external root, inclusive: ``[i, J[i], ...]``."""
    path = [i]
    seen = {i}
    cur = i
    while J[cur] != -1:
        cur = int(J[cur])
        if cur in seen:          # guard against a malformed (cyclic) tree
            break
        seen.add(cur)
        path.append(cur)
    return path


def divergence_premise(a: int, b: int, J: np.ndarray, Tinf: np.ndarray) -> int:
    """Premise whose infection time is the divergence time of lineages ``a`` and ``b``.

    This is the tree traversal behind Eq. 5: ``div(i, j)`` in the paper. The
    evolutionary duration separating the two observed sequences is then
    ``|Tobs_a - Tinf[div]| + |Tobs_b - Tinf[div]|``.

    Rule, validated against the worked four-premise example of Fig. S1
    (Text S1 Eq. 3):

    * trace both premises to the external root;
    * if one is an ancestor of the other, the divergence premise is the child of
      the ancestor on the path down to the descendant (the step where the
      descendant's lineage first leaves the ancestor's trunk);
    * otherwise both branch off their most recent common ancestor ``m``; the
      lineages separate at the earlier of the two branch points, so the
      divergence premise is whichever child of ``m`` has the smaller infection
      time.
    """
    if a == b:
        return a
    pa = _path_to_root(a, J)
    pb = _path_to_root(b, J)
    set_b = set(pb)
    # most recent common ancestor: first node of pa that is also an ancestor of b
    mrca = None
    for node in pa:
        if node in set_b:
            mrca = node
            break
    if mrca is None:
        # disjoint introductions (two external roots): lineages never share an
        # ancestor premise; treat them as diverging at t0 via the earlier of a,b.
        return a if Tinf[a] <= Tinf[b] else b
    # child of mrca on the path toward a (None if a == mrca), and toward b
    def child_toward(path: list[int]) -> int | None:
        idx = path.index(mrca)
        return path[idx - 1] if idx > 0 else None

    ca = child_toward(pa)
    cb = child_toward(pb)
    if ca is None:               # a is an ancestor of b
        return cb
    if cb is None:               # b is an ancestor of a
        return ca
    return ca if Tinf[ca] <= Tinf[cb] else cb


def _ancestor_sets(J: np.ndarray, I: int):
    """For each premise, its ordered ancestor chain to the root and that set."""
    chains = []
    sets = []
    for i in range(I):
        chains.append(_path_to_root(i, J))
        sets.append(set(chains[-1]))
    return chains, sets


def _divergence_time(a, b, chains, sets, Tinf):
    """Fast ``Tinf`` of the divergence premise, given precomputed ancestor chains."""
    if a == b:
        return Tinf[a]
    pa, pb = chains[a], chains[b]
    sb = sets[b]
    mrca = None
    for node in pa:
        if node in sb:
            mrca = node
            break
    if mrca is None:
        return Tinf[a] if Tinf[a] <= Tinf[b] else Tinf[b]
    ia = pa.index(mrca)
    ib = pb.index(mrca)
    ca = pa[ia - 1] if ia > 0 else None
    cb = pb[ib - 1] if ib > 0 else None
    if ca is None:
        return Tinf[cb]
    if cb is None:
        return Tinf[ca]
    return Tinf[ca] if Tinf[ca] <= Tinf[cb] else Tinf[cb]


def _log_pms_scalar(M, delta, m, s, logc):
    """log P_{m,s}(M | delta) for scalars, using a precomputed ``log C(s, M)``."""
    p = 0.75 * (1.0 - math.exp(-4.0 * m * abs(delta) / 3.0))
    if p <= 1e-300:
        p = 1e-300
    elif p >= 1.0 - 1e-15:
        p = 1.0 - 1e-15
    return logc + M * math.log(p) + (s - M) * math.log1p(-p)


def genetic_log_pseudo_likelihood(state: State, data: Data) -> float:
    """log of the genetic pseudo-likelihood of Eq. 5.

    Product over every unordered pair {i, j} of ``P_{m,s}(M_ij | Delta_ij)`` with
    ``Delta_ij = |Tobs_i - Tinf[div]| + |Tobs_j - Tinf[div]|`` and
    ``div = divergence_premise(i, j)``. The first premise's own sequence term is
    discarded, exactly as in Eq. 5 (which starts the outer product at i = 2).
    """
    J, Tinf = state.J, state.Tinf
    I = data.I
    Tobs, M, m, s, logC = data.Tobs, data.M, data.m, data.s, data.logC
    chains, sets = _ancestor_sets(J, I)
    total = 0.0
    for i in range(I):
        Ti = Tobs[i]
        for j in range(i):
            tdiv = _divergence_time(i, j, chains, sets, Tinf)
            delta = abs(Ti - tdiv) + abs(Tobs[j] - tdiv)
            total += _log_pms_scalar(M[i, j], delta, m, s, logC[i, j])
    return total


# --------------------------------------------------------------------------- #
# Epidemiological / timing model (Eqs. 7, 8, 9)
# --------------------------------------------------------------------------- #
def _kernel_value(r: np.ndarray, alpha2: float) -> np.ndarray:
    """Exponential transmission kernel f_{alpha2}(r) = 1/(2 pi alpha2^2) exp(-r/alpha2)."""
    return 1.0 / (2.0 * math.pi * alpha2 * alpha2) * np.exp(-r / alpha2)


def _dist_matrix(X: np.ndarray) -> np.ndarray:
    diff = X[:, None, :] - X[None, :, :]
    return np.sqrt((diff * diff).sum(-1))


def transmission_log_likelihood(state: State, data: Data, dist: np.ndarray | None = None) -> float:
    """log p(J, Tinf | L, D, theta, ...) of Eq. 7.

    The likelihood is invariant to premise ordering: it is written over infectious
    windows and all pairs, which reproduces the paper's Tinf-sorted formulation
    without re-indexing. ``dist`` defaults to the cached distance matrix.
    """
    if dist is None:
        dist = data.dist
    J, Tinf, L = state.J, state.Tinf, state.L
    alpha1, alpha2 = state.alpha
    Tend = data.Tend
    I = data.I
    t0 = data.t0

    # external-source premise (there must be exactly one; J == -1)
    ext = np.where(J == -1)[0]
    if len(ext) != 1:
        return LOG_EPS
    first = int(ext[0])
    minTend = Tend.min()
    # Eq. 7 first factor: uniform source 1/I and uniform infection time on [t0, min Tend]
    if not (t0 <= Tinf[first] <= minTend):
        return LOG_EPS
    total = -math.log(I) - math.log(minTend - t0)

    # infectious window of each premise: [Tinf + L, Tend]
    inf_start = Tinf + L
    inf_end = Tend

    for i in range(I):
        if i == first:
            continue
        src = int(J[i])
        if src < 0:
            return LOG_EPS
        ti = Tinf[i]
        # hazard contribution integrated from t0 to ti over all premises j that
        # are infectious during [t0, ti]: alpha1 * f(d_ij) * (overlap length)
        lo = np.minimum(np.maximum(inf_start, t0), ti)
        hi = np.minimum(inf_end, ti)
        overlap = np.clip(hi - lo, 0.0, None)
        overlap[i] = 0.0
        integral = alpha1 * np.sum(overlap * _kernel_value(dist[i], alpha2))
        # density that i is infected by its source at ti: source must be infectious at ti
        if not (inf_start[src] <= ti <= inf_end[src]):
            return LOG_EPS
        rate = alpha1 * _kernel_value(dist[i, src], alpha2)
        if rate <= 0.0:
            return LOG_EPS
        total += -integral + math.log(rate)
    return total


def _gamma_logpdf(x: np.ndarray, shape: float, scale: float) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    out = np.full_like(x, LOG_EPS)
    ok = x > 0
    if shape <= 0 or scale <= 0:
        return out
    out[ok] = ((shape - 1.0) * np.log(x[ok]) - x[ok] / scale
               - shape * math.log(scale) - math.lgamma(shape))
    return out


def latency_detection_log_likelihood(state: State, data: Data) -> float:
    """log p(L, D | theta, Dobs) of Eq. 8.

    L_i ~ Gamma(shape=b1^2/b2^2, scale=b2^2/b1)   (mean b1, var b2^2)
    D_i ~ Gamma(shape=Dobs_i/d^2, scale=d^2)       (mean Dobs_i, var d^2 Dobs_i)
    """
    b1, b2 = state.beta
    if b1 <= 0 or b2 <= 0:
        return LOG_EPS
    shapeL = b1 * b1 / (b2 * b2)
    scaleL = b2 * b2 / b1
    logL = _gamma_logpdf(state.L, shapeL, scaleL).sum()
    d2 = data.d * data.d
    total = logL
    for i in range(data.I):
        shapeD = data.Dobs[i] / d2
        total += float(_gamma_logpdf(np.array([state.D[i]]), shapeD, d2)[0])
    return total


def prior_log_density(state: State, data: Data) -> float:
    """log p(theta) of Eq. 9: independent exponential priors with means ``prior_mean``."""
    a1, a2, b1, b2 = data.prior_mean
    vals = [state.alpha[0], state.alpha[1], state.beta[0], state.beta[1]]
    means = [a1, a2, b1, b2]
    total = 0.0
    for v, mu in zip(vals, means):
        if v <= 0:
            return LOG_EPS
        total += -math.log(mu) - v / mu
    return total


def log_posterior(state: State, data: Data, dist: np.ndarray | None = None) -> float:
    """Unnormalised log pseudo-posterior (Eq. 1 / Text S1 Eq. 4)."""
    if dist is None:
        dist = data.dist
    return (genetic_log_pseudo_likelihood(state, data)
            + transmission_log_likelihood(state, data, dist)
            + latency_detection_log_likelihood(state, data)
            + prior_log_density(state, data))


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def read_fasta(path) -> dict[str, str]:
    """Read a FASTA file into an ordered ``{name: sequence}`` dict.

    The header name is the first whitespace-delimited token after ``>``.
    """
    seqs: dict[str, str] = {}
    name = None
    buf: list[str] = []
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if name is not None:
                    seqs[name] = "".join(buf)
                name = line[1:].strip().split()[0]
                buf = []
            elif line:
                buf.append(line.strip())
    if name is not None:
        seqs[name] = "".join(buf)
    return seqs


def hamming_matrix(seqs: list[str]) -> np.ndarray:
    """Pairwise Hamming distances between equal-length sequences.

    Positions where either sequence has a non-ACGT character (gap, N) are
    ignored for that pair, then the count is rescaled to the full length so the
    binomial over ``s`` sites stays well defined.
    """
    arr = [np.frombuffer(s.upper().encode(), dtype=np.uint8) for s in seqs]
    L = len(arr[0])
    valid_bases = set(b"ACGT")
    valid = [np.array([c in valid_bases for c in a], dtype=bool) for a in arr]
    n = len(arr)
    M = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            both = valid[i] & valid[j]
            k = int(both.sum())
            if k == 0:
                M[i, j] = M[j, i] = 0.0
                continue
            diff = int(np.sum((arr[i] != arr[j]) & both))
            M[i, j] = M[j, i] = diff * (L / k)
    return M


def read_epi_table(path) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Read an epidemiological table ``Premise Latitude Longitude Tobs Tend Di``.

    Returns ``(names, lonlat, Tobs, Tend, Dobs)``. The tables in Datasets S2/S4
    pack several rows on a line with ragged whitespace; this tokeniser walks the
    fields in groups of six and tolerates that.
    """
    with open(path) as fh:
        text = fh.read()
    tokens = text.split()
    # drop the header row
    header = ["premise", "latitude", "longitude", "tobs", "tend", "di"]
    low = [t.lower() for t in tokens[:6]]
    if low == header:
        tokens = tokens[6:]
    names, lat, lon, Tobs, Tend, Dobs = [], [], [], [], [], []
    for k in range(0, len(tokens) - 5, 6):
        names.append(tokens[k])
        lat.append(float(tokens[k + 1]))
        lon.append(float(tokens[k + 2]))
        Tobs.append(float(tokens[k + 3]))
        Tend.append(float(tokens[k + 4]))
        Dobs.append(float(tokens[k + 5]))
    lonlat = np.column_stack([np.array(lon), np.array(lat)])
    return names, lonlat, np.array(Tobs), np.array(Tend), np.array(Dobs)


def lonlat_to_km(lonlat: np.ndarray, origin: np.ndarray | None = None) -> np.ndarray:
    """Equirectangular projection of (lon, lat) degrees to km, about the mean latitude.

    Over a cluster a few tens of km across this is accurate to well under the
    pixel resolution of the figures.
    """
    lon = lonlat[:, 0]
    lat = lonlat[:, 1]
    lat0 = lat.mean()
    R = 6371.0
    x = np.radians(lon) * R * math.cos(math.radians(lat0))
    y = np.radians(lat) * R
    xy = np.column_stack([x, y])
    if origin is None:
        origin = xy[0]
    return xy - origin


def example_path(name: str) -> Path:
    """Path of a bundled example data file (see data/README.md)."""
    path = resources.files(__name__) / "data" / name
    if not path.is_file():
        raise FileNotFoundError(f"no bundled example file {name!r}")
    return Path(str(path))


def read_dataset(epi_csv, hamming_csv, s: float, m: float, **kw) -> Data:
    """Build a :class:`Data` from an epidemiological CSV and a Hamming-distance CSV.

    ``epi_csv`` has a header ``premise,x_km,y_km,Tobs,Tend,Dobs``; ``hamming_csv``
    is a square integer matrix (no header), in the same premise order.
    """
    names, xs, ys, Tobs, Tend, Dobs = [], [], [], [], [], []
    with open(epi_csv) as fh:
        header = fh.readline()
        for line in fh:
            if not line.strip():
                continue
            p, x, y, to, te, do = line.strip().split(",")
            names.append(p)
            xs.append(float(x)); ys.append(float(y))
            Tobs.append(float(to)); Tend.append(float(te)); Dobs.append(float(do))
    X = np.column_stack([np.array(xs), np.array(ys)])
    M = np.loadtxt(hamming_csv, delimiter=",")
    if M.ndim == 1:
        M = M.reshape(len(names), len(names))
    return Data(names=names, X=X, Tobs=np.array(Tobs), Tend=np.array(Tend),
                Dobs=np.array(Dobs), M=M.astype(float), s=s, m=m, **kw)


# --------------------------------------------------------------------------- #
# MCMC
# --------------------------------------------------------------------------- #
@dataclass
class MCMCConfig:
    iters: int = 500_000
    burn_in_frac: float = 0.2
    thin: int = 1
    sigma_T: float = 10.0        # sqrt(sigma_T^2 = 100)  (Text S1)
    sigma_D: float = 1.0         # sqrt(sigma_D^2 = 1)
    seed: int = 0
    fix_tree: bool = False       # skip the J moves (profile one fixed tree)
    joint_jt: bool = True        # extra joint (J(i), Tinf_i) move for mixing (deviation)
    init_state: object = None    # optional starting State


@dataclass
class Posterior:
    """Summaries of one MCMC run."""

    trans_prob: np.ndarray                 # (I, I+1) P(J(i)=src); col I is external
    names: list[str]
    mean_latency: np.ndarray               # samples of beta1
    mean_distance: np.ndarray              # samples of 2*alpha2
    alpha1: np.ndarray
    alpha2: np.ndarray
    beta1: np.ndarray
    beta2: np.ndarray
    latency_sd: np.ndarray                 # samples of beta2
    infection_times: np.ndarray            # (nsamp, I)
    infectiousness_times: np.ndarray       # (nsamp, I) = Tinf + L
    best_tree: np.ndarray                  # (I,) MAP-by-frequency source of each premise
    best_tree_prob: float
    accept: dict
    n_samples: int

    def median_ci(self, samples: np.ndarray) -> tuple[float, float, float]:
        return (float(np.median(samples)),
                float(np.quantile(samples, 0.025)),
                float(np.quantile(samples, 0.975)))


def _descendants(i, J, I):
    """All premises that have ``i`` as an ancestor (so they cannot be i's source)."""
    desc = set()
    changed = True
    frontier = {i}
    while changed:
        changed = False
        for k in range(I):
            if J[k] in frontier and k not in desc and k != i:
                desc.add(k)
                frontier.add(k)
                changed = True
    return desc


def _feasible_sources(i, state, data):
    """Sources ``j`` that satisfy the timing constraints (5) for i and keep the
    tree acyclic (``j`` must not be a descendant of ``i``)."""
    out = []
    ti = state.Tinf[i]
    inf_start = state.Tinf + state.L
    desc = _descendants(i, state.J, data.I)
    for j in range(data.I):
        if j == i or j in desc:
            continue
        if inf_start[j] <= ti <= data.Tend[j]:
            out.append(j)
    return out


def _init_state(data: Data, rng: np.random.Generator) -> State:
    """A starting point satisfying the timing constraints (5), Text S1."""
    I = data.I
    order = list(np.argsort(data.Tobs))
    Tinf = np.zeros(I)
    L = np.zeros(I)
    D = np.minimum(data.Dobs.copy(), data.Tobs - data.t0 - 0.1)
    D = np.clip(D, 0.0, None)
    J = np.full(I, -2, dtype=int)
    root = order[0]
    J[root] = -1
    Tinf[root] = data.t0
    L[root] = data.Tobs[root] - Tinf[root] - D[root]
    placed = [root]
    for i in order[1:]:
        # earliest time any placed premise is infectious
        starts = [Tinf[p] + L[p] for p in placed]
        best = None
        for p, st in zip(placed, starts):
            hi = min(data.Tend[p], data.Tobs[i] - D[i])
            if st <= hi:
                cand_t = st
                if best is None or cand_t < best[1]:
                    best = (p, cand_t)
        if best is None:
            # relax: shrink D[i] so a source fits
            p = placed[int(np.argmin(starts))]
            st = Tinf[p] + L[p]
            D[i] = max(0.0, data.Tobs[i] - st - 0.1)
            best = (p, st)
        src, ti = best
        J[i] = src
        Tinf[i] = ti
        L[i] = data.Tobs[i] - Tinf[i] - D[i]
        placed.append(i)
    alpha = np.array([1.0, 5.0])
    beta = np.array([5.0, 2.0])
    return State(J, Tinf, L, D, alpha, beta)


def _trunc_norm_logZ(center, sigma, lo, hi):
    """log normalising constant of a Normal(center, sigma) truncated to [lo, hi]."""
    from math import erf, sqrt
    def Phi(x):
        return 0.5 * (1.0 + erf(x / sqrt(2.0)))
    z = Phi((hi - center) / sigma) - Phi((lo - center) / sigma)
    return math.log(max(z, 1e-300))


def _sample_trunc_norm(center, sigma, lo, hi, rng):
    for _ in range(100):
        x = center + sigma * rng.standard_normal()
        if lo <= x <= hi:
            return x
    return min(max(center, lo), hi)


def run_mcmc(data: Data, config: MCMCConfig | None = None) -> Posterior:
    """Run the Metropolis-Hastings sampler of Text S1 and summarise the posterior.

    The log pseudo-posterior is kept as four separate terms (genetic, transmission,
    latency/detection, prior); each proposal recomputes only the terms it changes,
    which is what makes 10^5-10^6 iterations tractable in Python.
    """
    if config is None:
        config = MCMCConfig()
    rng = np.random.default_rng(config.seed)
    dist = data.dist
    state = config.init_state.copy() if config.init_state is not None else _init_state(data, rng)
    I = data.I

    def _tinf_window(i, src, st):
        """Feasible [lo, hi] for Tinf_i if its source is ``src`` (a premise)."""
        lo = st.Tinf[src] + st.L[src]
        hi = min(data.Tend[src], data.Tobs[i] - st.D[i])
        kids = np.where(st.J == i)[0]
        if len(kids):
            hi = min(hi, st.Tinf[kids].min())
        return lo, hi

    def g(st):   # genetic
        return genetic_log_pseudo_likelihood(st, data)

    def t(st):   # transmission
        return transmission_log_likelihood(st, data, dist)

    def ld(st):  # latency/detection
        return latency_detection_log_likelihood(st, data)

    def pr(st):  # prior
        return prior_log_density(st, data)

    terms = {"g": g(state), "t": t(state), "ld": ld(state), "pr": pr(state)}
    cur_lp = sum(terms.values())

    n_keep = 0
    burn = int(config.iters * config.burn_in_frac)
    src_counts = np.zeros((I, I + 1))   # col I = external
    tree_counts: dict[tuple, int] = {}
    rec_dist, rec_a1, rec_a2, rec_b1, rec_b2 = ([] for _ in range(5))
    rec_tinf = []
    rec_infec = []
    acc = {k: [0, 0] for k in ("J1", "J", "Tinf", "D", "alpha", "beta")}

    def accept(new_state, new_terms, log_q_ratio, key):
        """MH step: ``new_terms`` holds only the terms that changed."""
        nonlocal state, cur_lp, terms
        acc[key][1] += 1
        new_lp = cur_lp + sum(new_terms[k] - terms[k] for k in new_terms)
        if math.log(rng.random() + 1e-300) < (new_lp - cur_lp) + log_q_ratio:
            state = new_state
            terms = {**terms, **new_terms}
            cur_lp = new_lp
            acc[key][0] += 1
            return True
        return False

    for it in range(config.iters):
        if not config.fix_tree:
            # ---- J(1): swap root with the second-infected premise ----
            order = np.argsort(state.Tinf)
            root = int(order[0])
            second = int(order[1])
            ns = state.copy()
            ns.Tinf[root], ns.Tinf[second] = state.Tinf[second], state.Tinf[root]
            ns.L[root], ns.L[second] = state.L[second], state.L[root]
            ns.J[second] = -1
            ns.J[root] = second
            ns.D[root] = data.Tobs[root] - ns.Tinf[root] - ns.L[root]
            ns.D[second] = data.Tobs[second] - ns.Tinf[second] - ns.L[second]
            if ns.D[root] >= 0 and ns.D[second] >= 0:
                accept(ns, {"g": g(ns), "t": t(ns), "ld": ld(ns)}, 0.0, "J1")

            # ---- J(i), i not root: uniform among feasible sources ----
            for i in range(I):
                if state.J[i] == -1:
                    continue
                feas = _feasible_sources(i, state, data)
                if not feas:
                    continue
                ns = state.copy()
                ns.J[i] = int(rng.choice(feas))
                if ns.J[i] == state.J[i]:
                    continue
                accept(ns, {"g": g(ns), "t": t(ns)}, 0.0, "J")

            # ---- joint (J(i), Tinf_i): resample source and infection time together.
            # Not one of the paper's moves; added so the chain can move a premise to
            # an early-infected source in one step (e.g. IP5 <- IP1b with a long
            # latency). It targets the same posterior; recorded as a deviation.
            if config.joint_jt:
                for i in range(I):
                    if state.J[i] == -1:
                        continue
                    desc = _descendants(i, state.J, I)
                    cand = []
                    for j in range(I):
                        if j == i or j in desc:
                            continue
                        lo, hi = _tinf_window(i, j, state)
                        if hi > lo:
                            cand.append((j, lo, hi))
                    if not cand:
                        continue
                    # reverse window for the current source (same candidate set)
                    cur_lo, cur_hi = _tinf_window(i, int(state.J[i]), state)
                    k = rng.integers(len(cand))
                    j_new, lo_new, hi_new = cand[k]
                    t_new = rng.uniform(lo_new, hi_new)
                    ns = state.copy()
                    ns.J[i] = j_new
                    ns.Tinf[i] = t_new
                    ns.L[i] = data.Tobs[i] - t_new - state.D[i]
                    if ns.L[i] < 0:
                        continue
                    log_q = math.log(hi_new - lo_new) - math.log(max(cur_hi - cur_lo, 1e-12))
                    accept(ns, {"g": g(ns), "t": t(ns), "ld": ld(ns)}, log_q, "J")

        # ---- Tinf_i (and L_i) ----
        for i in range(I):
            inf_start = state.Tinf + state.L
            children = np.where(state.J == i)[0]
            tmax = data.Tobs[i] - state.D[i]
            if len(children):
                tmax = min(tmax, state.Tinf[children].min())
            if state.J[i] == -1:
                tmin = data.t0
                tmax = min(tmax, data.Tend.min())
            else:
                src = int(state.J[i])
                tmin = inf_start[src]
                tmax = min(tmax, data.Tend[src])
            if not (tmax > tmin):
                continue
            new_t = _sample_trunc_norm(state.Tinf[i], config.sigma_T, tmin, tmax, rng)
            ns = state.copy()
            ns.Tinf[i] = new_t
            ns.L[i] = data.Tobs[i] - new_t - state.D[i]
            if ns.L[i] < 0:
                continue
            logZf = _trunc_norm_logZ(state.Tinf[i], config.sigma_T, tmin, tmax)
            logZr = _trunc_norm_logZ(new_t, config.sigma_T, tmin, tmax)
            accept(ns, {"g": g(ns), "t": t(ns), "ld": ld(ns)}, logZf - logZr, "Tinf")

        # ---- D_i (and L_i) ----
        for i in range(I):
            dmin = 0.0
            dmax = data.Tobs[i] - state.Tinf[i]
            if dmax <= dmin:
                continue
            new_d = _sample_trunc_norm(state.D[i], config.sigma_D, dmin, dmax, rng)
            ns = state.copy()
            ns.D[i] = new_d
            ns.L[i] = data.Tobs[i] - state.Tinf[i] - new_d
            if ns.L[i] < 0:
                continue
            logZf = _trunc_norm_logZ(state.D[i], config.sigma_D, dmin, dmax)
            logZr = _trunc_norm_logZ(new_d, config.sigma_D, dmin, dmax)
            accept(ns, {"t": t(ns), "ld": ld(ns)}, logZf - logZr, "D")

        # ---- alpha (bivariate log-normal) ----
        ns = state.copy()
        ns.alpha = state.alpha * np.exp(rng.standard_normal(2))
        log_q_ratio = math.log(ns.alpha[0] * ns.alpha[1]) - math.log(state.alpha[0] * state.alpha[1])
        accept(ns, {"t": t(ns), "pr": pr(ns)}, log_q_ratio, "alpha")

        # ---- beta (bivariate log-normal) ----
        ns = state.copy()
        ns.beta = state.beta * np.exp(rng.standard_normal(2))
        log_q_ratio = math.log(ns.beta[0] * ns.beta[1]) - math.log(state.beta[0] * state.beta[1])
        accept(ns, {"ld": ld(ns), "pr": pr(ns)}, log_q_ratio, "beta")

        # ---- record ----
        if it >= burn and (it - burn) % config.thin == 0:
            n_keep += 1
            for i in range(I):
                src = state.J[i]
                src_counts[i, I if src == -1 else src] += 1
            key = tuple(int(x) for x in state.J)
            tree_counts[key] = tree_counts.get(key, 0) + 1
            rec_b1.append(state.beta[0]); rec_b2.append(state.beta[1])
            rec_a1.append(state.alpha[0]); rec_a2.append(state.alpha[1])
            rec_dist.append(2.0 * state.alpha[1])
            rec_tinf.append(state.Tinf.copy())
            rec_infec.append((state.Tinf + state.L).copy())

    trans_prob = src_counts / max(n_keep, 1)
    best_key = max(tree_counts, key=tree_counts.get)
    best_tree = np.array(best_key)
    best_prob = tree_counts[best_key] / max(n_keep, 1)
    accept_rates = {k: (v[0] / v[1] if v[1] else 0.0) for k, v in acc.items()}
    return Posterior(
        trans_prob=trans_prob, names=list(data.names),
        mean_latency=np.array(rec_b1), mean_distance=np.array(rec_dist),
        alpha1=np.array(rec_a1), alpha2=np.array(rec_a2),
        beta1=np.array(rec_b1), beta2=np.array(rec_b2),
        latency_sd=np.array(rec_b2),
        infection_times=np.array(rec_tinf),
        infectiousness_times=np.array(rec_infec),
        best_tree=best_tree, best_tree_prob=best_prob,
        accept=accept_rates, n_samples=n_keep,
    )


# --------------------------------------------------------------------------- #
# Simulator (Materials and Methods, "Simulation datasets"; Text S1)
# --------------------------------------------------------------------------- #
def simulate_outbreak(n: int, alpha, beta, s: float, m: float, domain=(22.0, 11.0),
                      d: float = 0.5, t0: float = -5.0, seed: int = 0,
                      max_tries: int = 2000, fixed_X=None) -> tuple[Data, dict]:
    """Simulate an outbreak under the model and return observable ``Data`` plus the truth.

    Premises are placed uniformly in ``domain`` km (first at the origin), unless
    ``fixed_X`` gives their coordinates (used for the 2007/2001 performance series,
    which reuse the real premise layout). The spread is drawn from the model's own
    conditional distributions (Eq. 7 for the next infection, Eq. 8 for
    latency/detection), then genetic distances are drawn from the binomial of
    Eq. 2 along the realised tree. Detection-to-cull interval is one day for every
    premise (Text S1).
    """
    alpha1, alpha2 = alpha
    beta1, beta2 = beta
    rng = np.random.default_rng(seed)
    if fixed_X is not None:
        fixed_X = np.asarray(fixed_X, float)
        n = fixed_X.shape[0]
    for attempt in range(max_tries):
        if fixed_X is not None:
            X = fixed_X.copy()
        else:
            X = rng.uniform([0, 0], list(domain), size=(n, 2))
            X[0] = [0.0, 0.0]
        J = np.full(n, -2, dtype=int)
        Tinf = np.zeros(n)
        L = np.zeros(n)
        D = np.zeros(n)
        shapeL = beta1 * beta1 / (beta2 * beta2)
        scaleL = beta2 * beta2 / beta1
        # root
        J[0] = -1
        Tinf[0] = 0.0
        infected = [0]
        ok = True
        dist = _dist_matrix(X)
        order_idx = 1
        # draw latency for root
        L[0] = rng.gamma(shapeL, scaleL)
        for step in range(1, n):
            # candidate infectors are all currently infected premises; each exerts
            # hazard alpha1 f(d) while infectious. Simulate next infection time and source
            # via competing exponential-type hazards using a fine time grid.
            inf_start = Tinf + L
            # current time = max infection time so far; step forward until a new infection
            t = max(Tinf[infected])
            susceptible = [k for k in range(n) if J[k] == -2]
            if not susceptible:
                break
            dt = 0.05
            infected_new = None
            src_new = None
            tt = t
            for _ in range(200000):
                tt += dt
                # total hazard on each susceptible from infectious sources
                best = None
                total_haz = np.zeros(len(susceptible))
                for si, k in enumerate(susceptible):
                    haz = 0.0
                    for j in infected:
                        if inf_start[j] <= tt:   # infectious from inf_start with no removal in sim
                            haz += alpha1 * _kernel_value(dist[k, j], alpha2)
                    total_haz[si] = haz
                p_any = 1.0 - np.exp(-total_haz.sum() * dt)
                if rng.random() < p_any and total_haz.sum() > 0:
                    si = rng.choice(len(susceptible), p=total_haz / total_haz.sum())
                    infected_new = susceptible[si]
                    # choose source proportional to its hazard on that premise
                    w = np.array([alpha1 * _kernel_value(dist[infected_new, j], alpha2)
                                  if inf_start[j] <= tt else 0.0 for j in infected])
                    src_new = infected[int(rng.choice(len(infected), p=w / w.sum()))]
                    break
            if infected_new is None:
                ok = False
                break
            k = infected_new
            J[k] = src_new
            Tinf[k] = tt
            L[k] = rng.gamma(shapeL, scaleL)
            infected.append(k)
        if not ok or np.any(J == -2):
            continue
        # detection / removal
        Dobs = np.zeros(n)
        for i in range(n):
            # D_i ~ Gamma(mean Dobs, var d^2 Dobs); but Dobs is what clinicians assess.
            # Simulate a true Dobs first (lesion age), then D with that mean.
            Dobs[i] = rng.uniform(2, 12)
            shapeD = Dobs[i] / (d * d)
            scaleD = d * d
            D[i] = rng.gamma(shapeD, scaleD)
        Tobs = Tinf + L + D
        Tend = Tobs + 1.0   # one day detection-to-cull (Text S1)
        # genetic distances along the tree from the binomial (Eq. 2)
        # evolutionary duration between observed seqs via divergence premise
        st = State(J.copy(), Tinf.copy(), L.copy(), D.copy(),
                   np.array(alpha, float), np.array(beta, float))
        M = np.zeros((n, n))
        p_site_cache = {}
        for i in range(n):
            for j in range(i):
                dv = divergence_premise(i, j, J, Tinf)
                delta = abs(Tobs[i] - Tinf[dv]) + abs(Tobs[j] - Tinf[dv])
                p = 0.75 * (1.0 - math.exp(-4.0 * m * delta / 3.0))
                mij = rng.binomial(int(s), p)
                M[i, j] = M[j, i] = mij
        names = [f"F{i+1}" for i in range(n)]
        data = Data(names=names, X=X, Tobs=Tobs, Tend=Tend, Dobs=Dobs, M=M,
                    s=s, m=m, t0=t0, d=d)
        truth = dict(J=J, Tinf=Tinf, L=L, D=D, alpha=np.array(alpha, float),
                     beta=np.array(beta, float), X=X)
        return data, truth
    raise RuntimeError("simulation failed to infect all premises")
