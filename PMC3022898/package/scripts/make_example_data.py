"""Write the bundled example: synthetic two-sample counts and their expected estimates.

Usage: python scripts/make_example_data.py   (from the package folder)

The counts are drawn with Python's own random module from six settings of the paper's simulation
grid (Reichmann et al. 2011, Table 1), one pair of samples each, plus one pair with no cases among
the exposed of sample 2 to show the zero-cell rule. The expected estimates are computed here with
the standard library only, straight from the paper's equations 2, 5, 6, 8, 9, 10, 11 and 12: a
second implementation, written apart from esrisk, so the package's tests compare two codes.
"""
import csv
import math
import random
from pathlib import Path

Z = 1.959963984540054
DATA = Path(__file__).resolve().parent.parent / "src" / "esrisk" / "data"

# label, P(E), P(D|not E), RR, N1, N2
SETTINGS = [
    ("scenario1_rr2_1000_1000", 0.05, 0.02, 2.0, 1000, 1000),
    ("scenario2_rr5_5000_5000", 0.05, 0.09, 5.0, 5000, 5000),
    ("scenario3_rr3_1000_5000", 0.20, 0.02, 3.0, 1000, 5000),
    ("scenario3_rr5_1000_1000", 0.20, 0.02, 5.0, 1000, 1000),
    ("scenario4_rr1_5000_1000", 0.20, 0.09, 1.0, 5000, 1000),
    ("scenario4_rr4_250_250", 0.20, 0.09, 4.0, 250, 250),
]


def draw(rng, pe, p0, rr, n1, n2):
    """One pair of samples from an infinite population (Bernoulli draws)."""
    def person():
        e = rng.random() < pe
        d = rng.random() < (rr * p0 if e else p0)
        return e, d
    s1 = [person() for _ in range(n1)]
    s2 = [person() for _ in range(n2)]
    d1 = sum(d for _, d in s1)
    d2e = sum(d for e, d in s2 if e)
    n2e = sum(e for e, _ in s2)
    d2u = sum(d for e, d in s2 if not e)
    return d1, n1, d2e, n2e, d2u, n2 - n2e


def expected(d1, n1, d2e, n2e, d2u, n2u):
    p1 = d1 / n1
    pe, pu = d2e / n2e, d2u / n2u
    p2e = n2e / (n2e + n2u)
    rr = pe / pu
    s = p1 * rr                                   # eq. 2
    p1u = p1 / ((rr - 1) * p2e + 1)               # eq. 8
    r = p1u * rr                                  # eq. 9
    out = {"esr_s": s, "esr_r": r}
    if d2e == 0 or d2u == 0:                      # log intervals undefined: (0, infinity)
        out.update(esr_s_log_lower=0.0, esr_s_log_upper=math.inf, esr_r_log_lower=0.0, esr_r_log_upper=math.inf)
    else:
        v_rr = (1 - pe) / (pe * n2e) + (1 - pu) / (pu * n2u)
        v_s = (1 - p1) / (n1 * p1) + v_rr         # eq. 5
        v_r = (1 - p1u) / (n1 * p1u) + v_rr       # eq. 10
        out.update(esr_s_log_lower=math.exp(math.log(s) - Z * math.sqrt(v_s)),   # eq. 6
                   esr_s_log_upper=math.exp(math.log(s) + Z * math.sqrt(v_s)),
                   esr_r_log_lower=math.exp(math.log(r) - Z * math.sqrt(v_r)),
                   esr_r_log_upper=math.exp(math.log(r) + Z * math.sqrt(v_r)))
    half = Z * math.sqrt(r * (1 - r) / (n1 * p2e))  # eqs 11-12
    out.update(esr_r_binomial_lower=r - half, esr_r_binomial_upper=r + half)
    return out


def main():
    rng = random.Random(20110105)
    rows = [(label, *draw(rng, *args)) for label, *args in SETTINGS]
    rows.append(("no_exposed_cases", 31, 1000, 0, 48, 19, 933))
    cols = ["label", "d1", "n1", "d2_exposed", "n2_exposed", "d2_unexposed", "n2_unexposed"]
    with open(DATA / "two_samples.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        w.writerows(rows)
    out_cols = ["esr_s", "esr_s_log_lower", "esr_s_log_upper", "esr_r", "esr_r_log_lower", "esr_r_log_upper",
                "esr_r_binomial_lower", "esr_r_binomial_upper"]
    with open(DATA / "two_samples_expected.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["label"] + out_cols)
        for label, *counts in rows:
            e = expected(*counts)
            w.writerow([label] + [repr(e[c]) for c in out_cols])
    print(f"wrote {len(rows)} rows to {DATA}")


if __name__ == "__main__":
    main()
