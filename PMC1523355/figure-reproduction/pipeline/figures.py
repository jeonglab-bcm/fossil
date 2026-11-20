"""Fig. 1 of our run, on the published picture, and its pixel score with negative controls.

Usage: figures.py PUBLISHED_FIGURE SIMULATION_JSON OUT_DIR

Panel A (a curve): the axes are calibrated from the published tick marks alone (x .01 to .08, y -.4 to
.4); the published curve (navy) is erased and ours is drawn in its place at the published line width
(fig1a_ours.png), or in green over the published picture (fig1a_overlay.png). Scored both ways at 2 px
on the published pixel grid, with wrong-input controls (harm 2 and 4 per 1,000 per year, Table 5's
neighbours) and near-miss controls (net RRR x 0.95 and x 1.05; CER shifted by 1% of the x axis).

Panel B is a table drawn inside the figure: our values are written into its cells on a copy of the
picture (fig1b_ours.png), and under the published values in green (fig1b_overlay.png). It is compared as
values (compare.py), not by pixels.

Writes figures.json (calibration, scores, controls, layout) and the four PNGs.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import stratpower as sp

TOL = 2
NAVY = (26, 47, 110)
GREEN = (0, 160, 90)
X_TICKS = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]
Y_TICKS = [0.4, 0.2, 0.0, -0.2, -0.4]
FIG1B_ROWS = {"1.5%": (604, 638), "3%": (638, 675), "6%": (675, 711), "9%": (711, 748)}
FIG1B_COLS = {"one_rf": (336, 440), "four_rf": (442, 586)}


def gray(im):
    return np.asarray(im.convert("L")).astype(float)


def centroids(profile, lo, hi, min_gap=20):
    """Dark-weighted centroids of tick marks in a 1-D darkness profile between lo and hi."""
    idx = np.arange(lo, hi)
    w = profile[lo:hi]
    peaks = []
    for i in range(1, len(w) - 1):
        if w[i] >= w[i - 1] and w[i] >= w[i + 1] and w[i] > 0.35 * w.max():
            if peaks and i - peaks[-1] < min_gap:
                if w[i] > w[peaks[-1]]:
                    peaks[-1] = i
                continue
            peaks.append(i)
    out = []
    for p in peaks:
        s = slice(max(p - 2, 0), p + 3)
        out.append(float((idx[s] * w[s]).sum() / w[s].sum()))
    return out


def calibrate(g):
    """Pixel <-> data maps for panel A from the tick marks; returns the fit and its residuals."""
    dark = np.clip(255 - g, 0, None)
    xt = centroids(dark[298:302, :].sum(0), 82, 580)  # x ticks hang below the axis line (row 296)
    yt = centroids(dark[:, 74:79].sum(1), 70, 300)  # y ticks sit left of the axis line (column 80)
    if len(xt) != len(X_TICKS) or len(yt) != len(Y_TICKS):
        raise SystemExit(f"tick detection failed: {len(xt)} x ticks, {len(yt)} y ticks")
    ax, bx = np.polyfit(X_TICKS, xt, 1)
    ay, by = np.polyfit(Y_TICKS, yt, 1)
    res_x = np.array(xt) - (ax * np.array(X_TICKS) + bx)
    res_y = np.array(yt) - (ay * np.array(Y_TICKS) + by)
    return {"x": [ax, bx], "y": [ay, by], "x_ticks_px": xt, "y_ticks_px": yt,
            "residual_px": float(max(np.abs(res_x).max(), np.abs(res_y).max()))}


def to_px(cal, x, y):
    return cal["x"][0] * np.asarray(x) + cal["x"][1], cal["y"][0] * np.asarray(y) + cal["y"][1]


def plot_box(g):
    """The plot region of panel A: inside the y axis (column 80) and above the x axis (row 296), below the
    title box and left of the graph region's edge."""
    return 82, 575, 79, 295  # x0, x1, y0, y1 (pixels), read once from the picture's axis lines


