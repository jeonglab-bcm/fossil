"""SP-SVM: zinc-binding residues from PSI-BLAST profiles (Passerini et al. 2007).

Two RBF support vector machines and a gating rule, implemented from the paper's Methods:

* the local predictor classifies one candidate residue from a window of 2k+1 profile descriptors;
* the semi-pattern predictor classifies a pair of candidate residues separated by a gap of 0-7
  residues, with the semi-pattern kernel of Eq. (1);
* each margin goes through a Platt sigmoid, and Eq. (2) combines them:
  P(bind) = P_sp + (1 - P_sp) * P_local, with P_sp the largest probability of the semi-patterns
  that contain the residue (0 when there is none).

The semi-pattern kernel (Eq. 1) is a sum of dot products: left window, right window, the mean
descriptor of the two gaps, and the full gap dot product when the gaps have the same length. It is
therefore the dot product of an explicit feature map (left, right, gap mean, and the gap placed in
a slot reserved for its length), and the Gaussian kernel on top of it is an ordinary RBF kernel on
that map. The local kernel is likewise an RBF kernel on the window vector.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from sklearn.svm import SVC

P = 23  # descriptor size: 20 profile frequencies, information, relative weight, out-of-chain flag
MAX_GAP = 7

# Model parameters of Additional file 1 (README), tuned by the authors on their 2005 profiles.
PAPER_PARAMS = {
    "CH": {
        "local": {"gamma": 0.1, "C": 5.0, "k": 5, "A": 2.6343, "B": -0.495946},
        "semipattern": {"gamma": 0.05, "C": 5.0, "k": 6, "A": 3.2717, "B": -0.077639},
    },
    "CHDE": {
        "local": {"gamma": 0.1, "C": 5.0, "k": 5, "A": 2.77445, "B": -0.533157},
        "semipattern": {"gamma": 0.05, "C": 5.0, "k": 6, "A": 3.35236, "B": -0.12628},
    },
}
DE_GAPS = (1, 3)  # semi-patterns with D or E are kept only for gaps 1-3 (SPCHDE-SVM)


# ----------------------------------------------------------------------------- profiles

@dataclass
class Profile:
    """A PSI-BLAST profile: sequence, weighted observed percentages (L x 20, as 0-1),
    information per position (bits) and relative weight of gapless real matches to pseudocounts."""

    sequence: str
    frequencies: np.ndarray
    information: np.ndarray
    weight: np.ndarray

    def __len__(self) -> int:
        return len(self.sequence)


def read_ascii_pssm(path) -> Profile:
    """Read a PSI-BLAST ``-out_ascii_pssm`` file."""
    seq, freq, info, wt = [], [], [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 44 and parts[0].isdigit() and len(parts[1]) == 1:
                seq.append(parts[1])
                freq.append([float(x) / 100.0 for x in parts[22:42]])
                info.append(float(parts[42]))
                wt.append(float(parts[43]))
    if not seq:
        raise ValueError(f"{path}: no profile rows")
    return Profile("".join(seq), np.array(freq), np.array(info), np.array(wt))


def write_profiles(profiles: dict[str, Profile], path) -> None:
    """Store profiles compactly (``.npz``): frequencies as integer percent, information and weight
    in hundredths, as the ASCII PSSM prints them. Reading back gives the parsed values."""
    names = sorted(profiles)
    arrays = {"names": np.array(names)}
    for i, n in enumerate(names):
        p = profiles[n]
        arrays[f"s{i}"] = np.frombuffer(p.sequence.encode(), dtype=np.uint8)
        arrays[f"f{i}"] = np.rint(p.frequencies * 100).astype(np.uint8)
        arrays[f"i{i}"] = np.rint(p.information * 100).astype(np.int32)
        arrays[f"w{i}"] = np.rint(p.weight * 100).astype(np.int32)
    np.savez_compressed(path, **arrays)


def read_profiles(path) -> dict[str, Profile]:
    """Read profiles written by :func:`write_profiles`."""
    z = np.load(path)
    out = {}
    for i, n in enumerate(z["names"]):
        out[str(n)] = Profile(
            bytes(z[f"s{i}"]).decode(),
            z[f"f{i}"].astype(float) / 100.0,
            z[f"i{i}"].astype(float) / 100.0,
            z[f"w{i}"].astype(float) / 100.0,
        )
    return out


def descriptors(profile: Profile) -> np.ndarray:
    """Position-specific descriptors, L x 23: frequencies, information, weight, flag (0 in chain)."""
    d = np.zeros((len(profile), P))
    d[:, :20] = profile.frequencies
    d[:, 20] = profile.information
    d[:, 21] = profile.weight
    return d


def _padded(desc: np.ndarray, pad: int) -> np.ndarray:
    """Descriptors with ``pad`` out-of-chain positions on each side (all-zero profile, flag 1)."""
    out = np.zeros((len(desc) + 2 * pad, P))
    out[pad:pad + len(desc)] = desc
    out[:pad, 22] = 1.0
    out[pad + len(desc):, 22] = 1.0
    return out


# ----------------------------------------------------------------------------- examples

def local_features(desc: np.ndarray, positions, k: int) -> np.ndarray:
    """Window vectors of size (2k+1)*23 centred on each position."""
    pad = _padded(desc, k)
    X = np.zeros((len(positions), (2 * k + 1) * P))
    for r, i in enumerate(positions):
        X[r] = pad[i:i + 2 * k + 1].ravel()
    return X


def semipattern_pairs(sequence: str, positions, variant: str = "CH", de_gaps=DE_GAPS):
    """Candidate semi-patterns: pairs (i, j) of candidate positions with gap j-i-1 in 0..7.

    Both residues must be candidates of the variant's residue types (C, H; or C, H, D, E). A pair
    that contains D or E is kept only when its gap is in ``de_gaps`` (inclusive)."""
    residues = "CH" if variant == "CH" else "CHDE"
    pos = sorted(p for p in positions if sequence[p] in residues)
    pairs = []
    for a, i in enumerate(pos):
        for j in pos[a + 1:]:
            gap = j - i - 1
            if gap > MAX_GAP:
                break
            if (sequence[i] in "DE" or sequence[j] in "DE") and not (de_gaps[0] <= gap <= de_gaps[1]):
                continue
            pairs.append((i, j))
    return pairs


def semipattern_features(desc: np.ndarray, pairs, k: int) -> np.ndarray:
    """Explicit feature map of the semi-pattern kernel (Eq. 1).

    [left window (k+1 positions ending at i) | right window (k+1 positions starting at j) |
     mean gap descriptor | gap descriptors in the slot of its length]. The dot product of two such
    vectors is K_sp: <left> + <right> + <mean gaps> + [same gap length] <gaps>. An empty gap
    contributes nothing."""
    w = (k + 1) * P
    offsets = np.cumsum([0] + [g * P for g in range(MAX_GAP + 1)])
    dim = 2 * w + P + int(offsets[-1])
    pad = _padded(desc, k)
    X = np.zeros((len(pairs), dim))
    for r, (i, j) in enumerate(pairs):
        gap = j - i - 1
        if not 0 <= gap <= MAX_GAP:
            raise ValueError(f"semi-pattern ({i}, {j}) has gap {gap}; gaps run from 0 to {MAX_GAP}")
        X[r, :w] = pad[i:i + k + 1].ravel()                    # positions i-k .. i
        X[r, w:2 * w] = pad[j + k:j + 2 * k + 1].ravel()       # positions j .. j+k
        if gap > 0:
            g = pad[i + k + 1:j + k]                            # positions i+1 .. j-1
            X[r, 2 * w:2 * w + P] = g.mean(axis=0)
            start = 2 * w + P + int(offsets[gap])
            X[r, start:start + gap * P] = g.ravel()
    return X


def semipattern_kernel(desc_x, pair_x, desc_z, pair_z, k: int) -> float:
    """K_sp of Eq. (1), computed directly from its definition (to check the feature map)."""
    w = k + 1
    px, pz = _padded(desc_x, k), _padded(desc_z, k)
    (i, j), (u, v) = pair_x, pair_z
    left = np.sum(px[i:i + w] * pz[u:u + w])
    right = np.sum(px[j + k:j + k + w] * pz[v + k:v + k + w])
    gx, gz = px[i + k + 1:j + k], pz[u + k + 1:v + k]
    kgap = 0.0
    if len(gx) and len(gz):
        kgap = float(gx.mean(axis=0) @ gz.mean(axis=0))
        if len(gx) == len(gz):
            kgap += float(np.sum(gx * gz))
    return float(left + right + kgap)


# ----------------------------------------------------------------------------- model

def platt(margin, A: float, B: float):
    """P(Y=1|x) = 1 / (1 + exp(-A f(x) - B))."""
    return 1.0 / (1.0 + np.exp(-A * np.asarray(margin, dtype=float) - B))


def fit_platt(margins, labels, iterations: int = 100):
    """Fit the Platt sigmoid P = 1 / (1 + exp(-A f - B)) to held-out margins (Platt 2000, with
    its smoothed targets), by Newton's method. Returns (A, B) in this module's sign convention."""
    f = np.asarray(margins, dtype=float)
    y = np.asarray(labels, dtype=int)
    n1, n0 = int(y.sum()), int(len(y) - y.sum())
    t = np.where(y == 1, (n1 + 1.0) / (n1 + 2.0), 1.0 / (n0 + 2.0))
    a, b = 1.0, float(np.log((n1 + 1.0) / (n0 + 1.0)))
    for _ in range(iterations):
        p = 1.0 / (1.0 + np.exp(-(a * f + b)))
        g = np.array([np.sum((p - t) * f), np.sum(p - t)])
        w = p * (1 - p) + 1e-12
        h = np.array([[np.sum(w * f * f), np.sum(w * f)], [np.sum(w * f), np.sum(w)]]) + 1e-9 * np.eye(2)
        step = np.linalg.solve(h, g)
        a, b = a - step[0], b - step[1]
        if np.max(np.abs(step)) < 1e-10:
            break
    return float(a), float(b)


@dataclass
class Chain:
    """One protein chain: its descriptors and its candidate residues.

    ``candidates`` maps a 0-based position to its label (1 binds zinc, 0 does not, None unknown)."""

    name: str
    sequence: str
    desc: np.ndarray
    candidates: dict = field(default_factory=dict)


def chain_from_profile(name: str, profile: Profile, candidates=None, residues: str = "CH",
                       min_weight: float = 0.0) -> Chain:
    """A chain whose candidates are all residues of ``residues`` (unlabelled) unless given.
    ``min_weight`` drops positions whose profile relative weight is below it (the paper: 0.015)."""
    if candidates is None:
        candidates = {i: None for i, a in enumerate(profile.sequence)
                      if a in residues and profile.weight[i] >= min_weight}
    return Chain(name, profile.sequence, descriptors(profile), dict(candidates))


class SPSVM:
    """Local SVM + semi-pattern SVM + gating (Eq. 2).

    ``variant`` is "CH" (SPCH-SVM) or "CHDE" (SPCHDE-SVM); ``params`` defaults to the tuned values
    of Additional file 1, Platt constants included."""

    def __init__(self, variant: str = "CH", params: dict | None = None):
        if variant not in PAPER_PARAMS:
            raise ValueError("variant must be 'CH' or 'CHDE'")
        self.variant = variant
        self.params = params or PAPER_PARAMS[variant]
        self.local = None
        self.semipattern = None

    def _pairs(self, c: Chain):
        return semipattern_pairs(c.sequence, c.candidates, self.variant)

    def local_examples(self, chains):
        k = self.params["local"]["k"]
        X, y = [], []
        for c in chains:
            pos = sorted(c.candidates)
            if pos:
                X.append(local_features(c.desc, pos, k))
                y.extend(c.candidates[p] for p in pos)
        return (np.vstack(X) if X else np.zeros((0, (2 * k + 1) * P))), y

    def semipattern_examples(self, chains):
        """Pairs are positive when both residues bind zinc, even different ions (as in the paper)."""
        k = self.params["semipattern"]["k"]
        X, y = [], []
        for c in chains:
            pairs = self._pairs(c)
            if pairs:
                X.append(semipattern_features(c.desc, pairs, k))
                y.extend(1 if (c.candidates[i] and c.candidates[j]) else 0 for i, j in pairs)
        return (np.vstack(X) if X else None), y

    def fit(self, chains):
        Xl, yl = self.local_examples(chains)
        if any(v is None for v in yl):
            raise ValueError("every training candidate needs a label")
        if len(set(yl)) < 2:
            raise ValueError("training needs positive and negative residues")
        pl = self.params["local"]
        self.local = SVC(kernel="rbf", gamma=pl["gamma"], C=pl["C"], cache_size=2000).fit(Xl, yl)
        Xs, ys = self.semipattern_examples(chains)
        ps = self.params["semipattern"]
        self.semipattern = None
        if Xs is not None and len(set(ys)) == 2:
            self.semipattern = SVC(kernel="rbf", gamma=ps["gamma"], C=ps["C"], cache_size=2000).fit(Xs, ys)
        return self

    def margins(self, chain: Chain):
        """Raw SVM margins: local per candidate position, semi-pattern per pair."""
        if self.local is None:
            raise RuntimeError("fit the model first")
        pl, ps = self.params["local"], self.params["semipattern"]
        pos = sorted(chain.candidates)
        loc = {}
        if pos:
            loc = dict(zip(pos, self.local.decision_function(local_features(chain.desc, pos, pl["k"]))))
        pairs = self._pairs(chain)
        sp = {}
        if pairs and self.semipattern is not None:
            sp = dict(zip(pairs, self.semipattern.decision_function(semipattern_features(chain.desc, pairs, ps["k"]))))
        return loc, sp

    def predict_chain(self, chain: Chain) -> dict:
        """Per candidate position: local, semi-pattern and gated probabilities."""
        loc, sp = self.margins(chain)
        return gate(loc, sp, self.params)


def gate(local_margins: dict, sp_margins: dict, params: dict) -> dict:
    """Platt-scale the margins and combine them with Eq. (2)."""
    pl, ps = params["local"], params["semipattern"]
    out = {p: {"local": float(platt(f, pl["A"], pl["B"])), "semipattern": 0.0} for p, f in local_margins.items()}
    for (i, j), f in sp_margins.items():
        q = float(platt(f, ps["A"], ps["B"]))
        for p in (i, j):
            if p in out:
                out[p]["semipattern"] = max(out[p]["semipattern"], q)
    for v in out.values():
        v["gated"] = v["semipattern"] + (1.0 - v["semipattern"]) * v["local"]
    return out


def predict_protein(probabilities: dict, threshold: float = 0.7, min_residues: int = 3) -> bool:
    """A chain is zinc-binding when at least ``min_residues`` residues have gated probability above
    ``threshold`` (0.7 and 3 in the paper's proteome scan)."""
    return sum(1 for v in probabilities.values() if v["gated"] > threshold) >= min_residues


# ----------------------------------------------------------------------------- evaluation

def pr_curve(scores, labels):
    """Recall-precision points at every distinct threshold, highest score first."""
    s = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=int)
    order = np.argsort(-s, kind="mergesort")
    s, y = s[order], y[order]
    tp = np.cumsum(y)
    fp = np.cumsum(1 - y)
    last = np.r_[np.diff(s) != 0, True]
    tp, fp = tp[last], fp[last]
    return tp / y.sum(), tp / (tp + fp)


