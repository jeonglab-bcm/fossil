#!/usr/bin/env python3
"""Build the PMC2735674 results page from results.json and the renders.

usage: build_page.py --results results.json --output OUTPUT_DIR --published PUBLISHED_DIR
                     --template page_template.html --out site/index.html

Every verdict and every number on the page is read from results.json (the verdicts computed there
by check_results.py). Prose that is not a number comes from the "page" section of
results_notes.json. Images are embedded, so the page works offline.
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
esc = html.escape

STAMP = {
    "exact": ("agrees", "Exact"),
    "agrees": ("agrees", "Agrees"),
    "partly": ("partly", "Partly agrees"),
    "inconclusive": ("partly", "Inconclusive"),
    "differs": ("differs", "Differs"),
}
PANELS = [("a", "enzyme"), ("b", "ion channel"), ("c", "GPCR"), ("d", "nuclear receptor")]
TABLES = [
    ("table1", "e", "Table 1, enzyme"),
    ("table2", "ic", "Table 2, ion channel"),
    ("table3", "gpcr", "Table 3, GPCR"),
    ("table4", "nr", "Table 4, nuclear receptor"),
]


def embed(path: Path, width_limit: int = 1400) -> tuple[str, tuple[int, int]]:
    buffer = io.BytesIO()
    image = Image.open(path).convert("RGB")
    if image.width > width_limit:
        image = image.resize(
            (width_limit, round(image.height * width_limit / image.width)), Image.LANCZOS
        )
    image.save(buffer, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode(), image.size


def stamp(verdict: str) -> str:
    if verdict == "not_attempted":
        return '<span class="stamp" data-v="running">Not attempted</span>'
    style, word = STAMP[verdict]
    return f'<span class="stamp" data-v="{style}">{esc(word)}</span>'


def worst(verdicts: list[str]) -> str:
    order = ["differs", "inconclusive", "partly", "agrees", "exact"]
    present = [v for v in verdicts if v in order]
    return min(present, key=order.index) if present else "not_attempted"


def measure(item: dict) -> str:
    if item["method"] == "values":
        from check_results import field_matches

        fields = item["values"]["fields"]
        hits = sum(field_matches(f, item["values"].get("tolerance")) for f in fields)
        return f"{hits} of {len(fields)} values"
    if item["method"] == "pixels":
        pixels = item["pixels"]
        score = min(pixels["published_near_ours"], pixels["ours_near_published"])
        return f"{100 * score:.1f}% within {pixels['tolerance_px']} px"
    if item["method"] == "check":
        return "passed" if item["check"]["passed"] else "failed"
    return ""


def table_block(tables: dict, dataset: str) -> str:
    rows = tables["tables"][dataset]["rows"]
    body = "".join(
        f"<tr><td>{esc(r['method'])}{'*' if r['auc_copied_from_yamanishi_2008'] else ''}</td>"
        f"<td>{esc(r['published_auc'])}</td><td><strong>{r['auc']:.1f}</strong></td>"
        f"<td>{esc(r['published_aupr'])}</td><td><strong>{r['aupr']:.1f}</strong></td></tr>"
        for r in rows
    )
    return (
        '<div class="table-wrap"><table class="record dense">'
        '<thead><tr><th scope="col">Method</th><th scope="col">AUC, paper</th>'
        '<th scope="col">AUC, ours</th><th scope="col">AUPR, paper</th>'
        '<th scope="col">AUPR, ours</th></tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--published", type=Path, required=True)
    ap.add_argument("--template", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    sys.path.insert(0, str(HERE))
    results = json.loads(args.results.read_text())
    notes = json.loads((HERE.parent / "results_notes.json").read_text())["page"]
    tables = json.loads((args.output / "tables.json").read_text())
    predictions = json.loads((args.output / "predictions.json").read_text())
    items = results["items"]
    by_id = {item["id"]: item for item in items}
    summary = results["summary"]

    lede = notes["lede"].format(**summary, attempted=summary["items"] - summary["not_attempted"])
    label = "".join(
        f'<a class="label-row" href="#{anchor}"><span>{esc(name)}</span>'
        f'<span>{esc(STAMP.get(worst([by_id[i]["verdict"] for i in ids if i in by_id]), ("", "Not attempted"))[1])}</span></a>'
        for anchor, name, ids in notes["label_rows"]
    )

    stations, figures = [], []
    for letter, _ in PANELS:
        item = by_id[f"fig1.{letter}"]
        published_src, (width, height) = embed(args.output / f"fig1{letter}_published.png")
        ours_src, _ = embed(args.output / f"fig1{letter}_ours.png")
        values = "".join(
            f"<div><dt>{esc(f['name'])}</dt><dd>paper {esc(str(f['expected']))}, ours {esc(str(f['observed']))}</dd></div>"
            for f in item["values"]["fields"]
        )
        stations.append(
            f'<section class="station surface" id="fig-1{letter}" aria-labelledby="fig-1{letter}-head">'
            f'<header class="station-head"><h2 id="fig-1{letter}-head">Fig. 1{letter}</h2>'
            f'<p class="caption">{esc(notes["panel_captions"][letter])}</p>{stamp(item["verdict"])}</header>'
            '<div class="stage"><div class="pair">'
            f'<figure class="plate"><figcaption>Published</figcaption><img src="{published_src}" alt="Figure 1{letter} as published" width="{width}" height="{height}"></figure>'
            f'<figure class="plate"><figcaption>Our run</figcaption><img src="{ours_src}" alt="Figure 1{letter} redrawn from our run" width="{width}" height="{height}"></figure>'
            '</div></div><div class="station-foot"><dl class="dose">'
            f'<div><dt>Pixels</dt><dd>{esc(measure(item))}</dd></div>{values}</dl>'
            f'<p class="note">{esc((item.get("cause") or {}).get("summary", ""))}</p></div></section>'
        )
        figures.append({"id": f"1{letter}", "w": width, "h": height})

    figure2 = by_id["fig2"]
    published2, (w2, h2) = embed(args.published / "figure-2.png")
    ours2, (w2o, h2o) = embed(args.output / "fig2_ours.png")
    stations.append(
        '<section class="station surface" id="fig-2" aria-labelledby="fig-2-head">'
        '<header class="station-head"><h2 id="fig-2-head">Fig. 2</h2>'
        f'<p class="caption">{esc(notes["figure2_caption"])}</p>{stamp(figure2["verdict"])}</header>'
        '<div class="stage"><div class="pair">'
        f'<figure class="plate"><figcaption>Published</figcaption><img src="{published2}" alt="Figure 2 as published" width="{w2}" height="{h2}"></figure>'
        f'<figure class="plate"><figcaption>Our run</figcaption><img src="{ours2}" alt="The same nodes redrawn from our run" width="{w2o}" height="{h2o}"></figure>'
        '</div></div><div class="station-foot"><dl class="dose">'
        + "".join(
            f"<div><dt>{esc(f['name'])}</dt><dd>paper {esc(str(f['expected']))}, ours {esc(str(f['observed']))}</dd></div>"
            for f in figure2["values"]["fields"]
        )
        + f'</dl><p class="note">{esc((figure2.get("cause") or {}).get("summary", ""))}</p></div></section>'
    )

    table_sections = "".join(
        f'<section class="station surface" id="{item_id}" aria-labelledby="{item_id}-head">'
        f'<header class="station-head"><h2 id="{item_id}-head">{esc(title)}</h2>'
        f'<p class="caption">{esc(notes["table_caption"])}</p>{stamp(by_id[item_id]["verdict"])}</header>'
        f'<div class="station-foot">{table_block(tables, dataset)}'
        f'<p class="note">{esc(measure(by_id[item_id]))}. {esc((by_id[item_id].get("cause") or {}).get("summary", ""))}</p>'
        "</div></section>"
        for item_id, dataset, title in TABLES
    )

    top5 = predictions["table5"]
    rows5 = "".join(
        f"<tr><td>{pair['rank']}</td><td>{esc(pair['drug'])} / {esc(pair['target'])}</td>"
        f"<td>{esc(str(top5['our_rank_of_each_published_pair'][index]))}</td></tr>"
        for index, pair in enumerate(top5["published"])
    )
    table5_section = (
        '<section class="station surface" id="table5" aria-labelledby="table5-head">'
        '<header class="station-head"><h2 id="table5-head">Table 5</h2>'
        f'<p class="caption">{esc(notes["table5_caption"])}</p>{stamp(by_id["table5"]["verdict"])}</header>'
        '<div class="station-foot"><div class="table-wrap"><table class="record dense">'
        '<thead><tr><th scope="col">Rank in the paper</th><th scope="col">Pair</th>'
        '<th scope="col">Rank in our run</th></tr></thead>'
        f"<tbody>{rows5}</tbody></table></div>"
        f'<p class="note">{esc((by_id["table5"].get("cause") or {}).get("summary", ""))}</p></div></section>'
    )

    rows = []
    for item in items:
        fields = ""
        if item["method"] == "values" and len(item["values"]["fields"]) <= 12:
            fields = (
                "<ul class=fields>"
                + "".join(
                    f"<li>{esc(f['name'])}: paper {esc(str(f['expected']))}, ours <strong>{esc(str(f['observed']))}</strong></li>"
                    for f in item["values"]["fields"]
                )
                + "</ul>"
            )
        cause = (item.get("cause") or {}).get("summary", "")
        rows.append(
            f"<tr><td>{esc(item['label'])}</td><td>{stamp(item['verdict'])}</td>"
            f"<td>{esc(measure(item))}{fields}</td><td>{esc(cause)}</td></tr>"
        )
    extra = (
        f"{table_sections}{table5_section}"
        '<section class="container after-bench" aria-labelledby="items-head">'
        '<div class="station surface" id="items">'
        '<header class="station-head"><h2 id="items-head">Every result</h2>'
        f'<p class="caption">{esc(notes["items_caption"])}</p></header>'
        '<div class="table-wrap"><table class="record dense"><thead><tr>'
        '<th scope="col">Result</th><th scope="col">Verdict</th><th scope="col">Measure</th>'
        '<th scope="col">Why</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
        f'<p class="note">{esc(notes["claims_line"])}</p></div></section>'
    )

    recovered = (
        '<section class="notes" aria-labelledby="back-head"><div class="container">'
        '<h2 id="back-head">What came back</h2><dl class="ledger">'
        + "".join(
            f'<div class="row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in notes["came_back"]
        )
        + '</dl></div></section><section class="buried" aria-labelledby="buried-head">'
        '<div class="container"><div class="plastic buried-band">'
        '<h2 id="buried-head">What stayed buried</h2><ul>'
        + "".join(f"<li>{esc(x)}</li>" for x in notes["buried"])
        + f'</ul><p class="so">{esc(notes["claims_line"])}</p></div></div></section>'
    )
    matched = "".join(
        f'<div class="row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in notes["matched"]
    )

    page = args.template.read_text()
    for key, value in {
        "LEDE": esc(lede),
        "LABEL": label,
        "STATIONS": "".join(stations),
        "EXTRA": extra,
        "RECOVERED": recovered,
        "MATCHED_INTRO": esc(notes["matched_intro"]),
        "MATCHED": matched,
        "CLOSING": esc(notes["closing"]),
    }.items():
        page = page.replace(f"<!--__{key}__-->", value)
    page = page.replace("/*__FIGS__*/[]", json.dumps(figures))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page)
    print(f"wrote {args.out} ({len(page) // 1024} KB)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
