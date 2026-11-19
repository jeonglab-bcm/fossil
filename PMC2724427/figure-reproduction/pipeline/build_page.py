"""Build the results page from results.json, the renders and the published figures.

usage: build_page.py RESULTS_JSON FIG_DIR PUBLISHED_DIR OUT_DIR [TABLES_JSON]
(renders fig*_ours.png in FIG_DIR; writes OUT_DIR/index.html; TABLES_JSON from compare.py adds
Tables 2 and 3 in the paper's layout, published next to ours)

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
FIGS = {"1": "fig1", "2": "fig2", "3": "fig3"}
CAPTIONS = {
    "1": "Fig. 1. Mean coefficient at each sample size from 100 to 1500 (1,000 samples each) and the fitted curve beta + b1/n, for the continuous and the discrete exposure. Ours is drawn on the published axes.",
    "2": "Fig. 2. Density of the continuous coefficient at six sample sizes, with the mean in each heading. Ours is drawn on the published axes.",
    "3": "Fig. 3. Box plots of the continuous coefficient at the same six sample sizes. Ours is drawn on the published axes.",
}
ROWS = [("continuous.intercept.estimate", "Continuous, intercept"), ("continuous.intercept.se", "  SE"),
        ("continuous.intercept.t", "  t"), ("continuous.inv_n.estimate", "Continuous, n\u207b\u00b9 (b1)"),
        ("continuous.inv_n.se", "  SE"), ("continuous.inv_n.t", "  t"), ("continuous.r2", "Continuous, R\u00b2"),
        ("discrete.intercept.estimate", "Discrete, intercept"), ("discrete.intercept.se", "  SE"),
        ("discrete.intercept.t", "  t"), ("discrete.inv_n.estimate", "Discrete, n\u207b\u00b9 (b1)"),
        ("discrete.inv_n.se", "  SE"), ("discrete.inv_n.t", "  t"), ("discrete.r2", "Discrete, R\u00b2")]


def num(v, ref):
    if v is None:
        return "\u2013"
    d = len(str(ref).split(".")[1]) if "." in str(ref) else 0
    d = max(d, 3) if abs(v) < 1 else d
    return f"{v:.{d}f}"


def tables_section(T):
    """Table 1: the paper, our run (two ways), the spread over 20 populations, and the sensitivity runs."""
    by = {r["key"]: r for r in T["table1"]}
    sp = T["seed_spread"]["fields"]
    body = ""
    for key, lab in ROWS:
        r = by[key]
        p = r["paper"]
        rng = sp.get(key)
        rng_s = f"{num(rng['min'], p)} to {num(rng['max'], p)}" if rng else "\u2013"
        body += (f"<tr><th scope=\"row\">{esc(lab.strip())}</th><td>{esc(str(p))}</td><td><strong>{num(r['ours'], p)}</strong></td>"
                 f"<td>{num(r['ours_all_estimates'], p)}</td><td>{rng_s}</td><td>{num(r['sensitivity_warning_rule'], p)}</td>"
                 f"<td>{num(r['sensitivity_every_fit_kept'], p)}</td><td>{num(r['hypothesis_x_sd_1'], p)}</td></tr>")
    n_seeds = len(T["seed_spread"]["seeds"])
    a = T["analytic_b1"]["at_population_fit"]
    pop = T["population"]["glm"]
    d = T["dropped"]
    notes = (f"<li>Our population of 100,000 (seed 2724427): logistic fit {pop['x']:.3f} and {pop['z']:.3f}; "
             f"analytic first-order bias b1 {a['x']:.1f} and {a['z']:.1f}.</li>"
             f"<li>Samples left out for separation or no convergence: {d['total']} of 281,000, all at n \u2264 {d['largest_n_with_drop']}.</li>")
    return (f'<section class="container after-bench" aria-labelledby="tables-head"><div class="station surface" id="tables">'
            f'<header class="station-head"><h2 id="tables-head">Table 1</h2><p class="caption">OLS of the coefficient on 1/n. '
            f'Ours fits the 281 per-size means (as Fig. 1 draws them); the next column fits all individual estimates. '
            f'The spread is the range over {n_seeds} other populations. The last three columns are sensitivity runs, not agreement: '
            f'only the fits R warns about left out, every fit kept, and a population with x of SD 1 in place of 0.7.</p></header>'
            f'<div class="table-wrap"><table class="record dense"><thead><tr><th scope="col">Table 1</th><th scope="col">Paper</th>'
            f'<th scope="col">Ours</th><th scope="col">Ours, all estimates</th><th scope="col">{n_seeds} populations</th>'
            f'<th scope="col">Sensitivity: warning rule</th><th scope="col">Sensitivity: every fit kept</th>'
            f'<th scope="col">Hypothesis: x SD 1</th></tr></thead><tbody>{body}</tbody></table></div>'
            f'<ul class="fields">{notes}</ul></div></section>')


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


def reviewed(its):
    """'on review' when a reviewer set the verdict of any of these items (their review block)."""
    return "on review" if any((i.get("review") or {}).get("verdict") == i.get("verdict") for i in its) else ""


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


def main(results, figs, pub, out, tables=None):
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
    for n, prefix in FIGS.items():
        its = [i for i in items if (i["id"] == prefix or (i["id"].startswith(prefix) and not i["id"][len(prefix)].isdigit()))
               and i["method"] in ("pixels", "values")]
        if not its:
            continue
        v = worst([i["verdict"] for i in its])
        pf = Path(pub) / f"figure-{n}.png"
        psrc, (w, h) = b64(pf if pf.exists() else Path(pub) / f"figure-{n}.jpg")
        osrc, _ = b64(Path(figs) / f"fig{n}_ours.png")
        stats = "".join(f"<div><dt>{esc(i['label'])}</dt><dd>{esc(measure(i))} · {esc(STAMP[i['verdict']][1] if i['verdict'] in STAMP else '')}</dd></div>"
                        .replace(" · ", ", ") for i in its)
        causes = []
        for i in its:
            c = (i.get("cause") or {}).get("summary")
            if c and c not in causes:
                causes.append(c)
        note = " ".join(causes)
        stations.append(
            f'<section class="station surface" id="fig-{n}" aria-labelledby="fig-{n}-head">'
            f'<header class="station-head"><h2 id="fig-{n}-head">Fig. {n}</h2><p class="caption">{esc(CAPTIONS[n])}</p>{stamp(v, reviewed(its))}</header>'
            f'<div class="stage"><div class="pair">'
            f'<figure class="plate"><figcaption>Published</figcaption><img src="{psrc}" alt="Figure {n} as published" width="{w}" height="{h}"></figure>'
            f'<figure class="plate"><figcaption>Our run</figcaption><img src="{osrc}" alt="Figure {n} redrawn from our run" width="{w}" height="{h}"></figure>'
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
        rows.append(f"<tr><td>{esc(i['label'])}</td><td>{stamp(i['verdict'], reviewed([i]))}</td><td>{esc(measure(i))}{fields}</td><td>{esc(cause)}</td></tr>")
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
    tables_html = tables_section(json.loads(Path(tables).read_text())) if tables else ""
    for k, v in {"LEDE": esc(lede), "LABEL": label, "STATIONS": "".join(stations), "EXTRA": extra, "TABLES": tables_html,
                 "RECOVERED": recovered, "MATCHED_INTRO": esc(N["matched_intro"]), "MATCHED": matched,
                 "CLOSING": esc(N["closing"])}.items():
        page = page.replace(f"<!--__{k}__-->", v)
    page = page.replace("/*__FIGS__*/[]", json.dumps(figjs))
    out = Path(out) / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    print(f"wrote {out} ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main(*sys.argv[1:6])
