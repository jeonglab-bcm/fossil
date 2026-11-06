#!/usr/bin/env python3
"""Build the PMC4015815 results page from results.json and the pipeline outputs.

usage: build_page.py RUN_DIR PUBLISHED_DIR OUT.html

RUN_DIR holds results.json, tables.json, fig{3,4,5}_scores.json, fig{3,4,5}_ours.png and
port_check.json. Every verdict on the page is read from results.json; every number from the
pipeline's own outputs. The page links ../results.css; images are embedded.
"""
from __future__ import annotations

import base64
import html
import io
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
RUN, PUB, OUT = map(Path, sys.argv[1:4])
esc = html.escape


def js(name):
    return json.loads((RUN / name).read_text())


R = js("results.json")
T = js("tables.json")
F3, F4, F5 = js("fig3_scores.json"), js("fig4_scores.json"), js("fig5_scores.json")
PORT = js("port_check.json")
ITEMS = {i["id"]: i for i in R["items"]}
TEXT = json.loads((HERE / "params" / "page_text.json").read_text())  # prose only; no verdicts

WORDS = {"exact": "Exact", "agrees": "Agrees", "partly": "Partly agrees",
         "inconclusive": "Inconclusive", "differs": "Differs", "not_attempted": "Not attempted"}
STAMP = {"exact": "agrees", "agrees": "agrees", "partly": "partly", "inconclusive": "partly",
         "differs": "differs"}


def b64(path: Path) -> str:
    buf = io.BytesIO()
    Image.open(path).convert("RGB").save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def stamp(ids, basis):
    vs = [ITEMS[i]["verdict"] for i in ids]
    order = ["differs", "inconclusive", "partly", "agrees", "exact"]
    worst = min(vs, key=order.index)
    return (f'<span class="stamp" data-v="{STAMP[worst]}">{esc(WORDS[worst])}'
            f'<small>{esc(basis)}</small></span>')


def dose(items):
    return "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in items)


def plate(label, src, alt, w, h):
    return (f'<figure class="plate"><figcaption>{esc(label)}</figcaption>'
            f'<img src="{src}" alt="{esc(alt)}" width="{w}" height="{h}"></figure>')


def pct(x):
    return f"{100 * x:.1f}%"


def station(fid, title, caption, ids, basis, stats, note):
    pub = PUB / f"figure-{fid}.png"
    w, h = Image.open(pub).size
    return (f'<section class="station surface" id="fig-{fid}" aria-labelledby="fig-{fid}-head">'
            f'<header class="station-head"><h2 id="fig-{fid}-head">{esc(title)}</h2>'
            f'<p class="caption">{esc(caption)}</p>{stamp(ids, basis)}</header>'
            '<div class="stage"><div class="pair">'
            + plate("Published", b64(pub), f"{title} as published", w, h)
            + plate("Our run", b64(RUN / f"fig{fid}_ours.png"), f"{title} reproduced", w, h)
            + "</div></div>"
            f'<div class="station-foot"><dl class="dose">{dose(stats)}</dl>'
            f'<p class="note">{esc(note)}</p></div></section>'), {"id": str(fid), "w": w, "h": h}


def pix(i):
    p = ITEMS[i]["pixels"]
    s = min(p["published_near_ours"], p["ours_near_published"])
    best = max(c["score"] for c in p["controls"])
    return s, best, p["threshold"]


# ---- Figure 3
s3 = F3["series"]
t1 = T["table1_ours"]
stats3 = []
for name, iid in (("SVM-DR", "fig3.dr"), ("SVM-DT", "fig3.dt")):
    if iid in ITEMS and ITEMS[iid]["method"] == "pixels":
        s, best, thr = pix(iid)
        stats3.append((f"{name}, ink within 2 px", f"{pct(s)} (best control {pct(best)})"))
    vi = ITEMS.get(iid + "-values")
    if vi and vi["method"] == "values":
        fs = vi["values"]["fields"]
        hit = sum(abs(float(f["observed"]) - float(f["expected"])) <= 0.0005 for f in fs)
        stats3.append((f"{name}, points within 0.0005", f"{hit} of {len(fs)}"))
