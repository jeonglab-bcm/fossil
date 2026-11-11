"""Does the Weka 3.4 release matter? Compare WekaRun outputs of other 3.4.x releases with 3.4.3's.

  weka_versions.py OUT.json REF_DIR VERSION=DIR [VERSION=DIR ...]

Each DIR is a WekaRun output folder (tree.txt, scores_*.tsv, weka.json) for the download page's
recipe on the archived sets. Passes when every release builds the same tree and the same scores;
the AUCs are reported (Weka 3.4.1 and 3.4.2 draw the threshold curve slightly differently).
"""
import json
import sys
from pathlib import Path


def load(d):
    d = Path(d)
    return {"tree": (d / "tree.txt").read_text().split("Alternating", 1)[1],
            "scores": {n: (d / f"scores_{n}.tsv").read_text() for n in ("training", "hgmd", "pocus", "cv")},
            "stats": json.loads((d / "weka.json").read_text())}


def main(out, ref, *others):
    r = load(ref)
    rows, ok = [], True
    for spec in others:
        v, d = spec.split("=", 1)
        o = load(d)
        same_tree = o["tree"] == r["tree"]
        same_scores = o["scores"] == r["scores"]
        auc = {k: o["stats"][k]["auc_disease"] - r["stats"][k]["auc_disease"] for k in ("training", "hgmd", "pocus", "cv10")}
        acc = {k: o["stats"][k]["pct_correct"] - r["stats"][k]["pct_correct"] for k in ("training", "hgmd", "pocus", "cv10")}
        ok &= same_tree and same_scores and max(abs(x) for x in acc.values()) == 0
        rows.append({"version": v, "same_tree": same_tree, "same_scores": same_scores,
                     "auc_minus_343": auc, "accuracy_minus_343": acc})
    worst = max(abs(x) for row in rows for x in row["auc_minus_343"].values())
    detail = (f"Weka {', '.join(r['version'] for r in rows)} against 3.4.3 on the archived sets: "
              f"{'same tree, same scores and same accuracy' if ok else 'results differ'}; AUC differs by at most {worst:.4f}")
    json.dump({"passed": bool(ok), "detail": detail, "versions": rows}, open(out, "w"), indent=1)
    print(detail)


if __name__ == "__main__":
    main(*sys.argv[1:])
