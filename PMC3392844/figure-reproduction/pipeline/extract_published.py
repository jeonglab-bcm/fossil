"""Read the paper's printed numbers and its ROC curves from the article, and crop its figures.

Usage: extract_published.py PAPER.xml PAPER.pdf OUT_DIR

Writes, into OUT_DIR:
  published_values.json   Tables 1-4 as printed (article XML), Table S1, Fig. 5's counts and the numbers
                          of the text (typed below from the article, with where each one is)
  published_curves.json   every ROC curve of Figs 2-4 as (FPR, TPR) points, read from the PDF's vector
                          paths: the axes run from (0, 0) to (1, 1), so each path's own frame gives the map
  fig2.png ... fig5.png   the published figures cropped from the PDF at 600 dpi (pdftoppm)
The pipeline uses the committed copies of these files; --extract reruns this script and checks that the
fresh copies equal them.
"""
import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

DPI = 600
# Figures: page, crop box in PDF points (x0, y0 from the top-left, x1, y1) and the curves in plot order.
FIGURES = {
    "fig2": {"page": 4, "box": (296.0, 52.0, 556.0, 240.0), "width": "0.45",
             "curves": ["chem", "bio", "pheno", "chem+bio", "chem+pheno", "chem+bio+pheno"]},
    "fig3": {"page": 5, "box": (31.5, 52.0, 291.5, 240.0), "width": "0.45",
             "curves": ["chem", "bio", "pheno", "chem+bio", "chem+pheno", "chem+bio+pheno"]},
    "fig4": {"page": 5, "box": (33.0, 531.5, 293.0, 719.5), "width": "0.397",
             "curves": ["svm", "rf", "knn", "nb", "lr"]},
}
FIG5 = {"page": 6, "box": (391.0, 507.0, 563.0, 700.0)}

# Numbers of the text, as printed. Section names follow the article.
TEXT = {
    "sider_drugs": {"value": "888", "where": "Methods, Data description"},
    "sider_terms": {"value": "1385", "where": "Methods, Data description"},
    "sider_associations": {"value": "61102", "where": "Methods, Data description ('61 102')"},
    "sider_mean_per_drug": {"value": "68.8", "where": "Methods, Data description"},
    "unmapped_drugs": {"value": "56", "where": "Methods, Data description"},
    "drugs": {"value": "832", "where": "Methods, Data description"},
    "feature_dimension": {"value": "4276", "where": "Methods, Features (881+1142+2253)"},
    "bio_dimension": {"value": "1142", "where": "Methods, Features"},
    "pheno_dimension": {"value": "2253", "where": "Methods, Features"},
    "adr_50_threshold": {"value": "50", "where": "Methods, Experimental design: 'associated with more than 50 of the 832 drugs'"},
    "pauwels_auc": {"value": "0.8930", "where": "Results, Feature assessment (Pauwels et al. 2011's AUC, cited)"},
    "ks_chem_vs_chembio": {"value": "1.45E-07", "where": "Results, Feature assessment"},
    "ks_chem_vs_chembiopheno": {"value": "1.10E-15", "where": "Results, Feature assessment"},
    "ks_pheno_vs_chembiopheno": {"value": "0.177", "where": "Results, Feature assessment"},
    "bio_gain_all": {"value": "0.004", "where": "Results, Feature assessment; Discussion"},
    "bio_gain_50": {"value": "0.02", "where": "Results, Feature assessment; Discussion"},
    "bio_precision_gain": {"value": "3", "where": "Results, Feature assessment: '~3% in precision'"},
    "bio_recall_gain": {"value": "1", "where": "Results, Feature assessment: '~1% in recall'"},
    "pheno_precision_gain": {"value": "21", "where": "Results, Feature assessment: '~21% in precision'"},
    "pheno_recall_gain": {"value": "15", "where": "Results, Feature assessment: '~15% in recall'"},
    "chem_indication_auc": {"value": "0.9110", "where": "Discussion"},
    "rf_weighted_auc": {"value": "0.9524", "where": "Discussion: RF AUC 'increased from 0.9491 to 0.9524' with class weights"},
    "nausea_headache_drugs": {"value": "596", "where": "Discussion: nausea and headache co-occurred with 596 of 832 drugs"},
    "pairs_over_400": {"value": "49", "where": "Discussion: 49 pairs of ADRs co-occurred with more than 400 drugs"},
    "rare_adrs": {"value": "554", "where": "Discussion: 554 ADRs associated with fewer than five drugs"},
    "rare_ratio": {"value": "166", "where": "Discussion: 'approximate 1:166 positive to negative ratio'"},
    "fig5_chem_or_bio_not_pheno": {"value": "5072", "where": "Discussion, Fig. 5"},
    "fig5_pheno_only": {"value": "10581", "where": "Discussion, Fig. 5"},
}
# Table S1 (online supplement, a PDF): % of informative features by feature type.
TABLE_S1 = {"chem": "5.0", "target": "5.7", "transporter": "0.5", "enzyme": "1.0", "pathway": "1.7",
            "indication": "7.7", "ade": "78.4"}
# Fig. 5 is a raster Venn diagram; its seven counts as printed in it.
FIG5_COUNTS = {"chem": "928", "chem&bio": "3260", "bio": "884", "chem&bio&pheno": "23025", "chem&pheno": "1950",
               "bio&pheno": "2688", "pheno": "10581"}