note3 = ("Mean ROC over the 54 families at each dMAX, ours drawn as the paper's markers on its own "
         "axes; frame, ticks and legend are the published pixels. "
         + " ".join(f"{k} at dMAX 150: {v['roc']:.4f} (paper {T['table1_published'][k][0]})."
                    for k, v in t1.items()))
st3, f3 = station(3, "Fig. 3", "Average ROC of SVM-DR and SVM-DT against the distance threshold dMAX.",
                  [i for i in ("fig3.dr", "fig3.dt") if i in ITEMS and ITEMS[i]["method"] != "none"],
                  "Mean ROC per dMAX", stats3, note3)

# ---- Figure 4
p4 = F4["panels"]
stats4, ids4 = [], []
for key, iid in (("A", "fig4.a"), ("B", "fig4.b")):
    e = p4[key]
    if e.get("ours") is None:
        continue
    ids4.append(iid)
    stats4 += [(f"({key}) Spearman with published", f"{e['ours']['spearman']:.3f}"),
               (f"({key}) maximum, ours / paper", f"{e['our_max']:.0f} / {e['published_max']:.0f}"),
               (f"({key}) rank of (G,G), (L,L)", f"{e['our_rank_GG']}, {e['our_rank_LL']} (paper 1, 2)")]
note4 = ("Cells filled with the published colour bar's grey for our L2 norm, on the paper's scale. "
         "The published cells are read back through the same bar.")
st4, f4 = station(4, "Fig. 4", "L2 norm of the discriminant weights of each pair, family 2.5.1.3: "
                  "(A) Top-1-gram pairs, SVM-DT; (B) residue pairs, SVM-DR.", ids4,
                  "Cell greys within 24", stats4, note4)

# ---- Figure 5
stats5, ids5 = [], []
for key in "ABCD":
    e = F5["panels"][key]
    if e.get("ours") is None:
        continue
    ids5.append(f"fig5.{key.lower()}")
    stats5.append((f"({key}) {e['pair']} {e['method']}",
                   f"r {e['correlation_x2_149']:.2f}, scale {e['published_scale_on_ours']:.2f}"))
note5 = ("Our weights drawn as bars at x = d + 1, where the published bars sit (the correlation "
         "with the published bars is highest at that offset in every panel). Scale is the "
         "least-squares factor of the published bars on ours; it is reported, not applied.")
st5, f5 = station(5, "Fig. 5", "Discriminant weights of (G,G) and (L,L) against distance, family 2.5.1.3.",
                  ids5, "Bars within 2 px", stats5, note5)

STATIONS = st3 + st4 + st5
FIGS_JS = [f3, f4, f5]

# ---- Table 1 and claims
pubt = T["table1_published"]
rows = ""
for name in pubt:
    ours = t1.get(name)
    o = (f"<td class=num><strong>{ours['roc_3dp']}</strong></td><td class=num><strong>{ours['roc50_3dp']}</strong></td>"
         if ours else "<td class=num>quoted</td><td class=num>quoted</td>")
    rows += (f"<tr><td>{esc(name)}</td><td class=num>{pubt[name][0]}</td><td class=num>{pubt[name][1]}</td>{o}</tr>")
claims = [i for i in R["items"] if i["id"].startswith("text.") and i["method"] == "values"]
crow = ""
for c in claims:
    fs = c["values"]["fields"]
    vals = "; ".join(f"{f['name']}: {f['expected']} / {f['observed']}" for f in fs)
    crow += (f"<tr><td>{esc(c['label'])}</td><td>{esc(vals)}</td>"
             f"<td><span class=\"stamp\" data-v=\"{STAMP.get(c['verdict'], 'partly')}\">"
             f"{esc(WORDS[c['verdict']])}</span></td></tr>")
