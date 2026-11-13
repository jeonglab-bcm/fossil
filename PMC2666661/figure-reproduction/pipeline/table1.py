"""Table 1: recompute the prevalence K, the marginal genotype relative risks and the sibling
recurrence risk ratio of each genetic model from its allele frequency and penetrance factors.

  table1.py OUT.json
"""

import json
import math
import sys

from rfld.simulate import MODELS, GeneticModel, table1_statistics

# Printed columns of Table 1: number of risk SNPs, GRR het, GRR hom, K, lambda_s
PRINTED = {
    "H1M1": ("1", "∞", "∞", "0.05", "9"),
    "H2M3": ("6", "5.22", "5.22", "0.02", "9"),
    "H3M3": ("9", "3.47", "3.47", "0.02", "9"),
    "H3M4": ("12", "2.54", "2.54", "0.02", "6"),
    "H9M2": ("18", "3.02", "3.02", "0.03", "9"),
    "H4M4": ("16", "1.63", "1.79", "0.10", "2"),
    "H8M4": ("32", "1.34", "1.4", "0.10", "2"),
}


def fmt(v, like):
    if math.isinf(v):
        return "∞"
    dec = len(like.split(".")[1]) if "." in like else 0
    return f"{v:.{dec + 3}f}"


def main():
    rows = []
    for name, m in MODELS.items():
        s = table1_statistics(m)
        n, het, hom, K, lam = PRINTED[name]
        rows += [
            {"name": f"{name} number of risk SNPs", "expected": n, "observed": str(m.h * m.m)},
            {"name": f"{name} GRR het", "expected": het, "observed": fmt(s["grr_het"], het)},
            {"name": f"{name} GRR hom", "expected": hom, "observed": fmt(s["grr_hom"], hom)},
            {"name": f"{name} K", "expected": K, "observed": fmt(s["K"], K)},
            {"name": f"{name} lambda_s", "expected": lam, "observed": fmt(s["lambda_s"], lam)},
        ]
    # H2M3: the allele frequency that gives lambda_s = 9 exactly (the printed 0.125 is rounded)
    lo, hi = 0.10, 0.15
    f = lambda p: table1_statistics(GeneticModel("H2M3", 2, 3, p, (0.0, 0.9, 0.9)))["lambda_s"] - 9  # noqa: E731
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    s = table1_statistics(GeneticModel("H2M3", 2, 3, (lo + hi) / 2, (0.0, 0.9, 0.9)))
    out = {"fields": rows, "h2m3_exact_lambda": {"p": (lo + hi) / 2, "grr": s["grr_het"], "K": s["K"]}}
    json.dump(out, open(sys.argv[1], "w"), indent=1)


if __name__ == "__main__":
    main()
