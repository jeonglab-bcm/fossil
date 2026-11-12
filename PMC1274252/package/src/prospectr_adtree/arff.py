"""A small reader for Weka ARFF files (dense data, numeric and nominal attributes)."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Attribute:
    name: str
    values: list[str] | None = None  # nominal values; None for numeric

    @property
    def is_nominal(self) -> bool:
        return self.values is not None


@dataclass
class Dataset:
    """Rows of floats (None = missing); a nominal value is stored as its index, as in Weka."""

    relation: str
    attributes: list[Attribute]
    rows: list[list[float | None]] = field(default_factory=list)
    class_index: int = -1

    def __post_init__(self):
        if self.class_index < 0:
            self.class_index = len(self.attributes) - 1

    @property
    def class_attribute(self) -> Attribute:
        return self.attributes[self.class_index]

    def index(self, name: str) -> int:
        for i, a in enumerate(self.attributes):
            if a.name == name:
                return i
        raise KeyError(name)

    def column(self, name: str) -> list[float | None]:
        i = self.index(name)
        return [r[i] for r in self.rows]

    def labels(self) -> list[str]:
        vals = self.class_attribute.values
        return [vals[int(r[self.class_index])] for r in self.rows]

    def select(self, names: list[str]) -> "Dataset":
        """Keep the named attributes (in file order) and the class, as Weka's Remove filter does."""
        keep = [i for i, a in enumerate(self.attributes) if a.name in set(names) or i == self.class_index]
        missing = set(names) - {self.attributes[i].name for i in keep}
        if missing:
            raise KeyError(f"attributes not in the data: {sorted(missing)}")
        attrs = [self.attributes[i] for i in keep]
        rows = [[r[i] for i in keep] for r in self.rows]
        return Dataset(self.relation, attrs, rows, keep.index(self.class_index))

    def as_dicts(self) -> list[dict[str, float | None]]:
        names = [a.name for a in self.attributes]
        return [dict(zip(names, r)) for r in self.rows]


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    return s


def _split(line: str) -> list[str]:
    return next(csv.reader([line], skipinitialspace=True, quotechar="'"))


def read_arff(path: str | Path) -> Dataset:
    """Read an ARFF file. Missing values ('?') become None; nominal values become their index."""
    relation = ""
    attrs: list[Attribute] = []
    rows: list[list[float | None]] = []
    in_data = False
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("%"):
                continue
            if in_data:
                vals = _split(line)
                if len(vals) != len(attrs):
                    raise ValueError(f"{path}: row has {len(vals)} values, header {len(attrs)}")
                row: list[float | None] = []
                for a, v in zip(attrs, vals):
                    v = _unquote(v)
                    if v == "?":
                        row.append(None)
                    elif a.is_nominal:
                        row.append(float(a.values.index(v)))
                    else:
                        row.append(float(v))
                rows.append(row)
                continue
            low = line.lower()
            if low.startswith("@relation"):
                relation = _unquote(line[len("@relation"):])
            elif low.startswith("@attribute"):
                rest = line[len("@attribute"):].strip()
                if rest[0] in "'\"":
                    q = rest[0]
                    end = rest.index(q, 1)
                    name, kind = rest[1:end], rest[end + 1:].strip()
                else:
                    name, kind = rest.split(None, 1)
                if kind.startswith("{"):
                    values = [_unquote(v) for v in _split(kind.strip()[1:-1])]
                    attrs.append(Attribute(name, values))
                elif kind.lower() in ("numeric", "real", "integer"):
                    attrs.append(Attribute(name))
                else:
                    raise ValueError(f"{path}: unsupported attribute type {kind!r}")
            elif low.startswith("@data"):
                in_data = True
    return Dataset(relation, attrs, rows)
