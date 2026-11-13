"""Draw our Figs 1b, 1c, 2 and 3 on the published pixel grids, overlay them, and score Fig. 1c.

  figures.py PUBLISHED_DIR RUN_DIR DOWNLOADS OUTDIR

Each figure is drawn on a copy of the published image (published ink removed inside the panels,
fig*_ours.png) and over the published image (fig*_overlay.png: published ink grey, ours in its own
colour). Fig. 1c (binding against coupling, three TFs) is scored by pixels: the share of the
published B+/C+ (red) and B+/C- (green) marker pixels that have a marker of the same colour of ours
within the tolerance, and the reverse. Controls: the other two TFs' points drawn on the panel
(wrong input), and our coupling scaled by 0.9 and 1.1 (near miss). Scores go to figures.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import validate

TOL = 2  # px; the published figure 1 is about 160 dpi (1140 px over 7.2 in)
RED = (255, 0, 0)
GREEN = (0, 128, 0)
BLUE = (0, 0, 255)

# Fig. 1 panel geometry, measured on published/figure-1.png (axes lines and tick labels).
# Fig. 1c: x0 = pixel of binding 0, px per binding unit; y0 = pixel of coupling 0, px per unit.
FIG1C = {
    "Hap4": {"x0": 846, "sx": 57.25, "y0": 941, "box": (760, 852, 989, 1008)},
    "Ndd1": {"x0": 847, "sx": 39.17, "y0": 1151, "box": (769, 1062, 1004, 1218)},
    "Ste12": {"x0": 847, "sx": 23.4, "y0": 1361, "box": (753, 1272, 987, 1428)},
}
FIG1C_SY = 111.25  # px per coupling unit (0.8 at the top of each y axis)
# Fig. 1b: x-axis row, x range of the bars, px per activity unit (10 at the top of a 59 px half axis)
FIG1B = {"Hap4": {"y0": 942}, "Ndd1": {"y0": 1149}, "Ste12": {"y0": 1363}}
FIG1B_X = (368, 601)
FIG1B_SY = 5.9
FIG1B_GROUPS = [("stress", "Gasch_2000", RED), ("pheromone", "Roberts_2000", GREEN), ("cell cycle", "Spellman_1998", BLUE)]


def masks(im):
    a = np.asarray(im.convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 170) & (g < 100) & (b < 100)
    green = (g > 80) & (r < 90) & (b < 90) & (g > r + 40)
    blue = (b > 150) & (r < 90) & (g < 90)
    dark = (r + g + b) < 200
    return red, green, blue, dark


def two_way(pub, ours, tol=TOL):
    """Share of published pixels within tol of ours, and of ours within tol of published."""
    if pub.sum() == 0 or ours.sum() == 0:
        return 0.0, 0.0
    d_ours = ndimage.distance_transform_edt(~ours)
    d_pub = ndimage.distance_transform_edt(~pub)
    return float((d_ours[pub] <= tol).mean()), float((d_pub[ours] <= tol).mean())


def cross(draw, x, y, colour, size=3):
    draw.line([(x - size, y), (x + size, y)], fill=colour, width=2)
    draw.line([(x, y - size), (x, y + size)], fill=colour, width=2)


def draw_scatter(canvas, box, geo, b, c, cls, scale=1.0):
    """Points (binding log2 ratio b, coupling r c, class) as crosses, clipped to the panel box."""
    d = ImageDraw.Draw(canvas)
    x1, y1, x2, y2 = box
    order = [(0, (0, 0, 0)), (2, GREEN), (1, RED)]
    for k, col in order:
        sel = (cls == k) & np.isfinite(b) & np.isfinite(c)
        for bb, cc in zip(b[sel], c[sel] * scale):
            x = geo["x0"] + bb * geo["sx"]
            y = geo["y0"] - cc * FIG1C_SY
            if x1 <= x <= x2 and y1 <= y <= y2:
                cross(d, round(x), round(y), col)


def blank_panel(im, box, pad=0):
    """Copy of im with the panel's coloured and black ink removed (axes kept)."""
    out = im.copy()
    a = np.asarray(out).copy()
    x1, y1, x2, y2 = box
    sub = a[y1 - pad:y2 + pad + 1, x1 - pad:x2 + pad + 1]
    red, green, blue, dark = masks(Image.fromarray(sub))
    ink = red | green | blue | dark
    sub[ink] = 255
    a[y1 - pad:y2 + pad + 1, x1 - pad:x2 + pad + 1] = sub
    return Image.fromarray(a)


