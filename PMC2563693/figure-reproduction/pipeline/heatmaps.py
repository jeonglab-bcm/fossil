"""Read the published heatmaps of Fig. 4 (lung) and Fig. S4 (breast): published_heatmaps.json.

Usage: heatmaps.py PUBLISHED_DIR SUPPLEMENT_DIR OUT.json

Each heatmap has one row per pathway and one column per patient, the patients of the poor-prognosis
(metastatic) class first, under a magenta bar, then the others under a green bar. For each row we
read the mean of red minus green over the cells of each class (the cell centres, away from the cell
borders). The figures print no values; what can be compared is the direction of each row: whether
its colour is redder in the poor-prognosis (metastatic) patients than in the others.

Fig. 4 is read from the PLOS PNG (published/figure-4.png); the class boundaries are the ends of the
magenta and green bars above each heatmap, the heatmap rows the band of coloured rows under them.
Its cells are large enough to read one by one: each class's span holds as many equal columns as
Table S1 has patients in that class (Boston 31 and 31, Michigan 24 and 62; the colour changes in the
picture fall on these column edges), and "cells" keeps red minus green at the centre of every cell,
rows in the printed order, poor-prognosis columns first, in the published left-to-right order.
Fig. S4 is read from the supplementary PDF rendered at 300 dpi; its class boundaries and rows come
from the PDF's own drawing commands (the bars) and image placements (the heatmaps).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

# Row labels as printed, top to bottom, with their C2 gene sets.
FIG4_ROWS = [
    ("B lymphocyte pathway", "blymphocytePathway"),
    ("Pyrimidine metabolism", "MAP00240_Pyrimidine_metabolism"),
    ("p53 hypoxia pathway", "p53hypoxiaPathway"),
    ("MTA3 pathway", "mta3Pathway"),
    ("Breast cancer estrogen signalling", "breast_cancer_estrogen_signalling"),
    ("p53 signalling", "p53_signalling"),
    ("Isulin up-regulated genes", "INSULIN_2F_UP"),
    ("Leucine starvation down-regulated genes", "LEU_DOWN"),
    ("Glutamine starvation down-regulated genes", "GLUT_DOWN"),
    ("Glycolysis and gluconeogenesis", "MAP00010_Glycolysis_Gluconeogenesis"),
    ("Glycolysis", "GLYCOL"),
    ("Gluconeogenesis", "GLUCO"),
    ("Estrogen receptor modulators down-regulated genes", "FRASOR_ER_DOWN"),
    ("NF-kB up-regulated genes", "NFKB_INDUCED"),
]
FIGS4_ROWS = [
    ("Actin pathway", "actinYPathway"),
    ("Repamycin starvation down-regulated genes", "RAP_DOWN"),
    ("Leucine starvation down-regulated genes", "LEU_DOWN"),
    ("Glutamine starvation down-regulated genes", "GLUT_DOWN"),
    ("Bretani cell cycle", "CR_CELL_CYCLE"),
    ("Cyclin regulated genes", "SA_REG_CASCADE_OF_CYCLIN_EXPR"),
    ("Cell cycle", "Cell_Cycle"),
    ("Cell cycle checkpoint II genes", "cell_cycle_checkpointII"),
    ("KRAS up-regulated genes", "KRAS_TOP100_KNOCKDOWN"),
    ("GNF female genes", "GNF_FEMALE_GENES"),
    ("IL7 pathway", "il7Pathway"),
    ("IL22 pathway", "il22bpPathway"),
    ("MMP/Cytokine connection", "SA_MMP_CYTOKINE_CONNECTION"),
]
FIG4_COLUMNS = {"lung_boston": (31, 31), "lung_michigan": (24, 62)}  # Table S1: poor, good
S4_DPI = 300
MAGENTA, GREEN = np.array([236, 0, 140]), np.array([140, 198, 63])


def near(px, colour, tol=45):
    return np.all(np.abs(px.astype(int) - colour) <= tol, axis=-1)


def rows_of(im, x0, x1, y0, y1, n):
    """Mean red minus green of each of n equal row bands, over columns x0..x1 (cell centres only)."""
    band = (y1 - y0) / n
    out = []
    for i in range(n):
        a, b = int(round(y0 + (i + 0.25) * band)), int(round(y0 + (i + 0.75) * band))
        cells = im[a:b, int(x0):int(x1)].astype(float)
        out.append(float(np.mean(cells[..., 0] - cells[..., 1])))
    return out


def cells_of(im, x0, x1, ncol, y0, y1, nrow):
    """Red minus green at the centre (middle 40% each way) of each of nrow x ncol equal cells."""
    w, h = (x1 - x0) / ncol, (y1 - y0) / nrow
    out = np.zeros((nrow, ncol))
    for i in range(nrow):
        for j in range(ncol):
            c = im[int(y0 + (i + 0.3) * h):int(y0 + (i + 0.7) * h), int(x0 + (j + 0.3) * w):int(x0 + (j + 0.7) * w)].astype(float)
            out[i, j] = np.mean(c[..., 0] - c[..., 1])
    return out


def block(im, xs, y0, y1, n):
    """Rows of one heatmap: xs = (poor start, boundary, good end) in pixels."""
    pad = 2
    poor = rows_of(im, xs[0] + pad, xs[1] - pad, y0, y1, n)
    good = rows_of(im, xs[1] + pad, xs[2] - pad, y0, y1, n)
    return poor, good


def fig4(pub):
    im = np.asarray(Image.open(pub / "figure-4.png").convert("RGB"))
    h, w, _ = im.shape
    out = {}
    for name, (lo, hi) in (("lung_boston", (0, w // 2)), ("lung_michigan", (w // 2, w))):
        sub = im[:, lo:hi]
        bar_rows = np.where(near(sub, MAGENTA).sum(axis=1) > 50)[0]
        bar_y, bar_end = int(np.median(bar_rows)), int(bar_rows.max())
        mag = np.where(near(sub[bar_y], MAGENTA))[0]
        grn = np.where(near(sub[bar_y], GREEN))[0]
        xs = (lo + mag.min(), lo + grn.min(), lo + grn.max() + 1)
        # heatmap rows: below the bar, the rows whose cells are mostly not white
        coloured = (im[:, xs[0]:xs[2]].astype(int).sum(axis=2) < 600).mean(axis=1) > 0.9
        ys = [y for y in range(bar_end + 3, h) if coloured[y]]
        y0, y1 = ys[0], ys[0]
        while y1 + 1 < h and coloured[y1 + 1]:
            y1 += 1
        poor, good = block(im, xs, y0, y1 + 1, len(FIG4_ROWS))
        npoor, ngood = FIG4_COLUMNS[name]
        cells = np.hstack([cells_of(im, xs[0], xs[1], npoor, y0, y1 + 1, len(FIG4_ROWS)),
                           cells_of(im, xs[1], xs[2], ngood, y0, y1 + 1, len(FIG4_ROWS))])
        out[name] = {"box": [int(xs[0]), int(y0), int(xs[2]), int(y1 + 1)], "boundary": int(xs[1]),
                     "rows": [{"label": l, "set": s, "poor": round(p, 2), "good": round(g, 2), "redder_in_poor": p > g}
                              for (l, s), p, g in zip(FIG4_ROWS, poor, good)],
                     "columns": [npoor, ngood], "cells": np.round(cells, 1).tolist()}
    return out


def figs4(supp):
    page = pymupdf.open(supp / "pcbi.1000217.s006.pdf")[0]
    z = S4_DPI / 72
    pix = page.get_pixmap(dpi=S4_DPI)
    im = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3]
    bars = sorted((d for d in page.get_drawings() if d["type"] == "f" and d["fill"]), key=lambda d: d["rect"].x0)
    images = sorted((r for x in page.get_images(full=True) for r in page.get_image_rects(x[0])), key=lambda r: r.x0)
    out = {}
    # left: Netherlands (two bars and two images), right: USA
    for name, bs, ims in (("breast_netherlands", bars[:2], images[:2]), ("breast_usa", bars[2:], images[2:])):
        mag = next(d["rect"] for d in bs if d["fill"][0] > 0.9)
        grn = next(d["rect"] for d in bs if d["fill"][0] < 0.9)
        xs = (mag.x0 * z, grn.x0 * z, grn.x1 * z)
        y0, y1 = max(r.y0 for r in ims) * z, min(r.y1 for r in ims) * z
        poor, good = block(im, xs, y0, y1, len(FIGS4_ROWS))
        out[name] = {"box": [round(xs[0], 1), round(y0, 1), round(xs[2], 1), round(y1, 1)], "boundary": round(xs[1], 1),
                     "dpi": S4_DPI,
                     "rows": [{"label": l, "set": s, "poor": round(p, 2), "good": round(g, 2), "redder_in_poor": p > g}
                              for (l, s), p, g in zip(FIGS4_ROWS, poor, good)]}
    return out


def main(pub: Path, supp: Path, out: Path):
    res = {"fig4": fig4(pub), "fig_s4": figs4(supp)}
    out.write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    for f, v in r.items():
        for d, b in v.items():
            print(f, d, b["box"], b["boundary"], [("R" if x["redder_in_poor"] else "g") + f"{x['poor'] - x['good']:+.0f}" for x in b["rows"]])
