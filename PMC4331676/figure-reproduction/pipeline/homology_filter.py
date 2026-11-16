"""Benchmark sequences to remove before the independent test (the paper's "CD-HIT at 25%").

Usage: homology_filter.py FASTA_DIR BLASTP_TSV OUT.tsv

cd-hit cannot cluster below 40% identity, so the paper's filter cannot be run as written. We use
cd-hit-2d's definition of identity (identical residues / length of the shorter sequence) on
blastp alignments: a benchmark sequence is removed when any alignment with a PDB186 sequence of the
same class (binding against binding, non-binding against non-binding: "in a same subset") reaches
more than 25%. BLASTP_TSV is blastp -outfmt "6 qseqid sseqid nident length qlen slen evalue" of the
benchmark against PDB186 (run_blastp.sh). OUT.tsv lists the removed sequences and why.
"""
import sys
from pathlib import Path


def labels(path):
    lines = Path(path).read_text().split()
    return dict(h[1:].split("|") for h in lines[0::2])


def main(fasta_dir, tsv, out):
    lb = labels(Path(fasta_dir) / "benchmark.fasta")
    lp = labels(Path(fasta_dir) / "pdb186.fasta")
    best = {}
    for line in Path(tsv).read_text().splitlines():
        q, s, nident, length, qlen, slen, ev = line.split("\t")
        q, s = q.split("|")[0], s.split("|")[0]
        if lb[q] != lp[s]:
            continue
        ident = int(nident) / min(int(qlen), int(slen))
        if ident > best.get(q, (0, ""))[0]:
            best[q] = (ident, s)
    removed = sorted((q, v) for q, v in best.items() if v[0] > 0.25)
    with open(out, "w") as f:
        f.write("benchmark_id\tpdb186_id\tidentity\n")
        for q, (ident, s) in removed:
            f.write(f"{q}\t{s}\t{ident:.4f}\n")
    print(f"{len(removed)} of {len(lb)} benchmark sequences removed")


if __name__ == "__main__":
    main(*sys.argv[1:4])