def fig1(published, R, tfap, out):
    pub = Image.open(published / "figure-1.png").convert("RGB")
    genes = [str(g) for g in R["genes"]]
    tfs = [str(t) for t in R["tfs"]]
    scores = {}
    ours = pub.copy()
    over = Image.fromarray(np.where(np.stack([masks(pub)[3] | masks(pub)[0] | masks(pub)[1] | masks(pub)[2]] * 3, -1), 170, 255).astype(np.uint8))
    # Fig. 1c
    for t, geo in FIG1C.items():
        j = tfs.index(t)
        b, c, cls = R["lee_logratio"][:, j].astype(float), R["r"][:, j].astype(float), R["classes"][:, j]
        ours = blank_panel(ours, geo["box"])
        # put the axes back
        x1, y1, x2, y2 = geo["box"]
        ao, ap = np.asarray(ours).copy(), np.asarray(pub)
        ao[geo["y0"] - 1:geo["y0"] + 2, x1:x2 + 1] = ap[geo["y0"] - 1:geo["y0"] + 2, x1:x2 + 1]
        ao[y1:y2 + 1, geo["x0"] - 1:geo["x0"] + 2] = ap[y1:y2 + 1, geo["x0"] - 1:geo["x0"] + 2]
        ours = Image.fromarray(ao)
        draw_scatter(ours, geo["box"], geo, b, c, cls)
        draw_scatter(over, geo["box"], geo, b, c, cls)

        def score(bb, cc, kk, scale=1.0):
            canvas = Image.new("RGB", pub.size, "white")
            draw_scatter(canvas, geo["box"], geo, bb, cc, kk, scale)
            x1, y1, x2, y2 = geo["box"]
            pr, pg, _, _ = masks(pub.crop((x1, y1, x2 + 1, y2 + 1)))
            orr, og, _, _ = masks(canvas.crop((x1, y1, x2 + 1, y2 + 1)))
            a1, b1 = two_way(pr, orr)
            a2, b2 = two_way(pg, og)
            npub, nours = pr.sum() + pg.sum(), orr.sum() + og.sum()
            pn = (a1 * pr.sum() + a2 * pg.sum()) / max(npub, 1)
            on = (b1 * orr.sum() + b2 * og.sum()) / max(nours, 1)
            return round(pn, 4), round(on, 4)

        s = score(b, c, cls)
        controls = []
        for other in FIG1C:
            if other == t:
                continue
            k = tfs.index(other)
            sc = score(R["lee_logratio"][:, k].astype(float), R["r"][:, k].astype(float), R["classes"][:, k])
            controls.append({"name": f"{other} points on the {t} panel", "kind": "wrong_input", "score": min(sc)})
        for f in (0.9, 1.1):
            sc = score(b, c, cls, f)
            controls.append({"name": f"coupling x{f}", "kind": "near_miss", "score": min(sc)})
        scores[f"fig1c.{t}"] = {"published_near_ours": s[0], "ours_near_published": s[1], "controls": controls,
                                "tolerance_px": TOL}
    # Fig. 1b: our profiles, each group spread evenly over the x span of its published colour
    pr, pg, pb, _ = masks(pub)
    for t, geo in FIG1B.items():
        y0 = geo["y0"]
        band = slice(y0 - 62, y0 + 62)
        spans = []
        for m in (pr, pg, pb):
            xs = np.nonzero(m[band, FIG1B_X[0]:FIG1B_X[1] + 1].any(0))[0] + FIG1B_X[0]
            spans.append((int(xs.min()), int(xs.max())) if xs.size else None)
        box = (FIG1B_X[0], y0 - 58, FIG1B_X[1], y0 + 52)
        ours = blank_panel(ours, (box[0], box[1], box[2], y0 - 2))
        ours = blank_panel(ours, (box[0], y0 + 2, box[2], box[3]))
        for canvas in (ours, over):
            d = ImageDraw.Draw(canvas)
            for (gname, src, col), span in zip(FIG1B_GROUPS, spans):
                vals = [float(r[t]) for r in tfap if r["source"] == src]
                if not span or not vals:
                    continue
                xs = np.linspace(span[0], span[1], len(vals))
                for x, v in zip(xs, vals):
                    v = max(-10, min(10, v))
                    d.line([(round(x), y0), (round(x), round(y0 - v * FIG1B_SY))], fill=col, width=1)
        scores[f"fig1b.{t}"] = {"spans_px": spans}
    ours.save(out / "fig1_ours.png")
    over.save(out / "fig1_overlay.png")
    return scores


