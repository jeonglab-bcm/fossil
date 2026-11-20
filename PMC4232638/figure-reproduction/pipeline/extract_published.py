"""Read the paper's printed numbers from its article XML and its supplement PDFs.

Usage: extract_published.py DOWNLOADS OUT.json OUT_COMBINATIONS.json.gz

DOWNLOADS holds PMC4232638.xml (Europe PMC full text) and supp/ (the supplement files). The PDF tables
are read with poppler's `pdftotext -layout`. Every value is kept as the printed string.

OUT.json (committed as output/published_values.json):
  table1, table2, table3, table4      the article's tables
  af3, af5, af11, af13                kappa matrices (all/non-COSMIC SNVs; 989/297 labelled; with the
                                      low-confidence category)
  af8                                 three-category calls by functional category
  af9                                 SNVs by number of low-confidence calls, and the majority-vote lists
  af16                                performance by gene class
  af19                                counts of combinations that beat the best single and meta-predictor
  af21, af22                          top-five combinations and the best single and meta-predictors
  af25, af27                          optimal p and n
  af28                                training-set SNVs left in the data
OUT_COMBINATIONS.json.gz (not committed, 2 x 11,253 rows): Additional files 17 and 18.
"""
import gzip
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PRED = ["CHASM (breast)", "CHASM (lung)", "CHASM (melanoma)", "FATHMM (cancer)", "FATHMM (missense)",
        "Mutation Assessor", "MutationTaster", "PolyPhen-2", "PROVEAN", "SIFT", "VEST",
        "CanDrA (breast)", "CanDrA (lung)", "CanDrA (melanoma)", "Condel"]
STATS = ["accuracy", "sensitivity", "specificity", "ppv", "npv", "composite"]
NUM = r"-?\d[\d.]*(?:e-?\d+)?%?|NA"
CI = re.compile(rf"({NUM})\s*\(\s*({NUM})\s*-\s*({NUM})\s*\)")
CI_PCT = re.compile(r"(\d[\d.]*)%\s*\((\d[\d.]*)-(\d[\d.]*)%\)|(\d[\d.]*)\s*\((\d[\d.]*)-(\d[\d.]*)\)")


def text_of(pdf):
    return subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True, capture_output=True, text=True).stdout


def af(downloads, i):
    return text_of(Path(downloads) / "supp" / f"13059_2014_484_MOESM{i}_ESM.pdf")


def xml_tables(xml):
    root = ET.parse(xml).getroot()
    out = {}
    for tw in root.iter("table-wrap"):
        out[tw.get("id")] = [["".join(td.itertext()).strip() for td in tr] for tr in tw.iter("tr")]
    return out


def article_tables(xml):
    t = xml_tables(xml)
    table1 = {r[0]: r[1:5] for r in t["Tab1"][2:]}
    table2, pred = {}, None
    for r in t["Tab2"][3:]:
        if len(r) == 6:
            pred = r[0]
            r = r[1:]
        table2.setdefault(pred, {})[r[0]] = r[1:5]
    tables = {"table1": table1, "table2": table2}
    for key, tab in (("table3", "Tab3"), ("table4", "Tab4")):
        rows = {}
        for r in t[tab][1:]:
            vals = []
            for cell in r[1:7]:
                m = CI_PCT.fullmatch(cell.strip())
                if not m:
                    raise ValueError(f"{key}: cannot read {cell!r}")
                g = m.groups()
                vals.append(list(g[:3]) if g[0] else list(g[3:]))
            rows[r[0]] = dict(zip(STATS, vals))
        tables[key] = rows
    return tables


def kappa_blocks(text):
    """The two 15 x 15 kappa matrices of a kappa table, as {row: {column: [k, low, high]}}."""
    blocks, cur = [], None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("Kappa scores"):
            cur = {}
            blocks.append(cur)
            continue
        if cur is None:
            continue
        name = next((p for p in sorted(PRED, key=len, reverse=True) if s.startswith(p + " ")), None)
        if name and len(cur) < 15:
            vals = CI.findall(s[len(name):])
            if len(vals) != 15:
                raise ValueError(f"kappa row {name!r}: {len(vals)} values")
            cur[name] = {c: list(v) for c, v in zip(PRED, vals)}
    if len(blocks) != 2 or any(len(b) != 15 for b in blocks):
        raise ValueError("expected two 15 x 15 kappa matrices")
    return blocks


AF8_CLASSES = [("CHASM (breast)", 3), ("CHASM (lung)", 3), ("CHASM (melanoma)", 3), ("FATHMM (cancer)", 3),
               ("FATHMM (missense)", 3), ("Mutation Assessor", 4), ("MutationTaster", 5), ("PolyPhen-2", 3),
               ("PROVEAN", 3), ("SIFT", 3), ("VEST", 3), ("CanDrA (breast)", 3), ("CanDrA (lung)", 3),
               ("CanDrA (melanoma)", 3), ("Condel", 3)]


