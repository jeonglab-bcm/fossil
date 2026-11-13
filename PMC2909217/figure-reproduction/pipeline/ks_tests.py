"""Table 1, Fig. 6 and Additional file 1 (Figs S1-S32): SGI against non-SGI pairs, per property.

    python ks_tests.py FEATURES.npz OUT_DIR

For the average and the absolute difference of degree, closeness, betweenness and clustering
coefficient, on the binary and the weighted network: the two-sample Kolmogorov-Smirnov D and P
(scipy, two-sided, exact when small, asymptotic otherwise) on every Tong 2004 SGI pair and every
tested non-SGI pair in the network (our main sample), and on the first repeat's 1,500 + 1,500
pairs (a hypothesis test). Densities as R's density() draws them (Gaussian kernel, bandwidth
bw.nrd0, 512 points from min - 3 bw to max + 3 bw), and empirical CDFs at 512 points.

Writes OUT_DIR/table1.json and OUT_DIR/densities.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from fgnssl.network import FEATURE_NAMES
from scipy.stats import ks_2samp

PROPS = ("degree", "closeness", "betweenness", "clustering")
KINDS = (("avg", "Average"), ("diff", "Absolute difference"))


def bw_nrd0(x: np.ndarray) -> float:
    """R's bw.nrd0: 0.9 min(sd, IQR / 1.34) n^(-1/5)."""
    x = np.asarray(x, dtype=float)
    hi = np.std(x, ddof=1)
    q75, q25 = np.quantile(x, [0.75, 0.25])
    lo = min(hi, (q75 - q25) / 1.34)
    if lo == 0:
        lo = hi or abs(x[0]) or 1.0
    return 0.9 * lo * len(x) ** (-0.2)


def r_density(x: np.ndarray, n: int = 512):
    """Gaussian kernel density on R's default grid, by exact summation in chunks."""
    x = np.asarray(x, dtype=float)
    bw = bw_nrd0(x)
    grid = np.linspace(x.min() - 3 * bw, x.max() + 3 * bw, n)
    dens = np.zeros(n)
    for a in range(0, len(x), 20000):
        z = (grid[:, None] - x[None, a:a + 20000]) / bw
        dens += np.exp(-0.5 * z * z).sum(axis=1)
    dens /= len(x) * bw * np.sqrt(2 * np.pi)
    return grid, dens, bw


def main(features: str, out: str) -> None:
    d = np.load(features)
    y = d["y"]
    od = Path(out)
    od.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)  # the first repeat's sample, as experiments.py draws it
    pos = rng.choice(np.where(y == 1)[0], 1500, replace=False)
    neg = rng.choice(np.where(y == 0)[0], 1500, replace=False)
    table, dens = {"rows": [], "n_sgi": int((y == 1).sum()), "n_nonsgi": int((y == 0).sum())}, {}
    for kind, kind_label in KINDS:
        for prop in PROPS:
            col = FEATURE_NAMES.index(f"{kind}_{prop}")
            row = {"id": f"{kind}_{prop}", "characteristic": kind_label, "property": prop}
            for net in ("binary", "weighted"):
                X = d[f"X_{net}"][:, col]
                a, b = X[y == 1], X[y == 0]
                r = ks_2samp(a, b)
                s = ks_2samp(X[pos], X[neg])
                row[net] = {"D": float(r.statistic), "P": float(r.pvalue),
                            "sample_D": float(s.statistic), "sample_P": float(s.pvalue),
                            "sgi_median": float(np.median(a)), "nonsgi_median": float(np.median(b)),
                            "sgi_higher": bool(np.median(a) > np.median(b))}
                ga, da, bwa = r_density(a)
                gb, db, bwb = r_density(b)
                qs = np.linspace(0, 1, 512)
                dens[f"{net}/{kind}_{prop}"] = {
                    "sgi": {"x": ga.tolist(), "y": da.tolist(), "bw": bwa},
                    "nonsgi": {"x": gb.tolist(), "y": db.tolist(), "bw": bwb},
                    "ecdf_sgi": np.quantile(a, qs).tolist(), "ecdf_nonsgi": np.quantile(b, qs).tolist(),
                    "D": float(r.statistic), "P": float(r.pvalue),
                }
            table["rows"].append(row)
    (od / "table1.json").write_text(json.dumps(table, indent=1) + "\n")
    def rounded(o):
        if isinstance(o, float):
            return float(f"{o:.6g}")
        if isinstance(o, list):
            return [rounded(x) for x in o]
        if isinstance(o, dict):
            return {k: rounded(v) for k, v in o.items()}
        return o
    with open(od / "densities.json", "w") as f:
        json.dump(rounded(dens), f)
    for row in table["rows"]:
        b, w = row["binary"], row["weighted"]
        print(f"{row['id']:18s} D {b['D']:.4f} {w['D']:.4f}  P {b['P']:.3g} {w['P']:.3g}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
