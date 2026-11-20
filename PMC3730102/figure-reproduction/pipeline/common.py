"""Loading the prepared inputs (shared by the pipeline steps)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from settings import CONDITIONS, STUDIES  # noqa: E402

from condloc.model import Proteome  # noqa: E402


def load_proteome(run: Path) -> tuple[Proteome, dict[str, str]]:
    rows = [line.rstrip("\n").split("\t") for line in open(run / "proteins.tsv")][1:]
    acc = [r[0] for r in rows]
    symbol = {r[0]: r[1] for r in rows}
    locs = [[x for x in r[2].split(",") if x] for r in rows]
    seq = dict(line.rstrip("\n").split("\t") for line in open(run / "sequences.tsv"))
    ann = json.load(open(run / "annotations.json"))
    links = [tuple(line.split("\t")[:2]) for line in list(open(run / "edges.tsv"))[1:]]
    p = Proteome.build(acc, [seq[a] for a in acc], [ann[a]["motif"] for a in acc], [ann[a]["go"] for a in acc],
                       locs, links)
    return p, symbol


def load_studies(run: Path) -> dict[str, list[tuple[list[str], np.ndarray, str]]]:
    out: dict[str, list] = {c: [] for c in CONDITIONS}
    for st in STUDIES:
        z = np.load(run / f"expr_{st['id']}.npz")
        out[st["condition"]].append((list(z["genes"]), z["x"].astype(float), st["id"]))
    return out


def dump(obj, path: Path) -> None:
    def conv(o):
        if isinstance(o, (np.floating,)):
            return round(float(o), 6)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, np.ndarray):
            return [conv(x) for x in o.tolist()]
        if isinstance(o, float):
            return round(o, 6)
        if isinstance(o, dict):
            return {str(k): conv(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [conv(x) for x in o]
        return o
    path.write_text(json.dumps(conv(obj), indent=1, sort_keys=True) + "\n")
