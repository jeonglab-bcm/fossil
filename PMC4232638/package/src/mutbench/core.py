"""The benchmark of Martelotto et al. (2014), implemented from the paper's text.

Calls of each predictor are merged into two categories (non-neutral 1, neutral 0); a call the predictor
did not make (CanDrA 'No-call', FATHMM 'No weights', Mutation Assessor N/A) is missing (NaN).

- performance(): accuracy, sensitivity, specificity, PPV, NPV and the composite score
  (sensitivity + specificity + PPV + NPV) of one predictor against the functional labels. Missing calls
  are left out of every count.
- bootstrap_ci(): 95% percentile intervals from resampling the labelled mutations with replacement.
- cohen_kappa(): unweighted Cohen's kappa between two predictors, with the missing call kept as a third
  category ('equivocal'), and the interval kappa +/- 1.96 SE0 (1.96 exactly, as the paper's intervals show), SE0 being the standard error under the null
  hypothesis (Fleiss, Cohen and Everitt 1969), the upper end capped at 1.
- hclust_complete(): complete-linkage clustering with R's hclust merge conventions.
- low_confidence(): the three-category calls (non-neutral, neutral, low confidence) of the paper's Methods.
- combination_calls() and split_sample(): the 'at least p of n' combinations of single predictors and
  their performance over random two-thirds / one-third splits.
"""

from __future__ import annotations

import csv
import itertools
import math
import warnings
from typing import Iterable, Sequence

import numpy as np

STATS = ("accuracy", "sensitivity", "specificity", "ppv", "npv", "composite")

# The paper's merge of each predictor's categories into two (Methods, 'Assessment of mutation effect
# predictors'), keyed by the lower-case category.
NON_NEUTRAL = {
    "driver", "cancer", "damaging", "deleterious", "functional", "disease", "d",
    "high", "medium", "disease_causing", "disease_causing_automatic",
    "probably damaging", "possibly damaging",
}
NEUTRAL = {
    "passenger", "passenger/other", "tolerated", "neutral", "benign", "n", "low",
    "polymorphism", "polymorphism_automatic",
}

# Low-confidence score intervals (Methods), end points included.
LOW_CONFIDENCE_SCORE = {
    "CHASM": (0.25, 0.35),
    "FATHMM (cancer)": (-1.65, 0.1),
    "FATHMM (missense)": (-2.5, 0.0),
    "PROVEAN": (-4.1, -1.3),
    "SIFT": (0.04, 0.1),
    "VEST": (0.45, 0.55),
    "Condel": (0.489, 0.547),
}
MUTATIONTASTER_LOW = 0.95  # probability at or below which a MutationTaster call is of low confidence


