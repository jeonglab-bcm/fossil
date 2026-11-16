"""Table 2: do the paper's GeCON scores follow each network's share of true pairs? (Review on #61.)

At the paper's settings GeCON connects 84% to 100% of all pairs. A network that connects every pair has
recall 1 and precision equal to the share of true pairs p. Scored as a single precision-recall point,
with the curve drawn straight from (0, 1) to that point, its area is (1 + p) / 2, whatever the data.
This step compares the paper's GeCON AUPR and AUROC with:
- (1 + p) / 2, for undirected pairs (p from the gold standard alone; it needs no simulation);
- our thresholded GeCON network scored the same way: (0, 1) -> (R, P) -> (1, p);
- our ranked AUPR (the score in Table 2), for contrast.

Usage: table2_density.py DREAM_DIR PAPER_VALUES.json OUT.json
"""
import json, os, sys
import numpy as np
import gecon
from gecon.evaluate import undirected_truth, upper


def printed_match(expected, observed):
    dec = len(expected.split(".")[1]) if "." in expected else 0
    return abs(float(expected) - observed) <= 0.5 * 10 ** -dec + 1e-12


def main():
    ddir, paper, out = sys.argv[1:4]
    meta = json.load(open(os.path.join(ddir, "datasets.json")))
    t2 = json.load(open(paper))["table2"]
    rows = {}
    for ds, m in meta.items():
        _, _, X = gecon.read_matrix(os.path.join(ddir, f"{ds}.tsv"))
        G = np.loadtxt(os.path.join(ddir, f"{ds}_gold.tsv"), dtype=int, ndmin=2)
        A, s = gecon.gecon(X, segments=m["segments"])
        y = undirected_truth(G)
        pred = upper(np.abs(A)) > 0
        tp = int((y.astype(bool) & pred).sum())
        P = tp / max(int(pred.sum()), 1)
        R = tp / int(y.sum())
        p = float(y.mean())
        rows[ds] = {"share_true": round(p, 6), "all_pairs_line": round((1 + p) / 2, 6),
                    "ours_point_line": round((1 + P) / 2 * R + (P + p) / 2 * (1 - R), 6),
                    "ours_ranked_aupr": round(gecon.aupr(y, upper(s.total)), 6),
                    "precision": round(P, 6), "recall": round(R, 6),
                    "paper_aupr": t2["aupr"][ds]["gecon"], "paper_auroc": t2["auroc"][ds]["gecon"]}
    ds = list(rows)
    res = {"datasets": rows, "comparisons": {}}
    for col in ("paper_aupr", "paper_auroc"):
        paper_v = np.array([float(rows[d][col]) for d in ds])
        for k in ("all_pairs_line", "ours_point_line", "ours_ranked_aupr", "share_true"):
            v = np.array([rows[d][k] for d in ds])
            res["comparisons"][f"{col} vs {k}"] = {
                "r": round(float(np.corrcoef(v, paper_v)[0, 1]), 3),
                "mean_ours": round(float(v.mean()), 3), "mean_paper": round(float(paper_v.mean()), 3),
                "max_abs_diff": round(float(np.abs(v - paper_v).max()), 3),
                "within_printed": int(sum(printed_match(rows[d][col], rows[d][k]) for d in ds)),
                "within_0.05": int(sum(abs(float(rows[d][col]) - rows[d][k]) <= 0.05 for d in ds))}
    json.dump(res, open(out, "w"), indent=1)
    for k, v in res["comparisons"].items():
        print(k, v)


if __name__ == "__main__":
    main()
