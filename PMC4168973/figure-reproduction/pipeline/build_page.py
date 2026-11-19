#!/usr/bin/env python3
"""Build the results page from results.json, the run's outputs and the published figures.

usage: build_page.py RESULTS_JSON OUTPUT_DIR PUBLISHED_DIR OUT_DIR

Every verdict and every number on the page is read from results.json (verdicts computed there by
check_results.py); prose that is not a number comes from results_notes.json ("page"). Images are
embedded (scaled to 1400 px wide), so the page works offline; it links ../results.css like the
site's other results pages.
"""
import base64
import html
import io
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_results import field_matches  # noqa: E402

esc = html.escape
WIDTH = 1400
STAMP = {"exact": ("agrees", "Exact"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs")}
ORDER = ["differs", "inconclusive", "partly", "agrees", "exact"]


def b64(path):
    im = Image.open(path).convert("RGB")
    if im.width > WIDTH:
        im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    # line plots: a 64-colour palette keeps the curves and makes the page a third the size
    im.quantize(colors=64, method=Image.MEDIANCUT).save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), im.size


def stamp(v):
    if v == "not_attempted":
        return '<span class="stamp" data-v="running">Not attempted</span>'
    cls, word = STAMP[v]
    return f'<span class="stamp" data-v="{cls}">{esc(word)}</span>'


def worst(vs):
    vs = [v for v in vs if v in ORDER]
    return min(vs, key=ORDER.index) if vs else "not_attempted"


def measure(it):
    if it["method"] == "values":
        ex = {e["field"] for e in it["values"].get("exceptions", [])}
        f = [x for x in it["values"]["fields"] if x["name"] not in ex]
        hits = sum(field_matches(x, it["values"].get("tolerance")) for x in f)
        slips = f"; {len(ex)} slips in the paper left out" if ex else ""
        return f"{hits} of {len(f)} values{slips}"
    if it["method"] == "check":
        return it["check"].get("detail", "")
    if it["method"] == "pixels":
        p = it["pixels"]
        s = min(p["published_near_ours"], p["ours_near_published"])
        best = max(c["score"] for c in p["controls"])
        return f"{100 * s:.1f}% of curve pixels within {p['tolerance_px']} px (pass {100 * p['threshold']:.1f}%, best control {100 * best:.1f}%)"
    return ""


def fmt(v):
    return "none" if v is None else str(v)


def values_table(it):
    rows = []
    tol = it["values"].get("tolerance")
    ex = {e["field"] for e in it["values"].get("exceptions", [])}
    for f in it["values"]["fields"]:
        ok = field_matches(f, tol)
        word = "yes" if ok else ("paper slip" if f["name"] in ex else "no")
        rows.append(f'<tr><td>{esc(f["name"])}</td><td class="num">{esc(fmt(f["expected"]))}</td>'
                    f'<td class="num">{esc(fmt(f["observed"]))}</td><td>{word}</td></tr>')
    return ('<div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Value</th>'
            '<th class="num" scope="col">Paper</th><th class="num" scope="col">Ours</th><th scope="col">Match</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def main(results, outdir, pub, out):
    R = json.loads(Path(results).read_text())
    N = json.loads((HERE.parent / "results_notes.json").read_text())["page"]
    items = R["items"]
    by = {i["id"]: i for i in items}
    sm = R["summary"]
    lede = N["lede"].format(**sm, attempted=sm["items"] - sm["not_attempted"])
    label = "".join(
        f'<a class="label-row" href="#{a}"><span>{esc(k)}</span><span>{esc(STAMP.get(worst([by[i]["verdict"] for i in ids if i in by]), ("", "Not attempted"))[1])}</span></a>'
        for a, k, ids in N["label_rows"])

    stations, figjs = [], []
    for st in N["stations"]:
        its = [by[i] for i in st["items"] if i in by]
        v = worst([i["verdict"] for i in its])
        head = (f'<header class="station-head"><h2 id="{st["id"]}-head">{esc(st["title"])}</h2>'
                f'<p class="caption">{esc(st["caption"])}</p>{stamp(v)}</header>')
        stats = "".join(f"<div><dt>{esc(i['label'])}</dt><dd>{esc(measure(i))}, {esc(STAMP.get(i['verdict'], ('', 'Not attempted'))[1])}</dd></div>" for i in its)
        causes = []
        for i in its:
            c = (i.get("cause") or {}).get("summary")
            if c and c not in causes:
                causes.append(c)
        note = f'<p class="note">{esc(" ".join(causes))}</p>' if causes else '<p class="note"></p>'
        if st.get("figure"):
            n = st["figure"]
            psrc, (w, h) = b64(Path(pub) / f"figure-{n}.png")
            osrc, _ = b64(Path(outdir) / f"fig{n}_ours.png")
            body = (f'<div class="stage"><div class="pair">'
                    f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="Figure {n} as published" width="{w}" height="{h}"></figure>'
                    f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="Figure {n} with our curves" width="{w}" height="{h}"></figure>'
                    f'</div></div>')
            figjs.append({"id": st["id"], "w": w, "h": h})
        else:
            body = '<div class="stack">' + "".join(
                f'<figure class="jt"><figcaption>{esc(i["label"])}. {esc(measure(i))}.</figcaption>{values_table(i)}</figure>'
                for i in its if i["method"] == "values") + "</div>"
        stations.append(f'<section class="station surface" id="{st["id"]}" aria-labelledby="{st["id"]}-head">{head}{body}'
                        f'<div class="station-foot"><dl class="dose">{stats}</dl>{note}</div></section>')

    rows = []
    for i in items:
        cause = (i.get("cause") or {}).get("summary", "")
        rows.append(f"<tr><td>{esc(i['label'])}</td><td>{stamp(i['verdict'])}</td><td>{esc(measure(i))}</td><td>{esc(cause)}</td></tr>")
    extra = (f'<section class="container after-bench" aria-labelledby="items-head"><div class="station surface" id="items">'
             f'<header class="station-head"><h2 id="items-head">Every result</h2><p class="caption">{esc(N["items_caption"])}</p></header>'
             f'<div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Result</th><th scope="col">Verdict</th>'
             f'<th scope="col">Measure</th><th scope="col">Why</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
             f'<p class="note">{esc(N["claims_line"])}</p></div></section>')
    recovered = ('<section class="notes" aria-labelledby="back-head"><div class="container"><h2 id="back-head">What came back</h2><dl class="ledger">'
                 + "".join(f'<div class="row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in N["came_back"])
                 + '</dl></div></section><section class="buried" aria-labelledby="buried-head"><div class="container"><div class="plastic buried-band">'
                 '<h2 id="buried-head">What stayed buried</h2><ul>' + "".join(f"<li>{esc(x)}</li>" for x in N["buried"])
                 + f'</ul><p class="so">{esc(N["claims_line"])}</p></div></div></section>')
    matched = "".join(f'<div class="row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in N["matched"])
    page = (HERE / "page_template.html").read_text()
    for k, v in {"LEDE": esc(lede), "LABEL": label, "STATIONS": "".join(stations), "EXTRA": extra,
                 "RECOVERED": recovered, "MATCHED_INTRO": esc(N["matched_intro"]), "MATCHED": matched,
                 "CLOSING": esc(N["closing"])}.items():
        page = page.replace(f"<!--__{k}__-->", v)
    page = page.replace("/*__FIGS__*/[]", json.dumps(figjs))
    page = page.replace('document.getElementById("fig-" + f.id)', 'document.getElementById(f.id)')
    o = Path(out) / "index.html"
    o.parent.mkdir(parents=True, exist_ok=True)
    o.write_text(page)
    print(f"wrote {o} ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main(*sys.argv[1:5])
