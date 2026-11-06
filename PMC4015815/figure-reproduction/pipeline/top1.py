"""Top-1-gram sequences from PSI-BLAST ASCII PSSMs.

usage: top1.py FASTA PSSM_DIR OUT_FASTA OUT_JSON [VARIANT]

VARIANT:
  zero_to_residue  (default) a column whose percentages are all zero gives the query residue
  pse_in_one       such a column gives A, as Pse-in-One 2.0's parser does
  scores           the largest log-odds score of the column instead of the largest percentage

As in the lab's Pse-in-One 2.0 (profile.py, produce_one_top_n_gram): for each query position,
the 20 "weighted observed percentages" of the ASCII PSSM (ARNDCQEGHILKMFPSTWYV order) and their
largest value; ties go to the first amino acid in that order (heapq.nlargest). One change: a
column with all zeros (9,042 of 560,022 positions) gives the query residue, not A. The paper
defines the Top-1-gram as the most frequent amino acid of a frequency profile computed from the
alignment, which includes the query, so such a column cannot be empty; Pse-in-One's A is an
artifact of its parser (mean ROC at dMAX 150: 0.9502 with the residue, 0.9412 with A). A query without a PSSM gets the BLOSUM62 Top-1-gram, which is the residue itself
(every BLOSUM62 row has its maximum on the diagonal). Residues outside the 20 letters stay as
they are and are not counted by the features.
"""
import json
import os
import sys

import features

PSSM_ORDER = "ARNDCQEGHILKMFPSTWYV"


def read_pssm(path, use_scores=False):
    cols = []
    with open(path) as fh:
        for n, line in enumerate(fh, 1):
            f = line.split()
            if n <= 3 or len(f) < 20:
                continue
            cols.append((f[1], [int(x) for x in (f[2:22] if use_scores else f[22:-2])]))
    return cols


def main(fasta, pssm_dir, out_fasta, out_json, variant="zero_to_residue"):
    names, seqs = features.read_fasta(fasta)
    stats = {"variant": variant, "sequences": len(names), "with_pssm": 0, "without_pssm": [], "all_zero_columns": 0,
             "tied_columns": 0, "positions": 0, "same_as_residue": 0}
    with open(out_fasta, "w") as out:
        for name, seq in zip(names, seqs):
            p = os.path.join(pssm_dir, name + ".pssm")
            if os.path.exists(p) and os.path.getsize(p) > 0:
                cols = read_pssm(p, use_scores=variant == "scores")
                assert len(cols) == len(seq), (name, len(cols), len(seq))
                stats["with_pssm"] += 1
                top = []
                for res, pct in cols:
                    m = max(pct)
                    if m == 0 and variant != "scores":
                        stats["all_zero_columns"] += 1
                        if variant == "zero_to_residue":
                            top.append(res.upper())
                            continue
                    if pct.count(m) > 1:
                        stats["tied_columns"] += 1
                    top.append(PSSM_ORDER[pct.index(m)])
                t = "".join(top)
            else:
                stats["without_pssm"].append(name)
                t = seq
            stats["positions"] += len(seq)
            stats["same_as_residue"] += sum(a == b for a, b in zip(seq, t))
            out.write(f">{name}\n{t}\n")
    stats["n_without_pssm"] = len(stats["without_pssm"])
    stats["share_same_as_residue"] = stats["same_as_residue"] / stats["positions"]
    json.dump(stats, open(out_json, "w"), indent=2)
    print({k: v for k, v in stats.items() if k != "without_pssm"})


if __name__ == "__main__":
    main(*sys.argv[1:])
