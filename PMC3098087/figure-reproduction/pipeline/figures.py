#!/usr/bin/env python3
"""Draw our results on the published figures' own frames.

  figures.py DOWNLOADS published_values.json summary.csv OUTDIR PUBLISHED_DIR

For each figure: the published page is rasterized from the vector PDF and cropped to its panels
(PUBLISHED_DIR/<fig>.png); fig*_ours.png is that frame with each plot area cleared and our means
drawn at the published marker size and colour, through the panel's own axis map; fig*_overlay.png
is the published figure with our points on top in green. Interval figures (Fig. 6, Additional
file 10) also get our 2.5th-97.5th percentile bars.
"""

import json
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare as cmp  # noqa: E402

ZOOM = 2.0  # 144 dpi
GREEN = (0, 170, 60)
SOURCES = {
    "fig1": ("PMC3098087.1.pdf", 3), "fig2": ("PMC3098087.1.pdf", 4), "fig3": ("PMC3098087.1.pdf", 5),
    "fig4": ("PMC3098087.1.pdf", 7), "fig5": ("PMC3098087.1.pdf", 8), "fig6": ("PMC3098087.1.pdf", 9),
    "af4": ("1471-2105-11-523-S4.PDF", 0), "af5": ("1471-2105-11-523-S5.PDF", 0),
    "af7": ("1471-2105-11-523-S7.PDF", 0), "af9": ("1471-2105-11-523-S9.PDF", 1), "af8": ("1471-2105-11-523-S8.PDF", 0), "af10": ("1471-2105-11-523-S10.PDF", 0),
    "af11": ("1471-2105-11-523-S11.PDF", 0), "af12": ("1471-2105-11-523-S12.PDF", 0),
}
SERIES_COLOUR = {"PA": (255, 0, 0), "PA1": (208, 32, 144), "PA2": (0, 0, 255),
                 40: (255, 0, 0), 1000: (0, 0, 255), 10000: (255, 0, 255),
                 0.5: (255, 0, 0), 0.6: (0, 0, 255), 0.7: (255, 165, 0), 0.8: (0, 0, 0), 0.9: (255, 0, 255)}


def series_of(rec):
    if rec["figure"] in ("fig2", "fig3", "af4", "af5"):
        return rec["p"]
    if rec["figure"] in ("fig4", "af7"):
        return rec["k1train"]
    return rec["metric"]


def crop_of(recs, page):
    x0 = min(r["box"][0] for r in recs) - 45
    y0 = min(r["box"][1] for r in recs) - 30
    x1 = max(r["box"][2] for r in recs) + 12
    y1 = max(r["box"][3] for r in recs) + 32
    return pymupdf.Rect(max(x0, 0), max(y0, 0), min(x1, page.rect.x1), min(y1, page.rect.y1))


def raster(page, clip):
    pix = page.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), clip=clip, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def to_px(clip, x_pt, y_pt):
    return (x_pt - clip.x0) * ZOOM, (y_pt - clip.y0) * ZOOM


def inv(m, x, y):
    ax, bx, ay, by = m
    return (x - ax) / bx, (y - ay) / by


def disc(draw, cx, cy, r, colour, filled, width=2):
    box = [cx - r, cy - r, cx + r, cy + r]
    if filled:
        draw.ellipse(box, fill=colour)
    else:
        draw.ellipse(box, outline=colour, width=width)


def cross(draw, cx, cy, r, colour):
    draw.line([cx - r, cy - r, cx + r, cy + r], fill=colour, width=2)
    draw.line([cx - r, cy + r, cx + r, cy - r], fill=colour, width=2)


def draw_points(fig, recs, summary, clip, ours_img, over_img):
    do, dv = ImageDraw.Draw(ours_img), ImageDraw.Draw(over_img)
    for rec in recs:
        col = SERIES_COLOUR.get(series_of(rec), (0, 0, 0))
        filled = series_of(rec) not in ("PA1", "PA2") or fig in ("af8", "af9", "af11")
        prev = None
        for x, _y in rec["points"]:
            o = cmp.ours(summary, cmp.sim_key(rec, x), strict=False)
            if o is None or o["mean"] is None:
                prev = None
                continue
            px, py = inv(rec["map"], x, o["mean"])
            cx, cy = to_px(clip, px, py)
            if prev:
                do.line([prev, (cx, cy)], fill=col, width=1)
            prev = (cx, cy)
            disc(do, cx, cy, 3.4, col, filled)
            cross(dv, cx, cy, 3.4, GREEN)