def _missing(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or (isinstance(v, str) and not v.strip())


def binary_call(category) -> float:
    """1.0 for a non-neutral call, 0.0 for a neutral one, NaN for no call."""
    if _missing(category):
        return math.nan
    k = str(category).strip().lower()
    if k in NON_NEUTRAL:
        return 1.0
    if k in NEUTRAL:
        return 0.0
    return math.nan


def binary_calls(categories: Iterable) -> np.ndarray:
    return np.array([binary_call(c) for c in categories], dtype=float)


def label_vector(labels: Iterable) -> np.ndarray:
    """Functional labels to 1.0 (non-neutral), 0.0 (neutral) or NaN (uncertain or missing)."""
    out = []
    for v in labels:
        k = "" if _missing(v) else str(v).strip().lower()
        out.append(1.0 if k in ("non-neutral", "1", "1.0") else 0.0 if k in ("neutral", "0", "0.0") else math.nan)
    return np.array(out, dtype=float)


def _ratio(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(b > 0, a / np.where(b > 0, b, 1), np.nan)


def _stats_from_counts(tp, tn, fp, fn):
    n = tp + tn + fp + fn
    out = {
        "accuracy": _ratio(tp + tn, n),
        "sensitivity": _ratio(tp, tp + fn),
        "specificity": _ratio(tn, tn + fp),
        "ppv": _ratio(tp, tp + fp),
        "npv": _ratio(tn, tn + fn),
    }
    out["composite"] = out["sensitivity"] + out["specificity"] + out["ppv"] + out["npv"]
    return out


def performance(labels, calls) -> dict:
    """Performance of one predictor. labels and calls are 1/0/NaN arrays; pairs with a NaN are left out.

    Returns the counts (n, tp, tn, fp, fn) and the six statistics as fractions (composite 0 to 4);
    a statistic whose denominator is 0 is NaN.
    """
    y = np.asarray(labels, dtype=float)
    c = np.asarray(calls, dtype=float)
    if y.shape != c.shape:
        raise ValueError("labels and calls differ in length")
    m = ~np.isnan(y) & ~np.isnan(c)
    y, c = y[m], c[m]
    tp = int(np.sum((c == 1) & (y == 1)))
    tn = int(np.sum((c == 0) & (y == 0)))
    fp = int(np.sum((c == 1) & (y == 0)))
    fn = int(np.sum((c == 0) & (y == 1)))
    out = {"n": tp + tn + fp + fn, "tp": tp, "tn": tn, "fp": fp, "fn": fn}
    out.update({k: float(v) for k, v in _stats_from_counts(tp, tn, fp, fn).items()})
    return out


def bootstrap_ci(labels, calls, n_boot: int = 1000, seed: int = 0, level: float = 0.95) -> dict:
    """Percentile bootstrap intervals of the six statistics (labelled mutations with a call resampled
    with replacement, not stratified). Returns {stat: (low, high)}; NaN replicates are dropped."""
    y = np.asarray(labels, dtype=float)
    c = np.asarray(calls, dtype=float)
    m = ~np.isnan(y) & ~np.isnan(c)
    y, c = y[m], c[m]
    n = len(y)
    if n == 0:
        raise ValueError("no labelled mutation with a call")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    Y, C = y[idx], c[idx]
    tp = np.sum((C == 1) & (Y == 1), axis=1)
    tn = np.sum((C == 0) & (Y == 0), axis=1)
    fp = np.sum((C == 1) & (Y == 0), axis=1)
    fn = np.sum((C == 0) & (Y == 1), axis=1)
    reps = _stats_from_counts(tp, tn, fp, fn)
    q = [100 * (1 - level) / 2, 100 * (1 + level) / 2]
    out = {}
    for k in STATS:
        v = reps[k][~np.isnan(reps[k])]
        out[k] = tuple(float(x) for x in np.percentile(v, q)) if len(v) else (math.nan, math.nan)
    return out


def ci_better(ci_a, ci_b) -> bool:
    """The paper's significance rule: A is significantly higher than B when their intervals touch or do
    not overlap, with A above (low end of A at or above the high end of B)."""
    return bool(ci_a[0] >= ci_b[1])


def _categories(calls):
    """Calls to category codes: 1 non-neutral, 0 neutral, 2 equivocal (no call)."""
    c = np.asarray(calls, dtype=float)
    return np.where(np.isnan(c), 2, c).astype(int)


def cohen_kappa(calls_a, calls_b, z: float = 1.96) -> tuple[float, float, float]:
    """Unweighted Cohen's kappa of two predictors over the same mutations, with a missing call as a third
    category. Returns (kappa, low, high), the interval being kappa +/- z * SE0 (SE under kappa = 0),
    clipped to [-1, 1]."""
    a, b = _categories(calls_a), _categories(calls_b)
    if a.shape != b.shape:
        raise ValueError("calls differ in length")
    n = len(a)
    t = np.zeros((3, 3))
    np.add.at(t, (a, b), 1)
    t /= n
    po = np.trace(t)
    r, s = t.sum(1), t.sum(0)
    pe = float(np.sum(r * s))
    if pe >= 1:
        return 1.0, 1.0, 1.0
    k = (po - pe) / (1 - pe)
    se0 = math.sqrt(max(pe + pe**2 - float(np.sum(r * s * (r + s))), 0.0) / n) / (1 - pe)
    return float(k), float(max(-1.0, k - z * se0)), float(min(1.0, k + z * se0))


def kappa_matrix(calls: dict) -> dict:
    """Pairwise kappa of every pair of predictors: {(name_a, name_b): (kappa, low, high)}."""
    names = list(calls)
    return {(a, b): cohen_kappa(calls[a], calls[b]) for a in names for b in names}


def landis_koch(k: float) -> str:
    """The paper's agreement bands."""
    if k < 0.01:
        return "no"
    if k <= 0.20:
        return "slight"
    if k <= 0.40:
        return "fair"
    if k <= 0.60:
        return "moderate"
    if k <= 0.80:
        return "substantial"
    return "almost perfect"


def hamming_matrix(rows: Sequence) -> np.ndarray:
    """Number of positions at which two rows of category codes differ (a missing call is its own code)."""
    X = np.array([_categories(r) for r in rows])
    return (X[:, None, :] != X[None, :, :]).sum(axis=2)


def hclust_complete(D) -> tuple[np.ndarray, np.ndarray]:
    """Complete-linkage clustering of a distance matrix with R's hclust conventions.

    Returns (merge, height): merge has one row per step; a negative entry -i is leaf i (1-based), a
    positive entry j is the cluster formed at step j. Ties go to the first pair found.
    """
    D = np.array(D, dtype=float)
    n = D.shape[0]
    if n < 2:
        raise ValueError("need at least two objects")
    np.fill_diagonal(D, np.inf)
    active = list(range(n))
    label = {i: -(i + 1) for i in range(n)}
    merges, heights = [], []
    for step in range(1, n):
        best, bi, bj = np.inf, None, None
        for x, i in enumerate(active):
            for j in active[x + 1:]:
                if D[i, j] < best:
                    best, bi, bj = D[i, j], i, j
        li, lj = label[bi], label[bj]
        if li < 0 and lj < 0:
            pair = sorted((li, lj), reverse=True)
        elif li < 0 or lj < 0:
            pair = [min(li, lj), max(li, lj)]
        else:
            pair = sorted((li, lj))
        merges.append(pair)
        heights.append(best)
        for k in active:
            if k not in (bi, bj):
                D[bi, k] = D[k, bi] = max(D[bi, k], D[bj, k])
        D[bj, :] = np.inf
        D[:, bj] = np.inf
        active.remove(bj)
        label[bi] = step
    return np.array(merges, dtype=int), np.array(heights, dtype=float)


def clades(merge) -> list[frozenset]:
    """The leaves (0-based) under each merge step, in step order."""
    out: list[frozenset] = []
    for a, b in merge:
        s = set()
        for v in (a, b):
            s |= {-v - 1} if v < 0 else set(out[v - 1])
        out.append(frozenset(s))
    return out


def leaf_order(merge) -> list[int]:
    """Leaf order (0-based) of the dendrogram as R draws it, without reordering."""
    def walk(k):
        if k < 0:
            return [-k - 1]
        a, b = merge[k - 1]
        return walk(a) + walk(b)

    return walk(len(merge))


def low_confidence(predictor: str, categories: Iterable, scores: Iterable) -> list[str]:
    """Three-category calls: 'non-neutral', 'neutral' or 'low'.

    Low confidence (Methods): CanDrA 'No-call', PolyPhen-2 'possibly damaging', Mutation Assessor 'low',
    MutationTaster probability <= 0.95, and the score intervals in LOW_CONFIDENCE_SCORE (end points
    included) for CHASM, FATHMM, PROVEAN, SIFT, VEST and Condel. A call the predictor did not make
    (FATHMM 'No weights', Mutation Assessor N/A) is also of low confidence.
    """
    out = []
    key = "CHASM" if predictor.startswith("CHASM") else predictor
    for cat, sc in zip(categories, scores):
        c = binary_call(cat)
        k = "" if _missing(cat) else str(cat).strip().lower()
        try:
            s = float(sc)
        except (TypeError, ValueError):
            s = math.nan
        if math.isnan(c):
            low = True
        elif predictor.startswith("CanDrA"):
            low = k == "no-call"
        elif predictor == "PolyPhen-2":
            low = k == "possibly damaging"
        elif predictor == "Mutation Assessor":
            low = k == "low"
        elif predictor == "MutationTaster":
            low = s <= MUTATIONTASTER_LOW
        elif key in LOW_CONFIDENCE_SCORE:
            lo, hi = LOW_CONFIDENCE_SCORE[key]
            low = lo <= s <= hi
        else:
            raise ValueError(f"no low-confidence rule for {predictor!r}")
        out.append("low" if low else ("non-neutral" if c == 1 else "neutral"))
    return out


def kappa_categorical(a: Sequence, b: Sequence, z: float = 1.96) -> tuple[float, float, float]:
    """Cohen's kappa for any categories (for example the three-category low-confidence calls)."""
    cats = sorted(set(a) | set(b), key=str)
    code = {c: i for i, c in enumerate(cats)}
    A = np.array([code[x] for x in a])
    B = np.array([code[x] for x in b])
    t = np.zeros((len(cats), len(cats)))
    np.add.at(t, (A, B), 1)
    t /= len(A)
    po, r, s = np.trace(t), t.sum(1), t.sum(0)
    pe = float(np.sum(r * s))
    if pe >= 1:
        return 1.0, 1.0, 1.0
    k = (po - pe) / (1 - pe)
    se0 = math.sqrt(max(pe + pe**2 - float(np.sum(r * s * (r + s))), 0.0) / len(A)) / (1 - pe)
    return float(k), float(max(-1.0, k - z * se0)), float(min(1.0, k + z * se0))


def combinations(predictors: Sequence[str], n_min: int = 2) -> list[tuple[tuple[str, ...], int]]:
    """Every 'at least p of n' rule: subsets of n_min or more predictors, p = 1..n.

    Ordered as in the paper's Additional file 17: by p, then by the subsets in lexicographic order of
    the predictor list. With 11 predictors there are 11,253.
    """
    idx = range(len(predictors))
    subsets = [s for n in range(n_min, len(predictors) + 1) for s in itertools.combinations(idx, n)]
    subsets.sort()
    out = []
    for p in range(1, len(predictors) + 1):
        for s in subsets:
            if p <= len(s):
                out.append((tuple(predictors[i] for i in s), p))
    return out


def combination_name(members: Sequence[str], p: int) -> str:
    return f"At least {p} of {', '.join(members)}"


def combination_calls(calls: dict, combos: Sequence[tuple[Sequence[str], int]]) -> np.ndarray:
    """Calls of each combination (rows) for each mutation (columns): 1 when at least p of the n members
    call it non-neutral. A missing call does not count as non-neutral."""
    names = list(calls)
    M = np.array([np.nan_to_num(np.asarray(calls[k], dtype=float), nan=0.0) for k in names])
    pos = {k: i for i, k in enumerate(names)}
    out = np.empty((len(combos), M.shape[1]), dtype=np.uint8)
    cache: dict = {}
    for r, (members, p) in enumerate(combos):
        key = tuple(members)
        if key not in cache:
            cache[key] = M[[pos[m] for m in members]].sum(axis=0)
        out[r] = cache[key] >= p
    return out


def random_splits(n: int, n_splits: int = 1000, frac: float = 2 / 3, seed: int = 0) -> np.ndarray:
    """Membership of subset 1 (round(frac * n) mutations drawn without replacement, not stratified) in
    each of n_splits random splits; subset 2 is the rest."""
    rng = np.random.default_rng(seed)
    k = int(round(frac * n))
    S = np.zeros((n_splits, n), dtype=bool)
    for i in range(n_splits):
        S[i, rng.choice(n, size=k, replace=False)] = True
    return S


def split_sample(labels, combo_calls: np.ndarray, splits: np.ndarray, level: float = 0.95, chunk: int = 2048) -> dict:
    """Performance of each combination in subset 1 and subset 2 of every split.

    labels: 1/0 for the mutations (no missing values); combo_calls: rows of 0/1 calls (combination_calls);
    splits: subset-1 membership (random_splits). Returns {"subset1": {stat: {"mean", "low", "high"}},
    "subset2": ...}, each an array over the combinations; the mean and the percentile interval are over the
    splits, leaving out splits where a statistic is undefined; "sd" is the standard deviation over the
    splits and "n" the number of splits where the statistic is defined.
    """
    y = np.asarray(labels, dtype=float)
    if np.isnan(y).any():
        raise ValueError("labels must be 1 or 0")
    C = np.asarray(combo_calls, dtype=np.float32)
    S1 = splits.astype(np.float32)
    q = [100 * (1 - level) / 2, 100 * (1 + level) / 2]
    out = {s: {k: {"mean": [], "sd": [], "n": [], "low": [], "high": []} for k in STATS} for s in ("subset1", "subset2")}
    P_all, n_all = float(y.sum()), len(y)
    P1 = S1 @ y.astype(np.float32)
    n1 = S1.sum(axis=1)
    for start in range(0, C.shape[0], chunk):
        Cc = C[start:start + chunk]
        TP1 = S1 @ (Cc * y).T
        PP1 = S1 @ Cc.T
        TPa = (Cc * y).sum(axis=1)
        PPa = Cc.sum(axis=1)
        for name, tp, pp, P, n in (
            ("subset1", TP1, PP1, P1[:, None], n1[:, None]),
            ("subset2", TPa[None, :] - TP1, PPa[None, :] - PP1, P_all - P1[:, None], n_all - n1[:, None]),
        ):
            fp = pp - tp
            fn = P - tp
            tn = n - P - fp
            st = _stats_from_counts(tp.astype(float), tn.astype(float), fp.astype(float), fn.astype(float))
            for k in STATS:
                v = st[k]
                with np.errstate(all="ignore"), warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    out[name][k]["mean"].append(np.nanmean(v, axis=0))
                    out[name][k]["sd"].append(np.nanstd(v, axis=0, ddof=1))
                    out[name][k]["n"].append(np.sum(~np.isnan(v), axis=0))
                    lo, hi = np.nanpercentile(v, q, axis=0)
                out[name][k]["low"].append(lo)
                out[name][k]["high"].append(hi)
    for s in out.values():
        for k in s.values():
            for part in ("mean", "sd", "n", "low", "high"):
                k[part] = np.concatenate(k[part])
    return out


def rank(values, descending: bool = True) -> np.ndarray:
    """Indices sorting the values, best first; ties keep the input order."""
    v = np.asarray(values, dtype=float)
    v = np.where(np.isnan(v), -np.inf if descending else np.inf, v)
    return np.argsort(-v if descending else v, kind="stable")


def recurrence(members_of_ranked: Sequence[Sequence[str]], predictors: Sequence[str], top: int) -> dict:
    """Percentage of the top combinations that include each predictor."""
    chosen = members_of_ranked[:top]
    return {p: 100.0 * sum(p in m for m in chosen) / len(chosen) for p in predictors}


def read_calls_csv(path) -> tuple[np.ndarray, dict]:
    """Read a CSV with a column 'label' (non-neutral, neutral or anything else for unlabelled) and one
    column per predictor holding its categories. Returns (labels, {predictor: calls})."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or "label" not in rows[0]:
        raise ValueError("the input needs a column 'label'")
    preds = [k for k in rows[0] if k not in ("label", "id", "gene", "mutation")]
    if not preds:
        raise ValueError("the input has no predictor columns")
    labels = label_vector(r["label"] for r in rows)
    calls = {p: binary_calls(r[p] for r in rows) for p in preds}
    return labels, calls


def evaluate(labels, calls: dict, n_boot: int = 1000, seed: int = 0) -> list[dict]:
    """Performance and bootstrap intervals of each predictor, one row per predictor."""
    out = []
    for i, (name, c) in enumerate(calls.items()):
        perf = performance(labels, c)
        ci = bootstrap_ci(labels, c, n_boot=n_boot, seed=seed + i) if n_boot else {}
        row = {"predictor": name, "n": perf["n"], "tp": perf["tp"], "tn": perf["tn"], "fp": perf["fp"], "fn": perf["fn"]}
        for k in STATS:
            row[k] = perf[k]
            if ci:
                row[k + "_low"], row[k + "_high"] = ci[k]
        out.append(row)
    return out


def write_rows(rows: list[dict], f, digits: int = 6) -> None:
    if not rows:
        return
    w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (("" if math.isnan(v) else f"{v:.{digits}g}") if isinstance(v, float) else v) for k, v in r.items()})
