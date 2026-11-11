"""Renders, overlays and pixel scores of Figures 1 to 3, and the numbers read off Figures 3 and 4.

  figures.py PUBLISHED_DIR ANALYSIS.json OUTDIR

PUBLISHED_DIR holds the authors' original figure files (BMC's additional files, CC BY 2.0):
figure-1.png, figure-2.jpg, figure-3.png, figure-4.png. Every pixel map comes from the axes alone
(gridlines and tick labels); nothing inside a plot is fitted.

Writes OUTDIR/figures.json and OUTDIR/figures/*.png:
  fig1{a..f}_ours.png, fig1{a..f}_overlay.png  bars of the archived training set on the published grid
  fig2_ours.png, fig2_overlay.png              the retrained tree drawn as a list next to the published
                                               tree, and the published tree annotated rule by rule
  fig3{a,b,c}_ours.png, fig3{a,b,c}_overlay.png  ROC points and hull of the published Figure 2 tree on the
                                               archived sets, on the published grid
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

TOL_PX = 2
FIG3_PASS = 0.90


def font(size):
    return ImageFont.load_default(size=size)


def near(mask_a, mask_b, tol):
    """Share of mask_a's pixels within tol px (Chebyshev) of a mask_b pixel."""
    if mask_a.sum() == 0:
        return 0.0
    from scipy.ndimage import binary_dilation
    grown = binary_dilation(mask_b, structure=np.ones((2 * tol + 1, 2 * tol + 1), bool))
    return float((mask_a & grown).sum() / mask_a.sum())


def row_background(img, x0, x1, y0, y1):
    """Most common colour of each row between x0 and x1: the panel without its bars."""
    out = np.zeros((y1 - y0, 3), int)
    for y in range(y0, y1):
        vals, counts = np.unique(img[y, x0:x1].reshape(-1, 3), axis=0, return_counts=True)
        out[y - y0] = vals[counts.argmax()]
    return out


# ---- Figure 1 -------------------------------------------------------------------------------------
FIG1_BOXES = {"a": (0, 0, 300, 276), "b": (300, 0, 600, 276), "c": (0, 276, 300, 552),
              "d": (300, 276, 600, 552), "e": (0, 552, 300, 829), "f": (300, 552, 600, 829)}
GREY_FILL, GREY_EDGE = (196, 196, 196), (174, 174, 174)
BLUE_FILL, BLUE_EDGE = (52, 93, 135), (44, 76, 108)


