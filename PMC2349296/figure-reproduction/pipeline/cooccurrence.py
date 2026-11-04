#!/usr/bin/env python3
"""Co-occurrence baseline (Table 2), corpus statistics (Table 3) and the filtered corpora (Table 4).

Usage: cooccurrence.py DATA_DIR OUT_DIR

Writes:
  cooccurrence.csv   P/R/F and counts per corpus, unfiltered and filtered
  table3.csv         per-sentence averages and fractions, with three tokenizers
  corpus_counts.csv  sentences, documents, entities, interactions per corpus
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import CORPORA, candidate_pairs, filter_noninteracting, load, score  # noqa: E402

# The paper does not state its tokenizer. These candidates bracket the plausible choices;
# tokens_medpost.csv (from the RelEx step, MedPost's own tokenizer) is added there when it runs.
TOKENIZERS = {
    "whitespace": lambda t: t.split(),
    "ptb_like": lambda t: re.findall(r"\w+(?:[-'./]\w+)*|[^\w\s]", t),
    "fine": lambda t: re.findall(r"[A-Za-z]+|\d+|[^\w\s]", t),
}


def cooccurrence(sentences):
    return {s.id: set(candidate_pairs(s)) for s in sentences}


def main(data_dir: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    rows, t3, counts = [], [], []
    for c in CORPORA:
        sents = load(c, data_dir)
        filt = filter_noninteracting(sents)
        for variant, ss in (("unfiltered", sents), ("filtered", filt)):
            sc = score(cooccurrence(ss), ss)
            ep = sum(len(candidate_pairs(s)) for s in ss)
            i = sum(len(s.interactions) for s in ss)
            rows.append({"corpus": c, "variant": variant, **sc, "I": i, "EP": ep,
                         "I_over_EP": i / ep, "F_approx": 2 * (i / ep) / (1 + i / ep)})
        n = len(sents)
        rec = {
            "corpus": c,
            "sentences": n,
            "entities": sum(len(s.entities) for s in sents) / n,
            "entity_pairs": sum(len(candidate_pairs(s)) for s in sents) / n,
            "interactions": sum(len(s.interactions) for s in sents) / n,
            "no_entities": sum(not s.entities for s in sents) / n,
            "no_interactions": sum(not s.interactions for s in sents) / n,
        }
        for name, tok in TOKENIZERS.items():
            rec[f"tokens_{name}"] = sum(len(tok(s.text)) for s in sents) / n
        t3.append(rec)
        counts.append({
            "corpus": c, "documents": len({s.doc for s in sents}), "sentences": n,
            "entities": sum(len(s.entities) for s in sents),
            "interactions": sum(len(s.interactions) for s in sents),
            "interaction_elements": sum(s.raw_interactions for s in sents),
            "self_interactions": sum(len(p) == 1 for s in sents for p in s.interactions),
            "discontinuous_entities": sum(len(e.spans) > 1 for s in sents for e in s.entities),
        })
    for name, data in (("cooccurrence.csv", rows), ("table3.csv", t3), ("corpus_counts.csv", counts)):
        with open(out / name, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    for r in rows:
        print(f"{r['corpus']:9s} {r['variant']:10s} P={r['P']:.3f} R={r['R']:.3f} F={r['F']:.3f} "
              f"I/EP={r['I_over_EP']:.3f}")
    for r in t3:
        print(r)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