def navy_mask(a):
    r, gg, b = a[..., 0], a[..., 1], a[..., 2]
    return (b - r > 40) & (b < 200) & (r < 140)


def equation_box(a, box):
    """The boxed equation inside panel A: masked from the scores (its text is navy too)."""
    g = a.mean(2)
    x0, x1, y0, y1 = box
    grey = (np.abs(a[..., 0] - a[..., 2]) < 40) & (np.abs(a[..., 0] - a[..., 1]) < 40)  # not the red lines
    d = (g < 180)[y0:y1, x0:x1] & grey[y0:y1, x0:x1]
    rows = [y0 + i for i, s in enumerate(d.sum(1)) if s > 200]  # the box's top and bottom borders
    cols = [x0 + j for j, s in enumerate(d[min(rows) - y0:max(rows) - y0].sum(0)) if s > 0.8 * (max(rows) - min(rows))]
    return min(cols), max(cols), min(rows), max(rows)


def dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def draw_curve(size, cal, xs, ys, width, colour=(0, 0, 0)):
    im = Image.new("RGB", size, (255, 255, 255))
    px, py = to_px(cal, xs, ys)
    ImageDraw.Draw(im).line(list(zip(px.tolist(), py.tolist())), fill=colour, width=width, joint="curve")
    return im


def score(pub, ours, valid):
    """Shares within TOL px both ways, on the valid region only."""
    p, o = pub & valid, ours & valid
    a = float((p & dilate(o, TOL)).sum() / max(p.sum(), 1))
    b = float((o & dilate(p, TOL)).sum() / max(o.sum(), 1))
    return a, b


