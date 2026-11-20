"""Table 4, the clinical validation: for cerivastatin (Baycol) and rofecoxib (Vioxx), train on every other
drug and predict each of the ADRs the paper lists, and each group of them, with chem, chem+bio and
chem+bio+pheno.

Usage: table4.py DATA_DIR PUBLISHED_VALUES.json OUT.json

The call is Yes when the SVM's probability is above 0.5: LIBSVM's predicted label with -b 1, the
probability outputs that give the paper's AUCs. The decision-value rule (Yes when the decision value is
positive) is kept as a hypothesis.
"""
import json
import sys

import adrfusion as A

from run_models import load

FEATURE_SETS = ["chem", "chem+bio", "chem+bio+pheno"]
DRUGS = {"Cerivastatin (Baycol)": "cerivastatin", "Rofecoxib (Vioxx)": "rofecoxib"}


def main():
    data_dir, pubf, out = sys.argv[1:4]
    data = load(data_dir)
    pub = json.load(open(pubf))["table4"]
    rows = []
    for label, name in DRUGS.items():
        i = data.names.index(name)
        prow = [r for r in pub if r["drug"] == label]
        singles = [data.adrs.index(r["cui"]) for r in prow if r["cui"]]
        targets = singles + [singles]
        res = {fs: A.predict_held_out(data, i, targets, fs, seed=0) for fs in FEATURE_SETS}
        for k, r in enumerate(prow):
            row = {"drug": label, "cui": r["cui"] or "group", "adr": r["adr"], "known_in_data": res["chem"][k]["known"]}
            for fs in FEATURE_SETS:
                x = res[fs][k]
                row[fs] = {"published": r[fs], "call": "Yes" if x["probability"] > 0.5 else "No",
                           "call_decision": x["call"], "probability": round(x["probability"], 10),
                           "decision": round(x["decision"], 10)}
            rows.append(row)
    fields = [{"name": f"{r['drug'].split(' ')[0]}|{r['adr']}|{fs}", "expected": r[fs]["published"], "observed": r[fs]["call"]}
              for r in rows for fs in FEATURE_SETS]
    alt = sum(r[fs]["call_decision"] == r[fs]["published"] for r in rows for fs in FEATURE_SETS)
    json.dump({"rows": rows, "fields": fields,
               "hypotheses": {"decision_rule_matches": alt, "fields": len(fields)}},
              open(out, "w"), indent=1)
    print(f"Table 4: {sum(f['expected'] == f['observed'] for f in fields)} of {len(fields)} calls; decision rule {alt}", file=sys.stderr)


if __name__ == "__main__":
    main()