def af8(text):
    """Two side-by-side tables (all 3,591 SNVs; 1,699 non-COSMIC SNVs) of the three-category calls:
    for each predictor and class, the counts among neutral, non-neutral and uncertain SNVs and the total."""
    sides = ([], [])
    row = re.compile(r"([A-Za-z][A-Za-z_/ -]*?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)")
    for line in text.splitlines():
        s = " ".join(line.split())
        for p in sorted(PRED, key=len, reverse=True):
            s = s.replace(p + " ", "")
        found = row.findall(s)
        if len(found) == 2:
            for side, f in zip(sides, found):
                side.append([f[0].strip()] + list(f[1:]))
    out = {}
    for name, side in zip(("all", "non_cosmic"), sides):
        if len(side) != sum(n for _, n in AF8_CLASSES):
            raise ValueError(f"AF8 {name}: {len(side)} rows")
        i, tab = 0, {}
        for pred, n in AF8_CLASSES:
            tab[pred] = {r[0]: r[1:] for r in side[i:i + n]}
            i += n
        out[name] = tab
    return out


def af6(text):
    """Additional file 6: the non-COSMIC SNVs by gene and functional category (as Table 1)."""
    out = {}
    for line in text.splitlines():
        m = re.fullmatch(r"\s*([A-Z][A-Z0-9]+|Total)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*", line)
        if m:
            out[m.group(1)] = list(m.group(2, 3, 4, 5))
    return out


def class_rows(text, n):
    """Rows 'class n1 ... nk' in reading order, for one or several side-by-side tables (k = n)."""
    num = r"\s+(\d+)" * n
    pat = re.compile(r"([A-Za-z][A-Za-z_/ .-]*?)" + num + r"(?=\s|$)")
    sides = []
    for line in text.splitlines():
        s = " ".join(line.split())
        for p in sorted(PRED, key=len, reverse=True):
            s = s.replace(p, " ")
        found = pat.findall(" " + s)
        for i, f in enumerate(found):
            while len(sides) <= i:
                sides.append([])
            sides[i].append([f[0].strip()] + list(f[1:]))
    return sides


def af9(text):
    rows = {}
    for line in text.splitlines():
        m = re.fullmatch(r"\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*", line)
        if m:
            rows[m.group(1)] = list(m.group(2, 3, 4, 5))
    lists = []
    for chunk in text.split("SNVs with a majority vote of low confidence:")[1:]:
        body = " ".join(chunk.split("\n\n")[0].split())
        lists.append({g: [x.strip() for x in v.split(",")] for g, v in re.findall(r"([A-Z0-9]+) \(([^)]*)\)", body)})
    return {"columns": ["all (3,591)", "non-COSMIC (1,699)", "labelled (989)", "labelled non-COSMIC (297)"],
            "by_count": rows, "majority": dict(zip(["all", "non-COSMIC", "labelled", "labelled non-COSMIC"], lists))}


ROW_CI = re.compile(r"(NA|[\d.]+%?)(?:\s*\(([\d.]+%?)-([\d.]+%?)\))?")


def stat_cells(rest):
    cells = re.findall(r"NA|[\d.]+%?\s*\([\d.]+%?-[\d.]+%?\)", rest)
    out = []
    for c in cells:
        if c == "NA":
            out.append(["NA", "NA", "NA"])
        else:
            m = re.fullmatch(r"([\d.]+%?)\s*\(([\d.]+%?)-([\d.]+%?)\)", c)
            out.append(list(m.groups()))
    return out


def af16(text):
    out, cur = {}, None
    alias = {"Provean": "PROVEAN"}
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("ONCOGENES"):
            cur = out.setdefault("oncogenes", {})
        elif s.startswith("TUMOR SUPPRESSOR"):
            cur = out.setdefault("tsg", {})
        elif cur is not None:
            name = next((p for p in sorted(PRED + list(alias), key=len, reverse=True) if s.startswith(p + " ")), None)
            if name:
                vals = stat_cells(s[len(name):])
                if len(vals) != 6:
                    raise ValueError(f"AF16 {name}: {len(vals)} values")
                cur[alias.get(name, name)] = dict(zip(STATS, vals))
    return out


