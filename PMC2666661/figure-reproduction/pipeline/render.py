"""Draw our results on the published figures' own pixel grids.

  render.py SOURCES_DIR PUBLISHED_VALUES.json SUMMARY.json OUTDIR

For each figure, fig<N>_ours.png is the published figure with the plotted data replaced by ours
(bars, error bars or curves at the published positions, in the published colours, through the axis
calibration read by read_published.py), and fig<N>_overlay.png puts the two together: the red
channel is the published figure and the green and blue channels are ours, so ink only in the paper
is cyan, ink only in ours is red, and ink in both is black.
"""

import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

from series import bar_series, curve_series

HATCH_STEP = 4


def _fill_colour(img, xl, xr, baseline):
    """Median colour of the published bar just above the baseline; hatched if mostly white."""
    cols = np.arange(int(np.ceil(xl + 2)), int(np.floor(xr - 2)) + 1)
    patch = img[int(baseline) - 12:int(baseline) - 3, cols].reshape(-1, 3)
    white = (patch.min(axis=1) > 225)
    hatched = white.mean() > 0.3
    ink = patch[~white] if (~white).any() else patch
    return tuple(int(v) for v in np.median(ink, axis=0)), hatched


def render_bars(src, pub, values, errors, path_ours, path_overlay):
    img = np.asarray(Image.open(src).convert("RGB"))
    a, base = pub["row_per_unit"], pub["baseline_row"]
    canvas = Image.fromarray(img.copy())
    draw = ImageDraw.Draw(canvas)
    k = 0
    fills = []
    for g, vals in enumerate(pub["values"]):
        for j, _ in enumerate(vals):
            xl, xr, _top = pub["bars_px"][k]
            fills.append(_fill_colour(img, xl, xr, base))
            k += 1
    # clear the published bars and their error bars: the bar columns from the plot top to the baseline
    plot_top = int(min(pub["tick_rows"])) + 2
    k = 0
    for g, vals in enumerate(pub["values"]):
        for j, _ in enumerate(vals):
            xl, xr, _ = pub["bars_px"][k]
            draw.rectangle([int(np.floor(xl)), plot_top, int(np.ceil(xr)), int(base) - 1], fill=(255, 255, 255))
            k += 1
    # restore the legend (masks) from the published image
    for (mx0, mx1, my1) in pub.get("masks", []):
        canvas.paste(Image.fromarray(img[plot_top:my1 + 1, mx0:mx1]), (mx0, plot_top))
    k = 0
    for g, vals in enumerate(values):
        for j, v in enumerate(vals):
            xl, xr, _ = pub["bars_px"][k]
            colour, hatched = fills[k]
            k += 1
            if v is None:
                continue
            top = base + a * v
            box = [xl, top, xr, base]
            if hatched:
                draw.rectangle(box, fill=(255, 255, 255))
                x = xl - (base - top)
                while x < xr:
                    # 45-degree hatch, clipped to the bar
                    p0 = (x, base)
                    p1 = (x + (base - top), top)
                    pts = _clip_line(p0, p1, xl, xr, top, base)
                    if pts:
                        draw.line(pts, fill=colour, width=1)
                    x += HATCH_STEP
            else:
                draw.rectangle(box, fill=colour)
            draw.rectangle(box, outline=(60, 60, 60), width=1)
            e = errors[g][j] if errors is not None else None
            if e:
                xc = (xl + xr) / 2
                y0, y1 = base + a * (v + e), base + a * (v - e)
                draw.line([(xc, y0), (xc, y1)], fill=(0, 0, 0), width=1)
                draw.line([(xc - 3, y0), (xc + 3, y0)], fill=(0, 0, 0), width=1)
                draw.line([(xc - 3, y1), (xc + 3, y1)], fill=(0, 0, 0), width=1)
    canvas.save(path_ours)
    _overlay(img, np.asarray(canvas), path_overlay)


def _clip_line(p0, p1, x0, x1, y0, y1):
    (ax, ay), (bx, by) = p0, p1
    t0, t1 = 0.0, 1.0
    dx, dy = bx - ax, by - ay
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if p == 0:
            if q < 0:
                return None
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
    if t0 > t1:
        return None
    return [(ax + t0 * dx, ay + t0 * dy), (ax + t1 * dx, ay + t1 * dy)]


def _overlay(pub, ours, path):
    g1 = pub.mean(axis=2)
    g2 = np.asarray(ours).mean(axis=2)
    out = np.stack([g1, g2, g2], axis=2).clip(0, 255).astype(np.uint8)
    Image.fromarray(out).save(path)


RCOL = {"black": (0, 0, 0), "grey": (190, 190, 190), "green": (0, 255, 0), "green4": (0, 139, 0),
        "blue": (0, 0, 255), "darkblue": (0, 0, 139), "purple": (160, 32, 240), "orange": (255, 165, 0),
        "orange4": (139, 90, 0), "darkred": (139, 0, 0), "red": (255, 0, 0)}


def render_curves(src, pub, series_by_panel, path_ours, path_overlay):
    img = np.asarray(Image.open(src).convert("RGB"))
    canvas = Image.fromarray(img.copy())
    draw = ImageDraw.Draw(canvas)
    for panel, series in zip(pub["panels"], series_by_panel):
        top, bottom, left, right = panel["box"]
        px = panel["px"]
        legend = panel.get("legend_box_px")
        draw.rectangle([left + 2, top + 2, right - 2, bottom - 2], fill=(255, 255, 255))
        if legend:
            x0, y0, x1, y1 = legend
            canvas.paste(Image.fromarray(img[y0:y1, x0:x1]), (x0, y0))
        for name, colour, xs, ys in series:
            pts = [(px["ax"] * x + px["bx"], px["ay"] * y + px["by"]) for x, y in zip(xs, ys)]
            pts = [(min(max(u, left + 2), right - 2), min(max(v, top + 2), bottom - 2)) for u, v in pts]
            if len(pts) > 1:
                draw.line(pts, fill=RCOL[colour], width=2)
    canvas.save(path_ours)
    _overlay(img, np.asarray(canvas), path_overlay)


def main():
    src, pubp, summp, outdir = sys.argv[1:5]
    os.makedirs(outdir, exist_ok=True)
    pub = json.load(open(pubp))
    summ = json.load(open(summp))
    for fig in ("fig1", "fig2", "fig4", "fig5"):
        vals, errs = bar_series(fig, summ)
        render_bars(os.path.join(src, pub[fig]["file"]), pub[fig], vals, errs,
                    os.path.join(outdir, f"{fig}_ours.png"), os.path.join(outdir, f"{fig}_overlay.png"))
    for fig in ("fig3", "fig6"):
        series = curve_series(fig, summ, pub[fig])
        render_curves(os.path.join(src, pub[fig]["file"]), pub[fig], series,
                      os.path.join(outdir, f"{fig}_ours.png"), os.path.join(outdir, f"{fig}_overlay.png"))


if __name__ == "__main__":
    main()
