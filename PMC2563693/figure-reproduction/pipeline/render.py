"""Draw our results: each figure as ours (fig*_ours.png) and over the published one (fig*_overlay.png).

Usage: render.py RUN_DIR PUBLISHED_DIR SUPPLEMENT_DIR OUTDIR

Raster figures (Figs 2 and 3): ours is drawn on a copy of the published figure with the
published series removed, through the same axis calibration that read the published values,
in the published colours; the overlay draws ours in black on the untouched figure.
Vector figures (Figs S1, S2, S3, S5): the PDF page is rasterized at 200 dpi and ours is drawn
in black over it through the calibration read from the PDF; ours alone is re-plotted with
matplotlib in the published colours. Figs 4 and S4 are heatmaps without printed values: ours is
painted into the published heatmap boxes (Fig. 4 with our patients in the published column order,
Fig. S4 with each class ordered by mean activity), and the overlay blends it with the published one.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pymupdf  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import digitize as DG  # noqa: E402
from common import LABELS  # noqa: E402
from compare import CROSS_ORDER, WITHIN_ORDER, cross_label  # noqa: E402

ZOOM = 200 / 72
BLACK = (0, 0, 0)


def save(im, path):
    im.save(path, optimize=True)


def cross_mark(d, x, y, r, colour, w):
    d.line([(x - r, y - r), (x + r, y + r)], fill=colour, width=w)
    d.line([(x - r, y + r), (x + r, y - r)], fill=colour, width=w)


# ----------------------------------------------------------------------------- Fig. 2

def fig2(run, pub, out):
    dig = json.loads((run / "digitized.json").read_text())["fig2"]
    ours = json.loads((run / "fig2.json").read_text())
    base = DG.load(pub / "figure-2.png")
    lab = DG.nearest(base, DG.FIG2_COLOURS, 40)
    clean = base.copy()
    for p in dig.values():
        x0, y0, x1, y1 = p["box"]
        sub = lab[y0 - 10 : y1 + 10, x0 - 10 : x1 + 12]
        clean[y0 - 10 : y1 + 10, x0 - 10 : x1 + 12][sub >= 0] = 255
    im_ours = Image.fromarray(clean.astype(np.uint8))
    im_over = Image.fromarray(base.astype(np.uint8))
    do, dv = ImageDraw.Draw(im_ours), ImageDraw.Draw(im_over)
    outputs = {}
    for panel, p in dig.items():
        row = lambda v: (v - p["a"]) / p["b"]
        for s, c in DG.FIG2_COLOURS.items():
            pts = [(x, row(v)) for x, v in zip(p["x"], ours[panel]["series"][s])]
            do.line(pts, fill=tuple(c), width=5)
            dv.line(pts, fill=BLACK, width=2)
            for x, y in pts:
                cross_mark(do, x, y, 8, tuple(c), 3)
                cross_mark(dv, x, y, 6, BLACK, 2)
    save(im_ours, out / "fig2_ours.png")
    save(im_over, out / "fig2_overlay.png")
    # the whole figure, on the published grid, for every panel's item
    files = ["figure-reproduction/output/figures/fig2_ours.png", "figure-reproduction/output/figures/fig2_overlay.png"]
    return {f"fig2.{panel.lower()}": files for panel in dig}


# ----------------------------------------------------------------------------- Fig. 3

def fig3(run, pub, out):
    dig = json.loads((run / "digitized.json").read_text())["fig3"]
    cv = json.loads((run / "cv_summary.json").read_text())
    base = DG.load(pub / "figure-3.png")
    im_ours = Image.fromarray(base.astype(np.uint8))
    im_over = Image.fromarray(base.astype(np.uint8))
    do, dv = ImageDraw.Draw(im_ours), ImageDraw.Draw(im_over)
    for panel, names in (("A", [(d, LABELS[d], f"within", d) for d in WITHIN_ORDER]),
                         ("B", [(f"{s}__{t}", cross_label(s, t), "cross", None) for s, t in CROSS_ORDER])):
        p = dig[panel]
        row = lambda v: (v - p["a"]) / p["b"]
        floor = row(0.4)
        for key, label, kind, _ in names:
            sc = cv[kind][key]["scores"]
            for m, (xa, xb) in p["extent"][label].items():
                top = row(sc[f"{m}/lr"]["mean"])
                # remove the published bar (and its error bar), put the grid lines back, and draw ours
                do.rectangle([xa - 1, row(1.0) - 30, xb + 1, floor - 1], fill=(255, 255, 255))
                for gv in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
                    do.line([(xa - 1, row(gv)), (xb + 1, row(gv))], fill=(128, 128, 128), width=2)
                do.rectangle([xa, top, xb, floor - 1], fill=DG.FIG3_COLOURS[m])
                dv.line([(xa - 3, top), (xb + 3, top)], fill=BLACK, width=3)
    save(im_ours, out / "fig3_ours.png")
    save(im_over, out / "fig3_overlay.png")
    files = ["figure-reproduction/output/figures/fig3_ours.png", "figure-reproduction/output/figures/fig3_overlay.png"]
    return {"fig3.a": files, "fig3.b": files, "fig3.pvalues": files}


# ----------------------------------------------------------------------------- vector figures

def vector_figs(run, supp, out):
    import render_vector as RV

    vec = json.loads((run / "published_vector.json").read_text())
    cv = json.loads((run / "cv_summary.json").read_text())
    rob = json.loads((run / "robustness.json").read_text())
    within = [(d, LABELS[d]) for d in WITHIN_ORDER]
    cross = [(f"{s}__{t}", cross_label(s, t)) for s, t in CROSS_ORDER]
    f = lambda n, k: str(out / f"fig{n}_{k}.png")
    # Fig. S1: the legend sits in its own box; its markers stay
    page = pymupdf.open(supp / "pcbi.1000217.s003.pdf")[0]
    hit = page.search_for("Pathways")
    legend = None
    if hit:
        cands = [d["rect"] for d in page.get_drawings() if d["rect"].contains(hit[0]) and d["rect"].width < 150]
        legend = min(cands, key=lambda r: r.width * r.height) if cands else None
    RV.figs1(supp / "pcbi.1000217.s003.pdf", vec["figS1"], rob["figS1"], legend, f("S1", "ours"), f("S1", "overlay"))
    RV.figs2(supp / "pcbi.1000217.s004.pdf", vec["figS2"], cv, [("within", within), ("cross", cross)],
             {"A": "knn3", "B": "knn5", "C": "nb", "D": "lda"}, f("S2", "ours"), f("S2", "overlay"))
    RV.figs3(supp / "pcbi.1000217.s005.pdf", vec["figS3_axis"], vec["figS3_positions"], cv["within"], within,
             f("S3", "ours"), f("S3", "overlay"))
    RV.figs5(supp / "pcbi.1000217.s007.pdf", vec["figS5"], rob, within, f("S5", "ours"), f("S5", "overlay"))
    files = lambda n: [f"figure-reproduction/output/figures/fig{n}_ours.png", f"figure-reproduction/output/figures/fig{n}_overlay.png"]
    outputs = {f"fig_s1.{d}": files("S1") for d in WITHIN_ORDER}
    outputs.update({f"fig_s2.{p}": files("S2") for p in "abcd"})
    outputs.update({f"fig_s2.{p}.pvalues": files("S2") for p in "abcd"})
    outputs.update({"fig_s3": files("S3"), "fig_s5": files("S5")})
    return outputs


# ----------------------------------------------------------------------------- heatmaps

def heat_colour(v):
    """Published palette: red for high activity, green for low, black in between (clipped at +-2)."""
    v = max(-2.0, min(2.0, v)) / 2
    return (int(round(240 * v)), 0, 0) if v >= 0 else (0, int(round(-220 * v)), 0)


def draw_heatmap(im, box, boundary, rows, activity, cases, scale=1.0, dx=0.0, dy=0.0, order=None):
    """Paint our activity into the published heatmap box: rows in the published order, the case
    columns between box[0] and the boundary, the others after it. Columns in the given order (our
    patient for each published column), else each class ordered by its patients' mean activity."""
    d = ImageDraw.Draw(im)
    A = np.asarray(activity)
    tx = lambda x: (x * scale) - dx
    ty = lambda y: (y * scale) - dy
    x0, y0, x1, y1 = tx(box[0]), ty(box[1]), tx(box[2]), ty(box[3])
    xb = tx(boundary)
    n = len(rows)
    for cls, (a, b) in ((np.arange(cases), (x0, xb)), (np.arange(cases, A.shape[1]), (xb, x1))):
        cols = [c for c in order if c in set(cls)] if order is not None else cls[np.argsort(-A[:, cls].mean(axis=0), kind="stable")]
        w = (b - a) / len(cols)
        for j, col in enumerate(cols):
            for i, r in enumerate(rows):
                d.rectangle([a + j * w, y0 + i * (y1 - y0) / n, a + (j + 1) * w, y0 + (i + 1) * (y1 - y0) / n],
                            fill=heat_colour(A[r, col]))


