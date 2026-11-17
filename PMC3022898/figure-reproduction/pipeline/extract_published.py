"""Read every printed number of the paper's tables into published_values.json.

Usage: extract_published.py ARTICLE_XML SUPPLEMENT_DOC OUT.json [--soffice soffice]

* Tables 2-5 come from the PMC article XML (JATS).
* Tables S1-S7 come from Additional file 1 (Word 97 .DOC), converted to .docx with LibreOffice and
  read from its document.xml.

Values stay strings, as printed ("9.5%" becomes "9.5"), so a comparison knows their precision.
The committed output/published_values.json is what the pipeline compares against; CI reruns this
step only when LibreOffice is installed (--extract), and then checks that it gives the same file.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

SCEN = {1: (0.05, 0.02), 2: (0.05, 0.09), 3: (0.20, 0.02), 4: (0.20, 0.09)}
RRS = ["1.0", "1.5", "2.0", "2.5", "3.0", "4.0", "5.0"]
SIZES = ["1000/1000", "1000/5000", "5000/1000", "5000/5000"]
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def clean(s):
    return s.replace("%", "").replace("−", "-").strip()


def text(el):
    return "".join(el.itertext()).strip()


def article_tables(xml_path):
    root = ET.parse(xml_path).getroot()
    out = {}
    for tw in root.iter("table-wrap"):
        tid = tw.get("id")
        rows = [[text(td) for td in tr if td.tag in ("td", "th")] for tr in tw.iter("tr")]
        out[tid] = rows
    res = {}
    # Tables 2 and 3: per scenario block, rows "RR/ESR" with 4 cells (S 1000/1000, R 1000/1000, S 5000/5000, R 5000/5000)
    for tid, key in (("T2", "table2"), ("T3", "table3")):
        scen, cells = 0, {}
        for r in out[tid]:
            if len(r) == 1 and "exposure probability" in r[0]:
                scen += 1
            m = re.match(r"^(\d\.\d)/", r[0]) if r else None
            if m and len(r) == 5:
                rr = m.group(1)
                for (size, est), v in zip((("1000/1000", "S"), ("1000/1000", "R"), ("5000/5000", "S"), ("5000/5000", "R")), r[1:]):
                    cells[f"S{scen}|{size}|{rr}|{est}"] = clean(v)
        res[key] = cells
    # Table 4: per scenario, rows by sample size with 7 RR cells
    scen, cells = 0, {}
    for r in out["T4"]:
        if len(r) == 1 and "exposure probability" in r[0]:
            scen += 1
        if r and re.match(r"^\d,\d{3}/\d,\d{3}$", r[0]):
            size = r[0].replace(",", "")
            for rr, v in zip(RRS, r[1:]):
                cells[f"S{scen}|{size}|{rr}"] = clean(v)
    res["table4"] = cells
    # Table 5: age rows
    t5 = {}
    for r in out["T5"]:
        if r and re.match(r"^\d\d-\d\d$", r[0]):
            t5[r[0]] = {"overall_risk": r[1], "esr_s": r[2], "esr_s_log_ci": r[3], "esr_r": r[4],
                        "esr_r_log_ci": r[5], "esr_r_binomial_ci": r[6]}
    res["table5"] = t5
    return res


def supplement_tables(doc_path, soffice):
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "S1.doc"
        shutil.copy(doc_path, src)
        subprocess.run([soffice, "--headless", "--convert-to", "docx", "--outdir", tmp, str(src)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with zipfile.ZipFile(Path(tmp) / "S1.docx") as z:
            body = ET.fromstring(z.read("word/document.xml")).find(W + "body")
    res, current, scen = {}, None, 0
    for el in body:
        if el.tag == W + "p":
            m = re.search(r"Table (S\d)\.", "".join(t.text or "" for t in el.iter(W + "t")))
            if m:
                current, scen = m.group(1), 0
                res[current] = {}
        elif el.tag == W + "tbl" and current:
            for tr in el.iter(W + "tr"):
                cells = ["".join(t.text or "" for t in tc.iter(W + "t")).strip() for tc in tr.iter(W + "tc")]
                cells = [c for c in cells if c != ""]
                if cells and "exposure probability" in cells[0]:
                    scen += 1
                if cells and re.match(r"^\d{4}/\d{4}$", cells[0]):
                    for rr, v in zip(RRS, cells[1:]):
                        res[current][f"S{scen}|{cells[0]}|{rr}"] = clean(v)
    for k, v in res.items():
        if len(v) != 112:
            raise SystemExit(f"{k}: {len(v)} cells, expected 112")
    return res


def main():
    args = sys.argv[1:]
    soffice = "soffice"
    if "--soffice" in args:
        i = args.index("--soffice")
        soffice = args[i + 1]
        del args[i:i + 2]
    xml_path, doc_path, out = args
    res = article_tables(xml_path)
    res.update(supplement_tables(doc_path, soffice))
    res["_note"] = ("Printed values of the paper (Tables 2-5, article XML) and of Additional file 1 (Tables S1-S7). "
                    "Keys are scenario|N1/N2|RR[|estimator]; percentages without the % sign.")
    Path(out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(f"{out}: tables {sorted(k for k in res if not k.startswith('_'))}")


if __name__ == "__main__":
    main()