CLAIM_LINE = TEXT["claims_line"]
EXTRA = f"""<section class="container after-bench" aria-labelledby="tables-head">
  <div class="station surface" id="tables">
    <header class="station-head"><h2 id="tables-head">Table 1</h2><p class="caption">Average ROC and ROC50 over the 54 families. Our run for SVM-DR and SVM-DT at dMAX = 150; the other rows are quoted by the paper from earlier work and were not rerun.</p>{stamp([i for i in ("table1.dr", "table1.dt") if i in ITEMS and ITEMS[i]['method'] != 'none'], "At the printed precision")}</header>
    <div class="table-wrap"><table class="record dense"><caption>Table 1 (paper ROC, ROC50; ours ROC, ROC50)</caption><thead><tr><th scope="col">Method</th><th scope="col" class=num>Paper ROC</th><th scope="col" class=num>Paper ROC50</th><th scope="col" class=num>Ours ROC</th><th scope="col" class=num>Ours ROC50</th></tr></thead><tbody>{rows}</tbody></table></div>
    <div class="table-wrap"><table class="record dense"><caption>Claims in the text (paper / ours)</caption><thead><tr><th scope="col">Claim</th><th scope="col">Values</th><th scope="col">Verdict</th></tr></thead><tbody>{crow}</tbody></table></div>
    <p class="note">{esc(CLAIM_LINE)}</p>
  </div>
</section>"""

not_att = [i for i in R["items"] if i["verdict"] == "not_attempted"]
BURIED = "".join(f"<li>{esc(i['label'])}: {esc(i['cause']['summary'])}</li>" for i in not_att)
RECOVERED = f"""<section class="buried" aria-labelledby="buried-head">
  <div class="container">
    <div class="plastic buried-band">
      <h2 id="buried-head">What stayed buried</h2>
      <ul>{BURIED}<li>The authors’ DistanceSVM package and server (bioinformatics.hitsz.edu.cn answers 503)</li><li>The 2014 profile database and PSI-BLAST settings</li></ul>
    </div>
  </div>
</section>"""

MATCHED_INTRO = TEXT["matched_intro"]
MATCHED = "".join(f'<div class="row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>'
                  for k, v in TEXT["matched"])
LABEL = "<ol>" + "".join(
    f'<li><a href="#{a}"><span>{esc(k)}</span><span class="v" data-v="{STAMP.get(ITEMS[i]["verdict"], "none")}">'
    f'{esc(WORDS[ITEMS[i]["verdict"]])}</span></a></li>'
    for a, k, i in [("tables", "Table 1, SVM-DR", "table1.dr"), ("tables", "Table 1, SVM-DT", "table1.dt"),
                    ("fig-3", "Fig. 3, SVM-DR", "fig3.dr"), ("fig-3", "Fig. 3, SVM-DT", "fig3.dt"),
                    ("fig-4", "Fig. 4A", "fig4.a"), ("fig-4", "Fig. 4B", "fig4.b"),
                    ("fig-5", "Fig. 5A–B", "fig5.a"), ("fig-5", "Fig. 5C–D", "fig5.c")]
    if i in ITEMS) + "</ol>"
LEDE = TEXT["lede"]
CLOSING = TEXT["closing"]

page = (HERE / "page_template.html").read_text()
for k, v in {"LEDE": esc(LEDE), "LABEL": LABEL, "STATIONS": STATIONS, "EXTRA": EXTRA,
             "RECOVERED": RECOVERED, "MATCHED": MATCHED, "MATCHED_INTRO": f"<p>{esc(MATCHED_INTRO)}</p>",
             "CLOSING": esc(CLOSING)}.items():
    page = page.replace(f"<!--__{k}__-->", v)
page = page.replace("/*__FIGS__*/[]", json.dumps(FIGS_JS))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page)
print(f"wrote {OUT} ({len(page) // 1024} KB)")
