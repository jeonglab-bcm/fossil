"""Write the synthetic example data of manetworker (src/manetworker/data/).

  python scripts/make_example_data.py

500 genes, 8 transcription factors (TFs), 60 experiments. Each TF binds 40 genes (ChIP log2 ratio
about 1.5, P below 1e-3); the other genes have log2 ratios around 0 and P above 1e-3. Three TFs
(TF1 to TF3) are active: each has a random activity per experiment, and 25 of its 40 bound genes are
functional targets whose expression follows that activity:

    E_gt = sum over active f of a_ft * B_fg * [g is a functional target of f] + noise (sd 0.3).

The other 15 bound genes of an active TF, and all genes bound by TF4 to TF8, do not respond. The
expected output (expected.json) is what the formula planted: the active TFs and the functional
targets. It does not come from the package.
"""
import json
from pathlib import Path

import numpy as np

rng = np.random.default_rng(20040318)
G, F, T = 500, 8, 60
genes = [f"G{g:03d}" for g in range(G)]
tfs = [f"TF{f + 1}" for f in range(F)]
arrays = [f"exp{t + 1:02d}" for t in range(T)]
B = rng.normal(0.0, 0.3, (G, F))
P = rng.uniform(2e-3, 1.0, (G, F))
bound = np.zeros((G, F), bool)
functional = np.zeros((G, F), bool)
for f in range(F):
    idx = rng.choice(G, 40, replace=False)
    bound[idx, f] = True
    B[idx, f] = rng.normal(1.5, 0.4, 40)
    P[idx, f] = 10 ** rng.uniform(-8, -3.2, 40)
    if f < 3:
        functional[idx[:25], f] = True
A = np.zeros((F, T))
A[:3] = rng.normal(0.0, 1.0, (3, T))
E = (B * functional) @ A + rng.normal(0.0, 0.3, (G, T))
ratio = 2.0 ** B
# a few missing values, as in real data
E[rng.choice(G, 10, replace=False), rng.integers(0, T, 10)] = np.nan
ratio[rng.choice(G, 5, replace=False), rng.integers(0, F, 5)] = np.nan

out = Path(__file__).resolve().parents[1] / "src" / "manetworker" / "data"
out.mkdir(parents=True, exist_ok=True)


def write(name, cols, M, fmt):
    with open(out / name, "w", encoding="utf-8") as f:
        f.write("gene\t" + "\t".join(cols) + "\n")
        for g, row in zip(genes, M):
            f.write(g + "\t" + "\t".join("" if np.isnan(v) else fmt % v for v in row) + "\n")


write("expression.tsv", arrays, E, "%.4f")
write("binding_ratio.tsv", tfs, ratio, "%.4f")
write("binding_p.tsv", tfs, P, "%.3g")
expected = {
    "about": "Planted by scripts/make_example_data.py: the active TFs and, for each, its functional targets "
             "(bound genes whose expression follows the TF's activity) and its non-functional bound genes.",
    "active_tfs": tfs[:3],
    "functional_targets": {tfs[f]: [genes[g] for g in np.nonzero(functional[:, f])[0]] for f in range(3)},
    "nonfunctional_bound": {tfs[f]: [genes[g] for g in np.nonzero(bound[:, f] & ~functional[:, f])[0]] for f in range(3)},
    "true_activity": {tfs[f]: [round(float(v), 6) for v in A[f]] for f in range(3)},
}
(out / "expected.json").write_text(json.dumps(expected, indent=1) + "\n")
print("wrote", ", ".join(p.name for p in sorted(out.glob("*.tsv"))), "expected.json")