def panel_a(src, out_dir):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(int)
    g = gray(im)
    cal = calibrate(g)
    box = plot_box(g)
    eq = equation_box(a, box)
    x0, x1, y0, y1 = box
    valid = np.zeros(g.shape, bool)
    valid[y0:y1, x0:x1] = True
    valid[eq[2] - 2:eq[3] + 3, eq[0] - 2:eq[1] + 3] = False
    pub = navy_mask(a) & valid
    # the published curve's ends, in data units (where our curve starts and stops)
    ys_, xs_ = np.nonzero(pub)
    x_lo = (xs_.min() - cal["x"][1]) / cal["x"][0]
    x_hi = (xs_.max() - cal["x"][1]) / cal["x"][0]
    lo, hi = round(float(x_lo), 3), round(float(x_hi), 3)
    # line width: navy pixels per column in the flat right part of the curve
    cols = [c for c in range(int(xs_.max()) - 60, int(xs_.max()) - 10)]
    width = int(round(np.median([pub[:, c].sum() for c in cols])))
    xs = np.linspace(lo, hi, 600)
    variants = {
        "ours": sp.net_rrr(xs),
        "wrong_input: harm 2 per 1,000 per year": sp.net_rrr(xs, harm_per_year=0.002),
        "wrong_input: harm 4 per 1,000 per year": sp.net_rrr(xs, harm_per_year=0.004),
        "near_miss: net RRR x 0.95": 0.95 * sp.net_rrr(xs),
        "near_miss: net RRR x 1.05": 1.05 * sp.net_rrr(xs),
        "near_miss: CER + 1% of the x axis": sp.net_rrr(np.maximum(xs - 0.0007, 1e-4)),
    }
    scores, controls = {}, []
    for name, ys in variants.items():
        m = np.asarray(draw_curve(im.size, cal, xs, ys, width).convert("L")) < 128
        s = score(pub, m & valid, valid)
        if name == "ours":
            scores = {"published_near_ours": s[0], "ours_near_published": s[1]}
            ours_mask = m
        else:
            kind, label = name.split(": ", 1)
            controls.append({"name": label, "kind": kind, "score": min(s)})
    # sensitivity to the curve's CER range (read from the published curve's ends): each end moved by 0.001
    range_sens = {}
    for a_lo, a_hi in ((lo + 0.001, hi), (lo - 0.001, hi), (lo, hi - 0.001), (lo, hi + 0.001)):
        xx = np.linspace(a_lo, a_hi, 600)
        m = np.asarray(draw_curve(im.size, cal, xx, sp.net_rrr(xx), width).convert("L")) < 128
        range_sens[f"{a_lo:.3f}-{a_hi:.3f}"] = min(score(pub, m & valid, valid))
    # renders: ours in place of the published curve; overlay in green on the published picture
    erase = dilate(navy_mask(a) & valid, 1)
    base = a.copy()
    base[erase] = 255
    ours_im = Image.fromarray(base.astype(np.uint8))
    px, py = to_px(cal, xs, variants["ours"])
    ImageDraw.Draw(ours_im).line(list(zip(px.tolist(), py.tolist())), fill=NAVY, width=width, joint="curve")
    ours_im.save(out_dir / "fig1a_ours.png", optimize=True)
    over = im.copy()
    ImageDraw.Draw(over).line(list(zip(px.tolist(), py.tolist())), fill=GREEN, width=max(width - 1, 1), joint="curve")
    over.save(out_dir / "fig1a_overlay.png", optimize=True)
    # layout: our curve is drawn on the published picture with the published axes
    xr = [(x0 - cal["x"][1]) / cal["x"][0], (x1 - cal["x"][1]) / cal["x"][0]]
    yr = [(y1 - cal["y"][1]) / cal["y"][0], (y0 - cal["y"][1]) / cal["y"][0]]
    return {"calibration": cal, "plot_box_px": box, "equation_box_px": eq, "line_width_px": width,
            "curve_cer_range": [lo, hi], "curve_range_sensitivity": range_sens, "tolerance_px": TOL, **scores, "controls": controls,
            "published_trace_px": int(pub.sum()), "our_trace_px": int((ours_mask & valid).sum()),
            "axes_data_range": {"x": xr, "y": yr}}


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def panel_b(src, sim, out_dir):
    im = Image.open(src).convert("RGB")
    ours_im, over = im.copy(), im.copy()
    a = np.asarray(im.convert("L")).astype(int)
    d_ours, d_over = ImageDraw.Draw(ours_im), ImageDraw.Draw(over)
    f = font(13)
    cells = {}
    for row, (r0, r1) in FIG1B_ROWS.items():
        res = sim["primary"][f"fig1b/{row}"]
        for col, (c0, c1) in FIG1B_COLS.items():
            sub = a[r0 + 3:r1 - 2, c0 + 3:c1 - 3] < 160
            ys, xs = np.nonzero(sub)
            bx0, bx1 = c0 + 3 + xs.min(), c0 + 3 + xs.max()
            by0, by1 = r0 + 3 + ys.min(), r0 + 3 + ys.max()
            text = f"{res[col]['power']:.2f} ({res[col]['auroc']:.2f})".replace("0.", ".")
            d_ours.rectangle([bx0 - 1, by0 - 1, bx1 + 1, by1 + 1], fill=(255, 255, 255))
            w = d_ours.textlength(text, font=f)
            cx = (bx0 + bx1) / 2
            d_ours.text((cx - w / 2, by0 - 1), text, fill=(0, 0, 0), font=f)
            d_over.text((cx - w / 2, by1 + 2), text, fill=GREEN, font=font(11))
            cells[f"{row}/{col}"] = {"text": text, "published_box_px": [int(bx0), int(bx1), int(by0), int(by1)]}
    ours_im.save(out_dir / "fig1b_ours.png", optimize=True)
    over.save(out_dir / "fig1b_overlay.png", optimize=True)
    return {"cells": cells}


def main(src, sim_path, out):
    out = Path(out)
    sim = json.load(open(sim_path))
    res = {"tolerance_px": TOL, "figures": {"fig1a": panel_a(src, out), "fig1b": panel_b(src, sim, out)}}
    (out / "figures.json").write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:4])