def fig1_geometry(img, box, printed_normal):
    x0, y0, x1, y1 = box
    sub = img[y0:y1, x0:x1].astype(int)
    dark = sub.sum(2) < 240
    runs = dark.sum(1)
    base = int(np.argmax(runs))  # the x axis: the longest dark row
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    blue = (b - r > 25) & (b > 60)
    cols = np.nonzero(blue[base - 3] | blue[base - 2])[0]
    bars = []
    for c in cols:
        if bars and c - bars[-1][1] <= 1:
            bars[-1][1] = c
        else:
            bars.append([c, c])
    idx = [i for i, v in enumerate(printed_normal) if v is None or int(v) > 0]
    if len(bars) != len(idx):
        raise RuntimeError(f"panel {box}: {len(bars)} blue bars at the axis, {len(idx)} expected")
    tops, heights = [], []
    for (c0, c1), i in zip(bars, idx):
        col = blue[:, (c0 + c1) // 2]
        top = base - 3
        while top > 0 and (col[top - 1] or col[top - 2]):  # the run of blue that stands on the axis
            top -= 1
        tops.append(top)
        if printed_normal[i] is not None and top > 2:  # a bar cut by the top of the axis has no label
            heights.append((float(printed_normal[i]), base - top))
    # pixel height per percent from the labelled bars (labels are truncated: use the bar centre +0.5)
    xs = np.array([h[0] + 0.5 for h in heights])
    ys = np.array([h[1] for h in heights])
    k = float((xs * ys).sum() / (xs * xs).sum())
    resid = float(np.abs(ys - k * xs).max())
    spacing = np.median(np.diff([b[0] for b in bars]) / np.diff(idx))
    first = np.median([b[0] - i * spacing for b, i in zip(bars, idx)])
    width = int(round(np.median([b[1] - b[0] for b in bars])))
    groups = [(int(round(first + i * spacing)), width) for i in range(10)]
    plot_top = int(np.nonzero(runs[:base] > 0.5 * runs[base])[0].min()) if (runs[:base] > 0.5 * runs[base]).any() else 0
    return {"base": base, "px_per_pct": k, "fit_max_residual_px": resid, "groups": groups, "plot_top": plot_top,
            "x0": x0, "y0": y0}


def draw_bar(d, x0, x1, top, base, fill, edge):
    if base - top < 1:
        return
    d.rectangle([x0, top, x1, base - 1], fill=fill, outline=edge)


def fig1_panel(img, panel, pub, ours, out):
    box = FIG1_BOXES[panel]
    geo = fig1_geometry(img, box, pub["normal"])
    x0, y0 = geo["x0"], geo["y0"]
    base = y0 + geo["base"]
    k = geo["px_per_pct"]
    clean = img.copy()
    # each row's background from the columns between the bar groups (bars fill most of a row near the axis)
    gaps = np.zeros(img.shape[1], bool)
    groups = geo["groups"]
    for (gx, w), (nx, _) in zip(groups, groups[1:]):
        gaps[x0 + gx + w + 1: x0 + nx - w - 2] = True  # the one or two columns between neighbouring groups
    bg = np.zeros((base - (y0 + 18), 3), int)
    for y in range(y0 + 18, base):
        px = img[y, gaps].reshape(-1, 3).astype(int)
        grey = (px.max(1) - px.min(1) < 6) & (px.mean(1) > 190) & (px.mean(1) < 253)  # not text, bar edge or glow
        px = px[grey] if grey.any() else px
        vals, counts = np.unique(px, axis=0, return_counts=True)
        bg[y - (y0 + 18)] = vals[counts.argmax()]
    f = font(7)
    rendered = Image.fromarray(clean.astype(np.uint8))
    overlay = Image.fromarray(img.astype(np.uint8))
    # erase the published bars and their labels (from 12 px above the taller bar down to the axis),
    # row by row, with the row's background
    arr = np.array(rendered)
    for i, (gx, w) in enumerate(geo["groups"]):
        a, b = x0 + gx - w - 3, x0 + gx + w + 3
        pub_pct = max(float(v) for v in (pub["disease"][i], pub["normal"][i]) if v is not None) if any(
            v is not None for v in (pub["disease"][i], pub["normal"][i])) else 0.0
        if pub["normal"][i] is None:  # the bar runs off the top of the axis
            pub_pct = 100.0
        top = max(y0 + 18, int(base - k * (pub_pct + 1)) - 12)
        for y in range(top, base):
            arr[y, a:b] = bg[y - (y0 + 18)]
    rendered = Image.fromarray(arr)
    d = ImageDraw.Draw(rendered)
    o = ImageDraw.Draw(overlay)
    for i, (gx, w) in enumerate(geo["groups"]):
        bx0, bx1 = x0 + gx, x0 + gx + w
        gx0, gx1 = bx0 - w - 2, bx0 - 1
        for cls, (c0, c1), fill, edge in (("disease", (gx0, gx1), GREY_FILL, GREY_EDGE),
                                           ("normal", (bx0, bx1), BLUE_FILL, BLUE_EDGE)):
            p = ours[cls][i]
            top = max(y0 + 2, int(round(base - k * p)))
            draw_bar(d, c0, c1, top, base, fill, edge)
            lab = f"{math.floor(p + 1e-9)}%"
            tw = d.textlength(lab, font=f)
            d.text(((c0 + c1) / 2 - tw / 2, top - 9), lab, fill=(40, 40, 40), font=f)
            o.line([c0, top, c1, top], fill=(220, 0, 0), width=2)
    crop = (box[0], box[1], box[2], box[3])
    rendered.crop(crop).save(out / f"fig1{panel}_ours.png")
    overlay.crop(crop).save(out / f"fig1{panel}_overlay.png")
    return {"px_per_pct": k, "fit_max_residual_px": geo["fit_max_residual_px"], "baseline_y": base}


# ---- Figure 2 -------------------------------------------------------------------------------------
# centre of each published rule's circle in the 1200 x 1050 figure (centres of the node-fill blobs)
FIG2_NODES = {1: (167, 268), 2: (360, 273), 3: (558, 272), 4: (855, 272), 5: (706, 382), 6: (1091, 383),
              7: (105, 635), 8: (302, 636), 9: (497, 635), 10: (697, 640), 11: (891, 635), 12: (154, 895),
              13: (407, 897), 14: (694, 893), 15: (1092, 640)}


def fig2(published_path, analysis, out):
    pub = Image.open(published_path).convert("RGB")
    W, H = pub.size
    sx, sy = W / 1200, H / 1050
    fields = analysis["items"]["fig2"]
    tree = analysis["runs"]["main"]["tree"]
    # ours: the retrained tree as Weka prints it, on a canvas of the published size
    ours = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(ours)
    f = font(max(10, int(13 * sx)))
    d.text((20 * sx, 15 * sy), "Retrained on the archived training set (Weka 3.4.3 ADTree -B 15 -E -1)", fill=(0, 0, 0), font=font(int(16 * sx)))
    y = 50 * sy
    for line in tree.splitlines()[2:]:
        d.text((20 * sx, y), line, fill=(30, 30, 30), font=f)
        y += 17 * sy
    ours.save(out / "fig2_ours.png")
    # overlay: the published tree with each rule marked: found in the same place or not
    ov = pub.copy()
    o = ImageDraw.Draw(ov)
    fo = font(max(10, int(12 * sx)))
    per_rule = {}
    for fl in fields:
        rid = int(fl["name"].split()[1])
        per_rule.setdefault(rid, []).append(fl)
    for rid, fl in per_rule.items():
        cx, cy = FIG2_NODES[rid]
        cx, cy = cx * sx, cy * sy
        same_place = fl[0]["observed"] == "yes"
        col = (0, 150, 0) if same_place else (220, 0, 0)
        o.ellipse([cx - 46 * sx, cy - 46 * sy, cx + 46 * sx, cy + 46 * sy], outline=col, width=max(2, int(3 * sx)))
        if same_place:
            obs = [x["observed"] for x in fl[1:]]
            txt = " / ".join(str(v) for v in obs)
            o.text((cx - 50 * sx, cy + 48 * sy), txt, fill=col, font=fo)
    o.text((12 * sx, H - 40 * sy), "Green: the retrained tree has a rule on this feature in the same place (its threshold / no / yes).",
           fill=(0, 150, 0), font=fo)
    o.text((12 * sx, H - 22 * sy), "Red: no such rule in the retrained tree.", fill=(220, 0, 0), font=fo)
    ov.save(out / "fig2_overlay.png")


# ---- Figure 3 -------------------------------------------------------------------------------------
FIG3_PANELS = {"a": {"set": "training", "dy": 0, "x0": 21.7, "x100": 286.0},
               "b": {"set": "hgmd", "dy": 343, "x0": 20.7, "x100": 285.0},
               "c": {"set": "oligogenic", "dy": 684, "x0": 20.7, "x100": 285.0}}
FIG3_Y100, FIG3_Y0 = 8.0, 272.3  # panel A: the top border (100) and ten gridlines 26.43 px apart
RED = (255, 0, 0)
LIGHT_GREEN = (140, 255, 139)


def fig3_masks(arr, y0, y1, x0, x1):
    sub = arr[y0:y1, x0:x1].astype(int)
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    red = (r > 180) & (g < 110) & (b < 110)
    green = (g > 200) & (r < 215) & (b < 215) & (g - r > 30)
    return red, green


def fig3_draw(base, cal, curve, hull, dy):
    img = base.copy()
    d = ImageDraw.Draw(img)
    X = lambda v: cal["x0"] + (cal["x100"] - cal["x0"]) * v
    Y = lambda v: dy + FIG3_Y0 + (FIG3_Y100 - FIG3_Y0) * v
    d.line([(X(x), Y(y)) for x, y in hull], fill=LIGHT_GREEN, width=1)
    for x, y, _ in curve:
        cx, cy = X(x), Y(y)
        d.rectangle([cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5], fill=RED)
    return img


def fig3_clean(pub_arr, dy):
    """The published panel with the red points and the green hull painted over by the row background."""
    arr = pub_arr.copy()
    y0, y1 = dy + 4, dy + 276
    red, green = fig3_masks(arr, y0, y1, 15, 292)
    bg = row_background(arr, 30, 280, y0, y1)
    m = red | green
    from scipy.ndimage import binary_dilation
    m = binary_dilation(m, structure=np.ones((3, 3), bool))
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        arr[y0 + y, 15 + x] = bg[y]
    return arr


def fig3(published_path, analysis, out):
    from prospectr_adtree import roc_hull
    pub = np.array(Image.open(published_path).convert("RGB"))
    res = {}
    rocs = analysis["roc"]
    for panel, cal in FIG3_PANELS.items():
        dy = cal["dy"]
        y0, y1 = dy + 4, dy + 276
        clean = Image.fromarray(fig3_clean(pub, dy))

        def score(curve):
            img = np.array(fig3_draw(clean, cal, curve, roc_hull(curve), dy))
            r_o, g_o = fig3_masks(img, y0, y1, 15, 292)
            r_p, g_p = fig3_masks(pub, y0, y1, 15, 292)
            po, pp = r_o | g_o, r_p | g_p
            return near(pp, po, TOL_PX), near(po, pp, TOL_PX)

        curve = analysis["roc_fig2tree"][cal["set"]]
        img = fig3_draw(clean, cal, curve, roc_hull(curve), dy)
        crop = (0, max(0, dy - 2), 300, min(pub.shape[0], dy + 330))
        img.crop(crop).save(out / f"fig3{panel}_ours.png")
        # overlay: published in grey, ours in red/green outline
        ov = Image.fromarray(pub.copy())
        o = ImageDraw.Draw(ov)
        X = lambda v: cal["x0"] + (cal["x100"] - cal["x0"]) * v
        Y = lambda v: dy + FIG3_Y0 + (FIG3_Y100 - FIG3_Y0) * v
        o.line([(X(x), Y(y)) for x, y in roc_hull(curve)], fill=(0, 90, 255), width=1)
        for x, y, _ in curve:
            o.rectangle([X(x) - 1.5, Y(y) - 1.5, X(x) + 1.5, Y(y) + 1.5], outline=(0, 0, 160))
        ov.crop(crop).save(out / f"fig3{panel}_overlay.png")
        pn, op = score(curve)
        controls = []
        others = {"training": "hgmd", "hgmd": "training", "oligogenic": "hgmd"}
        o_set = others[cal["set"]]
        pn2, op2 = score(analysis["roc_fig2tree"][o_set])
        controls.append({"name": f"the {o_set} set's curve", "kind": "wrong_input", "score": min(pn2, op2)})
        # scores that carry no information: the diagonal
        diag = [(1 - i / 50, 1 - i / 50, 0.0) for i in range(51)]
        pn3, op3 = score(diag)
        controls.append({"name": "a classifier at chance (the diagonal)", "kind": "wrong_input", "score": min(pn3, op3)})
        retrained = rocs[cal["set"]]
        pn4, op4 = score(retrained)
        controls.append({"name": "the tree retrained on the archived training set", "kind": "near_miss",
                         "score": min(pn4, op4), "note": "another model on the same data"})
        for shift in (0.02, -0.02):
            sh = [(min(1, max(0, x + shift)), y, t) for x, y, t in curve]
            a, b = score(sh)
            controls.append({"name": f"ours with FP rate shifted by {shift:+.2f}", "kind": "near_miss", "score": min(a, b)})
        # published points read back to numbers: AUC of the digitised curve
        r_p, _ = fig3_masks(pub, y0, y1, 15, 292)
        pts = _blobs(r_p)
        xy = sorted(((cx + 15 - cal["x0"]) / (cal["x100"] - cal["x0"]),
                     (dy + FIG3_Y0 - (cy + y0)) / (FIG3_Y0 - FIG3_Y100)) for cy, cx in pts)
        xy = [(0.0, 0.0)] + [(min(max(x, 0), 1), min(max(y, 0), 1)) for x, y in xy] + [(1.0, 1.0)]
        auc_pub = sum((x2 - x1) * (y1 + y2) / 2 for (x1, y1), (x2, y2) in zip(xy, xy[1:]))
        res[panel] = {"set": cal["set"], "published_near_ours": pn, "ours_near_published": op, "controls": controls,
                      "digitised_points": len(pts), "digitised_auc": auc_pub,
                      "calibration": {"x0_px": cal["x0"], "x100_px": cal["x100"], "y0_px": dy + FIG3_Y0, "y100_px": dy + FIG3_Y100}}
    return res


def _blobs(mask):
    from scipy.ndimage import label, center_of_mass
    lab, n = label(mask)
    return center_of_mass(mask, lab, range(1, n + 1)) if n else []


# ---- Figure 4 (read only) ---------------------------------------------------------------------------
def fig4(published_path):
    """The three published curves read back at whole percentages of the ranked list."""
    arr = np.array(Image.open(published_path).convert("RGB")).astype(int)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    masks = {"hgmd": (b - r > 40) & (b > 120) & (g > 100),
             "omim": (r > 200) & (g > 150) & (b < 120),
             "oligogenic": (g - r > 80) & (g - b > 80)}
    X = lambda v: 54.0 + 5.40 * v
    Yinv = lambda py: (474.5 - py) / 4.635
    legend = (405, 360, 560, 440)  # x0, y0, x1, y1 of the legend box, left out
    out = {}
    for name, m in masks.items():
        vals = {}
        for v in range(0, 100):
            x = int(round(X(v)))
            if legend[0] <= x <= legend[2]:
                ys = [y for y in np.nonzero(m[:, x])[0] if not (legend[1] <= y <= legend[3])]
            else:
                ys = list(np.nonzero(m[:, x])[0])
            ys = [y for y in ys if 5 < y < 476]
            if ys:
                vals[v] = round(Yinv(float(np.mean(ys))), 2)
        out[name] = vals
    claims = {}
    for fold, top in (("2", 50), ("5", 20), ("20", 5), ("25", 4)):
        vals = [out[k].get(top) for k in ("hgmd", "omim", "oligogenic")]
        claims[fold] = {"top_pct": top, "per_set": dict(zip(("hgmd", "omim", "oligogenic"), vals)),
                        "mean": round(sum(vals) / 3, 2) if None not in vals else None}
    return {"curves": out, "enrichment": claims, "calibration": {"x": "54.0 + 5.40 v px (tick labels 10-90, max residual 1.1 px)",
                                           "y": "474.5 - 4.635 v px (gridlines)"}}


def main(published, analysis_path, outdir):
    pubdir, out = Path(published), Path(outdir)
    figs = out / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    analysis = json.load(open(analysis_path))
    pv = json.load(open(pubdir / "published_values.json"))
    img1 = np.array(Image.open(pubdir / "figure-1.png").convert("RGB"))
    res = {"fig1": {}, "tolerance_px": TOL_PX, "fig3_pass": FIG3_PASS}
    for panel in "abcdef":
        ours = analysis["fig1"][panel]["variants"]["overflow"]
        res["fig1"][panel] = fig1_panel(img1, panel, pv["figure1"][panel], ours, figs)
    whole = Image.open(pubdir / "figure-1.png").convert("RGB")
    for panel, box in FIG1_BOXES.items():
        whole.paste(Image.open(figs / f"fig1{panel}_ours.png"), box[:2])
    whole.save(figs / "fig1_ours.png")
    fig2(pubdir / "figure-2.jpg", analysis, figs)
    res["fig3"] = fig3(pubdir / "figure-3.png", analysis, figs)
    whole = Image.open(pubdir / "figure-3.png").convert("RGB")
    for panel, cal in FIG3_PANELS.items():
        whole.paste(Image.open(figs / f"fig3{panel}_ours.png"), (0, max(0, cal["dy"] - 2)))
    whole.save(figs / "fig3_ours.png")
    res["fig4"] = fig4(pubdir / "figure-4.png")
    json.dump(res, open(out / "figures.json", "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:4])
