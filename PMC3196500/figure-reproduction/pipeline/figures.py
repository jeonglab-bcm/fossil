"""Draw our curves on the published figures' pixel grids, score them, and write renders and overlays.

Usage: figures.py PUBLISHED_DIR SIMULATION.json OUT_DIR   (PUBLISHED_DIR: figure-reproduction/published)

Fig. 2 and Figs S1-S12 are R base-graphics plots: an L-shaped box per panel, a log x axis with 1-2-5 ticks
and a y axis with ticks every 0.05. For each panel we find the box and the tick marks in the published
image, fit the pixel map to the tick positions and their printed labels (nothing inside the box is
fitted), and draw our two curves (RRR > 30% and > 20%) at the published line width.

Scores, both ways, with a 2 px tolerance on the published grid: the share of the published curve pixels
within 2 px of ours, and of ours within 2 px of the published ink (dotted and dash-dot lines are closed
along x first, so their gaps do not count against ours). The panel's score is the smaller one.

Controls per panel (same code, same panel): wrong inputs (the scenario with the other control-group risk
range; the scenario with another tau^2) and near misses (our curve x1.05 and x0.95; shifted by one point
along x). Our second run (other seeds) is scored too, as the chance-level reference.

Outputs: fig2_ours.png, fig2_overlay.png, figS<k>_ours.png, figS<k>_overlay.png (S5-S7 are byte copies
of S1-S3 in the paper, scored against both the scenario their captions name and the one they show), and
figures.json with every score.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

TOL = 2
DARK = 160
# Figure -> (file, panels). Panel order: top row left to right, then the bottom row (S figures);
# patients then events (Fig. 2).
FIGURES = {
    "fig2": ("fig2.png", "patients", [("cochrane", "5-15", 0.15, 0, "patients"), ("cochrane", "5-15", 0.15, 0, "events")]),
}
S_SCENARIOS = {
    1: ("cochrane", ("1-5", "5-15"), 0, "patients"), 2: ("cochrane", ("1-5", "5-15"), 0, "events"),
    3: ("cochrane", ("1-5", "5-15"), 10, "patients"), 4: ("cochrane", ("1-5", "5-15"), 10, "events"),
    5: ("common", ("1-5", "5-15"), 0, "patients"), 6: ("common", ("1-5", "5-15"), 0, "events"),
    7: ("common", ("1-5", "5-15"), 10, "patients"), 8: ("common", ("1-5", "5-15"), 10, "events"),
    9: ("common", ("15-40", "40-80"), 0, "patients"), 10: ("common", ("15-40", "40-80"), 0, "events"),
    11: ("common", ("15-40", "40-80"), 10, "patients"), 12: ("common", ("15-40", "40-80"), 10, "events"),
}
for k, (sizes, pcs, rrr, axis) in S_SCENARIOS.items():
    FIGURES[f"figS{k}"] = (f"figS{k}.png", axis,
                           [(sizes, pc, tau, rrr, axis) for pc in pcs for tau in (0.05, 0.15, 0.25)])
# S5-S7 in the paper are byte copies of S1-S3: the scenario they show.
DUPLICATE_OF = {"figS5": "figS1", "figS6": "figS2", "figS7": "figS3"}
TAUS = (0.05, 0.15, 0.25)
OTHER_PC = {"1-5": "5-15", "5-15": "1-5", "15-40": "40-80", "40-80": "15-40"}
OTHER_TAU = {0.05: 0.25, 0.15: 0.05, 0.25: 0.05}


def first_tick(fig, axis):
    """The first labelled x tick, as printed (read from the figures' tick labels)."""
    if axis == "events":
        return 50
    return 500 if fig in ("fig2", "figS3", "figS7") else 200


def width_of(fig, axis, sizes, pc, widths):
    return widths["events"] if axis == "events" else widths["patients_" + ("high_pc" if pc in ("15-40", "40-80") else "low_pc")]


def runs_of(seq):
    """(start, end) of runs of True."""
    out, start = [], None
    for i, v in enumerate(seq):
        if v and start is None:
            start = i
        if not v and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(seq) - 1))
    return out


