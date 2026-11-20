"""Read the printed numbers of Tables 1-5 from the article XML into published_values.json.

Usage: extract_published.py ARTICLE.xml OUT.json [--check COMMITTED.json]

Values stay strings, as printed, so their precision is known. With --check, exit 1 unless the values read
equal the committed file (the pipeline's default run uses the committed file; --extract reruns this).
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PARAMS = ["g00", "g01", "g10", "g11", "sigma0", "sigma1"]
LABELS = {"γ00": "g00", "γ01": "g01", "γ10": "g10", "γ11": "g11", "σ0": "sigma0", "σ1": "sigma1"}


def cells(tr):
    return ["".join(td.itertext()).strip().replace("−", "-") for td in tr.findall("td") + tr.findall("th")]


def table_rows(root, label):
    for tw in root.iter("table-wrap"):
        lab = tw.find("label")
        if lab is not None and lab.text.strip() == label:
            return [cells(tr) for tr in tw.find(".//table").iter("tr")]
    raise SystemExit(f"{label} not found")


def grid_rows(rows):
    """Rows of Tables 1 and 3: groups and size are printed once per block; fill them down."""
    out, g, n = [], None, None
    for r in rows[1:]:
        g = r[0] or g
        n = r[1] or n
        out.append((int(g), int(n), r[2], r[3:]))
    return out


def main():
    xml, out = sys.argv[1], sys.argv[2]
    root = ET.parse(xml).getroot()
    pub = {"source": "PMC1955447.1.xml (PMC open-access copy), Tables 1-5"}

    t1 = []
    for g, n, icc, v in grid_rows(table_rows(root, "Table 1")):
        assert len(v) == 7, v
        t1.append({"groups": g, "size": n, "icc": icc, "converged": v[0], **dict(zip(PARAMS, v[1:]))})
    assert len(t1) == 27
    pub["table1"] = t1

    rows = table_rows(root, "Table 2")
    t2 = {}
    for r in rows[2:]:
        p = LABELS[r[0]]
        t2[p] = {"groups": {"30": r[1], "50": r[2], "100": r[3], "p": r[4]},
                 "size": {"5": r[5], "30": r[6], "50": r[7], "p": r[8]},
                 "icc": {"0.04": r[9], "0.17": r[10], "0.38": r[11], "p": r[12]}}
    assert list(t2) == PARAMS
    pub["table2"] = t2

    t3 = []
    for g, n, icc, v in grid_rows(table_rows(root, "Table 3")):
        assert len(v) == 6, v
        t3.append({"groups": g, "size": n, "icc": icc, **dict(zip(PARAMS, v))})
    assert len(t3) == 27
    pub["table3"] = t3
    pub["table3_header_g10"] = table_rows(root, "Table 3")[0][5]

    rows = table_rows(root, "Table 4")
    t4 = {}
    for r in rows[2:]:
        p = LABELS[r[0]]
        t4[p] = {"bias": dict(zip(["0.10", "0.34", "0.45"], r[1:4])),
                 "noncoverage": dict(zip(["0.10", "0.34", "0.45"], r[4:7])),
                 "converged": dict(zip(["0.10", "0.34", "0.45"], r[7:10]))}
    pub["table4"] = t4

    rows = table_rows(root, "Table 5")
    t5, groups = [], None
    for r in rows[2:]:
        r = [c for c in r]
        model = int(r[0])
        groups = int(r[1]) if r[1] else groups
        vals = r[2:]
        assert len(vals) == 21, (model, vals)
        for k, size in enumerate((5, 30, 50)):
            block = vals[7 * k: 7 * k + 7]
            rec = {"model": model, "groups": groups, "size": size, "converged": block[0]}
            for p, cell in zip(PARAMS, block[1:]):
                m = re.fullmatch(r"(-?[\d.]+) \((\d+)\)", cell)
                assert m, cell
                rec[p] = {"bias": m.group(1), "noncoverage": m.group(2)}
            t5.append(rec)
    assert len(t5) == 72
    pub["table5"] = t5

    Path(out).write_text(json.dumps(pub, indent=1, ensure_ascii=False) + "\n")
    if "--check" in sys.argv:
        committed = json.load(open(sys.argv[sys.argv.index("--check") + 1]))
        if committed != pub:
            diff = [k for k in pub if pub[k] != committed.get(k)]
            print(f"printed values differ from the committed file: {diff}", file=sys.stderr)
            sys.exit(1)
        print("printed values equal the committed file", file=sys.stderr)


if __name__ == "__main__":
    main()
