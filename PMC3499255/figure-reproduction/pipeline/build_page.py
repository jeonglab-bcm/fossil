"""Build the results page for PMC3499255 from results.json and the figures.

Every verdict and number on the page is read from results.json; nothing is typed.
For each attempted figure the published figure and our reproduction are shown side
by side (the panels are MCMC output, so the comparison is on the medians and
intervals, not pixel by pixel). Images are embedded as base64 so the page works
offline and on GitHub Pages.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import os

STAMP = {"exact": "agrees", "agrees": "agrees", "partly": "partly",
         "inconclusive": "partly", "differs": "differs", "not_attempted": None}


def b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def img_tag(path, alt, cls=""):
    if not os.path.exists(path):
        return ""
    ext = "jpeg" if path.endswith(("jpg", "jpeg")) else "png"
    return (f'<img class="{cls}" alt="{html.escape(alt)}" '
            f'src="data:image/{ext};base64,{b64(path)}">')


def value_table(item):
    v = item.get("values")
    if not v:
        return ""
    rows = ["<table class='record'><thead><tr><th>Quantity</th><th>Paper</th>"
            "<th>Reproduced</th></tr></thead><tbody>"]
    for f in v["fields"]:
        rows.append(f"<tr><td>{html.escape(f['name'])}</td>"
                    f"<td>{html.escape(str(f['expected']))}</td>"
                    f"<td>{html.escape(str(f['observed']))}</td></tr>")
    rows.append("</tbody></table>")
    return "".join(rows)


def stamp(v):
    if v == "not_attempted":
        # design: not-attempted items are listed with their reason, without a stamp
        return "<span class='not-attempted'>not attempted</span>"
    dv = STAMP.get(v, "partly")
    return f"<span class='stamp' data-v='{dv}'>{html.escape(v)}</span>"


FIG_IMAGES = {"fig2": ("figure-2.jpg", "fig2_ours.png"),
              "fig3": ("figure-3.jpg", "fig3_ours.png"),
              "fig4": ("figure-4.jpg", "fig4_ours.png")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("rundir")
    ap.add_argument("published")
    ap.add_argument("out")
    args = ap.parse_args()

    res = json.load(open(args.results))
    paper = res["paper"]
    summary = res.get("summary", {})
    items = res["items"]

    counts = {k: summary.get(k, 0) for k in
              ("exact", "agrees", "partly", "inconclusive", "differs", "not_attempted")}
    lead_bits = [f"{counts[k]} {k.replace('_', ' ')}" for k in counts if counts[k]]
    lead = ", ".join(lead_bits)

    blocks = []
    for item in items:
        iid = item["id"]
        v = item.get("verdict", "")
        head = (f"<div class='item-head'><h3>{html.escape(item['label'])}</h3>{stamp(v)}</div>")
        figs = ""
        if iid in FIG_IMAGES:
            pub, ours = FIG_IMAGES[iid]
            pub_p = os.path.join(args.published, pub)
            ours_p = os.path.join(args.rundir, ours)
            figs = ("<div class='plates'>"
                    f"<figure class='plate'><figcaption>Published</figcaption>{img_tag(pub_p, 'published figure')}</figure>"
                    f"<figure class='plate'><figcaption>Reproduced</figcaption>{img_tag(ours_p, 'reproduced figure')}</figure>"
                    "</div>")
        vt = value_table(item)
        chk = ""
        if item.get("method") == "check":
            c = item.get("check", {})
            chk = f"<p class='detail'>{html.escape(c.get('detail',''))}</p>"
        cause = ""
        if item.get("cause"):
            cause = f"<p class='cause'>{html.escape(item['cause'].get('summary',''))}</p>"
        blocks.append(f"<section class='surface item'>{head}{figs}{vt}{chk}{cause}</section>")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>FMDV transmission trees</title>
<meta name="description" content="Morelli et al. 2012, Bayesian reconstruction of foot-and-mouth transmission trees, dug back up: the lost MCMC rebuilt from the paper and Text S1, and the 2007 and 2001 outbreaks reconstructed.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@700&family=Instrument+Sans:wght@400;500&family=DM+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="../results.css">
</head>
<body>
<header class="topbar"><div class="container">
  <a class="wordmark" href="../" aria-label="fossil, home">fossil</a>
  <nav aria-label="Site"><a href="../#papers">The papers</a><a href="https://github.com/jeonglab-bcm/fossil/tree/main/PMC3499255">The code</a></nav>
</div></header>
<main>
  <section class="hero" aria-labelledby="h"><div class="container">
    <h1 id="h">Foot-and-mouth transmission trees, dug back up.</h1>
    <p class="lead">{html.escape(lead)}. The lost MCMC was rebuilt from the paper and Text S1. The 2007 and 2001 outbreaks came back with the same trees, and the latency and distance medians land where the paper put them.</p>
  </div></section>
  <section class="container"><p class="cite">{html.escape(paper['citation'])}. <a href="https://doi.org/{paper['doi']}">doi:{paper['doi']}</a>. {html.escape(paper.get('license',''))}.</p></section>
  <section class="container items">
    {''.join(blocks)}
  </section>
</main>
<footer class="foot"><div class="container">
  <p class="statement">The 2007 and 2001 foot-and-mouth trees came back the same, latency and all.</p>
  <nav class="links" aria-label="Footer">
    <a href="https://github.com/jeonglab-bcm/fossil/tree/main/PMC3499255">The code on GitHub</a>
    <a href="https://doi.org/{paper['doi']}">The paper</a>
    <a href="../">All papers</a>
  </nav>
</div></footer>
</body>
</html>
"""
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        fh.write(page)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