def find_panels(dark):
    """Plot boxes (left, top, right, bottom) of the L-shaped R boxes, top row first."""
    h, w = dark.shape
    boxes = []
    for x in range(w):
        for a, b in runs_of(dark[:, x]):
            if b - a < 0.25 * h:
                continue
            # The x axis: a long horizontal run starting at this column, at the bottom of the vertical run.
            for y in range(b, max(a, b - 3), -1):
                runs = [r for r in runs_of(dark[y, x:]) if r[0] == 0]
                if runs and runs[0][1] > 0.15 * w:
                    boxes.append((x, a, x + runs[0][1], y))
                    break
    # Keep one box per axis (the leftmost column of a thick line).
    out = []
    for bx in sorted(boxes, key=lambda b: (b[3], b[0])):
        if not any(abs(bx[0] - o[0]) <= 3 and abs(bx[3] - o[3]) <= 3 for o in out):
            out.append(bx)
    out.sort(key=lambda b: (round(b[3] / 20), b[0]))
    return out


def ticks(dark, box):
    left, top, right, bottom = box
    # y ticks: short marks to the left of the y axis
    ys = [r for r in runs_of([dark[y, max(0, left - 6):left - 1].sum() >= 3 for y in range(top, bottom + 1)])]
    yt = [top + (a + b) / 2 for a, b in ys]
    xs = [r for r in runs_of([dark[bottom + 2:bottom + 7, x].sum() >= 3 for x in range(left, right + 1)])]
    xt = [left + (a + b) / 2 for a, b in xs]
    return yt, xt


def tick_values_x(first, n):
    """1-2-5 sequence from the first tick."""
    vals, v = [], first
    mant = {1: 2, 2: 5, 5: 10}
    for _ in range(n):
        vals.append(v)
        m = int(round(v / 10 ** math.floor(math.log10(v))))
        v = v // m * mant[m] if m != 5 else v * 2
    return vals


def fit(pix, vals):
    a, b = np.polyfit(vals, pix, 1)
    res = np.array(pix) - (a * np.array(vals) + b)
    return float(a), float(b), float(np.abs(res).max())


def calibrate(dark, box, fig, axis):
    yt, xt = ticks(dark, box)
    yv = [0.05 * i for i in range(len(yt))][::-1]  # ticks are listed top to bottom
    ya, yb, yres = fit(yt, yv)
    xv = tick_values_x(first_tick(fig, axis), len(xt))
    xa, xb, xres = fit(xt, np.log10(xv))
    return {"box": list(box), "y_ticks": len(yt), "x_ticks": xv, "y_fit": [ya, yb], "x_fit": [xa, xb],
            "y_residual_px": round(yres, 2), "x_residual_px": round(xres, 2)}


