"""Write the bundled example data and its expected output.

    python scripts/make_example_data.py src/diseasenet/data

The network, the diseases and their linkage intervals are synthetic: 240 proteins, eight
diseases whose genes sit in dense modules, background interactions, and for each disease an
interval of 30 candidate genes holding its known genes. The paper's data (HPRD, OMIM) cannot be
redistributed.

The expected scores are computed here without the package, from the definitions:

- Neighborhood and Oti by counting neighbours in plain Python;
- RW and Prop as the fixed points of their iterations, by solving the linear systems
  p = r (I - (1 - r) W)^-1 p0 and F = (1 - alpha) (I - alpha W')^-1 Y (then W' F) with numpy.

The package iterates until the L2 change is below 1e-6, so its RW and Prop scores sit within
1e-5 of the fixed points; Neighborhood and Oti must match exactly.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np  # noqa: E402

R, ALPHA = 0.75, 0.6


def main(out: Path):
    rng = np.random.default_rng(20100224)
    n = 240
    nodes = [f"P{i:03d}" for i in range(n)]
    edges = set()
    diseases = {}
    start = 0
    for k in range(8):
        size = 6 + k % 3
        module = list(range(start, start + size))
        start += size
        for i in module:  # dense module: each pair interacts with probability 0.5
            for j in module:
                if i < j and rng.random() < 0.5:
                    edges.add((i, j))
        n_known = 3 + k % 3
        diseases[f"Disease{k + 1}"] = sorted(rng.choice(module, size=n_known, replace=False).tolist())
    while len(edges) < 700:  # background interactions
        i, j = sorted(rng.choice(n, size=2, replace=False).tolist())
        edges.add((i, j))
    for i in range(n):  # one connected network: link each protein to the next if it has no partner
        if not any(i in e for e in edges):
            edges.add((min(i, (i + 1) % n), max(i, (i + 1) % n)))
    edges = sorted(edges)

    cands = []
    for d, genes in diseases.items():
        others = [g for g in range(n) if g not in genes]
        interval = sorted(genes + rng.choice(others, size=30 - len(genes), replace=False).tolist())
        for g in interval:
            cands.append((nodes[g], d, int(g in genes)))

    # ---- expected scores, independent of the package
    nb = {i: set() for i in range(n)}
    for i, j in edges:
        nb[i].add(j)
        nb[j].add(i)
    a = np.zeros((n, n))
    for i, j in edges:
        a[i, j] = a[j, i] = 1.0
    w = a / a.sum(axis=0, keepdims=True)  # column-normalised
    dg = a.sum(axis=1)
    wp = a / np.sqrt(np.outer(dg, dg))
    eye = np.eye(n)
    idx = {g: i for i, g in enumerate(nodes)}
    rows = []
    cache = {}
    for g, d, known in cands:
        i = idx[g]
        seeds = [s for s in diseases[d] if s != i]  # leave-one-out
        nh = len(nb[i] & set(seeds)) / len(nb[i])
        oti = len(nb[i] & set(seeds))
        key = tuple(seeds)
        if key not in cache:
            p0 = np.zeros(n)
            p0[seeds] = 1 / len(seeds)
            y = np.zeros(n)
            y[seeds] = 1.0
            f = np.linalg.solve(eye - ALPHA * wp, (1 - ALPHA) * y)
            cache[key] = (np.linalg.solve(eye - (1 - R) * w, R * p0), wp @ f)
        rw, prop = cache[key][0][i], cache[key][1][i]
        rows.append((g, d, known, nh, oti, rw, prop))

    out.mkdir(parents=True, exist_ok=True)
    with open(out / "network.tsv", "w") as fh:
        for i, j in edges:
            fh.write(f"{nodes[i]}\t{nodes[j]}\n")
    with open(out / "candidates.csv", "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["gene", "disease", "known"])
        wr.writerows(cands)
    with open(out / "expected_scores.csv", "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["gene", "disease", "known", "neighborhood", "oti", "rw", "prop"])
        for g, d, known, nh, oti, rw, prop in rows:
            wr.writerow([g, d, known, repr(nh), oti, repr(float(rw)), repr(float(prop))])
    print(f"{len(edges)} interactions, {len(diseases)} diseases, {len(cands)} candidate pairs")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "src/diseasenet/data"))
