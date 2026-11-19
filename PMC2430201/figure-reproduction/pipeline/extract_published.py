"""Read every printed number of Tables 1-8 from the article XML into published_values.json.

Usage: extract_published.py ARTICLE_XML OUT_JSON [--check COMMITTED_JSON]

Tables 3-8: 18 rows each (effect 0.2, 0.5, 0.8 x two trial sizes x k = 5, 10, 30), 21 printed integers per
row: % bias, % coverage and % power for MD, SMD and RoM at tau = 0 and 0.5 SD, and I2 (%) at tau = 0.5.
Table 2: the parameter grid. Table 1: the dopamine meta-analysis (estimates, CIs, p, I2).
--check: fail unless the values read equal the committed file (the pipeline's --extract run).
"""
import json
import re
import sys
import xml.etree.ElementTree as ET

COLS = [(q, tau, m) for q, taus in (("bias", (0, 0.5)), ("coverage", (0, 0.5)), ("power", (0, 0.5)), ("i2", (0.5,)))
        for tau in taus for m in ("MD", "SMD", "RoM")]
DESIGN = {  # sd, distribution, trial sizes (exp/contr) as printed, per table
    "3": (40, "normal", ("10/10", "100/100")),
    "4": (10, "normal", ("10/10", "100/100")),
    "5": (70, "normal", ("10/10", "100/100")),
    "6": (40, "skewed", ("10/10", "100/100")),
    "7": (40, "normal", ("14/6", "134/66")),
    "8": (40, "normal", ("6/14", "66/134")),
}


def text(e):
    return re.sub(r"\s+", " ", "".join(e.itertext())).strip()


def table(root, tid):
    tw = next(t for t in root.iter("table-wrap") if t.get("id") == tid)
    return [[text(td) for td in tr] for tr in tw.iter("tr")], text(tw.find("caption")) if tw.find("caption") is not None else ""


def sim_table(root, n):
    rows, caption = table(root, f"T{n}")
    data = [r for r in rows if len(r) == 24 and r[2].isdigit() and re.fullmatch(r"-?\d+", r[3])]
    if len(data) != 18:
        raise SystemExit(f"Table {n}: {len(data)} data rows, expected 18")
    sd, dist, sizes = DESIGN[n]
    out, labels = [], {}
    for i, r in enumerate(data):
        effect = (0.2, 0.5, 0.8)[i // 6]
        size = sizes[(i // 3) % 2]
        k = int(r[2])
        assert k == (5, 10, 30)[i % 3], (n, i, r[:3])
        if r[1]:
            assert r[1] == size, (n, i, r[1], size)
        for lab in r[0:1]:  # the row labels name the effect and the true MD and RoM
            m = re.fullmatch(r"(SMD|MD|RoM)\s*=\s*([\d.]+)", lab)
            if m:
                labels.setdefault(effect, {})[m.group(1)] = m.group(2)
        out.append({"effect": effect, "n": size, "k": k,
                    "cells": {f"{q}|{tau}|{m}": v for (q, tau, m), v in zip(COLS, r[3:])}})
    return {"sd": sd, "distribution": dist, "caption": caption, "row_labels": {str(k): v for k, v in labels.items()},
            "rows": out}


def table1(root):
    rows, caption = table(root, "T1")
    out, param = {}, None
    for r in rows:
        if len(r) < 7:
            continue
        if r[0] and r[1].isdigit():
            param = r[0]
            out[param] = {"trials": r[1], "patients": r[2]}
        if param and r[3] in ("Estimate", "95% CI", "p-value", "I2"):
            out[param][r[3]] = {"MD": r[4], "SMD": r[5], "RoM": r[6]}
    return {"caption": caption, "parameters": out}


def table2(root):
    rows, caption = table(root, "T2")
    return {"caption": caption, "rows": {r[0]: r[1] for r in rows if len(r) == 2 and r[0] and r[0] != "Varied Parameter"}}


def main():
    args = sys.argv[1:]
    check = None
    if "--check" in args:
        i = args.index("--check")
        check = args[i + 1]
        del args[i:i + 2]
    xml, out = args
    root = ET.parse(xml).getroot()
    doc = {"source": "PMC2430201.1.xml (PMC open-access copy), Tables 1-8",
           "columns": [f"{q}|{tau}|{m}" for q, tau, m in COLS],
           "table1": table1(root), "table2": table2(root),
           "tables": {n: sim_table(root, n) for n in DESIGN}}
    s = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    open(out, "w").write(s)
    cells = sum(len(r["cells"]) for t in doc["tables"].values() for r in t["rows"])
    print(f"{out}: Tables 3-8, {cells} cells; Table 1, {len(doc['table1']['parameters'])} parameters", file=sys.stderr)
    if check:
        same = json.load(open(check)) == json.loads(s)
        print(f"against {check}: {'the same' if same else 'DIFFERENT'}", file=sys.stderr)
        sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()
