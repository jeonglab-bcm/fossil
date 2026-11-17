#!/usr/bin/env python3
"""Score our Kaplan-Meier and ROC curves against the published figure panels, pixel by pixel.

  score_figures.py PANELS_JSON CURVES_DIR PUBLISHED_DIR OUT_DIR

For each panel (panels.json): the pixel-to-data map is fitted to the panel's tick marks; the
published curves are found by colour inside the axes box (legends and insets masked); our curves
are drawn on the same grid at the published line width; both are scored two ways (share of
published curve pixels within TOL px of ours, and of ours within TOL px of the published), per
colour, so a curve only matches the curve of its own colour. The same is done for each negative
control. Writes OUT_DIR/pixel_scores.json, and per figure fig<N>_ours.png (the published figure
with its curves replaced by ours) and fig<N>_overlay.png (cyan: only in the paper; red: only
ours; black: both).
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

TOL = 2          # px at 600 dpi (the repository's tolerance)
DARK = 110       # grey level below which a pixel is ink for the axes and ticks
SAT = 60         # max-min channel spread above which a pixel is coloured


def clusters(idx):
    out = []
    for i in idx:
        if out and i - out[-1][-1] <= 2:
            out[-1].append(i)
        else:
            out.append([i])
    return [(c[0] + c[-1]) / 2 for c in out]


def fit_axis(pos, vals):
    """Fit pixel = a * value + b to the tick marks. A tick hidden under a curve is skipped: ticks
    are equally spaced, so each found tick takes the value of its place in the sequence."""
    if len(pos) > len(vals) or len(pos) < 3:
        raise SystemExit(f"found {len(pos)} ticks, expected {len(vals)}")
    if len(pos) < len(vals):
        step = (pos[-1] - pos[0]) / (len(vals) - 1)
        idx = [int(round((q - pos[0]) / step)) for q in pos]
        vals = [vals[i] for i in idx]
    a, b = np.polyfit(vals, pos, 1)
    resid = float(np.max(np.abs(np.polyval([a, b], vals) - np.array(pos))))
    return a, b, resid


def calibrate(grey, box, xt, yt):
    x0, x1, y0, y1 = box
    dark = grey < DARK
    strip = dark[y1 + 6:y1 + 22, x0 - 15:x1 + 15]
    xs = clusters(np.where(strip.sum(0) >= 10)[0] + x0 - 15)
    left = dark[y0 - 15:y1 + 15, x0 - 22:x0 - 6]
    ys = clusters(np.where(left.sum(1) >= 10)[0] + y0 - 15)
    ax = fit_axis(xs, xt)
    ay = fit_axis(ys, sorted(yt, reverse=True))
    return ax, ay


def inner_boxes(grey, box, sat, min_len=150):
    """Rectangles drawn inside the panel (legends, insets). A legend drawn in a corner shares the
    axes box's lines, so a top line without a bottom line is taken to reach the panel bottom."""
    x0, x1, y0, y1 = box
    sub = (grey[y0 + 5:y1 - 4, x0 + 5:x1 - 4] < DARK) & (sat[y0 + 5:y1 - 4, x0 + 5:x1 - 4] < SAT)
    rows = []
    for y in range(sub.shape[0]):
        d = np.diff(np.concatenate([[0], sub[y].astype(np.int8), [0]]))
        for s_, e in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
            if e - s_ >= min_len:
                rows.append((y, s_, e))
    merged = []
    for y, s_, e in rows:
        if merged and y - merged[-1][0] <= 2 and abs(s_ - merged[-1][1]) < 6 and abs(e - merged[-1][2]) < 6:
            merged[-1] = (y, s_, e)
        else:
            merged.append((y, s_, e))
    out, used = [], set()
    for i, (ya, sa, ea) in enumerate(merged):
        if i in used:
            continue
        bottom = sub.shape[0]
        for j in range(i + 1, len(merged)):
            yb, sb, eb = merged[j]
            if yb - ya > 30 and abs(sa - sb) < 6 and abs(ea - eb) < 6:
                bottom = yb
                used.add(j)
                break
        out.append((sa + x0 + 5, ea + x0 + 5, ya + y0 + 5, bottom + y0 + 5))
    return out


def series_masks(rgb, box, colours, masks, maxdist=110):
    x0, x1, y0, y1 = box
    region = np.zeros(rgb.shape[:2], bool)
    region[y0 + 4:y1 - 3, x0 + 4:x1 - 3] = True
    for (a, b, c, d) in masks:
        region[c - 6:d + 7, a - 6:b + 7] = False
    px = rgb.astype(int)
    sat = px.max(2) - px.min(2)
    ref = np.array([c for c in colours.values()])
    dist = np.sqrt(((px[:, :, None, :] - ref[None, None]) ** 2).sum(-1))
    near = dist.argmin(-1)
    ok = region & (sat > SAT) & (dist.min(-1) < maxdist)
    return {k: ok & (near == i) for i, k in enumerate(colours)}, region


