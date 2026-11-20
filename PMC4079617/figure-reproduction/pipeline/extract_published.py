"""Read every printed value of the paper from its sources into published_values.json.

Usage: extract_published.py ARTICLE_XML S1_PDF S2_PDF OUT_JSON [--check COMMITTED_JSON]

Tables 1-3 (n = 1500) come from the article XML (PMC open-access copy); Tables A1-A3 (n = 500) from
Additional file 2 and the design (alpha0, beta0 of the 24 scenarios) from Additional file 1, both read with
pdftotext -layout (poppler-utils). Values are kept as printed strings ("-17.8", "0.09"); the Unicode minus is
written as "-". --check fails when the result differs from the committed copy.
"""
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

COLS = [f"{form}|{lev}|{m}" for form in ("linear", "nonlinear") for lev in ("moderate", "strong") for m in ("LB", "RP")]
ROWS = [(rr, py, c) for rr in ("1.5", "2.0") for py in ("10%", "25%", "40%") for c in ("0%", "2%", "5%")]
TITLES = {"table1": "Relative bias (%) in log scale (n = 1500)", "table2": "Standard error in log scale (n = 1500)",
          "table3": "Mean Square Error (MSE) in log scale (n = 1500)",
          "tableA1": "Relative Bias (%) in Log Scale When n=500", "tableA2": "Standard Error in Log Scale When n=500",
          "tableA3": "Mean Square Error (MSE) in Log Scale When n=500"}
QUANTITY = {"1": "relbias", "2": "se", "3": "mse"}
NUM = r"-?\d+\.\d+"


def clean(s):
    return s.replace("−", "-").replace("–", "-").strip()


def text(el):
    return clean("".join(el.itertext()))


def xml_tables(path):
    root = ET.parse(path).getroot()
    out = {}
    for tw in root.iter("table-wrap"):
        tid = tw.get("id")
        if tid not in ("T1", "T2", "T3"):
            continue
        rows = []
        for tr in tw.find(".//tbody").iter("tr"):
            cells = [text(td) for td in tr.iter("td")]
            vals = cells[-8:]
            if len(vals) == 8 and all(re.fullmatch(NUM, v) for v in vals):
                rows.append(vals)
        out["table" + tid[1]] = rows
    return out


def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", path, "-"], check=True, capture_output=True, text=True).stdout


def s2_tables(path):
    txt = pdf_text(path)
    parts = re.split(r"Table (A[123])\.", txt)
    out = {}
    for name, body in zip(parts[1::2], parts[2::2]):
        rows = []
        for line in body.splitlines():
            m = re.search(r"([025])%\s+((?:" + NUM + r"\s+){7}" + NUM + r")\s*$", line)
            if m:
                rows.append(m.group(2).split())
        out["table" + name] = rows
    return out


def s1_design(path):
    txt = pdf_text(path)
    design = {}
    # the six scenario lines in printed order (RR 1.5: 10, 25, 40%; RR 2.0: 10, 25, 40%); the 40% lines also
    # carry the two alpha0 values (alpha0, beta0 pairs)
    lines = [l for l in txt.splitlines() if re.search(r"\b(10|25|40)%\s+-\d", l)]
    if len(lines) != 6:
        sys.exit(f"Additional file 1: {len(lines)} scenario lines read, 6 expected")
    keys = [(r, p) for r in ("1.5", "2.0") for p in ("10%", "25%", "40%")]
    for (rr, py), line in zip(keys, lines):
        if not re.search(rf"\b{py}\s", line):
            sys.exit(f"Additional file 1: expected the {py} line, read {line!r}")
        nums = re.findall(r"-\d+\.\d+", line)
        betas = nums[1::2] if len(nums) == 8 else nums  # beta0: lin mod, lin str, non-lin mod, non-lin str
        for (form, lev), b in zip([("linear", "moderate"), ("linear", "strong"), ("nonlinear", "moderate"),
                                   ("nonlinear", "strong")], betas):
            design[f"{rr}|{py}|{form}|{lev}"] = b
        if len(nums) == 8:
            alpha = {"moderate": nums[0], "strong": nums[2]}
    return {"alpha0": alpha, "beta0": design}


def main():
    args = sys.argv[1:]
    check = None
    if "--check" in args:
        i = args.index("--check")
        check = args[i + 1]
        del args[i:i + 2]
    xml_path, s1, s2, out = args
    tables = {**xml_tables(xml_path), **s2_tables(s2)}
    doc = {"about": "Every printed value of Tables 1-3 (article XML) and Tables A1-A3 (Additional file 2), and the "
                    "design of Additional file 1, as printed.",
           "columns": COLS, "design": s1_design(s1), "tables": {}}
    for name in ("table1", "table2", "table3", "tableA1", "tableA2", "tableA3"):
        rows = tables[name]
        if len(rows) != 18:
            sys.exit(f"{name}: {len(rows)} rows read, 18 expected")
        doc["tables"][name] = {
            "title": TITLES[name], "n": 1500 if name[5] != "A" else 500, "quantity": QUANTITY[name[-1]],
            "rows": [{"rr": rr, "py": py, "contamination": c, "cells": dict(zip(COLS, vals))}
                     for (rr, py, c), vals in zip(ROWS, rows)]}
    if len(doc["design"]["beta0"]) != 24:
        sys.exit("design: 24 beta0 expected")
    s = json.dumps(doc, indent=1) + "\n"
    open(out, "w").write(s)
    if check:
        if json.load(open(check)) != doc:
            sys.exit(f"{out} differs from {check}")
        print(f"{out}: same as {check}", file=sys.stderr)
    print(f"{out}: 6 tables x 18 rows x 8 cells, 24 designs", file=sys.stderr)


if __name__ == "__main__":
    main()