def tables(xml):
    root = ET.parse(xml).getroot()
    out = {}
    for tw in root.iter("table-wrap"):
        rows = [[("".join(td.itertext())).strip() for td in tr] for tr in tw.iter("tr")]
        out[tw.get("id")] = rows
    t1 = {r[-3]: r[-1] for r in out["tbl1"][1:]}
    keys = ["auc", "acc", "precision", "recall"]

    def perf(rows):
        res = {}
        for r in rows[2:]:
            res[r[0].lower()] = {"all": dict(zip(keys, r[1:5])), "50+": dict(zip(keys, r[5:9]))}
        return res

    t4, drug = [], None
    for r in out["tbl4"][1:]:
        if len(r) == 1:
            drug = r[0]
            continue
        t4.append({"drug": drug, "cui": r[0], "adr": r[1], "chem": r[2], "chem+bio": r[3], "chem+bio+pheno": r[4]})
    return {"table1": t1, "table2": perf(out["tbl2"]), "table3": perf(out["tbl3"]), "table4": t4}


def svg_curves(pdf, page, width):
    """Stroked polylines of one width on a page, with their stroke colour, as PDF points (top-left)."""
    with tempfile.TemporaryDirectory() as tmp:
        svg = Path(tmp) / "p.svg"
        subprocess.run(["pdftocairo", "-svg", "-f", str(page), "-l", str(page), str(pdf), str(svg)], check=True)
        s = svg.read_text()
    body = s.split("</defs>", 1)[1]
    out = []
    for p in re.findall(r"<path([^>]*)/>", body):
        if f'stroke-width="{width}"' not in p:
            continue
        d = re.search(r' d="([^"]*)"', p).group(1)
        if d.count("L") < 20:
            continue
        m = [float(x) for x in re.search(r"matrix\(([^)]*)\)", p).group(1).replace(",", " ").split()]
        subs = []
        for seg in re.split(r"(?=M )", d.strip()):
            pts = np.array([[float(a), float(b)] for a, b in re.findall(r"[ML] ([-\d.]+) ([-\d.]+)", seg)])
            if len(pts):
                X = m[0] * pts[:, 0] + m[2] * pts[:, 1] + m[4]
                Y = m[1] * pts[:, 0] + m[3] * pts[:, 1] + m[5]
                subs.append(np.c_[X, Y])
        out.append({"stroke": re.search(r'stroke="([^"]*)"', p).group(1),
                    "dash": (re.search(r'stroke-dasharray="([^"]*)"', p) or [None, None])[1], "subpaths": subs})
    return out


def curves(pdf):
    res = {}
    for fig, spec in FIGURES.items():
        paths = svg_curves(pdf, spec["page"], spec["width"])
        if len(paths) != len(spec["curves"]):
            raise SystemExit(f"{fig}: {len(paths)} curves on page {spec['page']}, expected {len(spec['curves'])}")
        for p in paths:
            # MATLAB's export splits a curve into subpaths of about 100 points; the last subpath, two
            # points, is the curve's legend key.
            if len(p["subpaths"][-1]) != 2:
                raise SystemExit(f"{fig}: a curve does not end with its two-point legend key")
            p["curve"] = np.vstack(p["subpaths"][:-1])
        allpts = np.vstack([p["curve"] for p in paths])
        x0, x1 = allpts[:, 0].min(), allpts[:, 0].max()
        y0, y1 = allpts[:, 1].min(), allpts[:, 1].max()  # y0: TPR 1 (top), y1: TPR 0
        fig_out = {"frame_pt": [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)], "curves": {}}
        for name, p in zip(spec["curves"], paths):
            c = p["curve"]
            fpr = (c[:, 0] - x0) / (x1 - x0)
            tpr = (y1 - c[:, 1]) / (y1 - y0)
            # The subpaths are not in drawing order; a ROC curve is monotone, so sorting restores it.
            order = np.lexsort((tpr, fpr))
            fpr, tpr = fpr[order], tpr[order]
            fig_out["curves"][name] = {"stroke": p["stroke"], "dash": p["dash"], "points": len(c),
                                       "fpr": [round(float(v), 6) for v in fpr], "tpr": [round(float(v), 6) for v in tpr]}
        res[fig] = fig_out
    return res


def crop(pdf, page, box, out):
    x0, y0, x1, y1 = box
    s = DPI / 72.0
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(DPI), "-x", str(round(x0 * s)),
                        "-y", str(round(y0 * s)), "-W", str(round((x1 - x0) * s)), "-H", str(round((y1 - y0) * s)),
                        "-png", "-singlefile", str(pdf), f"{tmp}/c"], check=True)
        Path(f"{tmp}/c.png").replace(out)


def main():
    xml, pdf, out = sys.argv[1:4]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    vals = tables(xml)
    vals["tableS1"] = TABLE_S1
    vals["fig5"] = FIG5_COUNTS
    vals["text"] = TEXT
    vals["_source"] = ("Tables 1-4 from the article XML (PMC3392844.1.xml, PMC open-access copy); Table S1 from the "
                       "online supplement (amiajnl-2011-000699-s1.pdf), Fig. 5's counts from the figure and the text's "
                       "numbers from the article, typed in extract_published.py.")
    (out / "published_values.json").write_text(json.dumps(vals, indent=1) + "\n")
    (out / "published_curves.json").write_text(json.dumps(curves(pdf)) + "\n")
    for fig, spec in FIGURES.items():
        crop(pdf, spec["page"], spec["box"], out / f"{fig}.png")
    crop(pdf, FIG5["page"], FIG5["box"], out / "fig5.png")
    print(f"published values, curves and figure crops written to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
