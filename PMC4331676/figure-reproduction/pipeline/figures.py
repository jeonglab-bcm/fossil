"""Draw our curves on the published figures' pixel grids, overlay them, and score them.

Usage: figures.py PUBLISHED_DIR RUN_DIR LOU.json PUBLISHED_VALUES.json OUTDIR

RUN_DIR holds benchmark.json, benchmark_decisions.json, pdb186_decisions.json, lg_sweep.json and
weights.json from experiments.py. Writes OUTDIR/fig*_ours.png, fig*_overlay.png and scores.json.

ROC curves (Figs 3, 4, 5). The axis grid of each figure is fitted to its tick marks (0 to 100 % in
steps of 5 or 20; see GRID). Each published curve is picked out by its colour (hue, saturation and
value ranges in CLASSES), inside the plot and outside the legend. Our curve is drawn 2 px wide on a
blank canvas of the published size. The score is the smaller of two shares: published curve pixels
within TOL px of ours, and our pixels within TOL px of the published curve. Controls are scored
with the same code: another method's curve from the same run (wrong input) and our curve moved
up or down by 3 points of true positive rate (near miss).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.colors as mc
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, distance_transform_edt

import pssmdt

TOL = 2.0  # px; the figures are 600 px wide (about 4.4 px per percentage point)
PASS = 0.75  # exact-data curves of Fig. 5 (Lou et al.) score 0.78 to 0.97; dashed and dotted lines lose pixels in their gaps

# x pixel of FPR 0 and 100 %, y pixel of TPR 0 and 100 % (tick marks)
GRID = {
    "fig3": {"x0": 118.0, "x100": 554.0, "y0": 470.0, "y100": 33.5, "legend": (366, 359, 543, 462)},
    "fig4": {"x0": 122.5, "x100": 558.0, "y0": 470.0, "y100": 34.5, "legend": (301, 353, 564, 455)},
    "fig5": {"x0": 112.0, "x100": 547.0, "y0": 467.5, "y100": 32.5, "legend": (397, 340, 541, 461)},
}

# colour classes (hue in degrees, saturation, value) and the colour we draw each curve in
NAVY = {"h": (200, 270), "s": (0.25, 1.01), "v": (0.0, 0.80), "rgb": (40, 40, 120)}
DARKRED = {"h": (335, 15), "s": (0.40, 1.01), "v": (0.0, 0.75), "rgb": (110, 0, 0)}
ORANGE = {"h": (15, 45), "s": (0.55, 1.01), "v": (0.55, 1.01), "rgb": (230, 140, 40)}
PALEORANGE = {"h": (25, 65), "s": (0.18, 0.60), "v": (0.45, 1.01), "rgb": (200, 160, 80)}
GREEN = {"h": (90, 150), "s": (0.25, 1.01), "v": (0.0, 0.85), "rgb": (0, 100, 0)}
MAGENTA = {"h": (275, 335), "s": (0.25, 1.01), "v": (0.3, 1.01), "rgb": (200, 0, 200)}

CLASSES = {
    "fig3": {"ACC": NAVY, "AvePscore-20": DARKRED, "AvePscore-400": PALEORANGE, "Pscore-100": GREEN,
             "PSSM-DT": MAGENTA},
    "fig4": {"DNA-Prot": NAVY, "DNAbinder(dimension 400)": DARKRED, "DNAbinder(dimension 21)": PALEORANGE,
             "iDNA-Prot": GREEN, "PSSM-DT": MAGENTA},
    "fig5": {"DBPPred": NAVY, "DNA-Prot": DARKRED, "DNABIND": PALEORANGE, "DNAbinder": GREEN,
             "iDNA-Prot": MAGENTA, "PSSM-DT": ORANGE},
}
OVERLAY_RGB = (0, 200, 255)


def load_png(path):
    return np.array(Image.open(path).convert("RGB"))


def masks(img, fig):
    """Colour mask of each curve. Halo pixels of a saturated line can look like a paler class, so a
    pale class loses pixels within 1 px of a saturated one. Also returns, per curve, the pixels
    where other curves could cover it (within TOL of their ink and not of its own)."""
    raw = {n: class_mask(img, spec, fig) for n, spec in CLASSES[fig].items()}
    strong = [n for n, spec in CLASSES[fig].items() if spec is not PALEORANGE]
    near_strong = binary_dilation(np.any([raw[n] for n in strong], axis=0), iterations=1)
    for n, spec in CLASSES[fig].items():
        if spec is PALEORANGE:
            raw[n] = raw[n] & ~near_strong
    hidden = {}
    for n in raw:
        others = np.any([raw[m] for m in raw if m != n], axis=0)
        hidden[n] = (distance_transform_edt(~others) <= TOL) & (distance_transform_edt(~raw[n]) > TOL)
    return raw, hidden


def class_mask(img, spec, fig):
    hsv = mc.rgb_to_hsv(img.astype(float) / 255)
    h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    lo, hi = spec["h"]
    hue = (h >= lo) & (h <= hi) if lo < hi else (h >= lo) | (h <= hi)
    m = hue & (s >= spec["s"][0]) & (s < spec["s"][1]) & (v >= spec["v"][0]) & (v < spec["v"][1])
    return m & plot_area(img.shape, fig)


def plot_area(shape, fig):
    g = GRID[fig]
    a = np.zeros(shape[:2], bool)
    a[int(g["y100"]) - 3:int(g["y0"]) + 3, int(g["x0"]) - 3:int(g["x100"]) + 3] = True
    x0, y0, x1, y1 = g["legend"]
    a[y0 - 2:y1 + 3, x0 - 2:x1 + 3] = False
    return a


def to_px(fig, fpr, tpr):
    g = GRID[fig]
    return (g["x0"] + (g["x100"] - g["x0"]) * np.asarray(fpr) / 100.0,
            g["y0"] + (g["y100"] - g["y0"]) * np.asarray(tpr) / 100.0)


def draw_lines(size, lines, width=2):
    """lines: [(xs, ys, rgb)] in pixel coordinates; returns an RGBA image."""
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for xs, ys, rgb in lines:
        d.line(list(zip(np.asarray(xs, float), np.asarray(ys, float))), fill=tuple(rgb) + (255,), width=width)
    return im


def line_mask(size, xs, ys, fig):
    im = draw_lines(size, [(xs, ys, (0, 0, 0))])
    m = np.array(im)[..., 3] > 0
    return m & plot_area((size[1], size[0]), fig)


def two_way(pub, ours, hidden=None):
    """hidden: pixels where other curves may cover this one; our pixels there are not judged."""
    judged = ours if hidden is None else ours & ~hidden
    if pub.sum() == 0 or judged.sum() == 0:
        return {"published_near_ours": 0.0, "ours_near_published": 0.0, "score": 0.0}
    d_ours = distance_transform_edt(~ours)
    d_pub = distance_transform_edt(~pub)
    p = float(np.mean(d_ours[pub] <= TOL))
    o = float(np.mean(d_pub[judged] <= TOL))
    return {"published_near_ours": round(p, 4), "ours_near_published": round(o, 4), "score": round(min(p, o), 4)}


def blank_plot(img, fig):
    """The published figure with everything inside the plot (except the legend) painted white."""
    out = img.copy()
    g = GRID[fig]
    area = plot_area(img.shape, fig)
    area[:int(g["y100"]) + 1] = False  # keep the top frame line
    frame = img.mean(2) < 110
    long_rows = frame.sum(1) > 0.5 * img.shape[1]
    long_cols = frame.sum(0) > 0.5 * img.shape[0]
    keep = np.zeros_like(area)
    keep[long_rows] = True
    keep[:, long_cols] = True
    out[area & ~keep] = 255
    # the diagonal
    d = ImageDraw.Draw(im := Image.fromarray(out))
    x, y = to_px(fig, [0, 100], [0, 100])
    d.line(list(zip(x, y)), fill=(170, 150, 150), width=1)
    return np.array(im)


def compose(base, layer):
    im = Image.fromarray(base).convert("RGBA")
    im.alpha_composite(layer)
    return np.array(im.convert("RGB"))


def roc_figure(fig, pub_img, curves, controls, outdir):
    """curves: {name: (fpr, tpr)} ours (None: not attempted); controls: {name: [(cname, kind, (fpr, tpr))]}."""
    h, w = pub_img.shape[:2]
    res = {}
    lines_ours, lines_over = [], []
    pmasks, hidden = masks(pub_img, fig)
    for name, spec in CLASSES[fig].items():
        cur = curves.get(name)
        if cur is None:
            continue
        xs, ys = to_px(fig, *cur)
        lines_ours.append((xs, ys, spec["rgb"]))
        lines_over.append((xs, ys, OVERLAY_RGB))
        pub = pmasks[name]
        r = two_way(pub, line_mask((w, h), xs, ys, fig), hidden[name])
        r["controls"] = []
        for cname, kind, (cf, ct) in controls.get(name, []):
            cx, cy = to_px(fig, cf, ct)
            r["controls"].append({"name": cname, "kind": kind,
                                  "score": two_way(pub, line_mask((w, h), cx, cy, fig), hidden[name])["score"]})
        best = max(c["score"] for c in r["controls"]) if r["controls"] else 0.0
        r.update({"tolerance_px": TOL, "published_pixels": int(pub.sum()),
                  "threshold": round(max(PASS, best + 0.05), 4)})
        res[name] = r
    ours = compose(blank_plot(pub_img, fig), draw_lines((w, h), lines_ours))
    over = compose(pub_img, draw_lines((w, h), lines_over, width=1))
    Image.fromarray(ours).save(Path(outdir) / f"{fig}_ours.png")
    Image.fromarray(over).save(Path(outdir) / f"{fig}_overlay.png")
    return res


def shifted(cur, dy):
    f, t = cur
    return (np.asarray(f), np.clip(np.asarray(t) + dy, 0, 100))


def roc_of(y, dec):
    f, t = pssmdt.roc_curve_points(np.asarray(y), np.asarray(dec))
    return (f, t)


def with_controls(curves, name, wrong_name):
    cur = curves[name]
    return [(f"our {wrong_name} curve", "wrong_input", curves[wrong_name]),
            ("TPR + 3 points", "near_miss", shifted(cur, 3)),
            ("TPR - 3 points", "near_miss", shifted(cur, -3))]


# ---------------------------------------------------------------- Fig. 1

def fig1(pub_img, sweep, pubvals, outdir):
    fr = pubvals["fig1"]["frame_px"]
    left, right, top, bottom = fr
    px = lambda x: left + (right - left) * np.asarray(x) / 16.0
    py = lambda v: bottom - (np.asarray(v) - 0.40) / 0.60 * (bottom - top)
    lg = [r["LG"] for r in sweep]
    accs = [r["ACC"] for r in sweep]
    mccs = [r["MCC"] for r in sweep]
    h, w = pub_img.shape[:2]

    def layer(colour_acc, colour_mcc, width):
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for vals, col, marker in ((accs, colour_acc, "s"), (mccs, colour_mcc, "o")):
            pts = list(zip(px(lg), py(vals)))
            d.line(pts, fill=col + (255,), width=width)
            for x, y in pts:
                box = (x - 4, y - 4, x + 4, y + 4)
                (d.rectangle if marker == "s" else d.ellipse)(box, fill=col + (255,))
        return im

    base = pub_img.copy()
    inner = np.zeros(base.shape[:2], bool)
    inner[top + 2:bottom - 1, left + 2:right - 1] = True
    leg = (base.mean(2) < 250) & inner
    # keep the legend (top right box) and paint the rest of the plot white
    ys, xs = np.nonzero(leg)
    lx0 = left + (right - left) * 0.70
    keep = np.zeros_like(inner)
    keep[top: top + 75, int(lx0):right] = True
    base[inner & ~keep] = 255
    ours = compose(base, layer((0, 0, 0), (255, 0, 0), 1))
    over = compose(pub_img, layer((0, 160, 255), (0, 200, 0), 1))
    Image.fromarray(ours).save(Path(outdir) / "fig1_ours.png")
    Image.fromarray(over).save(Path(outdir) / "fig1_overlay.png")


# ---------------------------------------------------------------- Fig. 2

AA = pssmdt.AMINO_ACIDS
# Fig. 2A: the 20 x 20 grid spans these pixels (cell edges fitted to the axis letters)
F2A = {"x0": 28.0, "x1": 273.0, "y0": 23.0, "y1": 275.0, "vmax": 150.0}
# Fig. 2B: bar chart axes (y pixel of weights 0 and 60, from the tick marks), the x centre of each
# lg group (bars 11 px wide, groups 55 px apart), the plot interior and the legend box
F2B = {"y0": 544.0, "y60": 380.0, "x_lg": [55.5, 110.5, 165.5, 220.5, 275.5], "bar_w": 11.0,
       "inner": (30, 326, 301, 543), "legend": (55, 328, 126, 396)}


def fig2(pub_img, weights, outdir):
    P = np.asarray(weights["pair_weights"])
    scale = F2A["vmax"] / P.max()  # our weights in units of our largest pair weight x 150
    h, w = pub_img.shape[:2]
    base = pub_img.copy()
    over = Image.fromarray(pub_img.copy()).convert("RGBA")
    cw = (F2A["x1"] - F2A["x0"]) / 20
    chh = (F2A["y1"] - F2A["y0"]) / 20
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(20):
        for j in range(20):
            g = int(round(255 * (1 - min(P[i, j] * scale, F2A["vmax"]) / F2A["vmax"])))
            box = (F2A["x0"] + 1 + j * cw, F2A["y0"] + 1 + i * chh, F2A["x0"] + (j + 1) * cw, F2A["y0"] + (i + 1) * chh)
            d.rectangle(box, fill=(g, g, g, 255))
    # panel B: our weights of the paper's top four pairs, scaled like panel A
    W = weights["paper_top4_by_lg"]
    cols = {"RR": (0, 0, 0), "RP": (255, 0, 0), "PR": (0, 0, 255), "AR": (255, 0, 255)}
    unit = (F2B["y0"] - F2B["y60"]) / 60.0
    wscale = 57.6 / max(max(v) for v in W.values())  # tallest of our bars = tallest published bar
    blay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blay)
    olay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(olay)
    for k, pair in enumerate(["RR", "RP", "PR", "AR"]):
        for l in range(5):
            xc = F2B["x_lg"][l] + (k - 1.5) * F2B["bar_w"]
            top = F2B["y0"] - max(W[pair][l], 0) * wscale * unit
            bd.rectangle((xc - F2B["bar_w"] / 2, top, xc + F2B["bar_w"] / 2 - 1, F2B["y0"]), fill=cols[pair] + (255,))
            od.rectangle((xc - F2B["bar_w"] / 2, top, xc + F2B["bar_w"] / 2 - 1, top + 1), fill=(0, 200, 0, 255))
    # ours: panels A and B replaced, C and D left as published (not attempted)
    base[int(F2A["y0"]) + 1:int(F2A["y1"]), int(F2A["x0"]) + 1:int(F2A["x1"])] = 255
    x0, y0, x1, y1 = F2B["inner"]
    keep = base[F2B["legend"][1]:F2B["legend"][3], F2B["legend"][0]:F2B["legend"][2]].copy()
    base[y0:y1, x0:x1] = 255
    base[F2B["legend"][1]:F2B["legend"][3], F2B["legend"][0]:F2B["legend"][2]] = keep
    ours = Image.fromarray(base).convert("RGBA")
    ours.alpha_composite(lay)
    ours.alpha_composite(blay)
    ours.convert("RGB").save(Path(outdir) / "fig2_ours.png")
    # overlay: our panel A at half opacity over the published, our bar tops as green ticks
    lay_half = lay.copy()
    lay_half.putalpha(lay.getchannel("A").point(lambda a: a // 2))
    over.alpha_composite(lay_half)
    over.alpha_composite(olay)
    over.convert("RGB").save(Path(outdir) / "fig2_overlay.png")


def main(pubdir, run, lou_json, pubvals_json, outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    pub = {k: load_png(Path(pubdir) / f"{k}.png") for k in ("fig1", "fig2", "fig3", "fig4", "fig5")}
    run = Path(run)
    lou = json.loads(Path(lou_json).read_text())
    pubvals = json.loads(Path(pubvals_json).read_text())
    bd = json.loads((run / "benchmark_decisions.json").read_text())
    ind = json.loads((run / "pdb186_decisions.json").read_text())
    scores = {}

    ours3 = {name: roc_of(bd["label"], bd[name]) for name in ("ACC", "AvePscore-20", "AvePscore-400", "Pscore-100", "PSSM-DT")}
    c3 = {"PSSM-DT": with_controls(ours3, "PSSM-DT", "AvePscore-20")}
    for n in ("ACC", "AvePscore-20", "AvePscore-400", "Pscore-100"):
        c3[n] = with_controls(ours3, n, "PSSM-DT")
    scores["fig3"] = roc_figure("fig3", pub["fig3"], ours3, c3, out)

    ours4 = {"PSSM-DT": ours3["PSSM-DT"], "DNAbinder(dimension 21)": ours3["AvePscore-20"],
             "DNAbinder(dimension 400)": ours3["AvePscore-400"]}
    c4 = {"PSSM-DT": with_controls(ours4, "PSSM-DT", "DNAbinder(dimension 21)"),
          "DNAbinder(dimension 21)": with_controls(ours4, "DNAbinder(dimension 21)", "PSSM-DT"),
          "DNAbinder(dimension 400)": with_controls(ours4, "DNAbinder(dimension 400)", "PSSM-DT")}
    scores["fig4"] = roc_figure("fig4", pub["fig4"], ours4, c4, out)

    ours5 = {n: (np.asarray(lou["roc"][n]["fpr"]), np.asarray(lou["roc"][n]["tpr"])) for n in ("DBPPred", "DNAbinder", "DNABIND")}
    ours5["PSSM-DT"] = roc_of(ind["label"], ind["PSSM-DT"])
    c5 = {"PSSM-DT": with_controls(ours5, "PSSM-DT", "DBPPred"),
          "DBPPred": with_controls(ours5, "DBPPred", "DNABIND"),
          "DNABIND": with_controls(ours5, "DNABIND", "DNAbinder"),
          "DNAbinder": with_controls(ours5, "DNAbinder", "DNABIND")}
    scores["fig5"] = roc_figure("fig5", pub["fig5"], ours5, c5, out)

    fig1(pub["fig1"], json.loads((run / "lg_sweep.json").read_text()), pubvals, out)
    fig2(pub["fig2"], json.loads((run / "weights.json").read_text()), out)
    (out / "scores.json").write_text(json.dumps(scores, indent=1) + "\n")
    for f, d in scores.items():
        for n, r in d.items():
            print(f, n, r["score"], [c["score"] for c in r["controls"]], r["threshold"])


if __name__ == "__main__":
    main(*sys.argv[1:6])
