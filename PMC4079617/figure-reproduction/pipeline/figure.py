"""Fig. 1 (relative bias by contamination rate, n = 1500): our Table 1 drawn on the published frame, scored.

Usage: figure.py PUBLISHED_FIG1_PNG SIMULATION_JSON PUBLISHED_VALUES_JSON OUT_DIR

The published picture is SAS SGPANEL output: four panels (A linear moderate, B linear strong, C non-linear
moderate, D non-linear strong), each a 2 x 3 grid of cells (rows RR 1.5 and 2.0, columns outcome 10, 25 and
40%), with the log-binomial relative bias as a blue solid line and the robust Poisson one as a red dashed line
over the contamination rates 0%, 2% and 5% (category positions, equally spaced).

1. Calibrate every cell from the picture alone: its box from the frame lines, the y map (percentage bias) by
   least squares on the six tick marks 0 to -50 of its row, the x positions from the tick marks under its
   column. Nothing inside the boxes is fitted.
2. Read the published series: blue and red pixels inside each cell. Digitize their vertices (the median row of
   each colour within 3 px of each x tick) and compare them with Table 1 as printed (fig1.consistency).
3. Draw ours on the published frame: the published picture with both series removed (blue and red pixels
   painted white), our series drawn at the same places, colours, widths and dash pattern (fig1_ours.png), and
   on the published picture in green (fig1_overlay.png). Layout: drawn on the published picture.
4. Score each panel both ways at 2 px (300 dpi): the share of published series pixels within 2 px of ours and
   of ours within 2 px of the published, pooled over the panel's six cells; the smaller is the score (both series' ink together, since the red line hides the blue one where they overlap). Controls, scored with the same code: wrong input, the other confounder form at the same association
   level (A <-> C, B <-> D); near misses, ours x 1.05, x 0.95 and shifted by 0.6 points (1% of the 60-point
   axis). Pass mark: 0.95, or 0.02 above the best control when a control reaches 0.93. The dashed robust
   Poisson line is closed for scoring (gaps filled with a 4 px disk) and ours drawn solid. The resolution of the
   score: our second run (other seeds) scored against our main run with the same code.
Writes OUT_DIR/fig1_ours.png, fig1_overlay.png, fig1_<panel>_ours.png / _overlay.png (crops; the page crops the
published panel with the same box, panels.<p>.crop), figure.json.
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from scipy import ndimage  # noqa: E402

PANELS = {"a": ("linear", "moderate"), "b": ("linear", "strong"), "c": ("nonlinear", "moderate"),
          "d": ("nonlinear", "strong")}
PANEL_POS = {"a": (0, 0), "b": (1, 0), "c": (0, 1), "d": (1, 1)}   # (panel row, panel column) in the picture
WRONG = {"a": "c", "b": "d", "c": "a", "d": "b"}
RR = ("1.5", "2.0")
OUTCOMES = ("10%", "25%", "40%")
RATES = ("0%", "2%", "5%")
TOL = 2.0
DPI = 300
TICKS = (0, -10, -20, -30, -40, -50)


def runs(mask):
    """(start, end) of each run of True."""
    m = np.concatenate([[False], mask, [False]]).astype(int)
    d = np.diff(m)
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1))


def masks(a):
    r, g, b = (a[..., i].astype(int) for i in range(3))
    blue = (b - r > 40) & (b - g > 30)
    red = (r - b > 40) & (r - g > 30)
    return blue, red


def calibrate(a):
    """Cell boxes, y maps and x tick positions from the frame lines and tick marks."""
    gray = a.mean(2)
    dark = gray < 80
    H, W = gray.shape
    vcols = [x for x in range(W) if dark[:, x].sum() > 1150]
    hrows = [y for y in range(H) if dark[y, :].sum() > 1650]

    def groups(v):
        out = []
        for x in v:
            if out and x - out[-1][-1] <= 2:
                out[-1].append(x)
            else:
                out.append([x])
        return [(g[0], g[-1]) for g in out]
    vl, hl = groups(vcols), groups(hrows)
    # vertical frame lines: 4 per panel column; horizontal: 3 per panel row (top, middle, bottom of the grid)
    if len(vl) != 8 or len(hl) != 6:
        raise SystemExit(f"fig1: frame lines not found as expected ({len(vl)} vertical, {len(hl)} horizontal)")
    cells = {}
    for p, (pr, pc) in PANEL_POS.items():
        xs = vl[4 * pc:4 * pc + 4]
        ys = hl[3 * pr:3 * pr + 3]
        left = xs[0][0]
        for i, rr_ in enumerate(RR):
            y0, y1 = ys[i][1] + 1, ys[i + 1][0] - 1          # interior rows
            ticks = [(s + e) / 2 for s, e in runs(dark[:, left - 6]) if y0 - 3 <= (s + e) / 2 <= y1 + 3 and e - s <= 3]
            if len(ticks) != 6:
                raise SystemExit(f"fig1 {p} RR {rr_}: {len(ticks)} y ticks found")
            A = np.vstack([TICKS, np.ones(6)]).T
            (slope, icpt), res, *_ = np.linalg.lstsq(A, np.array(ticks), rcond=None)
            resid = float(np.abs(A @ [slope, icpt] - ticks).max())
            bottom = ys[2][1] + 1
            for j, py in enumerate(OUTCOMES):
                x0, x1 = xs[j][1] + 1, xs[j + 1][0] - 1
                xt = [(s + e) / 2 for s, e in runs(dark[bottom + 6, :]) if x0 <= (s + e) / 2 <= x1 and e - s <= 3]
                if len(xt) != 3:
                    raise SystemExit(f"fig1 {p} {py}: {len(xt)} x ticks found")
                cells[(p, rr_, py)] = {"box": [int(x0), int(x1), int(y0), int(y1)], "xticks": xt,
                                       "y_per_point": float(slope), "y_at_0": float(icpt), "tick_residual_px": resid,
                                       "y_limits": [float((y1 + 0.5 - icpt) / slope), float((y0 - 0.5 - icpt) / slope)]}
    return cells


def series(values, key):
    """Our (or the paper's) Table 1 values of one cell: {model: [v0, v2, v5]}."""
    return values[key]


def ours_values(sim, run="main"):
    out = {}
    cells = sim["runs"][run]["n1500"]
    for p, (form, lev) in PANELS.items():
        for rr_ in RR:
            for py in OUTCOMES:
                c = cells[f"{rr_}|{py}|{form}|{lev}"]
                out[(p, rr_, py)] = {m: [c[r][m]["relbias"] for r in RATES] for m in ("LB", "RP")}
    return out


def paper_values(pub):
    out = {}
    rows = pub["tables"]["table1"]["rows"]
    for p, (form, lev) in PANELS.items():
        for rr_ in RR:
            for py in OUTCOMES:
                rs = [r for r in rows if r["rr"] == rr_ and r["py"] == py]
                out[(p, rr_, py)] = {m: [float(r["cells"][f"{form}|{lev}|{m}"]) for r in rs] for m in ("LB", "RP")}
    return out


def to_px(cal, vals):
    xs = np.array(cal["xticks"])
    ys = cal["y_at_0"] + cal["y_per_point"] * np.array(vals)
    return xs, ys


def draw(base, cal, values, colors, width_px, out, only=None, mono=None, models=("LB", "RP"), solid=False, dash=(16.0, 8.0)):
    """Draw values on base (an RGB array) at the calibrated places; returns the RGB array of the drawing."""
    H, W = base.shape[:2]
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(base, interpolation="nearest", extent=(-0.5, W - 0.5, H - 0.5, -0.5))
    ax.set_xlim(-0.5, W - 0.5)
    ax.set_ylim(H - 0.5, -0.5)
    ax.axis("off")
    lw = width_px * 72 / 100
    for key, c in cal.items():
        if only and key[0] != only:
            continue
        for m in models:
            xs, ys = to_px(c, values[key][m])
            ls = "-" if (m == "LB" or solid) else (0, (dash[0] / width_px, dash[1] / width_px))
            ax.plot(xs, ys, color=mono or colors[m], lw=lw, ls=ls, solid_capstyle="butt", dash_capstyle="butt",
                    antialiased=True)
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    plt.close(fig)
    if out:
        Image.fromarray(img).save(out)
    return img


def score_panel(pub_masks, our_masks, cal, p):
    """Both-way shares within TOL px, pooled over the cells of panel p. The ink of both series is scored
    together: where the two published lines overlap, the red one hides the blue one."""
    pn = po = on = oo = 0
    for key, c in cal.items():
        if key[0] != p:
            continue
        x0, x1, y0, y1 = c["box"]
        sl = (slice(y0 + 2, y1 - 1), slice(x0 + 2, x1 - 1))   # inside the frame lines
        P = pub_masks["LB"][sl] | pub_masks["RP"][sl]
        O = our_masks["LB"][sl] | our_masks["RP"][sl]
        dO = ndimage.distance_transform_edt(~O) if O.any() else np.full(O.shape, np.inf)
        dP = ndimage.distance_transform_edt(~P) if P.any() else np.full(P.shape, np.inf)
        pn += P.sum(); po += (dO[P] <= TOL).sum()
        on += O.sum(); oo += (dP[O] <= TOL).sum()
    return {"published_near_ours": round(float(po / pn), 4), "ours_near_published": round(float(oo / on), 4),
            "published_px": int(pn), "ours_px": int(on)}


def our_masks_of(blank_shape, cal, values, width, colors):
    white = np.full(blank_shape, 255, np.uint8)
    out = {}
    for m in ("LB", "RP"):
        img = draw(white, cal, values, colors, width, None, models=(m,), solid=True)
        b, r = masks(img)
        out[m] = b if m == "LB" else r
    return out


def main():
    pub_png, sim_path, pub_path, out_dir = sys.argv[1:5]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    a = np.asarray(Image.open(pub_png).convert("RGB"))
    sim = json.load(open(sim_path))
    pub = json.load(open(pub_path))
    cal = calibrate(a)
    blue, red = masks(a)
    inside = np.zeros(blue.shape, bool)
    for c in cal.values():
        x0, x1, y0, y1 = c["box"]
        inside[y0:y1 + 1, x0:x1 + 1] = True
    pub_m = {"LB": blue & inside, "RP": red & inside}
    # for scoring, the dashed robust Poisson line is closed (its gaps filled) and ours is drawn solid, so
    # the score does not depend on the phase of the dashes
    yy, xx = np.mgrid[-4:5, -4:5]
    pub_s = {"LB": pub_m["LB"], "RP": ndimage.binary_closing(red, structure=(xx**2 + yy**2) <= 16) & inside}
    # colours and line width of the published series
    colors = {m: tuple(a[pub_m[m]].mean(0) / 255) for m in ("LB", "RP")}
    paper = paper_values(pub)
    # stroke width: the blue ink of each cell over the length of the paper's log-binomial polyline (the median over
    # the cells); dash pattern: the red runs along the first segment of each cell, sampled at 0.1 px, corrected
    # for the stroke's round ends
    wl, on_l, off_l = [], [], []
    for key, c in cal.items():
        x0, x1, y0, y1 = c["box"]
        xs, ys = to_px(c, paper[key]["LB"])
        wl.append(pub_m["LB"][y0 + 2:y1 - 1, x0 + 2:x1 - 1].sum() / np.hypot(np.diff(xs), np.diff(ys)).sum())
        xr, yr = to_px(c, paper[key]["RP"])
        L = float(np.hypot(xr[1] - xr[0], yr[1] - yr[0]))
        t = np.linspace(0, 1, int(L * 10))
        on = np.array([pub_m["RP"][int(round(y)) - 1:int(round(y)) + 2, int(round(x))].any()
                       for x, y in zip(xr[0] + (xr[1] - xr[0]) * t, yr[0] + (yr[1] - yr[0]) * t)])
        r = runs(on)
        on_l += [(e - s_ + 1) / 10 for s_, e in r[1:-1]]
        off_l += [(e - s_ + 1) / 10 for s_, e in runs(~on)[1:-1]]
    width = float(np.median(wl))
    dash = (float(np.median(on_l)) - width, float(np.median(off_l)) + width)
    # 2. the published vertices against Table 1
    digit = []
    for key, c in cal.items():
        x0, x1, y0, y1 = c["box"]
        for m, mk in (("LB", pub_m["LB"]), ("RP", pub_m["RP"])):
            for xi, (xt, rate) in enumerate(zip(c["xticks"], RATES)):
                lo, hi = int(round(xt - 3)), int(round(xt + 3))
                ys = np.flatnonzero(mk[y0:y1 + 1, lo:hi + 1].any(1)) + y0
                v = None if ys.size == 0 else round((float(np.median(ys)) - c["y_at_0"]) / c["y_per_point"], 2)
                digit.append({"panel": key[0], "rr": key[1], "py": key[2], "model": m, "rate": rate,
                              "printed": paper[key][m][xi], "read": v})
    read = [d for d in digit if d["read"] is not None]
    within = [d for d in read if abs(d["read"] - d["printed"]) <= 1.0]
    # 3. draw
    blank = a.copy()
    sat = a.max(2).astype(int) - a.min(2).astype(int)
    blank[inside & (sat > 30)] = 255
    left = int((masks(blank)[0] | masks(blank)[1]).sum())
    ours = ours_values(sim)
    draw(blank, cal, ours, colors, width, out_dir / "fig1_ours.png", dash=dash)
    draw(a, cal, ours, colors, width, out_dir / "fig1_overlay.png", mono=(0.0, 0.62, 0.25), dash=dash)
    # 4. score
    our_m = our_masks_of(a.shape, cal, ours, width, colors)
    variants = {"x1.05": {k: {m: [x * 1.05 for x in v[m]] for m in v} for k, v in ours.items()},
                "x0.95": {k: {m: [x * 0.95 for x in v[m]] for m in v} for k, v in ours.items()},
                "shift": {k: {m: [x - 0.6 for x in v[m]] for m in v} for k, v in ours.items()}}
    var_m = {n: our_masks_of(a.shape, cal, v, width, colors) for n, v in variants.items()}
    wrong = {k: ours[(WRONG[k[0]],) + k[1:]] for k in ours}
    wrong_m = our_masks_of(a.shape, cal, wrong, width, colors)
    second = ours_values(sim, "second")
    second_m = our_masks_of(a.shape, cal, second, width, colors)
    paper_m = our_masks_of(a.shape, cal, paper, width, colors)
    panels = {}
    for p, (form, lev) in PANELS.items():
        s = score_panel(pub_s, our_m, cal, p)
        ctrls = [{"name": f"Panel {WRONG[p].upper()} values (the other confounder form)", "kind": "wrong_input",
                  "score": min(score_panel(pub_s, wrong_m, cal, p)[k] for k in ("published_near_ours", "ours_near_published"))}]
        for n, why in (("x1.05", "ours x 1.05"), ("x0.95", "ours x 0.95"), ("shift", "ours shifted by -0.6 points")):
            sc = score_panel(pub_s, var_m[n], cal, p)
            ctrls.append({"name": why, "kind": "near_miss", "score": min(sc["published_near_ours"], sc["ours_near_published"])})
        best = max(c["score"] for c in ctrls)
        thr = 0.95 if best < 0.93 else round(best + 0.02, 4)
        s2 = score_panel(pub_s, second_m, cal, p)
        s22 = score_panel(our_m, second_m, cal, p)
        sp = score_panel(pub_s, paper_m, cal, p)
        boxes = [c for k, c in cal.items() if k[0] == p]
        x0 = min(c["box"][0] for c in boxes) - 1
        x1 = max(c["box"][1] for c in boxes) + 1
        y0 = min(c["box"][2] for c in boxes) - 1
        y1 = max(c["box"][3] for c in boxes) + 1
        for name in ("ours", "overlay"):
            Image.open(out_dir / f"fig1_{name}.png").crop((x0 - 120, y0 - 45, x1 + 42, y1 + 105)).save(
                out_dir / f"fig1_{p}_{name}.png")
        panels[p] = {"form": form, "level": lev, "tolerance_px": TOL, "dpi": DPI, **s, "threshold": thr,
                     "controls": ctrls, "second_run": {k: s2[k] for k in ("published_near_ours", "ours_near_published")},
                     "second_run_vs_ours": round(min(s22["published_near_ours"], s22["ours_near_published"]), 4),
                     "paper_table1_drawn": {k: sp[k] for k in ("published_near_ours", "ours_near_published")},
                     "crop": [x0 - 120, y0 - 45, x1 + 42, y1 + 105]}
    doc = {"about": "Fig. 1: our Table 1 (n = 1500) drawn on the published picture with its series removed; "
                    "both-way pixel scores per panel with controls; the published vertices read back against Table 1.",
           "picture": {"size": [int(a.shape[1]), int(a.shape[0])], "dpi": DPI, "line_width_px": round(width, 2), "dash_px": [round(d, 1) for d in dash],
                       "colors": {m: [round(255 * x) for x in c] for m, c in colors.items()},
                       "series_pixels_left_after_removal": left},
           "calibration": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in cal.items()},
           "max_tick_residual_px": round(max(c["tick_residual_px"] for c in cal.values()), 3),
           "panels": panels,
           "consistency": {"vertices": len(digit), "read": len(read), "within_1_point": len(within),
                           "max_abs_difference": round(max(abs(d["read"] - d["printed"]) for d in read), 2),
                           "vertices_detail": digit}}
    (out_dir / "figure.json").write_text(json.dumps(doc, indent=1) + "\n")
    for p, v in panels.items():
        print(f"fig1 {p}: {min(v['published_near_ours'], v['ours_near_published']):.4f} (threshold {v['threshold']}, "
              f"controls {[c['score'] for c in v['controls']]}; second run {v['second_run']}; paper's Table 1 drawn {v['paper_table1_drawn']})",
              file=sys.stderr)
    print(f"fig1 vertices: {len(within)} of {len(read)} read within 1 point of Table 1", file=sys.stderr)


if __name__ == "__main__":
    main()
