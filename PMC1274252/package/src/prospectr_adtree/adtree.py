"""Alternating decision trees (Freund and Mason 1999) as Weka 3.4's ADTree builds them.

PROSPECTR's tree was built with Weka's ADTree (-B 15 -E -1). This is a port of that learner, written
to make the same choices in the same order: the Z criterion with +1 smoothing, prediction values
0.5 ln((W+ + 1) / (W- + 1)), cut points halfway between neighbouring values, Weka's sort and its
tie-breaking, merging of repeated splitters, and the four search modes. The port is checked against
Weka 3.4.3 on the PROSPECTR data in the reproduction (identical trees and scores).

Class value 0 is the "negative" class, as in Weka: a negative score points to it. In the PROSPECTR
files class 0 is "disease".
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .arff import Dataset
from .javarandom import JavaRandom

SEARCH_ALL, SEARCH_HEAVIEST, SEARCH_ZPURE, SEARCH_RANDOM = 0, 1, 2, 3
_SEARCH_NAMES = {"all": SEARCH_ALL, "heaviest": SEARCH_HEAVIEST, "zpure": SEARCH_ZPURE, "random": SEARCH_RANDOM}
_SMALL = 1e-6


class _Inst:
    __slots__ = ("values", "cls", "weight")

    def __init__(self, values, cls, weight=1.0):
        self.values = values
        self.cls = cls
        self.weight = weight

    def copy(self):
        return _Inst(self.values, self.cls, self.weight)


def _sum_weights(insts) -> float:
    s = 0.0
    for i in insts:
        s += i.weight
    return s


@dataclass
class Splitter:
    """A two-way test. Numeric: branch 0 is value < split, branch 1 is value >= split.
    Nominal: branch 0 is value == split (a value index), branch 1 is any other value."""

    attribute: str
    att_index: int
    split: float
    nominal: bool = False
    values: list[str] | None = None  # nominal value names, for printing
    order: int = 0
    children: list["PredictionNode"] = field(default_factory=lambda: [None, None])

    def branch(self, x) -> int:
        v = x[self.att_index]
        if v is None:
            return -1
        if self.nominal:
            return 0 if v == self.split else 1
        return 0 if v < self.split else 1

    def down(self, b: int, insts):
        i = self.att_index
        if self.nominal:
            if b == 0:
                return [t for t in insts if t.values[i] is not None and t.values[i] == self.split]
            return [t for t in insts if t.values[i] is not None and t.values[i] != self.split]
        if b == 0:
            return [t for t in insts if t.values[i] is not None and t.values[i] < self.split]
        return [t for t in insts if t.values[i] is not None and t.values[i] >= self.split]

    def equal_to(self, other: "Splitter") -> bool:
        return (self.nominal == other.nominal and self.att_index == other.att_index
                and self.split == other.split)

    def comparison(self, b: int) -> str:
        if self.nominal:
            v = self.values
            if len(v) != 2:
                return ("= " if b == 0 else "!= ") + v[int(self.split)]
            k = int(self.split)
            return "= " + (v[k] if b == 0 else v[1 - k])
        return ("< " if b == 0 else ">= ") + weka_double(self.split, 3)

    def clone(self) -> "Splitter":
        s = Splitter(self.attribute, self.att_index, self.split, self.nominal, self.values, self.order)
        s.children = [c.clone() if c is not None else None for c in self.children]
        return s


@dataclass
class PredictionNode:
    value: float
    children: list[Splitter] = field(default_factory=list)

    def clone(self) -> "PredictionNode":
        return PredictionNode(self.value, [s.clone() for s in self.children])

    def add_child(self, new: Splitter, tree: "ADTree") -> None:
        for s in self.children:
            if new.equal_to(s):
                for b in range(2):
                    if s.children[b] is not None and new.children[b] is not None:
                        s.children[b].merge(new.children[b], tree)
                return
        c = new.clone()
        tree._set_order(c)
        self.children.append(c)

    def merge(self, other: "PredictionNode", tree: "ADTree") -> None:
        self.value += other.value
        for s in other.children:
            self.add_child(s, tree)


def weka_double(value: float, digits: int) -> str:
    """weka.core.Utils.doubleToString(value, digits): round half away from zero, trim zeros."""
    temp = value * math.pow(10.0, digits)
    p = int(temp + 0.5) if temp > 0 else -int(abs(temp) + 0.5)
    s = str(abs(p)).rjust(digits + 1, "0")
    out = s[:-digits] + "." + s[-digits:] if digits else s
    out = out.rstrip("0").rstrip(".")
    if p < 0:
        out = "-" + out
    return out if p != 0 else "0"


class ADTree:
    """Weka 3.4 ADTree. ``search`` is 'all' (-E -3), 'heaviest' (-E -2), 'zpure' (-E -1) or
    'random' (-E >= 0, with ``seed``)."""

    def __init__(self, iterations: int = 10, search: str = "zpure", seed: int = 0):
        if iterations < 0:
            raise ValueError("iterations must be >= 0")
        if search not in _SEARCH_NAMES:
            raise ValueError(f"search must be one of {sorted(_SEARCH_NAMES)}")
        self.iterations = iterations
        self.search = _SEARCH_NAMES[search]
        self.seed = seed
        self.root: PredictionNode | None = None
        self.legend = ""

    # ---- training -------------------------------------------------------------------------
    def fit(self, data: Dataset) -> "ADTree":
        cls = data.class_attribute
        if not cls.is_nominal or len(cls.values) != 2:
            raise ValueError("ADTree needs a two-valued nominal class")
        self._attrs = data.attributes
        self._class_index = data.class_index
        self.legend = f"-ve = {cls.values[0]}, +ve = {cls.values[1]}"
        self._random = JavaRandom(self.seed)
        self._last_order = 0
        self._train = [_Inst(r, int(r[data.class_index])) for r in data.rows if r[data.class_index] is not None]
        if not self._train:
            raise ValueError("no training instances")
        self._pos = [t for t in self._train if t.cls != 0]
        self._neg = [t for t in self._train if t.cls == 0]
        root_value = self._prediction_value(self._pos, self._neg)
        self.root = PredictionNode(root_value)
        self._update_weights(self._pos, self._neg, root_value)
        idx = [i for i in range(len(self._attrs)) if i != self._class_index]
        self._nominal = [i for i in idx if self._attrs[i].is_nominal]
        self._numeric = [i for i in idx if not self._attrs[i].is_nominal]
        for _ in range(self.iterations):
            self._boost()
        del self._train, self._pos, self._neg
        return self

    def _set_order(self, s: Splitter) -> None:
        self._last_order += 1
        s.order = self._last_order
        for c in s.children:
            if c is not None:
                for g in c.children:
                    self._set_order(g)

    @staticmethod
    def _prediction_value(pos, neg) -> float:
        return 0.5 * math.log((_sum_weights(pos) + 1.0) / (_sum_weights(neg) + 1.0))

    @staticmethod
    def _update_weights(pos, neg, value: float) -> None:
        m = math.pow(math.e, -value)
        for t in pos:
            t.weight = t.weight * m
        m = math.pow(math.e, value)
        for t in neg:
            t.weight = t.weight * m

    def _zpure(self, pos, neg) -> float:
        pw, nw = _sum_weights(pos), _sum_weights(neg)
        return 2.0 * (math.sqrt(pw + 1.0) + math.sqrt(nw + 1.0)) + (self._total - (pw + nw))

    def _boost(self) -> None:
        self._total = _sum_weights(self._train)
        self._best_z = math.inf
        self._best = None
        self._search(self.root, self._pos, self._neg)
        if self._best is None:
            return
        node, split, pos, neg = self._best
        for b in range(2):
            p, n = split.down(b, pos), split.down(b, neg)
            v = self._prediction_value(p, n)
            self._update_weights(p, n, v)
            split.children[b] = PredictionNode(v)
        node.add_child(split, self)

    def _search(self, node: PredictionNode, pos, neg) -> None:
        if not pos or not neg:
            return
        if self._zpure(pos, neg) >= self._best_z:
            return
        for a in self._nominal:
            k, z = self._nominal_split(pos, neg, a)
            if z < self._best_z:
                at = self._attrs[a]
                self._best_z = z
                self._best = (node, Splitter(at.name, a, float(k), True, at.values), pos, neg)
        if self._numeric:
            allinst = [t.copy() for t in pos] + [t.copy() for t in neg]
            for a in self._numeric:
                cut, z = self._numeric_split(allinst, a)
                if z < self._best_z:
                    self._best_z = z
                    self._best = (node, Splitter(self._attrs[a].name, a, cut), pos, neg)
        if not node.children:
            return
        if self.search == SEARCH_ALL:
            for s in node.children:
                for b in range(2):
                    self._search(s.children[b], s.down(b, pos), s.down(b, neg))
        elif self.search == SEARCH_HEAVIEST:
            best, largest = None, 0.0
            for s in node.children:
                for b in range(2):
                    w = _sum_weights(s.down(b, pos)) + _sum_weights(s.down(b, neg))
                    if w > largest:
                        best, largest = (s, b), w
            if best is not None:
                s, b = best
                self._search(s.children[b], s.down(b, pos), s.down(b, neg))
        elif self.search == SEARCH_ZPURE:
            lowest, best = self._best_z, None
            for s in node.children:
                for b in range(2):
                    p, n = s.down(b, pos), s.down(b, neg)
                    z = self._zpure(p, n)
                    if z < lowest:
                        lowest, best = z, (s.children[b], p, n)
            if best is not None:
                self._search(*best)
        else:
            s = node.children[self._random.next_int(len(node.children))]
            b = self._random.next_int(2)
            self._search(s.children[b], s.down(b, pos), s.down(b, neg))

    def _nominal_split(self, pos, neg, a: int):
        nvals = len(self._attrs[a].values)
        pw, nw = [0.0] * nvals, [0.0] * nvals
        for t in pos:
            if t.values[a] is not None:
                pw[int(t.values[a])] += t.weight
        for t in neg:
            if t.values[a] is not None:
                nw[int(t.values[a])] += t.weight
        ptot, ntot = _psum(pw), _psum(nw)
        lowest, best = 1.7976931348623157e308, 0
        for i in range(1 if nvals == 2 else nvals):
            w1, w2 = pw[i] + 1.0, nw[i] + 1.0
            w3, w4 = ptot - w1 + 2.0, ntot - w2 + 2.0
            rem = self._total + 4.0 - (w1 + w2 + w3 + w4)
            z = 2.0 * (math.sqrt(w1 * w2) + math.sqrt(w3 * w4)) + rem
            if z < lowest:
                lowest, best = z, i
        return best, lowest

    def _numeric_split(self, insts, a: int):
        # class distribution as Weka indexes it: [row][class value]
        d = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
        missing = 0
        for t in insts:
            if t.values[a] is not None:
                d[1][t.cls] += t.weight
            else:
                d[2][t.cls] += t.weight
                missing += 1
        _weka_sort(insts, a)
        split, best = 0.0, 1.7976931348623157e308
        for i in range(len(insts) - (missing + 1)):
            t, u = insts[i], insts[i + 1]
            d[0][t.cls] += t.weight
            d[1][t.cls] -= t.weight
            if u.values[a] - t.values[a] > _SMALL:
                cut = (t.values[a] + u.values[a]) / 2.0
                w1, w2 = d[0][0] + 1.0, d[0][1] + 1.0
                w3, w4 = d[1][0] + 1.0, d[1][1] + 1.0
                rem = self._total + 4.0 - (w1 + w2 + w3 + w4)
                z = 2.0 * (math.sqrt(w1 * w2) + math.sqrt(w3 * w4)) + rem
                if z < best:
                    split, best = cut, z
        return split, best

    # ---- prediction -----------------------------------------------------------------------
    def score(self, x) -> float:
        """Additive score of one row (a list in the training attribute order).
        Negative: class 0 (disease in PROSPECTR); positive: class 1."""
        if self.root is None:
            raise ValueError("tree not trained")
        return _score(self.root, x, 0.0)

    def scores(self, data: Dataset) -> list[float]:
        self._check_header(data)
        return [self.score(r) for r in data.rows]

    def _check_header(self, data: Dataset) -> None:
        names = [a.name for a in data.attributes]
        if names != [a.name for a in self._attrs]:
            raise ValueError("data attributes differ from the training data's")

    # ---- output ---------------------------------------------------------------------------
    def to_weka_string(self) -> str:
        """The model as Weka 3.4 prints it (``Alternating decision tree:`` ... ``Leaves ...``)."""
        body = _tree_text(self.root, 1)
        size, leaves = _count_all(self.root), _count_pred(self.root)
        return (f"Alternating decision tree:\n\n{body}\nLegend: {self.legend}"
                f"\nTree size (total number of nodes): {size}"
                f"\nLeaves (number of predictor nodes): {leaves}")

    def splitters(self) -> list[Splitter]:
        out: list[Splitter] = []
        _walk(self.root, out)
        return sorted(out, key=lambda s: s.order)

    def to_dict(self) -> dict:
        return {"legend": self.legend, "root": _node_dict(self.root)}


def _psum(xs) -> float:
    s = 0.0
    for x in xs:
        s += x
    return s


def _weka_sort(insts, a: int) -> None:
    """weka.core.Instances.sort(attIndex): missing values to the end, then Weka's quicksort."""
    j = len(insts) - 1
    i = 0
    while i <= j:
        if insts[j].values[a] is None:
            j -= 1
        else:
            if insts[i].values[a] is None:
                insts[i], insts[j] = insts[j], insts[i]
                j -= 1
            i += 1
    _quicksort(insts, a, 0, j)