def read_curves(path):
    rows = list(csv.DictReader(open(path)))
    return rows


def km_paths(rows, ax, ay, scale=1.0):
    """Polylines and censor marks of Kaplan-Meier step curves, in pixels, per group. Times are
    multiplied by scale (365 for panels drawn in days)."""
    groups = {}
    for r in rows:
        groups.setdefault(r["group"], []).append(r)
    out = {}
    X = lambda t: ax[0] * t + ax[1]
    Y = lambda s: ay[0] * s + ay[1]
    for g, rs in groups.items():
        pts = [(X(0.0), Y(1.0))]
        s_prev = 1.0
        marks = []
        for r in rs:
            t, s = float(r["time"]) * scale, float(r["surv"])
            pts.append((X(t), Y(s_prev)))
            pts.append((X(t), Y(s)))
            if int(float(r["n_censor"])) > 0:
                marks.append((X(t), Y(s)))
            s_prev = s
        out[g] = (pts, marks)
    return out


def roc_paths(rows, ax, ay):
    pts = [(ax[0] * float(r["fpr"]) + ax[1], ay[0] * float(r["tpr"]) + ay[1]) for r in rows]
    return {"all": (pts, [])}


def draw(shape, paths, width, mark):
    im = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(im)
    for pts, marks in paths:
        d.line(pts, fill=255, width=width, joint="curve")
        for (x, y) in marks:
            d.line([(x - mark, y), (x + mark, y)], fill=255, width=max(2, width - 1))
            d.line([(x, y - mark), (x, y + mark)], fill=255, width=max(2, width - 1))
    return np.asarray(im) > 0


def close_gaps(m, r):
    """Fill the gaps of dashed and dotted published lines, so a solid line can be scored against them."""
    if r <= 0:
        return m
    st = np.ones((2 * r + 1, 2 * r + 1), bool)
    return ndimage.binary_erosion(ndimage.binary_dilation(m, st), st, border_value=0) | m


def score(pubs, ours, region):
    """Two-way share within TOL px, pooled over colours. pubs = (raw, closed): published pixels are
    counted from the raw mask; our pixels are matched against the mask with dash gaps closed, so a
    solid line drawn over a dashed published line is not penalized for the gaps."""
    raw, closed = pubs
    pn = on = pt = ot = 0
    for k in raw:
        P = raw[k]
        O = ours.get(k, np.zeros_like(P)) & region
        if P.sum() == 0 and O.sum() == 0:
            continue
        dO = ndimage.distance_transform_edt(~O) if O.any() else np.full(P.shape, 1e9)
        dP = ndimage.distance_transform_edt(~closed[k]) if closed[k].any() else np.full(P.shape, 1e9)
        pn += int((dO[P] <= TOL).sum()); pt += int(P.sum())
        on += int((dP[O] <= TOL).sum()); ot += int(O.sum())
    return (pn / pt if pt else 0.0), (on / ot if ot else 0.0)


def transform(rows, kind, how, p_scale=1.0):
    out = []
    for r in rows:
        r = dict(r)
        if kind == "km":
            if how == "x0.95":
                r["surv"] = float(r["surv"]) * 0.95
            elif how == "x1.05":
                r["surv"] = min(1.0, float(r["surv"]) * 1.05)
            elif how.startswith("shift"):
                r["time"] = float(r["time"]) + float(how[5:]) / p_scale
        else:
            if how == "x0.95":
                r["tpr"] = float(r["tpr"]) * 0.95
            elif how.startswith("shift"):
                r["fpr"] = min(1.0, float(r["fpr"]) + float(how[5:]))
        out.append(r)
    return out


