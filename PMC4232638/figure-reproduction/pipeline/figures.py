"""Draw our numbers on copies of the published figures (Figs 1-4) and write the overlays.

Usage: figures.py PUBLISHED_DIR FIGURES.json ANALYSIS.json COMBINATIONS.npz FIG1_READING.json XLSX OUT_DIR

PUBLISHED_DIR holds figure-1.png ... figure-4.png (the article PDF rendered at 300 dpi by
render_published.py) and frames.json. FIGURES.json is read_figures.py's reading of the vector drawing:
the axes boxes and their calibration, the bar positions, the dendrograms. Every figure of ours is drawn on
a copy of the published picture: inside each plot the published marks are painted over with white and
ours are drawn at the published positions, with the published axes, colours and line widths. So ours is
on the published frame by construction (layout drawn_on_published).

fig*_ours.png      our figure
fig*_overlay.png   the published figure with ours drawn on top in red (outlines of our bars, our
                   whiskers, lines and dendrogram)
figures.json       per figure: what was drawn, the points of ours outside the published axis limits.
Drawn with Pillow only (no anti-aliasing), so a rerun gives the same pixels.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from data import META, PRED, SINGLE, load, snvs  # noqa: F401  (load used for Fig. 1)

RED = (230, 0, 60)
WHITE = (255, 255, 255)
BLACK = (6, 7, 5)
STATS = ["accuracy", "sensitivity", "specificity", "ppv", "npv", "composite"]
BLUE, ORANGE, COMBO = (68, 76, 169), (248, 164, 0), (235, 70, 64)


class Frame:
    def __init__(self, info):
        self.s = info["dpi"] / 72
        self.ox, self.oy = info["origin_pt"]

    def x(self, pt):
        return round((pt - self.ox) * self.s)

    def y(self, pt):
        return round((pt - self.oy) * self.s)

    def w(self, pt):
        return max(1, round(pt * self.s))


def ycal(ax):
    """Value -> y (pt) for an axes record (linear between its top and bottom)."""
    t, b, vt, vb = ax["top"], ax["bottom"], ax["value_at_top"], ax["value_at_bottom"]
    return lambda v: b + (v - vb) * (t - b) / (vt - vb)


def scale(stat, v):
    return v


def draw_bar_panels(img, ov, fr, panels, outside, whiten=True):
    """panels: list of (axes record, [published bar records], [(value, low, high, colour)])."""
    d, do = ImageDraw.Draw(img), ImageDraw.Draw(ov)
    for ax, bars, ours in panels:
        y = ycal(ax)
        lo_v, hi_v = sorted((ax["value_at_bottom"], ax["value_at_top"]))
        right = max((b["x1"] or b["x0"] + 4.8) for b in bars) + 1.2
        if whiten:
            d.rectangle([fr.x(ax["spine_x"] + 0.4), fr.y(ax["top"] - 4), fr.x(right), fr.y(ax["bottom"]) - 1], fill=WHITE)
        for b, (v, lo, hi, colour) in zip(bars, ours):
            x0 = b["x0"]
            x1 = b["x1"] if b["x1"] else x0 + 4.83
            cx = (x0 + x1) / 2
            for val in (v, lo, hi):
                if val is not None and not np.isnan(val) and not (lo_v - 1e-9 <= val <= hi_v + 1e-9):
                    outside.append(val)
            if v is not None and not np.isnan(v):
                vv = min(max(v, lo_v), hi_v)
                top = fr.y(y(vv))
                if top < fr.y(ax["bottom"]):
                    d.rectangle([fr.x(x0), top, fr.x(x1) - 1, fr.y(ax["bottom"]) - 1], fill=colour)
                bot = fr.y(ax["bottom"]) - 1
                if top <= bot:
                    do.rectangle([fr.x(x0), top, fr.x(x1) - 1, bot], outline=RED, width=2)
                else:
                    do.line([fr.x(x0), bot, fr.x(x1) - 1, bot], fill=RED, width=2)
            if lo is not None and hi is not None and not (np.isnan(lo) or np.isnan(hi)):
                ylo, yhi = fr.y(y(min(max(lo, lo_v), hi_v))), fr.y(y(min(max(hi, lo_v), hi_v)))
                cap = (x1 - x0) * 0.25
                for dd, col in ((d, BLACK), (do, RED)):
                    dd.line([fr.x(cx), ylo, fr.x(cx), yhi], fill=col, width=fr.w(0.604))
                    dd.line([fr.x(cx - cap), ylo, fr.x(cx + cap), ylo], fill=col, width=fr.w(0.604))
                    dd.line([fr.x(cx - cap), yhi, fr.x(cx + cap), yhi], fill=col, width=fr.w(0.604))


def fig2(pub_dir, frames, figs, ours, out, key="fig2", src="figure-2.png", tables=None):
    """Fig. 2, or Additional file 15 (key af15, tables: oncogenes and tumour suppressor genes)."""
    img = Image.open(pub_dir / src).convert("RGB")
    ov = img.copy()
    fr = Frame(frames[key])
    outside, panels = [], []
    tables = tables or (ours["table3"], ours["table4"])
    for panel, table in zip(("a", "b"), tables):
        for k in STATS:
            sub = figs[key][panel][k]
            vals = []
            for b in sub["bars"]:
                r = table[b["name"]][k]
                colour = BLUE if b["name"] in SINGLE else ORANGE
                vals.append((r["value"], r["low"], r["high"], colour))
            panels.append((sub["axes"], sub["bars"], vals))
    draw_bar_panels(img, ov, fr, panels, outside)
    img.save(out / f"{key}_ours.png")
    ov.save(out / f"{key}_overlay.png")
    return {"outside_axis": len(outside), "size": list(img.size)}


def font(px):
    import matplotlib
    return ImageFont.truetype(str(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"), px)


def fig3(pub_dir, frames, figs, ours, arr, out, key="fig3", src="figure-3.png", by="composite"):
    """Fig. 3, or Additional file 20 (key af20, ranked by accuracy)."""
    img = Image.open(pub_dir / src).convert("RGB")
    ov = img.copy()
    fr = Frame(frames[key])
    outside, panels, legends, marks = [], [], {}, []
    for panel, dkey, sub, table in (("a", "all", "subset1", ours["table3"]), ("b", "all", "subset2", ours["table3"]),
                                    ("c", "non_cosmic", "subset1", ours["table4"]), ("d", "non_cosmic", "subset2", ours["table4"])):
        names = list(arr[f"{dkey}|names"])
        top5 = [t["name"] for t in ours["combinations"][dkey]["run1"]["top5"][f"{sub}/{by}"]]
        best_s = max(SINGLE, key=lambda p: table[p][by]["value"])
        best_m = max(META, key=lambda p: table[p][by]["value"])
        legends[panel] = top5 + [best_s, best_m]
        for k in STATS:
            fp = figs[key][panel][k]
            vals = []
            for nm in top5:
                i = names.index(nm)
                vals.append(tuple(float(arr[f"{dkey}|run1|{sub}|{k}|{part}"][i]) for part in ("mean", "low", "high")) + (COMBO,))
            for p, colour in ((best_s, BLUE), (best_m, ORANGE)):
                r = table[p][k]
                vals.append((r["value"], r["low"], r["high"], colour))
            panels.append((fp["axes"], fp["bars"], vals))
            if "markers" in fp:
                marks.append((fp, vals))
        # The legend under the panel: ours, in the published place and size.
        x0, t, x1, b = figs[key][panel]["legend_box"]
        step = (b - t) / 5
        ImageDraw.Draw(img).rectangle([fr.x(x0) - 2, fr.y(t - step), fr.x(x1 + 0.3 * (x1 - x0)), fr.y(b) + 2], fill=WHITE)
        f = font(max(4, round(fr.s * step * 0.8)))
        for j, nm in enumerate(top5):
            ImageDraw.Draw(img).text((fr.x(x0), fr.y(t + j * step)), f"#{j + 1}: {nm}", fill=BLACK, font=f)
    draw_bar_panels(img, ov, fr, panels, outside)
    # Significance marks of ours where the paper draws its own (painted over first): blue, the low end of
    # the combination's interval reaches the high end of the best single predictor's; orange, of the best
    # meta-predictor's (bars 6 and 7).
    d = ImageDraw.Draw(img)
    for fp, vals in marks:
        m = fp["markers"]
        size = (m["size"] or [2.5])[0]
        rows = {k: (v[0] if v else None) for k, v in m["rows_top"].items()}
        top_all = min(v for v in rows.values() if v is not None) if any(rows.values()) else fp["axes"]["top"] - 8
        x_left = fp["bars"][0]["x0"]
        x_right = fp["bars"][4]["x1"] or fp["bars"][4]["x0"] + 4.83
        d.rectangle([fr.x(x_left) - 4, fr.y(top_all) - 4, fr.x(x_right) + 4, fr.y(fp["axes"]["top"]) - 2], fill=WHITE)
        for j in range(5):
            b = fp["bars"][j]
            cx = (b["x0"] + (b["x1"] or b["x0"] + 4.83)) / 2
            for kind, ref_j, colour in (("vs best single", 5, (68, 66, 164)), ("vs best meta", 6, (254, 181, 58))):
                if rows.get(kind) is None or not (vals[j][1] >= vals[ref_j][2]):
                    continue
                t = rows[kind]
                if m["shape"] == "triangle":
                    pts = [(fr.x(cx - size / 2), fr.y(t + size)), (fr.x(cx + size / 2), fr.y(t + size)), (fr.x(cx), fr.y(t))]
                else:
                    import math
                    pts = [(fr.x(cx + (size / 2 if q % 2 == 0 else size / 5) * math.sin(q * math.pi / 5)),
                            fr.y(t + size / 2 - (size / 2 if q % 2 == 0 else size / 5) * math.cos(q * math.pi / 5))) for q in range(10)]
                d.polygon(pts, fill=colour)
    img.save(out / f"{key}_ours.png")
    ov.save(out / f"{key}_overlay.png")
    return {"outside_axis": len(outside), "size": list(img.size), "legends": legends}


def fig4(pub_dir, frames, figs, ours, out, key="fig4", src="figure-4.png", by="composite"):
    """Fig. 4, or Additional file 23 (key af23, ranked by accuracy)."""
    img = Image.open(pub_dir / src).convert("RGB")
    ov = img.copy()
    fr = Frame(frames[key])
    d, do = ImageDraw.Draw(img), ImageDraw.Draw(ov)
    outside = 0
    for panel, dkey in (("a", "all"), ("b", "non_cosmic")):
        for sub in ("subset1", "subset2"):
            p = figs[key][panel][sub]
            ax = p["axes"]
            x0, t, x1, b = ax["frame"]
            d.rectangle([fr.x(x0) + 2, fr.y(t) + 2, fr.x(x1) - 2, fr.y(b) - 2], fill=WHITE)
            y = ycal(ax)
            rec = ours["combinations"][dkey]["run1"]["recurrence"][f"{sub}/{by}"]
            for name in SINGLE:
                c = p["colours"][name]
                if len(c) == 4:  # CMYK in the supplement PDFs
                    c = [(1 - c[0]) * (1 - c[3]), (1 - c[1]) * (1 - c[3]), (1 - c[2]) * (1 - c[3])]
                col = tuple(round(255 * v) for v in c)
                pts = [(fr.x(x), fr.y(y(rec[str(tp)][name]))) for x, tp in zip(ax["category_x"], (10, 20, 50, 100))]
                outside += sum(not (-1e-9 <= rec[str(tp)][name] <= 100 + 1e-9) for tp in (10, 20, 50, 100))
                d.line(pts, fill=col, width=fr.w(0.915))
                do.line(pts, fill=RED, width=max(1, fr.w(0.915) // 2))
    img.save(out / f"{key}_ours.png")
    ov.save(out / f"{key}_overlay.png")
    return {"outside_axis": outside, "size": list(img.size)}


KAPPA_KEY = [(0, (1, 0.984, 0.875)), (0.2, (0.969, 0.898, 0.2)), (0.4, (0.976, 0.847, 0)), (0.6, (0.965, 0.624, 0)),
             (0.8, (0.925, 0.345, 0.008)), (9, (0.878, 0.18, 0.071))]
CALL_RGB = {1.0: (68, 76, 169), 0.0: (248, 164, 0), "nan": (236, 236, 236)}
TYPE_RGB = {"Oncogene": (130, 126, 125), "New cancer gene": (24, 23, 22), "Tumor suppressor": (188, 185, 185)}


def kappa_rgb(k):
    for hi, c in KAPPA_KEY:
        if k <= hi:
            return tuple(round(255 * v) for v in c)


def fig1(pub_dir, frames, figs, ours, reading, rows_all, out):
    """Kappa heat maps: our bin colour in each cell. Call heat maps: our calls, rows in the published
    order, SNVs in the order of a lexicographic sort of their calls (the published column order comes
    from a clustering of the 3,591 SNVs that we do not compare), and the gene-class bar in the same order.
    Dendrograms: ours, drawn with the root at the published root and heights to scale."""
    import mutbench as mb
    img = Image.open(pub_dir / "figure-1.png").convert("RGB")
    ov = img.copy()
    fr = Frame(frames["fig1"])
    d, do = ImageDraw.Draw(img), ImageDraw.Draw(ov)
    place = figs["fig1"]["image"]
    sx = (place["x1"] - place["x0"]) / place["size"][0]
    sy = (place["bottom"] - place["top"]) / place["size"][1]
    ipt = lambda ix, iy: (place["x0"] + ix * sx, place["top"] + iy * sy)
    boxes = figs["fig1"]["boxes"]
    sets = {"a": [r for r in rows_all if r["snv"]], "c": [r for r in rows_all if r["snv"] and r["cosmic"] is None]}
    for panel, kpanel, kkey in (("a", "b", "all"), ("c", "d", "non_cosmic")):
        order = reading[panel]["rows"]
        # Kappa cells.
        x0, x1, y0, y1 = boxes[kpanel]
        w, h = (x1 - x0 + 1) / 15, (y1 - y0 + 1) / 15
        for j, a in enumerate(order):
            for i, b in enumerate(order):
                p0 = ipt(x0 + i * w, y0 + j * h)
                p1 = ipt(x0 + (i + 1) * w, y0 + (j + 1) * h)
                rgb = kappa_rgb(ours["kappa"][kkey][a][b][0])
                d.rectangle([fr.x(p0[0]), fr.y(p0[1]), fr.x(p1[0]) - 1, fr.y(p1[1]) - 1], fill=rgb)
                if figs["fig1"][kpanel]["cells"][j][i]["bin"] != _bin(ours["kappa"][kkey][a][b][0]):
                    do.rectangle([fr.x(p0[0]), fr.y(p0[1]), fr.x(p1[0]) - 1, fr.y(p1[1]) - 1], outline=RED, width=3)
        # Call heat map and gene-class bar.
        rows = sets[panel]
        M = np.array([mb.binary_calls(r["cat"][p] for r in rows) for p in order])
        key = np.where(np.isnan(M), 0.5, M)
        cols = np.lexsort(key[::-1])
        rgb = np.zeros((15, len(rows), 3), dtype=np.uint8)
        for j in range(15):
            for i, c in enumerate(cols):
                v = M[j, c]
                rgb[j, i] = CALL_RGB["nan" if np.isnan(v) else v]
        x0, x1, y0, y1 = boxes[panel]
        p0, p1 = ipt(x0, y0), ipt(x1 + 1, y1 + 1)
        W, H = fr.x(p1[0]) - fr.x(p0[0]), fr.y(p1[1]) - fr.y(p0[1])
        heat = Image.fromarray(rgb).resize((W, H), Image.Resampling.BOX)
        img.paste(heat, (fr.x(p0[0]), fr.y(p0[1])))
        g0, g1 = ipt(x0, y0 - 18 + (0 if panel == "a" else 0)), ipt(x1 + 1, y0 - 3)
        gene = np.array([[TYPE_RGB[rows[c]["type"]] for c in cols]], dtype=np.uint8)
        gb = Image.fromarray(gene).resize((W, fr.y(g1[1]) - fr.y(g0[1])), Image.Resampling.BOX)
        img.paste(gb, (fr.x(p0[0]), fr.y(g0[1])))
        # Dendrogram.
        dg = figs["fig1"][panel]["dendrogram"]
        cl = ours["clustering"][kkey]
        d.rectangle([fr.x(dg["root_x"]) - 3, fr.y(dg["top"]) - 3, fr.x(dg["leaf_x"]) + 1, fr.y(dg["bottom"]) + 3], fill=WHITE)
        row_y = {p: ipt(0, y0 + (j + 0.5) * (y1 - y0 + 1) / 15)[1] for j, p in enumerate(order)}
        hroot = cl["height"][-1]
        xh = lambda hh: dg["leaf_x"] - hh / hroot * (dg["leaf_x"] - dg["root_x"])
        pos = {}

        def node(k):
            if k < 0:
                return dg["leaf_x"], row_y[PRED[-k - 1]]
            if k in pos:
                return pos[k]
            a, b = cl["merge"][k - 1]
            (xa, ya), (xb, yb) = node(a), node(b)
            xn = xh(cl["height"][k - 1])
            for dd, col, wd in ((d, BLACK, fr.w(0.33)), (do, RED, 2)):
                dd.line([(fr.x(xa), fr.y(ya)), (fr.x(xn), fr.y(ya)), (fr.x(xn), fr.y(yb)), (fr.x(xb), fr.y(yb))], fill=col, width=wd)
            pos[k] = (xn, (ya + yb) / 2)
            return pos[k]
        node(len(cl["merge"]))
    img.save(out / "fig1_ours.png")
    ov.save(out / "fig1_overlay.png")
    return {"size": list(img.size), "column_order": "lexicographic sort of the calls (not the published SNV clustering)"}


def af29_page(pub_dir, frames, figs, ours, out):
    """Additional file 29: our bars and error bars, red all SNVs, blue non-COSMIC, orange without the
    training-set SNVs; the composite score on the right axis."""
    img = Image.open(pub_dir / "additional-file-29.png").convert("RGB")
    ov = img.copy()
    fr = Frame(frames["af29"])
    d = ImageDraw.Draw(img)
    src = {"all": ours["table3"], "non_cosmic": ours["table4"], "excluding_training": ours["training_excluded"]}
    outside, panels = [], []
    for pred, panel in figs["af29"].items():
        la, ra = panel["left_axis"], panel["right_axis"]
        d.rectangle([fr.x(la["spine_x"] + 0.4), fr.y(la["top"] - 4), fr.x(ra["x"]) - 1, fr.y(la["bottom"]) - 1], fill=WHITE)
        for k in STATS:
            ax = dict(la) if k != "composite" else {"top": ra["top"], "bottom": ra["bottom"], "value_at_top": ra["value_at_top"],
                                                     "value_at_bottom": ra["value_at_bottom"], "spine_x": la["spine_x"]}
            bars, vals = [], []
            for series in ("all", "non_cosmic", "excluding_training"):
                b = panel["bars"][series][k]
                x0, t, x1, bt = b["box"]
                bars.append({"x0": x0, "x1": x1})
                r = src[series][pred][k]
                c = b["colour"]
                if len(c) == 4:
                    c = [(1 - c[0]) * (1 - c[3]), (1 - c[1]) * (1 - c[3]), (1 - c[2]) * (1 - c[3])]
                vals.append((r["value"], r["low"], r["high"], tuple(round(255 * v) for v in c)))
            panels.append((dict(ax, spine_x=ax["spine_x"] - 1e6), bars, vals))
    draw_bar_panels(img, ov, fr, panels, outside, whiten=False)
    img.save(out / "af29_ours.png")
    ov.save(out / "af29_overlay.png")
    return {"size": list(img.size), "outside_axis": len(outside)}


def boxplot_page(pub_dir, frames, figs, arr, out, n, key):
    """Additional files 24 and 26: our boxes (hinges) and medians in each panel, at the published box
    positions; whiskers and outlying points are not drawn."""
    from compare import fivenum
    img = Image.open(pub_dir / f"additional-file-{n}.png").convert("RGB")
    ov = img.copy()
    fr = Frame(frames[f"af{n}"])
    d, do = ImageDraw.Draw(img), ImageDraw.Draw(ov)
    names = list(arr[f"{key}|names"])
    acc = 100 * arr[f"{key}|run1|subset1|accuracy|mean"]
    pn = [(int(nm.split(" of ")[0].split()[-1]), len(nm.split(" of ", 1)[1].split(", "))) for nm in names]
    for panel in figs[f"af{n}"]:
        var, k = panel["title"]
        others = list(range(max(2, k), 12)) if var == "n" else list(range(1, k + 1))
        x0, t, x1, b = panel["frame"]
        d.rectangle([fr.x(x0) + 2, fr.y(t) + 2, fr.x(x1) - 2, fr.y(b) - 2], fill=WHITE)
        ax = panel["axis"]
        y = lambda v: ax["bottom"] + (v - ax["value_at_bottom"]) * (ax["top"] - ax["bottom"]) / (ax["value_at_top"] - ax["value_at_bottom"])
        for g, o in zip(panel["groups"], others):
            idx = [i for i, (pp, nn) in enumerate(pn) if (pp == k and nn == o) if var == "n"] if var == "n" else \
                  [i for i, (pp, nn) in enumerate(pn) if nn == k and pp == o]
            q = fivenum(acc[idx])
            half = ((g["box"][2] - g["box"][0]) / 2) if "box" in g else 8.5
            xa, xb = g["x"] - half, g["x"] + half
            for dd, col, wd in ((d, BLACK, fr.w(0.75)), (do, RED, 2)):
                if q[3] > q[1]:
                    dd.rectangle([fr.x(xa), fr.y(y(q[3])), fr.x(xb), fr.y(y(q[1]))], outline=col, width=wd)
                dd.line([fr.x(xa), fr.y(y(q[2])), fr.x(xb), fr.y(y(q[2]))], fill=col, width=fr.w(2.25) if dd is d else 2)
    img.save(out / f"af{n}_ours.png")
    ov.save(out / f"af{n}_overlay.png")
    return {"size": list(img.size), "drawn": "boxes (hinges) and medians; whiskers and outlying points not drawn"}


def kappa_page(pub_dir, frames, figs, ours, out, n, src, sets):
    """Additional files 4, 10 and 12: our kappa bin colour painted into each cell of both heat maps."""
    key = f"af{n}"
    img = Image.open(pub_dir / f"additional-file-{n}.png").convert("RGB")
    ov = img.copy()
    fr = Frame(frames[key])
    d, do = ImageDraw.Draw(img), ImageDraw.Draw(ov)
    for part, st in zip(("first", "second"), sets):
        g = figs[key][part]
        for i, a in enumerate(g["rows"]):
            for j, b in enumerate(g["rows"]):
                x0, t, x1, bt = g["boxes"][i][j]
                k = ours[src][st][a][b][0]
                d.rectangle([fr.x(x0), fr.y(t), fr.x(x1) - 1, fr.y(bt) - 1], fill=kappa_rgb(k))
                if g["bins"][i][j] != _bin(k):
                    do.rectangle([fr.x(x0), fr.y(t), fr.x(x1) - 1, fr.y(bt) - 1], outline=RED, width=2)
    img.save(out / f"{key}_ours.png")
    ov.save(out / f"{key}_overlay.png")
    return {"size": list(img.size)}


def _bin(k):
    for hi, name in ((0, "negative"), (0.2, "0.01-0.2"), (0.4, "0.21-0.4"), (0.6, "0.41-0.6"), (0.8, "0.61-0.8")):
        if k <= hi:
            return name
    return "0.81-1"


def main():
    pub_dir, figs_p, ours_p, npz_p, reading_p, xlsx, out = sys.argv[1:8]
    pub_dir, out = Path(pub_dir), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    frames = json.load(open(pub_dir / "frames.json"))
    figs = json.load(open(figs_p))
    ours = json.load(open(ours_p))
    arr = dict(np.load(npz_p))
    reading = json.load(open(reading_p))
    res = {"fig1": fig1(pub_dir, frames, figs, ours, reading, load(xlsx), out),
           "fig2": fig2(pub_dir, frames, figs, ours, out),
           "fig3": fig3(pub_dir, frames, figs, ours, arr, out),
           "fig4": fig4(pub_dir, frames, figs, ours, out),
           "af15": fig2(pub_dir, frames, figs, ours, out, "af15", "additional-file-15.png",
                        (ours["gene_classes"]["oncogenes"], ours["gene_classes"]["tsg"])),
           "af20": fig3(pub_dir, frames, figs, ours, arr, out, "af20", "additional-file-20.png", "accuracy"),
           "af23": fig4(pub_dir, frames, figs, ours, out, "af23", "additional-file-23.png", "accuracy"),
           "af29": af29_page(pub_dir, frames, figs, ours, out),
           "af24": boxplot_page(pub_dir, frames, figs, arr, out, 24, "all"),
           "af26": boxplot_page(pub_dir, frames, figs, arr, out, 26, "non_cosmic"),
           "af4": kappa_page(pub_dir, frames, figs, ours, out, 4, "kappa", ("labelled", "labelled_non_cosmic")),
           "af10": kappa_page(pub_dir, frames, figs, ours, out, 10, "kappa_low_confidence", ("all", "non_cosmic")),
           "af12": kappa_page(pub_dir, frames, figs, ours, out, 12, "kappa_low_confidence", ("labelled", "labelled_non_cosmic"))}
    for k, v in res.items():
        v["drawn_on_published"] = True
    (out / "figures.json").write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
