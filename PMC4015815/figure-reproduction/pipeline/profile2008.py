"""Top-1-gram sequences from frequency profiles built the way the lab's 2008 Top-n-gram paper did.

usage: profile2008.py FASTA ALN_DIR OUT_FASTA OUT_JSON [--workers N]

The paper cites its Top-n-gram paper (ref. [28]: Liu, Wang, Lin, Wang and Chou, BMC Bioinformatics
9:510, 2008) for the Top-n-grams. That paper's Methods, "Generation of protein sequence frequency
profiles":
  - PSI-BLAST with default parameters except 10 iterations, against nrdb90 (run_psiblast.sh with
    10 iterations and "align"; nrdb90 here is the lab's 2016 copy, EBI's is gone);
  - "A subset of multiple sequence alignments with sequence identity less than 98% is used";
  - position-based sequence weights (Henikoff and Henikoff 1994);
  - target frequencies as in PSI-BLAST: pseudocounts g_i = sum_j f_j q_ij / p_j from BLOSUM62,
    Q_i = (alpha f_i + beta g_i) / (alpha + beta), beta = 10, alpha = (number of different amino
    acids in the column) - 1;
  - the Top-1-gram of a position is the amino acid with the largest Q_i.

Here: the alignment is the last PSI-BLAST round's hits that pass its inclusion threshold
(E <= 0.002, PSI-BLAST's default), each laid on the query (query gaps dropped, subject gaps kept as
gaps), the query itself first. A subject with several HSPs gets them in E-value order, without
overwriting. Rows are kept greedily in E-value order when under 98% identical (over the positions
both cover) to every row already kept. Weights: Henikoff's position-based weights over all
columns, each column counting only rows with a residue there. f_i: weighted frequency of residue i
among the rows with a residue in the column. q_ij / p_j = r_ij p_i with r the BLOSUM62 frequency
ratios and p the Robinson and Robinson background PSI-BLAST uses (params/blosum62_psiblast.json,
from the NCBI C++ Toolkit). A column with the query residue alone (alpha = 0) takes g, so a
query-only M becomes L (r_LM p_L > r_MM p_M); every other residue stays itself.

Not stated in either paper, so chosen here: E <= 0.002 for the rows, one row per subject, the
greedy order of the 98% filter, Henikoff weights over the whole alignment rather than per block,
and residues outside the 20 letters (X) left out of f.
"""
import json
import multiprocessing as mp
import os
import sys

import numpy as np

import features

HERE = os.path.dirname(os.path.abspath(__file__))
AA = "ARNDCQEGHILKMFPSTWYV"
IDX = {a: i for i, a in enumerate(AA)}
INCLUSION = 0.002
IDENTITY = 0.98
BETA = 10.0
_P = json.load(open(os.path.join(HERE, "params", "blosum62_psiblast.json")))
assert _P["alphabet"] == AA
RATIO = np.array(_P["freq_ratios"])          # r[i][j]
BG = np.array(_P["background"])               # p[i]
GMAT = RATIO * BG[:, None]                    # g_i = sum_j f_j * GMAT[i, j]


def last_round_hits(path):
    """Rows of the last PSI-BLAST round in an outfmt 7 file, as (sseqid, evalue, qs, qseq, sseq)."""
    rows, cur = [], None
    with open(path) as fh:
        for line in fh:
            if line.startswith("# Iteration:"):
                cur = []
                rows.append(cur)
            elif line.startswith("#") or not line.strip() or line.startswith("Search has"):
                continue
            elif cur is not None:
                f = line.rstrip("\n").split("\t")
                cur.append((f[1], float(f[2]), int(f[3]), f[7], f[8]))
    return rows[-1] if rows else []


def alignment(query, hits):
    """Query-anchored rows, int codes: 0..19 residues, -1 gap or not covered, -2 other letters."""
    L = len(query)
    q = np.array([IDX.get(c, -2) for c in query])
    by_subject = {}
    for sid, ev, qs, qseq, sseq in sorted(hits, key=lambda h: h[1]):
        if ev > INCLUSION:
            continue
        row = by_subject.setdefault(sid, np.full(L, -1))
        pos = qs - 1
        for a, b in zip(qseq, sseq):
            if a == "-":
                continue                      # insertion in the subject: not on the query
            if row[pos] == -1:
                row[pos] = -1 if b == "-" else IDX.get(b.upper(), -2)
            pos += 1
    return [q] + list(by_subject.values())


def purge(rows):
    kept = [rows[0]]
    for r in rows[1:]:
        ok = True
        for k in kept:
            both = (r >= 0) & (k >= 0)
            n = both.sum()
            if n and (r[both] == k[both]).sum() / n >= IDENTITY:
                ok = False
                break
        if ok:
            kept.append(r)
    return np.array(kept)


def henikoff(M):
    n, L = M.shape
    w = np.zeros(n)
    for c in range(L):
        col = M[:, c]
        has = col >= 0
        if not has.any():
            continue
        vals, counts = np.unique(col[has], return_counts=True)
        r = len(vals)
        cnt = dict(zip(vals, counts))
        for k in np.flatnonzero(has):
            w[k] += 1.0 / (r * cnt[col[k]])
    if w.sum() == 0:
        w[:] = 1.0
    return w / w.sum()


def top1(M, w):
    L = M.shape[1]
    out, alpha0 = [], 0
    for c in range(L):
        col = M[:, c]
        has = col >= 0
        f = np.zeros(20)
        np.add.at(f, col[has], w[has])
        if f.sum() == 0:
            out.append(None)
            continue
        f /= f.sum()
        alpha = float(len(np.unique(col[has])) - 1)
        if alpha == 0:
            alpha0 += 1
        g = GMAT @ f
        Q = (alpha * f + BETA * g) / (alpha + BETA)
        out.append(AA[int(np.argmax(Q))])
    return out, alpha0


def one(args):
    name, seq, aln_dir = args
    hits = last_round_hits(os.path.join(aln_dir, name + ".tsv"))
    M = purge(alignment(seq, hits))
    t, alpha0 = top1(M, henikoff(M))
    s = "".join(c if c is not None else q for c, q in zip(t, seq))
    return name, s, len(M), alpha0


def main(fasta, aln_dir, out_fasta, out_json, *rest):
    workers = int(rest[1]) if len(rest) > 1 and rest[0] == "--workers" else os.cpu_count()
    names, seqs = features.read_fasta(fasta)
    with mp.get_context("fork").Pool(workers) as pool:
        res = pool.map(one, [(n, s, aln_dir) for n, s in zip(names, seqs)], chunksize=8)
    with open(out_fasta, "w") as fh:
        for name, s, _, _ in res:
            fh.write(f">{name}\n{s}\n")
    same = sum(a == b for (_, s, _, _), q in zip(res, seqs) for a, b in zip(s, q))
    total = sum(len(q) for q in seqs)
    rows = [r for _, _, r, _ in res]
    stats = {"sequences": len(res), "positions": total, "same_as_residue": same,
             "share_same_as_residue": same / total,
             "query_only_columns": sum(a for _, _, _, a in res),
             "rows_after_filter": {"median": float(np.median(rows)), "min": int(min(rows)),
                                   "max": int(max(rows)),
                                   "queries_with_query_only": int(sum(r == 1 for r in rows))}}
    json.dump(stats, open(out_json, "w"), indent=1)
    print(stats)


if __name__ == "__main__":
    main(*sys.argv[1:])