def fig2(published, downloads, go, out):
    pub = Image.open(published / "figure-2.jpg").convert("RGB")
    a = np.asarray(pub).astype(int)
    red, green, _, dark = masks(pub)
    base = int(np.nonzero(dark.sum(1) > 800)[0][0])
    eps = validate.read_fig2_eps(Path(downloads) / "moesm2.eps")
    # map EPS x to image x from the visible red bars (heights above 1 count), in order
    yb = base - 3
    def runs(m):
        r, s = [], None
        for x in range(m.size):
            if m[x] and s is None:
                s = x
            if not m[x] and s is not None:
                r.append((s, x - 1))
                s = None
        return r
    text = open(Path(downloads) / "moesm2.eps", encoding="latin-1").read()
    import re
    xt = sorted({int(m.group(1)) for m in re.finditer(r"^(\d+) 6773 m  \1 6694 l  ps", text, re.M)})
    slot_px = [(xt[k] + xt[k + 1]) / 2 for k in range(len(xt) - 1)]
    vis = [k for k, h in enumerate(eps["red_raw"]) if h is not None and h > 1]
    rr = runs(red[yb])
    if len(rr) != len(vis):
        raise SystemExit(f"Fig. 2: {len(rr)} red bars in the image, {len(vis)} in the EPS")
    cx = np.polyfit([slot_px[k] for k in vis], [(s + e) / 2 for s, e in rr], 1)
    # y scale from the tallest unclipped bar heights
    tops = []
    for (s, e), k in zip(rr, vis):
        col = red[:base, (s + e) // 2]
        tops.append((eps["red_raw"][k], base - int(np.nonzero(col)[0].min())))
    hs = np.array([t for t in tops if t[0] < 59.5])
    sy = float(np.polyfit(hs[:, 0], hs[:, 1], 1)[0])
    width = np.mean([e - s + 1 for s, e in rr])
    offset = np.mean([((s + e) / 2) for (s, e) in runs(green[yb])][:1]) - np.polyval(cx, slot_px[0]) if runs(green[yb]) else width
    ours = pub.copy()
    ao = np.asarray(ours).copy()
    panel = (slice(0, base), slice(int(np.polyval(cx, slot_px[0]) - width), int(np.polyval(cx, slot_px[-1]) + 2 * width)))
    ink = (a.sum(2) < 735)[panel]
    sub = ao[panel]
    sub[ink] = 255
    ao[panel] = sub
    ours = Image.fromarray(ao)
    over = Image.fromarray(np.where(np.stack([red | green | dark] * 3, -1), 175, 255).astype(np.uint8))
    tfs = go["tfs"]
    gap = 10.0  # px between the red and green bar of one TF in the published image
    for canvas in (ours, over):
        d = ImageDraw.Draw(canvas)
        for k, t in enumerate(tfs):
            o = go["ours"].get(t)
            if not o:
                continue
            xc = np.polyval(cx, slot_px[k])
            for val, col, dx in ((o["B+/C+"]["bonferroni"], RED, 0), (o["B+/C-"]["bonferroni"], GREEN, gap)):
                h = min(val, 61) * sy
                x1 = round(xc + dx - width / 2)
                d.rectangle([x1, round(base - max(h, 1)), x1 + round(width) - 1, base - 1], fill=col, outline=(0, 0, 0))
    ours.save(out / "fig2_ours.png")
    over.save(out / "fig2_overlay.png")
    return {"baseline_px": base, "px_per_count": round(sy, 3), "x_fit": [round(float(v), 5) for v in cx]}


def fig3(published, div, out):
    pub = Image.open(published / "figure-3.png").convert("RGB")
    a = np.asarray(pub).astype(int)
    dark = a.sum(2) < 300
    # approximate windows of the eight printed scores (x1, y1, x2, y2), in FIG3 order
    win = [(820, 65, 880, 100), (395, 60, 442, 95), (395, 280, 480, 310), (832, 280, 870, 310),
           (395, 490, 480, 520), (820, 490, 885, 520), (395, 620, 446, 650), (832, 620, 870, 650)]
    ours = pub.copy()
    over = pub.copy()
    font = ImageFont.truetype(_font(), 20)
    dr_o, dr_v = ImageDraw.Draw(ours), ImageDraw.Draw(over)
    for (x1, y1, x2, y2), row in zip(win, div["fig3"]):
        m = dark[y1:y2, x1:x2]
        ys, xs = np.nonzero(m)
        if not xs.size:
            continue
        bx1, by1, bx2, by2 = x1 + xs.min(), y1 + ys.min(), x1 + xs.max(), y1 + ys.max()
        # leave the X marks of the arrows: text is the part right or left of them; blank the box
        dr_o.rectangle([bx1, by1, bx2, by2], fill="white")
        v = row.get("neglog10_p_one_sided")
        txt = "n/a" if v is None else (">12.0" if v > 12 else f"{v:.1f}")
        dr_o.text((bx1, by1 - 2), txt, fill=RED, font=font)
        dr_v.text((bx1, by2 + 2), txt, fill=RED, font=font)
    ours.save(out / "fig3_ours.png")
    over.save(out / "fig3_overlay.png")


def _font():
    import matplotlib
    return str(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSerif.ttf")


def main(published, run_dir, downloads, outdir):
    published, out = Path(published), Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    R = validate.load_run(run_dir)
    import csv
    with open(Path(run_dir) / "tfap.tsv", encoding="utf-8") as f:
        tfap = list(csv.DictReader(f, delimiter="\t"))
    go = json.load(open(Path(run_dir) / "go.json"))
    div = json.load(open(Path(run_dir) / "divergent.json"))
    res = {"fig1": fig1(published, R, tfap, out), "fig2": fig2(published, downloads, go, out)}
    fig3(published, div, out)
    (out / "figures.json").write_text(json.dumps(res, indent=1) + "\n")
    print("figures done")


if __name__ == "__main__":
    main(*sys.argv[1:5])
