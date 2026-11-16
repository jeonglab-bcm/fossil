"""Write src/pssmdt/data/expected_pssm_dt.csv from the bundled example PSSMs, without pssmdt.

Usage: python scripts/make_expected.py

The expected output must not come from the package. This script reads each ASCII PSSM with its own
parser and computes PSSM-DT with plain loops transliterated from the authors' later toolkit,
BioSeq-Analysis2.0 (profile.pyc: preHandleColumns, generate_ksb_pssm and aver, read from the
bytecode): for lag = 1..5, M[i][j] += PSSM[k][i] * PSSM[k + lag][j] for k < L - lag, divided by
L - lag, flattened row by row. Values are written with repr(), so they round-trip exactly.
"""
import csv
from pathlib import Path

AA = "ARNDCQEGHILKMFPSTWYV"
LG = 5
DATA = Path(__file__).resolve().parent.parent / "src" / "pssmdt" / "data"


def read_scores(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        f = line.split()
        if len(f) >= 22 and f[0].isdigit() and len(f[1]) == 1:
            rows.append([int(x) for x in f[2:22]])
    return rows


def bioseq_pssm_dt(rows, lag):
    seq_cn = len(rows)
    vector = []
    for step in range(1, lag + 1):
        m = [[0.0] * 20 for _ in range(20)]
        for i in range(20):
            for j in range(20):
                for k in range(seq_cn - step):
                    m[i][j] += float(rows[k][i]) * float(rows[k + step][j])
        vector += [m[i][j] / float(seq_cn - step) for i in range(20) for j in range(20)]
    return vector


def main():
    names = [f"{a}-{b}_lg{l}" for l in range(1, LG + 1) for a in AA for b in AA]
    with open(DATA / "expected_pssm_dt.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", *names])
        for p in sorted((DATA / "pssm").glob("*.pssm")):
            w.writerow([p.stem, *(repr(v) for v in bioseq_pssm_dt(read_scores(p), LG))])
    print("wrote", DATA / "expected_pssm_dt.csv")


if __name__ == "__main__":
    main()
