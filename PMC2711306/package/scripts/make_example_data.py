"""Write the bundled example: a noisy geometric graph.

150 points uniform in the unit square, joined when closer than 0.15 (a geometric random graph,
the paper's model of a PPI network). 10% of the true edges are deleted (the "missing
interactions" a de-noising method should recover) and as many spurious edges between random
non-adjacent pairs are added. The largest connected component is kept.

Writes, into src/geodenoise/data/:
  geometric_network.tsv   the observed (noisy) network, the example input
  geometric_missing.tsv   the deleted true edges
  geometric_spurious.tsv  the added edges
  geometric_numbered.txt  the network as numbered pairs (1-based), the input of the authors' code
The expected output (geometric_expected_distances.csv) comes from the authors' Matlab code; see
make_expected_output.sh.
"""
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[1] / "src" / "geodenoise" / "data"
rng = np.random.default_rng(20090807)
n, radius = 150, 0.15
pts = rng.random((n, 2))
d = np.sqrt(((pts[:, None] - pts[None]) ** 2).sum(-1))
iu, ju = np.triu_indices(n, 1)
true = [(i, j) for i, j in zip(iu, ju) if d[i, j] < radius]
k = len(true) // 10
drop = set(rng.choice(len(true), k, replace=False).tolist())
missing = [true[t] for t in sorted(drop)]
kept = [e for t, e in enumerate(true) if t not in drop]
truth = set(true)
spurious = set()
while len(spurious) < k:
    i, j = sorted(rng.choice(n, 2, replace=False).tolist())
    if (i, j) not in truth:
        spurious.add((i, j))
edges = sorted(set(kept) | spurious)

# largest connected component
parent = list(range(n))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for i, j in edges:
    parent[find(i)] = find(j)
roots = [find(i) for i in range(n)]
big = max(set(roots), key=roots.count)
keep = [i for i in range(n) if roots[i] == big]
name = {i: f"P{i + 1:03d}" for i in keep}
num = {i: r + 1 for r, i in enumerate(keep)}


def write(path, pairs):
    with open(path, "w") as f:
        f.write("protein_a\tprotein_b\n")
        for i, j in pairs:
            if i in name and j in name:
                f.write(f"{name[i]}\t{name[j]}\n")


write(OUT / "geometric_network.tsv", edges)
write(OUT / "geometric_missing.tsv", missing)
write(OUT / "geometric_spurious.tsv", sorted(spurious))
with open(OUT / "geometric_numbered.txt", "w") as f:
    for i, j in edges:
        if i in num and j in num:
            f.write(f"{num[i]} {num[j]}\n")
print(len(keep), "proteins,", sum(1 for i, j in edges if i in num and j in num), "edges,",
      len(missing), "missing,", len(spurious), "spurious")
