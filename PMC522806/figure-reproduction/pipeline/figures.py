"""Figs 3 and 4: read the published bar heights, redraw our bars on the published pixel grid.

  figures.py PUBLISHED_DIR ACCURACY_JSON OUT_DIR

Both figures are bar charts of printed accuracies. For each one:

1. The value axis is calibrated from the published gridlines and the axis baseline (pixel rows of
   the printed tick values; nothing inside the bars is fitted). The height of every published bar
   is read off at its top edge, as a check that the drawing shows its printed label.
2. ``fig*_ours.png``: the published figure with the "Our method" bars and their labels replaced
   by ours, at our accuracies, in the published bar texture. The other bars are values quoted from
   other papers and stay as published.
3. ``fig*_overlay.png``: red channel the published figure, green and blue ours. Grey is where they
   agree; cyan is ink only in the paper, red ink only in ours.

Writes figures.json with the calibration, the published bar heights and ours.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSerif.ttf"

# Layout of the published figures (600 px wide PMC images), measured once from the images:
# gridline rows with their printed tick values, bar column ranges, and the bars' meaning.
FIGS = {
    "fig3": {
        "file": "figure-3.jpg",
        "ticks": {100: 119, 90: 282, 80: 443, 70: 606},
        "baseline": 606,
        "label_h": 19,  # height of the printed bar labels, px
        "bars": [  # (x0, x1, group, series, printed label)
            (158, 187, "ALL-AML", "bagged", "91.18"), (188, 216, "ALL-AML", "best", "97.06"),
            (217, 246, "ALL-AML", "ours", "100"),
            (266, 295, "Lung", "bagged", "93.29"), (296, 324, "Lung", "best", "97.99"),
            (325, 354, "Lung", "ours", "100"),
            (373, 402, "Prostate", "bagged", "73.53"), (403, 431, "Prostate", "best", "73.53"),
            (432, 461, "Prostate", "ours", "97.06"),
        ],
        "ours": {"ALL-AML": "test.allaml.s0", "Lung": "test.lung.s0", "Prostate": "test.prostate.s0"},
    },
    "fig4": {
        "file": "figure-4.jpg",
        "ticks": {100: 129.5, 90: 343.5, 80: 557.5},
        "baseline": 557,
        "label_h": 27,
        "bars": [
            (149, 179, "DLBCL", "other", "96"), (180, 210, "DLBCL", "ours", "98"),
            (269, 299, "Ovarian", "other", "100"), (300, 330, "Ovarian", "ours", "98.82"),
            (376, 406, "Colon", "other", "85.48"), (407, 436, "Colon", "ours", "91.94"),
        ],
        # DLBCL: Cho and Won's 22/25 split (mean of our 20 random splits); Ovarian: 10-fold CV;
        # Colon: LOOCV (the bars the text describes).
        "ours": {"DLBCL": "cho.dlbcl", "Ovarian": "cv10.ovarian.f0", "Colon": "loocv.colon"},
    },
}


def calibration(ticks):
    """Least-squares map row -> value from the gridline rows; returns (slope, intercept, residual)."""
    v = np.array(list(ticks), float)
    r = np.array(list(ticks.values()), float)
    A = np.vstack([r, np.ones_like(r)]).T
    (m, b), *_ = np.linalg.lstsq(A, v, rcond=None)
    resid = float(np.abs(A @ [m, b] - v).max())
    return float(m), float(b), resid


def bar_top(gray, x0, x1, grid_rows, start, stop):
    """First row (from the top) where the bar's fill begins, skipping gridline rows."""
    seg = gray[:, x0 + 4 : x1 - 3]
    for r in range(start, stop):
        if any(abs(r - g) <= 1 for g in grid_rows):
            continue
        if (seg[r : r + 6] < 235).mean() > 0.6:
            return r
    return None


def ours_value(acc, key):
    if key == "cho.dlbcl":
        runs = [v for k, v in acc.items() if k.startswith("cho.dlbcl.r")]
        return 100.0 * sum(r["correct"] for r in runs) / sum(r["total"] for r in runs)
    return 100.0 * acc[key]["correct"] / acc[key]["total"]


def fmt(v):
    return "100" if abs(v - 100) < 1e-9 else f"{v:.2f}"