def dilate(mask, r):
    out = mask.copy()
    h, w = mask.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            src = mask[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
            out[max(0, dy):h - max(0, -dy), max(0, dx):w - max(0, -dx)] |= src
    return out


def close_x(mask, g):
    """Close gaps of up to 2g pixels along x (dilate then erode with a horizontal segment)."""
    h, w = mask.shape
    d = mask.copy()
    for dx in range(1, g + 1):
        d[:, dx:] |= mask[:, :-dx]
        d[:, :-dx] |= mask[:, dx:]
    e = d.copy()
    for dx in range(1, g + 1):
        e[:, dx:] &= d[:, :-dx]
        e[:, :-dx] &= d[:, dx:]
    return e | mask


def curve_xy(run, rule, axis, width, th):
    c = run["curves"][rule][axis][str(width)]
    n = np.array(c["n"], float)
    h = np.array(c[f"over{th}"], float)
    x = np.arange(1, len(n) + 1) * width
    keep = n > 0
    return x[keep], h[keep] / n[keep]


def to_pix(cal, x, y):
    px = cal["x_fit"][0] * np.log10(x) + cal["x_fit"][1]
    py = cal["y_fit"][0] * y + cal["y_fit"][1]
    return px, py


def draw_curves(shape, cal, curves, width=1, dash=False, img=None, color=255):
    """Polylines of the curves, clipped to the panel box. Returns a boolean mask (or draws on img)."""
    left, top, right, bottom = cal["box"]
    canvas = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(canvas)
    for (x, y), pattern in curves:
        if len(x) == 0:
            continue
        px, py = to_pix(cal, x, y)
        pts = list(zip(px.tolist(), py.tolist()))
        if not dash or pattern is None:
            d.line(pts, fill=255, width=width)
        else:
            # a dash pattern along the polyline length (on, off, on, off ...)
            seg, total = pattern, sum(pattern)
            pos = 0.0
            for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
                L = math.hypot(x1 - x0, y1 - y0)
                t = 0.0
                while t < L:
                    ph = (pos + t) % total
                    acc, on, rest = 0, True, 0
                    for i, s in enumerate(seg):
                        if ph < acc + s:
                            on = i % 2 == 0
                            rest = acc + s - ph
                            break
                        acc += s
                    step = min(rest, L - t)
                    if on:
                        a = t / L
                        b = (t + step) / L
                        d.line([(x0 + a * (x1 - x0), y0 + a * (y1 - y0)), (x0 + b * (x1 - x0), y0 + b * (y1 - y0))],
                               fill=255, width=width)
                    t += step
                pos += L
    m = np.array(canvas) > 0
    clip = np.zeros_like(m)
    clip[top:bottom - 1, left + 2:right + 1] = True
    return m & clip


def published_ink(dark, cal):
    left, top, right, bottom = cal["box"]
    m = np.zeros_like(dark)
    m[top:bottom - 1, left + 2:right + 1] = dark[top:bottom - 1, left + 2:right + 1]
    return m


def score(pub, ours):
    """Share of published ink within TOL px of ours, and of ours within TOL px of the published ink."""
    if ours.sum() == 0 or pub.sum() == 0:
        return {"published_near_ours": 0.0, "ours_near_published": 0.0}
    near_ours = dilate(ours, TOL)
    near_pub = dilate(close_x(pub, 3), TOL)
    return {"published_near_ours": round(float((pub & near_ours).sum() / pub.sum()), 4),
            "ours_near_published": round(float((ours & near_pub).sum() / ours.sum()), 4)}


def scenario_key(sizes, pc, tau, rrr):
    return f"{sizes}_pc{pc}_tau{tau:.2f}_rrr{rrr}"


def panel_curves(run, rule, axis, width, scale=1.0, shift=0):
    out = []
    for th in ("30", "20"):
        x, y = curve_xy(run, rule, axis, width, th)
        out.append(((x + shift * width, np.clip(y * scale, 0, 1)), None))
    return out


def panel_specs(fig, gray):
    fname, axis, panels = FIGURES[fig]
    dark = gray < DARK
    boxes = find_panels(dark)
    if len(boxes) != len(panels):
        raise SystemExit(f"{fig}: found {len(boxes)} panels, expected {len(panels)}")
    out = []
    for box, (sizes, pc, tau, rrr, ax) in zip(boxes, panels):
        cal = calibrate(dark, box, fig, ax)
        out.append((cal, sizes, pc, tau, rrr, ax))
    return dark, out


def choose_rules(images, main_runs, widths):
    """The binning rule of each axis: the one whose curves score best on the figures (S5-S7 left out)."""
    scores = {}
    for fig, gray in images.items():
        if fig in DUPLICATE_OF:
            continue
        dark, specs = panel_specs(fig, gray)
        for cal, sizes, pc, tau, rrr, ax in specs:
            w = width_of(fig, ax, sizes, pc, widths)
            pub = published_ink(dark, cal)
            for rule in ("nearest", "interval"):
                s = score(pub, draw_curves(dark.shape, cal, panel_curves(main_runs[scenario_key(sizes, pc, tau, rrr)], rule, ax, w)))
                scores.setdefault(ax, {}).setdefault(rule, []).append(min(s.values()))
    search = {ax: {r: round(float(np.mean(v)), 4) for r, v in d.items()} for ax, d in scores.items()}
    chosen = {ax: max(d, key=d.get) for ax, d in search.items()}
    return chosen, {ax: {"mean_score": d, "panels": len(scores[ax]["nearest"])} for ax, d in search.items()}


def main():
    pub_dir, sim_path, out_dir = map(Path, sys.argv[1:4])
    widths = {"patients_low_pc": 500, "patients_high_pc": 200, "events": 50}
    sim = json.load(open(sim_path))
    main_runs, second = sim["runs"]["main"], sim["runs"]["replicate"]
    out_dir.mkdir(parents=True, exist_ok=True)
    images = {fig: np.array(Image.open(pub_dir / spec[0]).convert("L")) for fig, spec in FIGURES.items()}
    rules, search = choose_rules(images, main_runs, widths)
    res = {"tolerance_px": TOL, "rules": rules, "rule_search": search, "widths": widths, "figures": {}}
    for fig, (fname, axis, panels) in FIGURES.items():
        gray = images[fig]
        dark, specs = panel_specs(fig, gray)
        import hashlib
        fres = {"file": fname, "sha256": hashlib.sha256((pub_dir / fname).read_bytes()).hexdigest(),
                "size": list(gray.shape[::-1]), "panels": []}
        ours_all = np.zeros_like(dark)
        pub_all = np.zeros_like(dark)
        render = Image.fromarray(gray).convert("RGB")
        for cal, sizes, pc, tau, rrr, ax in specs:
            rule = rules[ax]
            w = width_of(fig, ax, sizes, pc, widths)
            key = scenario_key(sizes, pc, tau, rrr)
            pub = published_ink(dark, cal)
            ours = draw_curves(dark.shape, cal, panel_curves(main_runs[key], rule, ax, w))
            s = score(pub, ours)
            controls = []
            for name, kind, run, kw in (
                    (f"PC {OTHER_PC[pc]}% (wrong input)", "wrong_input", main_runs[scenario_key(sizes, OTHER_PC[pc], tau, rrr)], {}),
                    (f"tau2 {OTHER_TAU[tau]} (wrong input)", "wrong_input", main_runs[scenario_key(sizes, pc, OTHER_TAU[tau], rrr)], {}),
                    ("ours x1.05", "near_miss", main_runs[key], {"scale": 1.05}),
                    ("ours x0.95", "near_miss", main_runs[key], {"scale": 0.95}),
                    ("ours one point right", "near_miss", main_runs[key], {"shift": 1})):
                cm = draw_curves(dark.shape, cal, panel_curves(run, rule, ax, w, **kw))
                cs = score(pub, cm)
                controls.append({"name": name, "kind": kind, "score": min(cs.values())})
            sec_mask = draw_curves(dark.shape, cal, panel_curves(second[key], rule, ax, w))
            sec = score(pub, sec_mask)
            # Chance ceiling: our second run scored against our first, both drawn the same way.
            self_score = score(sec_mask, ours)
            other_rule = "interval" if rule == "nearest" else "nearest"
            alt = score(pub, draw_curves(dark.shape, cal, panel_curves(main_runs[key], other_rule, ax, w)))
            p = {"scenario": key, "axis": ax, "rule": rule, "calibration": cal, "width": w, **s, "controls": controls,
                 "chance_ceiling": min(self_score.values()),
                 "hypotheses": {"second_run": sec, f"rule_{other_rule}": alt}}
            if fig in DUPLICATE_OF:
                ck = scenario_key("cochrane", pc, tau, rrr)
                p["hypotheses"]["cochrane_sizes"] = score(pub, draw_curves(dark.shape, cal, panel_curves(main_runs[ck], rule, ax, w)))
            fres["panels"].append(p)
            ours_all |= ours
            pub_all |= pub
            left, top, right, bottom = cal["box"]
            dashed = [((x, y), pat) for ((x, y), _), pat in zip(panel_curves(main_runs[key], rule, ax, w), ((4, 3, 1, 3), (1, 2)))]
            ink = draw_curves(dark.shape, cal, dashed, dash=True)
            arr = np.array(render)
            region = np.zeros_like(dark)
            region[top:bottom - 1, left + 2:right + 1] = True
            arr[region & dark] = 255
            arr[ink] = 0
            render = Image.fromarray(arr)
        render.save(out_dir / f"{fig}_ours.png", optimize=True)
        ov = np.stack([gray] * 3, axis=-1).astype(np.uint8)
        ov[pub_all] = (110, 110, 110)
        ov[ours_all] = (215, 48, 39)
        ov[ours_all & dilate(pub_all, 1)] = (0, 0, 0)
        Image.fromarray(ov).save(out_dir / f"{fig}_overlay.png", optimize=True)
        res["figures"][fig] = fres
    with open(out_dir / "figures.json", "w") as f:
        json.dump(res, f, indent=1)
        f.write("\n")
    print("rules", rules, search, file=sys.stderr)
    for fig, fr in res["figures"].items():
        print(fig, [(round(min(p["published_near_ours"], p["ours_near_published"]), 2),
                     round(p["chance_ceiling"], 2),
                     [round(c["score"], 2) for c in p["controls"]]) for p in fr["panels"]], file=sys.stderr)


if __name__ == "__main__":
    main()