def draw_fig6(recs, summary, clip, ours_img, over_img):
    do, dv = ImageDraw.Draw(ours_img), ImageDraw.Draw(over_img)
    for r in recs:
        key = (f"er_{r['center']}_{r['correction']}_neg{r['n_neg']}_pos{r['n_pos']}", "bal40", r["classifier"],
               cmp.MAP_ER[r["metric"]])
        o = cmp.ours(summary, key, strict=False)
        if o is None:
            continue
        ax, bx, ay, by = r["map"]
        px = (r["x_pos"] - ax) / bx
        col = (255, 0, 0) if r["correction"] == "multds" else (0, 0, 0)
        to_y = lambda v: (100 * v - ay) / by  # noqa: E731
        cx, cy = to_px(clip, px, to_y(o["mean"]))
        _, lo = to_px(clip, px, to_y(o["q025"]))
        _, hi = to_px(clip, px, to_y(o["q975"]))
        do.line([cx, lo, cx, hi], fill=col, width=2)
        disc(do, cx, cy, 4.0, col, r["metric"] == "PA_ER-")
        if r["metric"] == "PA_ER+":
            disc(do, cx, cy, 2.8, (255, 255, 255), True)
        dv.line([cx + 2, lo, cx + 2, hi], fill=GREEN, width=2)
        cross(dv, cx, cy, 3.4, GREEN)


def draw_af12(recs, summary, clip, ours_img, over_img):
    """Additional file 12: our 2.5th-97.5th percentile bars at each plotted bar's position."""
    do, dv = ImageDraw.Draw(ours_img), ImageDraw.Draw(over_img)
    for r in recs:
        key = (f"er_{r['center']}_{r['correction']}_neg{r['n_neg']}_pos{r['n_pos']}", "bal40", r["classifier"], cmp.MAP_ER[r["metric"]])
        o = cmp.ours(summary, key, strict=False)
        if o is None or o["q025"] is None:
            continue
        ax, bx, ay, by = r["map"]
        px = (r["x_pos"] - ax) / bx + (-0.9 if r["metric"] == "PA_ER+" else 0.9)
        col = (255, 0, 0) if r["correction"] == "multds" else (0, 0, 0)
        cx, lo = to_px(clip, px, (100 * o["q025"] - ay) / by)
        _, hi = to_px(clip, px, (100 * o["q975"] - ay) / by)
        _, cm = to_px(clip, px, (100 * o["mean"] - ay) / by)
        do.line([cx, lo, cx, hi], fill=col, width=1)
        disc(do, cx, cm, 1.6, col, r["metric"] == "PA_ER-")
        dv.line([cx + 1, lo, cx + 1, hi], fill=GREEN, width=1)


def draw_af10(recs, summary, clip, ours_img, over_img):
    do, dv = ImageDraw.Draw(ours_img), ImageDraw.Draw(over_img)
    for r in recs:
        name = {"none": "alt20", "over": "over", "down": "down", "multds": "multds"}[r["correction"]]
        for x, _lo, _hi in r["points"]:
            o = cmp.ours(summary, (f"{name}_p1000_k{cmp.kfmt(x)}", "bal20", r["classifier"], "PA"), strict=False)
            if o is None:
                continue
            px, py_lo = inv(r["map"], x, o["q025"])
            _, py_hi = inv(r["map"], x, o["q975"])
            _, py_m = inv(r["map"], x, o["mean"])
            cx, lo = to_px(clip, px, py_lo)
            _, hi = to_px(clip, px, py_hi)
            _, cm = to_px(clip, px, py_m)
            do.line([cx, lo, cx, hi], fill=(0, 0, 0), width=2)
            do.line([cx - 3, cm, cx + 3, cm], fill=(0, 0, 0), width=2)
            dv.line([cx + 2, lo, cx + 2, hi], fill=GREEN, width=2)


def main():
    dl, pub, summ, outdir, pubdir = Path(sys.argv[1]), json.load(open(sys.argv[2])), cmp.load_summary(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5])
    outdir.mkdir(parents=True, exist_ok=True)
    pubdir.mkdir(parents=True, exist_ok=True)
    made = {}
    for fig, (pdf, pno) in SOURCES.items():
        recs = [r for r in pub["figures"] if r["figure"] == fig]
        if not recs:
            continue
        page = pymupdf.open(dl / pdf)[pno]
        clip = crop_of(recs, page)
        published = raster(page, clip)
        published.save(pubdir / f"{fig}.png")
        ours = published.copy()
        d = ImageDraw.Draw(ours)
        for b in {tuple(r["box"]) for r in recs}:
            x0, y0 = to_px(clip, b[0], b[1])
            x1, y1 = to_px(clip, b[2], b[3])
            d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], fill=(255, 255, 255))
        over = published.copy()
        if fig == "fig6":
            draw_fig6(recs, summ, clip, ours, over)
        elif fig == "af10":
            draw_af10(recs, summ, clip, ours, over)
        elif fig == "af12":
            draw_af12(recs, summ, clip, ours, over)
        else:
            draw_points(fig, recs, summ, clip, ours, over)
        ours.save(outdir / f"{fig}_ours.png")
        over.save(outdir / f"{fig}_overlay.png")
        made[fig] = {"published": f"published/{fig}.png", "ours": f"output/{fig}_ours.png",
                     "overlay": f"output/{fig}_overlay.png", "size": list(published.size), "dpi": 72 * ZOOM}
    json.dump(made, open(outdir / "figures.json", "w"), indent=1)
    print(", ".join(made))


if __name__ == "__main__":
    main()
