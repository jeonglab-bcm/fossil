"""Tables S1-S7 of the supplement as JSON.

Usage: parse_supplement.py SUPPLEMENT_DIR OUT.json
SUPPLEMENT_DIR holds pcbi.1000454.s002.doc ... s008.doc (Tables S1-S7, in caption order: s007 is
Table S6, predicted false positives; s008 is Table S7, the physical systems; the main text swaps
these two labels).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from doc2txt import doc_text  # noqa: E402

FILES = {"S1": "s002", "S2": "s003", "S3": "s004", "S4": "s005", "S5": "s006", "S6": "s007", "S7": "s008"}


def rows(text):
    lines = [l for l in text.split("\n") if l.strip()]
    caption, header, body = lines[0], lines[1], "\n".join(lines[2:])
    cells = header.split("\t")
    out = []
    if body:
        header_cells = [c.strip() for c in cells if c.strip()]
        for r in body.split("\t\t"):
            c = [x.strip() for x in r.split("\t")]
            if any(c):
                out.append(c)
        return caption.strip(), header_cells, out
    # header and body on one line (tables S1, S2, S6): the header's first cells, then rows
    parts = header.split("\t\t")
    header_cells = [c.strip() for c in parts[0].split("\t") if c.strip()]
    for r in parts[1:]:
        c = [x.strip() for x in r.split("\t")]
        if any(c):
            out.append(c)
    return caption.strip(), header_cells, out


def main(d, out):
    d = Path(d)
    tables = {}
    for k, f in FILES.items():
        text = doc_text(d / f"pcbi.1000454.{f}.doc")
        if k == "S7":
            lines = [l for l in text.split("\n") if l.strip()]
            tables[k] = {"caption": lines[0].strip(),
                         "systems": [c.strip() for l in lines[1:] for c in l.split("\t") if c.strip()]}
            continue
        caption, header, body = rows(text)
        tables[k] = {"caption": caption, "header": header, "rows": body}
    for k in ("S1", "S2", "S3", "S4", "S5", "S6"):
        tables[k]["pairs"] = [[r[0].upper(), r[1].upper()] for r in tables[k]["rows"]]
    json.dump(tables, open(out, "w"), indent=1)
    print({k: len(v.get("rows", v.get("systems"))) for k, v in tables.items()})


if __name__ == "__main__":
    main(*sys.argv[1:3])
