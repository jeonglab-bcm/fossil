"""Draw our LIMPIC results on the published figures' pixel grids and score the match.

Usage: python compare.py <data_dir> <published_dir> <S4_csv> <out_dir>

For each panel the pixel-to-data map comes from the published axes box and its tick marks
alone; nothing inside the box is fitted. Our trace is drawn 3 px wide, or as wide as the
published line where that is smooth enough to measure (Figs 7 and 8), and compared both ways: the share of
published trace pixels within 2 px of ours, and of ours within 2 px of the published.
Peak markers (Figs 7 and 8) are compared by position and colour.

Writes, per figure: <fig>_ours.png (the published figure with its traces replaced by ours),
<fig>_overlay.png (published in blue, ours in orange) and a summary in comparison.json.
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figmeasure as fm  # noqa: E402

# Fig. 2 and the panels drawn from it plot raw counts divided by 5. The divisor is the only
# constant read from the figures; at 0.19 or 0.21 times the counts the Fig. 2 match drops
# from 99.99% to 98.97% and 98.26% of published pixels within 2 px.
RAW_SCALE = 1 / 5
ORANGE = (255, 140, 0)

# Axes boxes (left, top, right, bottom: the pixel columns/rows of the box lines), x limits
# from the printed tick labels, y tick values from top to bottom, tick-mark depth in px.
# Rows kept in <fig>_ours.png and <fig>_overlay.png: panels made by other software
# (APEX, CENTROID, CROMWELL, Savitzky-Golay and wavelet filters) are cut away.
CROP_ROWS = {"fig4": (1690, None), "fig6": (0, 1045), "fig7": (0, 1250)}
# Published traces that are not LIMPIC's and stay inside a kept panel: removed from our render.
CLEAR_OTHER = {"fig5": dict(keep=[(1731, 420, 2617, 603)])}

PANELS = {
    "fig2": [dict(panel="", box=(317, 190, 2943, 2258), xlim=(5, 20), yticks=[300, 250, 200, 150, 100, 50], yzero_at_bottom=True, series="raw")],
    "fig3": [
        dict(panel="a", box=(282, 222, 2908, 639), xlim=(5, 20), yticks=[10, -10], series="noise10"),
        dict(panel="b", box=(282, 905, 2906, 1322), xlim=(5, 20), yticks=[10, -10], series="noise20"),
        dict(panel="c", box=(284, 1584, 2908, 2001), xlim=(5, 20), yticks=[10, -10], series="noise30"),
        dict(panel="d", box=(278, 2253, 2903, 2670), xlim=(5, 20), yticks=[10, -10], series="noise40"),
    ],
    "fig4": [dict(panel="c", box=(293, 1763, 2918, 2331), xlim=(5, 20), yticks=[10, -10], series="noise20")],
    "fig5": [dict(panel="peak-elimination", box=(209, 192, 2890, 2307), xlim=(5, 20), yticks=list(range(11, 0, -1)), yzero_at_bottom=True, series="baseline", colour=fm.RED, legend=[(1731, 420, 2617, 603)])],
    "fig6": [
        dict(panel="a", box=(97, 93, 531, 435), xlim=(5, 8), yticks=[40, 30, 20, 10], yzero_at_bottom=True, series="raw", depth=(1, 4)),
        dict(panel="b", box=(718, 94, 1152, 435), xlim=(14.75, 17.75), yticks=[40, 30, 20, 10], yzero_at_bottom=True, series="raw", depth=(1, 4)),
        dict(panel="c", box=(99, 616, 533, 958), xlim=(5, 8), yticks=[30, 20, 0, -10], series="limpic_noise", depth=(1, 4)),
        dict(panel="d", box=(716, 616, 1150, 958), xlim=(14.75, 17.75), yticks=[20, 10, -10, -20], series="limpic_noise", depth=(1, 4)),
    ],
    "fig7": [dict(panel="LIMPIC", box=(351, 234, 2921, 1088), xlim=(8.73, 9.02), yticks=[150, 100, 50], yzero_at_bottom=True, series="processed", markers="red", width=5)],
    "fig8": [dict(panel="", box=(275, 186, 2869, 2233), xlim=(8.73, 9.02), yticks=[180, 160, 140, 120, 100, 80, 60, 40, 20], yzero_at_bottom=True, series="processed", markers="classes", width=6, legend=[(2070, 342, 2684, 517)])],
}


def load_series(data):
    raw = np.loadtxt(os.path.join(data, "p15_raw.csv"), delimiter=",")
    proc = np.loadtxt(os.path.join(data, "p15_processed.csv"), delimiter=",")
    smooth = np.loadtxt(os.path.join(data, "p15_smooth.csv"), delimiter=",")
    x, w = raw[:, 0] / 1000, raw[:, 1]
    xr, wxr, baseline, wxrbn = proc[:, 0] / 1000, proc[:, 1], proc[:, 2], proc[:, 3]
    s = {
        "raw": (x, w * RAW_SCALE),
        "baseline": (xr, baseline * RAW_SCALE),
        "processed": (xr, wxrbn),
        # What LIMPIC removes from the raw spectrum: the smoothing residual plus the baseline.
        "limpic_noise": (x, (w - raw[:, 2] + np.interp(x, xr, baseline)) * RAW_SCALE),
    }
    for k, f in enumerate((10, 20, 30, 40)):
        s[f"noise{f}"] = (x, (w - smooth[:, k + 1]) * RAW_SCALE)
    return s


def peak_classes(data):
    """P_15's peaks and whether their class reaches PDR >= 0.5 in our 30-spectrum run."""
    peaks = pd.read_csv(os.path.join(data, "plasma_peaks.csv"))
    peaks = peaks[peaks.spectrum == 15]
    classes = pd.read_csv(os.path.join(data, "plasma_classes.csv"))
    present = classes[classes.s15 > 0]
    green = []
    for mz in peaks.mz:
        j = np.argmin(np.abs(present.mz.values - mz))
        green.append(present.n.values[j] >= 15)
    return peaks.mz.values / 1000, peaks.intensity.values, np.array(green)