def aurpc(scores, labels, method: str = "average_precision") -> float:
    """Area under the recall-precision curve.

    ``average_precision``: sum over thresholds of precision times the recall step;
    ``trapezoid``: straight lines between the points, starting from recall 0 at the first precision."""
    r, p = pr_curve(scores, labels)
    if method == "average_precision":
        return float(np.sum(np.diff(np.r_[0.0, r]) * p))
    if method == "trapezoid":
        rr, pp = np.r_[0.0, r], np.r_[p[0], p]
        return float(np.sum(np.diff(rr) * (pp[1:] + pp[:-1]) / 2))
    raise ValueError(f"unknown method {method!r}")


def auc_with_se(scores, labels):
    """ROC AUC (Wilcoxon-Mann-Whitney, ties counted half) and its Hanley-McNeil standard error."""
    from scipy.stats import rankdata

    s = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=int)
    ranks = rankdata(s)
    n1, n0 = int(y.sum()), int(len(y) - y.sum())
    if n1 == 0 or n0 == 0:
        raise ValueError("AUC needs positive and negative examples")
    auc = (ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    q1, q2 = auc / (2 - auc), 2 * auc * auc / (1 + auc)
    se = math.sqrt((auc * (1 - auc) + (n1 - 1) * (q1 - auc * auc) + (n0 - 1) * (q2 - auc * auc)) / (n1 * n0))
    return float(auc), float(se)


def protein_scores(chain_probs: dict, min_residues: int = 3) -> dict:
    """Chain score for the protein-level curve: its ``min_residues``-th highest gated probability
    (a chain is called at threshold t when that many residues are above t); 0 with fewer residues."""
    out = {}
    for n, probs in chain_probs.items():
        g = sorted((v["gated"] for v in probs.values()), reverse=True)
        out[n] = g[min_residues - 1] if len(g) >= min_residues else 0.0
    return out


def read_table(path):
    """Read a candidate table: whitespace-separated ``class chain position residue [cofactor]`` rows,
    the format of the paper's Additional file 1. Returns {chain: {position: label}} (label 1 or 0)."""
    out: dict[str, dict] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[0] not in ("1", "-1"):
            continue
        out.setdefault(parts[1], {})[int(parts[2])] = 1 if parts[0] == "1" else 0
    return out
