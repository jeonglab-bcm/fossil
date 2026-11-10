#!/usr/bin/env python3
"""The arithmetic check: the paper's claims recomputed from its own tables and supplements, and the
counts of the evaluation sets in Additional file 1 against the text.

This says whether we compute each statistic the way the paper did; it says nothing about our run.

Usage: text_arithmetic.py PUBLISHED_TABLES_JSON SUPPLEMENT_DIR S3_TXT OUT_DIR
Writes arithmetic.json (each check with the paper's value and the value recomputed from its
tables) and dataset.json (chain counts of Additional file 1).
"""
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path


def main(tables, sup, s3, out):
    t = json.load(open(tables))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    checks = []

    def add(name, paper, recomputed, ok):
        checks.append({"claim": name, "paper": paper, "recomputed": recomputed, "agrees": bool(ok)})

    t1 = t["table1"]
    sites = sum(int(t1[k]["sites"]) for k in ("Zn1", "Zn2", "Zn3", "Zn4"))
    add("Table 1: sites of the four types add up to 'Any'", t1["Any"]["sites"], sites, sites == int(t1["Any"]["sites"]))
    # Chains with at least one site: inclusion-exclusion over the bottom half of Table 1.
    single = sum(int(t1[k]["chains"]) for k in ("Zn1", "Zn2", "Zn3", "Zn4"))
    mt = {k: int(v) for k, v in t1["multiple_types"].items()}
    ie = single - sum(v for k, v in mt.items() if k.count(",") == 1) + sum(v for k, v in mt.items() if k.count(",") == 2) - mt["{1,2,3,4}"]
    add("Table 1: chains of the four types, by inclusion-exclusion over the multiple-type counts, give 'Any'", t1["Any"]["chains"], ie, ie == int(t1["Any"]["chains"]))

    t2 = t["table2"]
    types = ("Zn4", "Zn3", "Zn2", "Zn1")
    ligands = {k: int(t1[k]["sites"]) * int(k[2]) for k in types}
    for k in types:
        add(f"Table 2: {k} total = {k[2]} ligands x {t1[k]['sites']} sites", t2["Total"][k], ligands[k], ligands[k] == int(t2["Total"][k]))
    bad_fa, bad_fs, n = [], [], 0
    for a in "CHDENQ":
        row = t2[a]
        s = sum(int(row[k][0]) for k in types)
        add(f"Table 2: row {a} adds up to 'All'", row["All"], s, s == int(row["All"]))
        for k in types:
            na = int(row[k][0])
            fa = round(100 * na / int(t2["Total"][k]), 1)
            fs = round(100 * na / int(row["All"]), 1)
            n += 1
            if abs(fa - float(row[k][1])) > 0.051:
                bad_fa.append(f"{a} {k}: {row[k][1]} vs {fa}")
            if abs(fs - float(row[k][2])) > 0.051:
                bad_fs.append(f"{a} {k}: {row[k][2]} vs {fs}")
    # One known slip: C in Zn4, 663 / 956 = 69.35%, printed 69.3 (every other cell rounds to nearest).
    slips = [b for b in bad_fa if b.startswith("C Zn4:")]
    add(f"Table 2: fa recomputed from Na ({n} cells)", "printed", bad_fa or "all equal", not [b for b in bad_fa if b not in slips])
    if slips:
        checks[-1]["paper_error"] = "rounding slip: 663 / 956 = 69.351%, printed 69.3"
    add(f"Table 2: fs recomputed from Na ({n} cells)", "printed", bad_fs or "all equal", not bad_fs)
    de3 = int(t2["D"]["Zn3"][0]) + int(t2["E"]["Zn3"][0])
    de = int(t2["D"]["All"]) + int(t2["E"]["All"])
    add("Text: 'half of [DE] residues binding zinc are contained in Zn3 sites'", "about half", f"{100 * de3 / de:.1f}%", 0.4 <= de3 / de <= 0.6)
    add("Text: 'cysteines are mainly involved in structural sites' (fs of C in Zn4)", "mainly", t2["C"]["Zn4"][2] + "%", float(t2["C"]["Zn4"][2]) > 50)

    f2 = t["fig2"]
    for kind, col in (("sites", "sites"), ("chains", "chains")):
        for k, (cov, nc) in f2[kind].items():
            ref = t1["Any" if k == "Overall" else k][col]
            add(f"Fig. 2 {kind} {k}: covered + not covered = Table 1", ref, int(cov) + int(nc), int(cov) + int(nc) == int(ref))

    flags = defaultdict(int)
    for line in open(s3, encoding="latin-1"):
        p = [x.strip() for x in line.split("|")]
        if len(p) == 3 and p[1] in ("X", "-") and p[2] in ("X", "-"):
            flags[(p[1], p[2])] += 1
    pred = flags[("X", "X")] + flags[("-", "X")]
    prev = flags[("X", "X")] + flags[("X", "-")]
    add("Text: the SPCH-SVM identified 2,833 human zinc-binding chains (Additional file 3)", "2833", pred, pred == 2833)
    add("Text: 965 of 3,207 previously found chains not confirmed (Additional file 3)", "965 of 3207", f"{flags[('X', '-')]} of {prev}", flags[("X", "-")] == 965 and prev == 3207)
    add("Text: about 600 proteins not detected in [9] are predicted (Additional file 3)", "about 600", flags[("-", "X")], abs(flags[("-", "X")] - 600) <= 50)

    passed = all(c["agrees"] for c in checks)
    good = sum(c["agrees"] for c in checks)
    slip = " (Table 2 fa has one rounding slip: C in Zn4, 663/956 = 69.35%, printed 69.3)" if any(c.get("paper_error") for c in checks) else ""
    json.dump({"passed": passed, "detail": f"{good} of {len(checks)} claims come back from the paper's own tables and Additional file 3{slip}",
               "checks": checks}, open(out / "arithmetic.json", "w"), indent=1)

    # Chain counts of Additional file 1.
    chains = defaultdict(lambda: defaultdict(set))
    for f in sorted(Path(sup).glob("C*_*")):
        part = "loo" if f.name.endswith("loo") else "cv"
        for line in open(f):
            cls, ch = line.split()[:2]
            chains[part][ch].add(cls)
    allc = {c for part in chains.values() for c in part}
    zinc = {c for part in chains.values() for c, cl in part.items() if "1" in cl}
    ds = {"zinc_chains": len(zinc), "negative_chains": len(allc - zinc),
          "loo_zinc_chains": sum(1 for cl in chains["loo"].values() if "1" in cl),
          "loo_negative_chains": sum(1 for cl in chains["loo"].values() if "1" not in cl),
          "cv_zinc_chains": sum(1 for cl in chains["cv"].values() if "1" in cl),
          "cv_negative_chains": sum(1 for cl in chains["cv"].values() if "1" not in cl)}
    json.dump(ds, open(out / "dataset.json", "w"), indent=1)
    print(json.dumps({"passed": passed, "failed": [c for c in checks if not c["agrees"]], "dataset": ds}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