def axes(img, spec):
    box = spec["box"]
    ys, xs = fm.ticks(img, box, depth=spec.get("depth", (6, 14)))
    vals = list(spec["yticks"])
    if len(ys) != len(vals):
        raise SystemExit(f"{spec}: found {len(ys)} y ticks, expected {len(vals)}")
    if spec.get("yzero_at_bottom"):
        ys, vals = ys + [box[3]], vals + [0]
    return fm.Axis([box[0], box[2]], spec["xlim"]), fm.Axis(ys, vals)


def draw(shape, X, Y, box, x, y, width=3):
    im = Image.new("1", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(im)
    m = (x >= X(box[0]) - 0.01) & (x <= X(box[2]) + 0.01)
    py = np.clip(Y.inverse(y[m]), box[1] - 20, box[3] + 20)
    d.line(list(zip(X.inverse(x[m]), py)), fill=1, width=width)
    return np.array(im)


def main(data, published, s4, out):
    os.makedirs(out, exist_ok=True)
    series = load_series(data)
    summary = {}
    for fig, panels in PANELS.items():
        img = fm.load(os.path.join(published, f"figure-{fig[3:]}.png"))
        ours_img = img.copy().astype(np.uint8)
        overlay = img.copy().astype(np.uint8)
        results = []
        ours_all = np.zeros(img.shape[:2], bool)
        for spec in panels:
            box = spec["box"]
            colour = spec.get("colour", fm.BLUE)
            X, Y = axes(img, spec)
            x, y = series[spec["series"]]
            inner = np.s_[box[1] + 3 : box[3] - 2, box[0] + 3 : box[2] - 2]
            pub = np.zeros(img.shape[:2], bool)
            pub[inner] = fm.mask(img, colour, tol=200)[inner]
            width = spec.get("width", 3)
            ours = np.zeros(img.shape[:2], bool)
            ours[inner] = draw(img.shape, X, Y, box, x, y, width)[inner]
            if spec.get("markers"):
                # Crosses sit on the curve; leave their neighbourhood out of the line comparison.
                for c in (fm.RED, fm.GREEN):
                    cross = ndimage.binary_dilation(fm.mask(img, c, tol=150), iterations=4)
                    pub &= ~cross
                    ours &= ~cross
            d_ours = ndimage.distance_transform_edt(~ours)
            d_pub = ndimage.distance_transform_edt(~pub)
            r = {
                "panel": spec["panel"],
                "published_within_2px": round(float(np.mean(d_ours[pub] <= 2)), 4),
                "ours_within_2px": round(float(np.mean(d_pub[ours] <= 2)), 4),
                "y_tick_fit_residual": round(Y.residual, 4),
                "line_width_px": width,
            }
            if spec.get("markers"):
                mx, my, green = peak_classes(data)
                keep = (mx >= spec["xlim"][0]) & (mx <= spec["xlim"][1])
                mx, my, green = mx[keep], my[keep], green[keep]
                pos = list(zip(X.inverse(mx), Y.inverse(my)))
                # For each of our peaks, the published marker colour at that point (crosses
                # of neighbouring peaks touch, so they are not separated into blobs).
                red = fm.mask(img, fm.RED, tol=150)
                grn = fm.mask(img, fm.GREEN, tol=150)
                covered = np.zeros(img.shape[:2], bool)
                found = []
                for px, py in pos:
                    win = np.s_[int(py) - 4 : int(py) + 5, int(px) - 4 : int(px) + 5]
                    covered[int(py) - 32 : int(py) + 33, int(px) - 32 : int(px) + 33] = True
                    found.append("protein" if grn[win].sum() > red[win].sum() else "noise" if red[win].any() else None)
                inside = np.zeros(img.shape[:2], bool)
                inside[box[1] : box[3], box[0] : box[2]] = True
                for lb in spec.get("legend", []):
                    inside[lb[1] : lb[3], lb[0] : lb[2]] = False
                extra, _ = ndimage.label((red | grn) & inside & ~covered)
                r["markers_ours"] = len(pos)
                r["published_marker_at_each_of_ours"] = sum(f is not None for f in found)
                r["published_markers_without_ours"] = int(extra.max())
                r["peaks"] = [
                    {"kDa": round(float(a), 4), "intensity": round(float(b), 2), "our_class": "protein" if g else "noise"}
                    for a, b, g in zip(mx, my, green)
                ]
                if spec["markers"] == "classes":
                    for p, f in zip(r["peaks"], found):
                        p["published_class"] = f
                    agree = sum(p["published_class"] == p["our_class"] for p in r["peaks"])
                    r["class_agreement"] = f"{agree} of {len(found)}"
                ours_markers = [
                    (px, py, (0, 255, 0) if (spec["markers"] == "classes" and g) else (255, 0, 0))
                    for (px, py), g in zip(pos, green)
                ]
            results.append(r)
            # Our render: the published panel with its trace pixels cleared and ours drawn in.
            clear = np.zeros(img.shape[:2], bool)
            clear[inner] = fm.mask(img, colour, tol=200)[inner]
            if spec.get("markers"):
                for c in (fm.RED, fm.GREEN):
                    clear[inner] |= fm.mask(img, c, tol=150)[inner]
            for lb in spec.get("legend", []):
                clear[lb[1] : lb[3], lb[0] : lb[2]] = False
            ours_img[clear] = 255
            ours_img[ours] = colour
            ours_all |= ours
            if spec.get("markers"):
                # Crosses as in the published figure: about 2.5% of the box width, 7 px strokes.
                im = Image.fromarray(ours_img)
                dr = ImageDraw.Draw(im)
                h = (box[2] - box[0]) * 0.0085 * (1.6 if spec["markers"] == "classes" else 1)
                for px, py, c in ours_markers:
                    dr.line([(px - h, py - h), (px + h, py + h)], fill=c, width=7)
                    dr.line([(px - h, py + h), (px + h, py - h)], fill=c, width=7)
                ours_img = np.array(im)
            overlay[ours & ~pub] = ORANGE
            overlay[ours & pub] = (0, 0, 120)
        if fig in CLEAR_OTHER:
            spec = CLEAR_OTHER[fig]
            box = panels[0]["box"]
            other = np.zeros(img.shape[:2], bool)
            other[box[1] + 2 : box[3] - 1, box[0] + 1 : box[2] - 1] = True
            for k in spec["keep"]:
                other[k[1] : k[3], k[0] : k[2]] = False
            # Include the anti-aliased edge of the line: any pixel clearly bluer than grey.
            other &= (img[:, :, 2] - np.maximum(img[:, :, 0], img[:, :, 1])) > 30
            ours_img[other & ~ours_all] = 255
        top, bottom = CROP_ROWS.get(fig, (0, None))
        Image.fromarray(ours_img[top:bottom]).save(os.path.join(out, f"{fig}_ours.png"), optimize=True)
        Image.fromarray(overlay[top:bottom]).save(os.path.join(out, f"{fig}_overlay.png"), optimize=True)
        summary[fig] = results
        print(fig, [(r["panel"], r["published_within_2px"], r["ours_within_2px"]) for r in results])

    summary["fig9"] = fig9(published, s4, out)
    with open(os.path.join(out, "comparison.json"), "w") as f:
        json.dump(summary, f, indent=2)


def fig9(published, s4, out):
    """Fig. 9a and 9b from Additional File 4: PDR = num_elem / 30 for each of its 1581 classes."""
    d = pd.read_csv(s4)
    mz = d["M/z"].values / 1000
    pdr = d[" num_elem"].values / 30
    img = fm.load(os.path.join(published, "figure-9.png"))
    bar = (8, 40, 144)
    res = {}

    # (a) one vertical line per class, from 0 to its PDR.
    box = (478, 361, 2695, 2105)
    X = fm.Axis([box[0], box[2]], (5, 20))
    # Fig. 9a's y ticks are partly hidden by the lines; take the scale from the box (0 to 1.05).
    Y = fm.Axis([box[3], box[1]], (0, 1.05))
    inner = np.s_[box[1] + 3 : box[3] - 2, box[0] + 3 : box[2] - 2]
    pub = np.zeros(img.shape[:2], bool)
    pub[inner] = fm.mask(img, bar, tol=120)[inner]
    im = Image.new("1", (img.shape[1], img.shape[0]), 0)
    dr = ImageDraw.Draw(im)
    for a, p in zip(mz, pdr):
        if 5 <= a <= 20:
            dr.line([(X.inverse(a), Y.inverse(0)), (X.inverse(a), Y.inverse(p))], fill=1, width=3)
    ours = np.array(im) & np.pad(np.ones((box[3] - box[1] - 5, box[2] - box[0] - 5), bool), ((box[1] + 3, img.shape[0] - box[3] + 2), (box[0] + 3, img.shape[1] - box[2] + 2)))
    d_ours = ndimage.distance_transform_edt(~ours)
    d_pub = ndimage.distance_transform_edt(~pub)
    res["a"] = {
        "published_within_2px": round(float(np.mean(d_ours[pub] <= 2)), 4),
        "ours_within_2px": round(float(np.mean(d_pub[ours] <= 2)), 4),
        "classes": int(len(pdr)),
    }

    # (b) MATLAB hist(PDR, 10): ten equal bins from the smallest to the largest PDR.
    box = (493, 2447, 2709, 4192)
    ys, _ = fm.ticks(img, box)
    Y = fm.Axis(ys + [box[3]], [800, 700, 600, 500, 400, 300, 200, 100, 0])
    edges = np.linspace(pdr.min(), pdr.max(), 11)
    counts, _ = np.histogram(pdr, edges)
    X = fm.Axis([box[0], box[2]], (0, 1.1))
    # Bar top: the first non-white pixel at the bar centre (bars have a dark outline).
    m = img.sum(axis=2) < 600
    published = []
    for k in range(10):
        cx = int(round(X.inverse((edges[k] + edges[k + 1]) / 2)))
        col = np.flatnonzero(m[box[1] + 4 : box[3] - 3, cx])
        published.append(round(float(Y(box[1] + 4 + col.min())), 1) if len(col) else 0.0)
    res["b"] = {"S4_counts": counts.tolist(), "published_bar_heights": published,
                "max_abs_difference": round(float(np.max(np.abs(np.array(published) - counts))), 1),
                "y_tick_fit_residual": round(Y.residual, 4)}
    print("fig9", res)
    return res


if __name__ == "__main__":
    main(*sys.argv[1:5])
