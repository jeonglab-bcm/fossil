"""Write the package's example alignment and its expected output.

The alignment is simulated: a small population of 90 bp sequences at three time points, with
mutation and crossing over at a set rate. The expected output is computed here by a slow,
straightforward enumeration in plain Python, not by the package, so the package's vectorized
code is tested against an independent implementation.

    python scripts/make_example_data.py src/hivrecomb/data
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

LENGTH = 90
POP = 200
SAMPLE = 14
GENERATIONS = 40          # between consecutive samples
TIMEPOINTS = 3
MUTATION = 1.5e-3         # per site and generation
BURN_IN = 300             # generations of standing variation before the first sample
RECOMBINATION = 3.0e-4    # per site and generation
SEED = 20100129
BINS = (0, 30, 60, 90)


def simulate(rng):
    """A Wright-Fisher population with mutation and one crossover per recombining pair."""
    founder = [rng.choice("ACGT") for _ in range(LENGTH)]
    pop = [list(founder) for _ in range(POP)]
    samples = []
    for tp in range(TIMEPOINTS):
        for _ in range(BURN_IN if tp == 0 else GENERATIONS):
            if True:
                nxt = []
                for _ in range(POP):
                    a = pop[rng.randrange(POP)]
                    if rng.random() < RECOMBINATION * LENGTH:
                        b = pop[rng.randrange(POP)]
                        k = rng.randrange(1, LENGTH)
                        child = a[:k] + b[k:]
                    else:
                        child = list(a)
                    for site in range(LENGTH):
                        if rng.random() < MUTATION:
                            child[site] = rng.choice("ACGT")
                    nxt.append(child)
                pop = nxt
        idx = rng.sample(range(POP), SAMPLE)
        samples.append([("".join(pop[i]), tp * GENERATIONS) for i in idx])
    return samples


def reference_events(samples, min_count=3):
    """Every qualifying pair of sites, by enumeration. Returns rows (d, dt, found)."""
    rows = []
    for first, second in zip(samples[:-1], samples[1:]):
        A = [s for s, _ in first]
        B = [s for s, _ in second]
        t0, t1 = first[0][1], second[0][1]
        sites = []
        for j in range(LENGTH):
            col = [s[j] for s in A]
            kinds = sorted(set(col))
            if len(kinds) != 2 or any(c not in "ACGT" for c in kinds):
                continue
            if min(col.count(k) for k in kinds) < min_count:
                continue
            sites.append((j, kinds))
        for x in range(len(sites)):
            for y in range(x + 1, len(sites)):
                j1, k1 = sites[x]
                j2, k2 = sites[y]
                seen = {(s[j1], s[j2]) for s in A}
                possible = {(p, q) for p in k1 for q in k2}
                if len(seen & possible) != 3:
                    continue
                missing = next(iter(possible - seen))
                found = any((s[j1], s[j2]) == missing for s in B)
                rows.append((j2 - j1, t1 - t0, int(found)))
    return rows


def main(argv=None) -> int:
    out = Path((argv or sys.argv[1:])[0])
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    samples = simulate(rng)
    with open(out / "example_alignment.fasta", "w") as f:
        for tp, group in enumerate(samples):
            for k, (seq, t) in enumerate(group):
                f.write(f">t{tp}_s{k:02d}|{t}\n{seq}\n")
    rows = reference_events(samples)
    counts = [[0, 0] for _ in range(len(BINS) - 1)]
    for d, _dt, found in rows:
        for b in range(len(BINS) - 1):
            if BINS[b] <= d < BINS[b + 1]:
                counts[b][0] += 1
                counts[b][1] += found
    with open(out / "example_expected.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bin_low", "bin_high", "pairs", "found", "probability"])
        for b, (pairs, found) in enumerate(counts):
            w.writerow([BINS[b], BINS[b + 1], pairs, found,
                        "" if not pairs else f"{found / pairs:.6f}"])
    print(f"{sum(len(g) for g in samples)} sequences, {len(rows)} qualifying pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