def af19(text):
    """Two blocks (compared to single predictors, to meta-predictors), each 6 statistics x (mean,
    significant) x (all: subset 1, 2, both; non-COSMIC: subset 1, 2, both). In the text layout a
    statistic's name sits between its 'Mean' row and its 'Statistically significant' row."""
    names = {"Accuracy": "accuracy", "Sensitivity": "sensitivity", "Specificity": "specificity", "PPV": "ppv",
             "NPV": "npv", "Composite score": "composite"}
    out, block, mean, stat = {}, None, None, None
    for line in text.splitlines():
        s = " ".join(line.split())
        if s.startswith("Compared to single"):
            block = out.setdefault("single", {})
        elif s.startswith("Compared to meta"):
            block = out.setdefault("meta", {})
        elif block is None:
            continue
        elif s.startswith("Mean "):
            mean = s.split()[-6:]
        elif s in names:
            stat = names[s]
            block[stat] = {"mean": mean}
        elif s.startswith("Statistically significant "):
            block[stat]["significant"] = s.split()[-6:]
    for b in out.values():
        if len(b) != 6 or any(set(d) != {"mean", "significant"} or None in d.values() for d in b.values()):
            raise ValueError(f"AF19: {b}")
    cols = ["all subset 1", "all subset 2", "all both", "non-COSMIC subset 1", "non-COSMIC subset 2", "non-COSMIC both"]
    return {"columns": cols, **out}


def top_tables(text):
    """Additional files 21 and 22: per subset, by accuracy and by composite score, five combinations then
    the best single and meta-predictor."""
    rows = []
    for line in text.splitlines():
        s = " ".join(line.split())
        vals = stat_cells(s)
        if len(vals) == 6:
            name = re.split(r"\s[\d.]+%?\s*\(", s, maxsplit=1)[0]
            name = re.sub(r"^(By accuracy|By composite score)\s+", "", name).strip()
            rows.append({"name": name, **dict(zip(STATS, vals))})
    if len(rows) != 28:
        raise ValueError(f"top-five table: {len(rows)} rows")
    out = {}
    for i, sub in enumerate(("subset1", "subset2")):
        for j, by in enumerate(("accuracy", "composite")):
            blk = rows[14 * i + 7 * j: 14 * i + 7 * j + 7]
            out[f"{sub}/{by}"] = {"top5": blk[:5], "best_single": blk[5], "best_meta": blk[6]}
    return out


def optimal(text):
    """Additional files 25 and 27: (A) for each p the n with the highest mean accuracy in subset 1,
    (B) for each n the best p. Rows: p, n, combination, accuracy (CI)."""
    out, cur = {}, None
    for line in text.splitlines():
        s = " ".join(line.split())
        if re.match(r"^[AB] n p ", s):
            cur = out.setdefault("by_p" if s[0] == "A" else "by_n", [])
            continue
        m = re.match(r"^(\d+) (\d+) (At least \d+ of .*?) (\d[\d.]*%) \(", s)
        if m and cur is not None:
            cur.append({"p": m.group(1), "n": m.group(2), "name": m.group(3), "accuracy": m.group(4)})
    return out


def af28(text):
    out = {}
    for line in text.splitlines():
        s = " ".join(line.split())
        m = re.match(r"^(CHASM \(\w+\)|FATHMM \(\w+\)|PolyPhen-2) (\d+) (\d+)$", s)
        if m:
            out[m.group(1)] = [m.group(2), m.group(3)]
    return out


def combinations(text):
    out = {}
    for line in text.splitlines():
        if not line.startswith("At least"):
            continue
        m = re.match(r"(At least \d+ of .*?)\s{2,}(\S.*)$", line.rstrip())
        vals = stat_cells(m.group(2)) if m else []
        if len(vals) != 12:
            raise ValueError(f"cannot read {line[:120]!r}")
        out[m.group(1).strip()] = {"subset1": dict(zip(STATS, vals[:6])), "subset2": dict(zip(STATS, vals[6:]))}
    if len(out) != 11253:
        raise ValueError(f"{len(out)} combinations, expected 11,253")
    return out


def main():
    downloads, out, out_comb = sys.argv[1:4]
    d = Path(downloads)
    res = article_tables(d / "PMC4232638.xml")
    for i in (3, 5, 11, 13):
        a, b = kappa_blocks(af(d, i))
        res[f"af{i}"] = {"first": a, "second": b}
    res["af8"] = af8(af(d, 8))
    res["af9"] = af9(af(d, 9))
    res["af6"] = af6(af(d, 6))
    res["af7"] = class_rows(af(d, 7), 4)[0]
    res["af14"] = dict(zip(("oncogenes", "tsg", "new"), class_rows(af(d, 14), 2)))
    res["af16"] = af16(af(d, 16))
    res["af19"] = af19(af(d, 19))
    res["af21"] = top_tables(af(d, 21))
    res["af22"] = top_tables(af(d, 22))
    res["af25"] = optimal(af(d, 25))
    res["af27"] = optimal(af(d, 27))
    res["af28"] = af28(af(d, 28))
    Path(out).write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    comb = {"af17": combinations(af(d, 17)), "af18": combinations(af(d, 18))}
    with gzip.open(out_comb, "wt", encoding="utf-8") as f:
        json.dump(comb, f)


if __name__ == "__main__":
    main()