def draw(name, spec, pub_dir, acc, out_dir):
    im = Image.open(pub_dir / spec["file"]).convert("L")
    gray = np.asarray(im).astype(int)
    m, b, resid = calibration(spec["ticks"])
    grid_rows = [int(round(r)) for r in spec["ticks"].values()]
    row_of = lambda v: (v - b) / m  # noqa: E731
    top_row = int(row_of(100)) - 15
    base = spec["baseline"]

    # Offset of the top-edge reading, from the bars printed as exactly 100.
    raw = []
    for x0, x1, g, s, lab in spec["bars"]:
        r = bar_top(gray, x0, x1, grid_rows, top_row, base)
        raw.append(m * (r - 0.5) + b)
    hundreds = [h for h, bar in zip(raw, spec["bars"]) if bar[4] == "100"]
    offset = float(np.mean(hundreds) - 100.0) if hundreds else 0.0
    published = []
    for h, (x0, x1, g, s, lab) in zip(raw, spec["bars"]):
        published.append({"group": g, "series": s, "label": lab, "drawn": round(h - offset, 2),
                          "drawn_minus_label": round(h - offset - float(lab), 2)})

    # Our figure: replace the "ours" bars and their labels.
    ours_img = gray.copy()
    font = ImageFont.truetype(str(FONT), 13 if spec["label_h"] < 25 else 15)
    ours = []
    texture = {}
    for x0, x1, g, s, lab in spec["bars"]:
        if s != "ours":
            continue
        # The published bar's texture: a block from the lower part of the bar, tiled upwards.
        texture[g] = gray[base - 64 : base - 4, x0 : x1 + 1].copy()
    pil = Image.fromarray(ours_img.astype(np.uint8))
    d = ImageDraw.Draw(pil)
    for x0, x1, g, s, lab in spec["bars"]:
        if s != "ours":
            continue
        pub_top = bar_top(gray, x0, x1, grid_rows, top_row, base)
        # Erase the bar and its printed label (label_h px above the bar, a little wider than it);
        # then put back what the label box covered of the neighbouring bars and the gridlines.
        d.rectangle([x0, pub_top - 1, x1 + 2, base - 1], fill=255)
        lh = spec["label_h"]
        d.rectangle([x0 - 8, pub_top - lh, x1 + 14, pub_top], fill=255)
        arr = np.asarray(pil).astype(int)
        lx0, lx1 = x0 - 8, x1 + 15
        for bx0, bx1, _, bs, _ in spec["bars"]:
            if bs == "ours" or bx1 < lx0 or bx0 >= lx1:
                continue
            btop = bar_top(gray, bx0, bx1, grid_rows, top_row, base)
            c0, c1 = max(bx0, lx0), min(bx1 + 2, lx1)
            arr[btop - lh : pub_top + 1, c0:c1] = gray[btop - lh : pub_top + 1, c0:c1]
        for gr in grid_rows:
            if pub_top - lh <= gr <= pub_top:
                arr[gr, x0 - 8 : x1 + 15] = gray[gr, x0 - 8 : x1 + 15]
        pil = Image.fromarray(arr.astype(np.uint8))
        d = ImageDraw.Draw(pil)
        v = ours_value(acc, spec["ours"][g])
        r = int(round(row_of(v + offset)))
        tex = texture[g]
        h = base - r
        reps = int(np.ceil(h / tex.shape[0])) + 1
        tiled = np.vstack([tex] * reps)[-h:] if h > 0 else tex[:0]
        arr = np.asarray(pil).astype(int)
        arr[r:base, x0 : x1 + 1] = tiled
        for gr in grid_rows:  # gridlines run behind the bars: restore them where we erased
            if gr < r and gr < base:
                arr[gr, x0 : x1 + 1] = gray[gr, x0 - 30]
        arr[r, x0 : x1 + 1] = 90  # top edge
        arr[r:base, x0] = 90
        arr[r:base, x1] = 90
        pil = Image.fromarray(arr.astype(np.uint8))
        d = ImageDraw.Draw(pil)
        text = fmt(v)
        w = d.textlength(text, font=font)
        d.text(((x0 + x1) / 2 - w / 2, r - spec["label_h"]), text, fill=0, font=font)
        ours.append({"group": g, "source": spec["ours"][g], "value": round(v, 4), "printed": fmt(v),
                     "row": r})
    pil.save(out_dir / f"{name}_ours.png", optimize=False)
    ours_arr = np.asarray(pil)
    overlay = np.stack([gray.astype(np.uint8), ours_arr, ours_arr], axis=2)
    Image.fromarray(overlay, "RGB").save(out_dir / f"{name}_overlay.png", optimize=False)
    return {"calibration": {"value_per_row": round(m, 6), "intercept": round(b, 4), "tick_residual": round(resid, 4),
                            "top_edge_offset": round(offset, 3)},
            "published_bars": published, "ours": ours,
            "outputs": [f"figure-reproduction/output/{name}_ours.png", f"figure-reproduction/output/{name}_overlay.png"]}


def main():
    pub_dir, acc_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out_dir.mkdir(parents=True, exist_ok=True)
    acc = json.loads(acc_path.read_text())
    res = {name: draw(name, spec, pub_dir, acc, out_dir) for name, spec in FIGS.items()}
    (out_dir / "figures.json").write_text(json.dumps(res, indent=1) + "\n")
    for name, r in res.items():
        print(name, [(b["group"], b["series"], b["label"], b["drawn"]) for b in r["published_bars"]])


if __name__ == "__main__":
    main()
