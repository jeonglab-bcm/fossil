"""Read the paper's printed tables into published_values.json.

Usage: extract_published.py ARTICLE.xml TABLE_S3.doc TABLE_S4.doc OUT.json [--soffice soffice]

Tables 1-4 come from the article XML (Europe PMC full text); Tables S3 and S4 from the supplement's Word
files, converted to text with LibreOffice. Every cell is kept as printed ('>50000', '<100', '3500–5500').
Keys: table -> "<rrr>|<threshold>|<pc>|<tau2>" -> [patients 10%, 5%, 1%, events 10%, 5%, 1%] for Tables 1,
S3 and S4; "<rrr>|<pc>|<i2>" -> [patients beta 20%, 10%, 5%, events ...] for Table 2; for Tables 3 and 4,
"<pc>|<threshold>|<acceptability>" -> {sim_patients, sim_events, ois_power, ois_patients, ois_events}.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PCS4 = ["1-5", "5-15"]
TAUS = ["0.05", "0.15", "0.25"]


def cells_of(xml, tid):
    i = xml.find(f'<table-wrap id="pone-0025491-{tid}"')
    j = xml.find("</table-wrap>", i)
    rows = re.findall(r"<tr>(.*?)</tr>", xml[i:j], re.S)
    out = []
    for r in rows:
        cs = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
        out.append([c.replace("&gt;", ">").replace("&lt;", "<").replace(" ", "") for c in cs])
    return out


def numbers_table(tokens, pcs):
    """24 rows of 6 numbers in the order RRR 0/10 x threshold 30/20 x PC x tau2."""
    assert len(tokens) == 144, len(tokens)
    out, k = {}, 0
    for rrr in ("0", "10"):
        for th in ("30", "20"):
            for pc in pcs:
                for tau in TAUS:
                    out[f"{rrr}|{th}|{pc}|{tau}"] = tokens[k:k + 6]
                    k += 6
    return out


def table1(xml):
    toks = []
    for row in cells_of(xml, "t001")[2:]:
        toks += row[-6:]
    return numbers_table(toks, PCS4)


def table2(xml):
    out = {}
    rows = cells_of(xml, "t002")[2:]
    pcs = ["3", "10", "27.5", "60"]
    k = 0
    for pc in pcs:
        for rrr in ("30", "20"):
            for i2 in ("0", "25", "50"):
                out[f"{rrr}|{pc}|{i2}"] = rows[k][-6:]
                k += 1
    return out


def table34(xml, tid, pcs):
    out = {}
    rows = cells_of(xml, tid)[2:]
    k = 0
    for pc in pcs:
        for th in ("30", "20"):
            for acc, power in (("good", "80"), ("very_good", "90"), ("excellent", "95")):
                r = rows[k]
                k += 1
                i = [c.lower() for c in r].index(acc.replace("_", " "))
                out[f"{pc}|{th}|{acc}"] = {"sim_patients": r[i + 1], "sim_events": r[i + 2], "ois_power": power,
                                           "ois_patients": r[-2], "ois_events": r[-1],
                                           "ois_pc": r[5] if len(r) == 10 else None}
    return out


def doc_tokens(doc, soffice):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run([soffice, "--headless", "--convert-to", "txt:Text", "--outdir", d, doc], check=True,
                       capture_output=True)
        txt = next(Path(d).glob("*.txt")).read_text(encoding="utf-8", errors="replace")
    txt = txt[txt.index("RRR=0%"):]  # the data start at the first true-effect label
    toks = re.findall(r"[<>]?\d[\d.]*%?(?:-\d+%)?", txt)
    # Drop the header (10% 5% 1% twice), the RRR labels, the PC ranges and the tau^2 values.
    keep = [t for t in toks if not t.endswith("%") and t not in ("0.05", "0.15", "0.25")]
    return keep


def main():
    args = sys.argv[1:]
    soffice = "soffice"
    if "--soffice" in args:
        i = args.index("--soffice")
        soffice = args[i + 1]
        del args[i:i + 2]
    xml_path, s3, s4, out = args
    xml = Path(xml_path).read_text(encoding="utf-8")
    res = {
        "table1": table1(xml),
        "table2": table2(xml),
        "table3": table34(xml, "t003", ["1-5", "5-15"]),
        "table4": table34(xml, "t004", ["1-5", "5-15", "15-40", "40-80"]),
        "tableS3": numbers_table(doc_tokens(s3, soffice), ["15-40", "40-80"]),
        "tableS4": numbers_table(doc_tokens(s4, soffice), PCS4),
    }
    Path(out).write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