def main():
    cfg_path, curves, pubdir, outdir = map(Path, sys.argv[1:5])
    outdir.mkdir(parents=True, exist_ok=True)
    cfg = json.load(open(cfg_path))
    results = {}
    canvases = {}
    for pid, p in cfg["panels"].items():
        fig = p["figure"]
        if fig not in canvases:
            rgb = np.asarray(Image.open(pubdir / f"figure-{fig}.png").convert("RGB"))
            canvases[fig] = {"rgb": rgb, "ours": rgb.copy(), "pub_ink": np.zeros(rgb.shape[:2], bool),
                             "our_ink": np.zeros(rgb.shape[:2], bool)}
        cv = canvases[fig]
        full = cv["rgb"]
        fgrey = np.asarray(Image.fromarray(full).convert("L")).astype(int)
        ax, ay = calibrate(fgrey, p["box"], p["xticks"], p["yticks"])
        # work in a window around the panel: coordinates relative to (wx, wy)
        M = 40
        wx, wy = max(0, p["box"][0] - M), max(0, p["box"][2] - M)
        wx1, wy1 = min(full.shape[1], p["box"][1] + M), min(full.shape[0], p["box"][3] + M)
        rgb = full[wy:wy1, wx:wx1]
        grey = fgrey[wy:wy1, wx:wx1]
        box = [p["box"][0] - wx, p["box"][1] - wx, p["box"][2] - wy, p["box"][3] - wy]
        ax = (ax[0], ax[1] - wx, ax[2])
        ay = (ay[0], ay[1] - wy, ay[2])
        sat = rgb.astype(int).max(2) - rgb.astype(int).min(2)
        masks = inner_boxes(grey, box, sat) + [(m[0] - wx, m[1] - wx, m[2] - wy, m[3] - wy) for m in p.get("mask", [])]
        colours = {k: tuple(v) for k, v in p["colours"].items()}
        pub, region = series_masks(rgb, box, colours, masks)
        pub_closed = {k: close_gaps(v, p.get("close", 0)) & region for k, v in pub.items()}
        width, mark = p.get("width", 5), p.get("mark", 14)

        def render(series_files, how=None):
            out = {k: np.zeros(rgb.shape[:2], bool) for k in colours}
            for s in series_files:
                rows = read_curves(curves / s["file"])
                if how:
                    rows = transform(rows, p["kind"], how, p.get("time_scale", 1))
                if s.get("group"):
                    rows = [r for r in rows if r["group"] == s["group"]]
                paths = (km_paths(rows, ax, ay, p.get("time_scale", 1)) if p["kind"] == "km"
                         else roc_paths(rows, ax, ay))
                out[s["colour"]] |= draw(rgb.shape, paths.values(), width, mark)
            return {k: v & region for k, v in out.items()}

        ours = render(p["series"])
        pn, on = score((pub, pub_closed), ours, region)
        controls = []
        for c in p.get("wrong_input", []):
            cpn, con = score((pub, pub_closed), render(c["series"]), region)
            controls.append({"name": c["name"], "kind": "wrong_input", "score": round(min(cpn, con), 4)})
        xr = (p["xticks"][-1] - p["xticks"][0])
        for how in ["x0.95", "x1.05", f"shift{0.01 * xr * 1.08}"]:
            if p["kind"] == "roc" and how == "x1.05":
                continue
            cpn, con = score((pub, pub_closed), render(p["series"], how), region)
            name = {"x0.95": "survival x0.95" if p["kind"] == "km" else "TPR x0.95",
                    "x1.05": "survival x1.05"}.get(how, "shift 1% of the x axis")
            controls.append({"name": name, "kind": "near_miss", "score": round(min(cpn, con), 4)})
        for c in p.get("near_miss", []):
            cpn, con = score((pub, pub_closed), render(c["series"]), region)
            controls.append({"name": c["name"], "kind": "near_miss", "score": round(min(cpn, con), 4)})
        best = max(c["score"] for c in controls)
        thr = round(max(0.9, best + 0.005), 4)
        results[pid] = {"figure": fig, "pixels": {
            "tolerance_px": TOL, "dpi": 600, "published_near_ours": round(pn, 4), "ours_near_published": round(on, 4),
            "threshold": thr, "controls": controls},
            "calibration": {"x_residual_px": round(ax[2], 2), "y_residual_px": round(ay[2], 2)},
            "masked_boxes": [[int(m[0] + wx), int(m[1] + wx), int(m[2] + wy), int(m[3] + wy)] for m in masks],
            "published_pixels": {k: int(v.sum()) for k, v in pub.items()},
            "our_pixels": {k: int(v.sum()) for k, v in ours.items()}}
        # render: erase the published curves, draw ours in the published colours
        erase = np.zeros(rgb.shape[:2], bool)
        for v in pub.values():
            erase |= v
        erase = ndimage.binary_dilation(erase, iterations=2) & region & (grey > 60)
        win = (slice(wy, wy1), slice(wx, wx1))
        cv["ours"][win][erase] = 255
        for k, m in ours.items():
            cv["ours"][win][m] = colours[k]
            cv["our_ink"][win] |= m
        for v in pub.values():
            cv["pub_ink"][win] |= v
    for fig, cv in canvases.items():
        Image.fromarray(cv["ours"]).save(outdir / f"fig{fig}_ours.png", optimize=True)
        grey = np.asarray(Image.fromarray(cv["rgb"]).convert("L"))
        base = np.where(grey < 200, 200, 255).astype(np.uint8)
        ov = np.stack([base, base, base], -1)
        P, O = cv["pub_ink"], cv["our_ink"]
        ov[P & ~O] = (0, 190, 210)
        ov[O & ~P] = (220, 30, 30)
        ov[P & O] = (0, 0, 0)
        Image.fromarray(ov).save(outdir / f"fig{fig}_overlay.png", optimize=True)
    (outdir / "pixel_scores.json").write_text(json.dumps(results, indent=1) + "\n")
    for k, v in results.items():
        print(k, v["pixels"]["published_near_ours"], v["pixels"]["ours_near_published"],
              [c["score"] for c in v["pixels"]["controls"]])


if __name__ == "__main__":
    main()