def _quicksort(insts, a: int, lo0: int, hi0: int) -> None:
    stack = [(lo0, hi0)]
    while stack:
        lo0, hi0 = stack.pop()
        lo, hi = lo0, hi0
        if hi0 <= lo0:
            continue
        mid = insts[(lo0 + hi0) // 2].values[a]
        while lo <= hi:
            while insts[lo].values[a] < mid and lo < hi0:
                lo += 1
            while insts[hi].values[a] > mid and hi > lo0:
                hi -= 1
            if lo <= hi:
                insts[lo], insts[hi] = insts[hi], insts[lo]
                lo += 1
                hi -= 1
        # Weka recurses left first, then right; the order does not change the result
        if lo < hi0:
            stack.append((lo, hi0))
        if lo0 < hi:
            stack.append((lo0, hi))


def _score(node: PredictionNode, x, acc: float) -> float:
    acc += node.value
    for s in node.children:
        b = s.branch(x)
        if b >= 0:
            acc = _score(s.children[b], x, acc)
    return acc


def _tree_text(node: PredictionNode, level: int) -> str:
    text = ": " + weka_double(node.value, 3)
    for s in node.children:
        for b in range(2):
            c = s.children[b]
            if c is not None:
                text += "\n" + "|  " * level + f"({s.order}){s.attribute} {s.comparison(b)}"
                text += _tree_text(c, level + 1)
    return text


def _count_all(node) -> int:
    n = 1
    for s in node.children:
        n += 1
        for c in s.children:
            if c is not None:
                n += _count_all(c)
    return n


def _count_pred(node) -> int:
    n = 1
    for s in node.children:
        for c in s.children:
            if c is not None:
                n += _count_pred(c)
    return n


def _walk(node, out) -> None:
    for s in node.children:
        out.append(s)
        for c in s.children:
            if c is not None:
                _walk(c, out)


def _node_dict(node: PredictionNode) -> dict:
    return {"value": node.value, "splitters": [
        {"order": s.order, "attribute": s.attribute, "split": s.split, "nominal": s.nominal,
         "branches": [s.comparison(0), s.comparison(1)],
         "children": [_node_dict(c) for c in s.children]} for s in node.children]}


# ---- Weka's cross-validation ------------------------------------------------------------------
def weka_folds(n_rows: int, classes: list[int], folds: int, random: JavaRandom) -> list[int]:
    """Row order after Instances.randomize(random) and stratify(folds), as original row numbers."""
    order = list(range(n_rows))
    for j in range(n_rows - 1, 0, -1):
        k = random.next_int(j + 1)
        order[j], order[k] = order[k], order[j]
    # stratify: group by class (Weka's in-place sort), then deal round-robin
    index = 1
    while index < n_rows:
        c1 = classes[order[index - 1]]
        for j in range(index, n_rows):
            if classes[order[j]] == c1:
                order[index], order[j] = order[j], order[index]
                index += 1
        index += 1
    out: list[int] = []
    start = 0
    while len(out) < n_rows:
        j = start
        while j < n_rows:
            out.append(order[j])
            j += folds
        start += 1
    return out


def cross_validate(data: Dataset, iterations: int = 10, search: str = "zpure", folds: int = 10,
                   seed: int = 1) -> list[dict]:
    """Weka's Evaluation.crossValidateModel(ADTree, data, folds, new Random(seed)).

    Returns one record per row: row number, fold, class value and the held-out score."""
    if folds < 2 or folds > len(data.rows):
        raise ValueError("folds must be between 2 and the number of rows")
    rnd = JavaRandom(seed)
    classes = [int(r[data.class_index]) for r in data.rows]
    order = weka_folds(len(data.rows), classes, folds, rnd)
    n = len(order)
    out = []
    for f in range(folds):
        size = n // folds
        if f < n % folds:
            size += 1
            offset = f
        else:
            offset = n % folds
        first = f * (n // folds) + offset
        train_idx = order[:first] + order[first + size:]
        # trainCV(folds, f, random) shuffles the training fold with the same generator
        for j in range(len(train_idx) - 1, 0, -1):
            k = rnd.next_int(j + 1)
            train_idx[j], train_idx[k] = train_idx[k], train_idx[j]
        train = Dataset(data.relation, data.attributes, [data.rows[i] for i in train_idx], data.class_index)
        model = ADTree(iterations, _name(search) if isinstance(search, int) else search).fit(train)
        for i in order[first:first + size]:
            out.append({"index": i, "fold": f, "class": classes[i], "score": model.score(data.rows[i])})
    return out


def _name(code: int) -> str:
    return {v: k for k, v in _SEARCH_NAMES.items()}[code]
