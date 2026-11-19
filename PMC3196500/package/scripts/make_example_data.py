"""Write the package's example data (src/oisim/data/).

cumulative_trials.csv  12 two-arm trials drawn as Appendix S2 describes (Cochrane trial-size mixture, control
                       risk U(5%, 15%), tau^2 = 0.15, no true effect), with a fixed seed. One trial has no
                       events in the treatment arm, so the 0.5 correction is used.
cumulative_expected.csv  the cumulative DerSimonian-Laird analysis after each trial, computed here with plain
                       Python loops straight from Appendix S1's formulas (not with the package), so the package
                       is tested against an independent implementation.
table2_printed.csv     rows of the paper's Table 2 as printed (PC 3%, RRR 30%): the optimal information sizes
                       the package's formula is compared with.

Run from the package folder: python scripts/make_example_data.py
"""
import csv
import math
import random
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "src" / "oisim" / "data"
SIZES = ((20, 200, 0.50), (201, 500, 0.275), (501, 1000, 0.10), (1001, 2000, 0.075), (2001, 5000, 0.05))


def draw(rng):
    u, acc = rng.random(), 0.0
    for lo, hi, p in SIZES:
        acc += p
        if u < acc:
            return rng.randint(lo, hi)
    return rng.randint(SIZES[-1][0], SIZES[-1][1])


def binom(rng, n, p):
    return sum(rng.random() < p for _ in range(n))


def trials():
    rng = random.Random(3196500)
    out = []
    for i in range(12):
        n = draw(rng)
        arm = (n + 1) // 2
        pc = rng.uniform(0.05, 0.15)
        rr = math.exp(rng.gauss(0.0, math.sqrt(0.15)))
        out.append({"trial": f"T{i + 1:02d}", "events_treatment": binom(rng, arm, min(pc * rr, 1.0)),
                    "n_treatment": arm, "events_control": binom(rng, arm, pc), "n_control": arm})
    out[2]["events_treatment"] = 0  # a zero cell, so the example shows the continuity correction
    return out


def dl(ts):
    """Appendix S1, written out: log RR, its variance (0.5 added to every cell of a trial with a zero cell),
    Q, tau^2_DL = max(0, (Q - k + 1) / (S1 - S2 / S1)), and the random-effects weighted mean."""
    ys, vs = [], []
    rows = []
    cp = ce = 0
    for t in ts:
        a, n1, c, n0 = t["events_treatment"], t["n_treatment"], t["events_control"], t["n_control"]
        cp += n1 + n0
        ce += a + c
        if (a == 0 and c == 0) or (a == n1 and c == n0):
            pass  # no information on the relative risk: left out
        else:
            cc = 0.5 if 0 in (a, c, n1 - a, n0 - c) else 0.0
            a2, c2, n12, n02 = a + cc, c + cc, n1 + 2 * cc, n0 + 2 * cc
            ys.append(math.log(a2 / n12) - math.log(c2 / n02))
            vs.append(1 / a2 - 1 / n12 + 1 / c2 - 1 / n02)
        k = len(ys)
        w = [1 / v for v in vs]
        s1, s2 = sum(w), sum(x * x for x in w)
        mu_f = sum(wi * yi for wi, yi in zip(w, ys)) / s1
        q = sum(wi * (yi - mu_f) ** 2 for wi, yi in zip(w, ys))
        tau2 = max(0.0, (q - k + 1) / (s1 - s2 / s1)) if k >= 2 else 0.0
        ws = [1 / (v + tau2) for v in vs]
        mu = sum(wi * yi for wi, yi in zip(ws, ys)) / sum(ws)
        rr = math.exp(mu)
        rows.append({"trial": t["trial"], "cum_patients": cp, "cum_events": ce, "rr": f"{rr:.10g}",
                     "rrr": f"{1 - rr:.10g}", "tau2": f"{tau2:.10g}"})
    return rows


def write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    ts = trials()
    write(DATA / "cumulative_trials.csv", ts)
    write(DATA / "cumulative_expected.csv", dl(ts))
    t2 = []
    printed = {0.0: (9600, 13000, 16000, 250, 350, 400), 0.25: (13000, 17000, 21500, 350, 450, 550),
               0.50: (19500, 26000, 32000, 500, 650, 800)}
    for i2, row in printed.items():
        for j, beta in enumerate((0.20, 0.10, 0.05)):
            t2.append({"pc": 0.03, "rrr": 0.30, "i2": i2, "beta": beta, "patients_printed": row[j], "events_printed": row[3 + j]})
    write(DATA / "table2_printed.csv", t2)


if __name__ == "__main__":
    main()
