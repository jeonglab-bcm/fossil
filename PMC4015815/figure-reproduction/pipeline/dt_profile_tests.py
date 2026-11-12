"""Are our Top-1-gram sequences too close to the residues? Hypothesis tests for the SVM-DT items.

usage: dt_profile_tests.py FASTA MEMBERSHIP TOP1_FASTA_GZ OUTPUT_DIR OUT_JSON

The paper's reference [28] (Liu et al. 2008, the lab's Top-n-gram paper, whose SVM-Top-n-gram
values Table 1 quotes) builds its profiles with 10 PSI-BLAST iterations and BLOSUM62 pseudocounts
(target frequency (alpha f + beta g) / (alpha + beta), beta = 10, alpha = distinct residues in the
column - 1). Our profiles use 3 iterations and PSI-BLAST's observed percentages, with no
pseudocounts. Three tests on the committed outputs, none of them a rebuild of the profiles
(profile2008.py does that):

1. closeness: the share of our Top-1-gram positions equal to the query residue, and how our
   Fig. 4A heatmap correlates with the paper's Fig. 4A and with its residue heatmap, Fig. 4B.
2. pseudocount limit: a column that holds only the query residue r has alpha = 0, so its target
   frequencies are the pseudocounts alone, g_i = p_i * BLOSUM62 ratio(i, r), and its Top-1-gram
   is argmax_i g_i. Over the 20 amino acids only M changes (to L).
3. M to L: turn M into L wherever our Top-1-gram is the query's own M, rerun
   discriminant_weights.py for family 2.5.1.3 at dMAX 150, and score Fig. 4A and Fig. 5A-B
   against the paper as fig4_scores.json and fig5_scores.json do (Spearman over the 400 cells;
   bar correlation over x = 2..149, our weight at d = x - 1).

Not part of the pipeline; a cause test like dt_variants.json.
"""
import gzip
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from scipy.stats import spearmanr

import features

HERE = os.path.dirname(os.path.abspath(__file__))


def pseudocount_limit():
    b = json.load(open(os.path.join(HERE, "params", "blosum62_psiblast.json")))
    A, R, p = b["alphabet"], np.array(b["freq_ratios"]), np.array(b["background"])
    out = {}
    for k, r in enumerate(A):
        g = p * R[:, k]                                  # g_i = sum_j f_j q_ij / p_j with f_r = 1
        out[r] = A[int(np.argmax(g))]
    return out


def weights(fasta, membership, top1_path, out):
    subprocess.run([sys.executable, os.path.join(HERE, "discriminant_weights.py"), "--fasta", fasta,
                    "--membership", membership, "--sequences", f"top1:{top1_path}",
                    "--family", "2.5.1.3", "--dmax", "150", "--seed", "1", "--out", out],
                   check=True, capture_output=True)
    return json.load(open(out))


def score(w, pub4, pub5):
    A = features.ALPHABET
    L = np.array(w["l2_first_second"])
    m = A.index("M")
    res = {"fig4a_spearman": round(float(spearmanr(pub4["A"].ravel(), L.ravel())[0]), 4),
           "fig4a_M_row_col_mean": [round(float(L[m].mean()), 1), round(float(L[:, m].mean()), 1)],
           "rank_LL": int(np.flatnonzero(np.argsort(-L.ravel()) == A.index("L") * 21)[0]) + 1}
    x = np.arange(2, 150)
    for panel, pair in (("A", "G,G"), ("B", "L,L")):
        ours = np.array(w["weights"][pair])              # d = 0..150
        res[f"fig5{panel.lower()}_r"] = round(float(np.corrcoef(pub5[panel][x], ours[x - 1])[0, 1]), 4)
    return res


def main(fasta, membership, top1_gz, outdir, out_json):
    names, seqs = features.read_fasta(fasta)
    with gzip.open(top1_gz, "rt") as fh, tempfile.TemporaryDirectory() as tmp:
        base = os.path.join(tmp, "top1.fasta")
        open(base, "w").write(fh.read())
        tnames, top1 = features.read_fasta(base)
        assert tnames == names
        same = sum(a == b for s, t in zip(seqs, top1) for a, b in zip(s, t))
        total = sum(len(s) for s in seqs)

        limit = pseudocount_limit()
        changes = {r: t for r, t in limit.items() if r != t}
        ml = os.path.join(tmp, "top1_M_to_L.fasta")
        n_changed = 0
        with open(ml, "w") as fh2:
            for name, s, t in zip(names, seqs, top1):
                t2 = "".join(changes.get(b, b) if a == b else b for a, b in zip(s, t))
                n_changed += sum(x != y for x, y in zip(t, t2))
                fh2.write(f">{name}\n{t2}\n")

        f4 = json.load(open(os.path.join(outdir, "fig4_scores.json")))["panels"]
        f5 = json.load(open(os.path.join(outdir, "fig5_scores.json")))["panels"]
        pub4 = {k: np.array(f4[k]["published_values"]) for k in ("A", "B")}
        pub5 = {k: np.array(f5[k]["published_values_x0_150"]) for k in ("A", "B")}
        ours = json.load(open(os.path.join(outdir, "weights_dt_2.5.1.3.json")))
        w_base = weights(fasta, membership, base, os.path.join(tmp, "w_base.json"))
        assert np.allclose(w_base["l2_first_second"], ours["l2_first_second"]), \
            "rerun does not reproduce the committed weights_dt_2.5.1.3.json"
        w_ml = weights(fasta, membership, ml, os.path.join(tmp, "w_ml.json"))

    L = np.array(ours["l2_first_second"])
    m = features.ALPHABET.index("M")
    res = {
        "about": __doc__.split("\n\n")[0],
        "closeness": {
            "top1_equal_to_residue": round(same / total, 4),
            "fig4a_ours_vs_paper_4a_spearman": round(float(spearmanr(pub4["A"].ravel(), L.ravel())[0]), 4),
            "fig4a_ours_vs_paper_4b_spearman": round(float(spearmanr(pub4["B"].ravel(), L.ravel())[0]), 4),
            "paper_4a_vs_paper_4b_spearman": round(float(spearmanr(pub4["A"].ravel(), pub4["B"].ravel())[0]), 4),
        },
        "pseudocount_limit": {"query_only_column_top1": limit, "changes": changes},
        "m_to_l": {
            "positions_changed": n_changed,
            "paper": {"fig4a_M_row_col_mean": [round(float(pub4["A"][m].mean()), 1),
                                               round(float(pub4["A"][:, m].mean()), 1)]},
            "ours": score(w_base, pub4, pub5),
            "ours_M_to_L": score(w_ml, pub4, pub5),
        },
    }
    json.dump(res, open(out_json, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:6])