def heatmaps(run, pub, supp, out):
    import render_vector as RV

    hm = json.loads((run / "published_heatmaps.json").read_text())
    act = json.loads((run / "figure4.json").read_text())["heatmap"]
    matched = json.loads((run / "comparison.json").read_text())["fig4_columns"]
    outputs = {}
    # Fig. 4: on the PLOS PNG, our patients in the published column order (compare.py, fig4_columns)
    base = Image.open(pub / "figure-4.png").convert("RGB")
    ours = base.copy()
    for d_, h in hm["fig4"].items():
        a = act["fig4"][d_]
        rows = [a["pathways"].index(r["set"]) for r in h["rows"]]
        draw_heatmap(ours, h["box"], h["boundary"], rows, a["activity"], a["cases"], order=matched[d_]["order"])
    save(ours, out / "fig4_ours.png")
    save(Image.blend(base, ours, 0.5), out / "fig4_overlay.png")
    outputs["fig4"] = ["figure-reproduction/output/figures/fig4_ours.png", "figure-reproduction/output/figures/fig4_overlay.png"]
    # Fig. S4: on the supplementary page rasterized as published/figure-S4.png
    page = pymupdf.open(supp / "pcbi.1000217.s006.pdf")[0]
    clip = RV.clip_of(page)
    base = Image.open(pub / "figure-S4.png").convert("RGB")
    ours = base.copy()
    for d_, h in hm["fig_s4"].items():
        a = act["fig_s4"][d_]
        rows = [a["pathways"].index(r["set"]) for r in h["rows"]]
        sc = RV.DPI / h["dpi"]
        draw_heatmap(ours, h["box"], h["boundary"], rows, a["activity"], a["cases"], scale=sc,
                     dx=clip.x0 * RV.DPI / 72, dy=clip.y0 * RV.DPI / 72)
    save(ours, out / "figS4_ours.png")
    save(Image.blend(base, ours, 0.5), out / "figS4_overlay.png")
    outputs["fig_s4"] = ["figure-reproduction/output/figures/figS4_ours.png", "figure-reproduction/output/figures/figS4_overlay.png"]
    return outputs


def main(run: Path, pub: Path, supp: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for f in (lambda: fig2(run, pub, out), lambda: fig3(run, pub, out), lambda: vector_figs(run, supp, out),
              lambda: heatmaps(run, pub, supp, out)):
        outputs.update(f())
    # every render is drawn on the published figure's own grid: same size as the published picture
    for item, files in outputs.items():
        for fpath in files:
            name = Path(fpath).name
            n = name.split("_")[0][3:]
            pubf = pub / f"figure-{n}.png"
            if pubf.exists() and Image.open(out / name).size != Image.open(pubf).size:
                raise SystemExit(f"{name}: {Image.open(out / name).size} is not the published size {Image.open(pubf).size}")
    (out / "outputs.json").write_text(json.dumps(outputs, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
