"""Build the results page from results.json, the renders and the published figures.

usage: build_page.py RESULTS_JSON FIG_DIR PUBLISHED_DIR OUT_DIR  (renders fig*_ours.png in FIG_DIR; writes OUT_DIR/index.html)

Every verdict on the page is read from results.json (computed there by check_results.py); prose
that is not a number comes from results_notes.json ("page"). Images are embedded, so the page
works offline; it links ../results.css like the site's other results pages.
"""
import base64
import html
import io
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
esc = html.escape
STAMP = {"exact": ("agrees", "Exact"), "agrees": ("agrees", "Agrees"), "partly": ("partly", "Partly agrees"),
         "inconclusive": ("partly", "Inconclusive"), "differs": ("differs", "Differs")}
# One station per drawn panel: (panel, title, caption, result ids)
STATIONS = [
    ("fig2a", "Fig. 2A", "Share of protein pairs that share a location: all pairs and interacting pairs by the sign of their expression correlation, and random link sets.", ["fig2a"]),
    ("fig2b", "Fig. 2B", "ROC curves and AUC of DC-kNN with single-protein, physical-link and correlated-pair features (leave-two-out).", ["fig2b"]),
    ("fig2c", "Fig. 2C", "Share of known interactions among the most correlated protein pairs of each condition and among the pairs common to all three.", ["fig2c"]),
    ("fig2d", "Fig. 2D", "Average AUC of each kind of feature set and of the selected models (TR).", ["fig2d"]),
    ("fig2e", "Fig. 2E", "AUC of every feature set for each location; boxes mark the sets chosen by forward selection.", ["fig2e"]),
    ("fig3a", "Fig. 3A", "Conditional location map of NKX2-2 in normal brain, low- and high-grade glioma; H marks the top location.", ["fig3a"]),
    ("fig3e", "Fig. 3E", "Conditional location map of CPB1.", ["fig3e"]),
    ("fig3i", "Figs 3I and 3J", "Predicted possibility of 20 proteins at five locations, with the observed locations (+) of the paper's imaging; boxes are our high-confidence calls.", ["fig3j"]),
    ("fig4a", "Fig. 4A", "Conditional location map of KIF13A.", ["fig4a", "fig4eg"]),
    ("fig5a", "Fig. 5A", "Kinds of mislocation from normal brain to glioma, as shares of all mislocations (the paper draws them as a surface).", ["fig5a", "text.mislocations"]),
    ("fig5b", "Fig. 5B", "Conditional location map of RNF138.", ["fig5b"]),
    ("fig5c", "Fig. 5C", "Conditional location map of TLX3.", ["fig5c"]),
    ("fig6a", "Fig. 6A", "Conditional location map of GFRA4.", ["fig6a"]),
    ("fig6b", "Fig. 6B", "Conditional location map of PSPN.", ["fig6b"]),
    ("fig6c", "Fig. 6C", "Conditional location map of RET.", ["fig6c"]),
]


def b64(path):
    buf = io.BytesIO()
    im = Image.open(path).convert("RGB")
    if im.width > 2000:
        im = im.resize((2000, round(im.height * 2000 / im.width)), Image.LANCZOS)
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), im.size


def stamp(v, small=""):
    if v == "not_attempted":
        return '<span class="stamp" data-v="running">Not attempted</span>'
    cls, word = STAMP[v]
    return f'<span class="stamp" data-v="{cls}">{esc(word)}' + (f"<small>{esc(small)}</small>" if small else "") + "</span>"


def worst(vs):
    order = ["differs", "inconclusive", "partly", "agrees", "exact"]
    vs = [v for v in vs if v in order]
    return min(vs, key=order.index) if vs else "not_attempted"


def measure(it):
    if it["method"] == "values":
        f = it["values"]["fields"]
        from check_results import field_matches
        hits = sum(field_matches(x, it["values"].get("tolerance")) for x in f)
        return f"{hits} of {len(f)} values"
    if it["method"] == "pixels":
        p = it["pixels"]
        s = min(p["published_near_ours"], p["ours_near_published"])
        return f"{100 * s:.1f}% within {p['tolerance_px']} px"
    return ""


def fmt(v):
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def main(results, figs, pub, out):
    sys.path.insert(0, str(HERE))
    R = json.loads(Path(results).read_text())
    N = json.loads((HERE.parent / "results_notes.json").read_text())["page"]
    items = R["items"]
    by = {i["id"]: i for i in items}
    sm = R["summary"]

    lede = N["lede"].format(**sm, attempted=sm["items"] - sm["not_attempted"])
    label = "".join(
        f'<a class="label-row" href="#{a}"><span>{esc(k)}</span><span>{esc(STAMP.get(worst([by[i]["verdict"] for i in ids]), ("", "Not attempted"))[1])}</span></a>'
        for a, k, ids in N["label_rows"])

    stations, figjs = [], []
    for n, title, caption, ids in STATIONS:
        its = [by[i] for i in ids if i in by]
        v = worst([i["verdict"] for i in its])
        psrc, (w, h) = b64(Path(pub) / f"{n}.png")
        osrc, _ = b64(Path(figs) / f"{n}_ours.png")
        w, h = w * 3, h * 3
        stats = "".join(f"<div><dt>{esc(i['label'])}</dt><dd>{esc(measure(i))}, {esc(STAMP[i['verdict']][1] if i['verdict'] in STAMP else '')}</dd></div>" for i in its)
        causes = []
        for i in its:
            c = (i.get("cause") or {}).get("summary")
            if c and c not in causes:
                causes.append(c)
        note = " ".join(causes)
        stations.append(
            f'<section class="station surface" id="fig-{n}" aria-labelledby="{n}-head">'
            f'<header class="station-head"><h2 id="{n}-head">{esc(title)}</h2><p class="caption">{esc(caption)}</p>{stamp(v)}</header>'
            f'<div class="stage"><div class="pair">'
            f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="{esc(title)} as published" width="{w}" height="{h}"></figure>'
            f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="{esc(title)} redrawn from our run" width="{w}" height="{h}"></figure>'
            f'</div></div><div class="station-foot"><dl class="dose">{stats}</dl><p class="note">{esc(note)}</p></div></section>')
        figjs.append({"id": n, "w": w, "h": h})

    rows = []
    for i in items:
        fields = ""
        if i["method"] == "values":
            fields = "<ul class=fields>" + "".join(
                f"<li>{esc(f['name'])}: paper {esc(fmt(f['expected']))}, ours <strong>{esc(fmt(f['observed']))}</strong></li>"
                for f in i["values"]["fields"]) + "</ul>"
        cause = (i.get("cause") or {}).get("summary", "")
        rows.append(f"<tr><td>{esc(i['label'])}</td><td>{stamp(i['verdict'])}</td><td>{esc(measure(i))}{fields}</td><td>{esc(cause)}</td></tr>")
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
    out = Path(out) / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    print(f"wrote {out} ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main(*sys.argv[1:5])
