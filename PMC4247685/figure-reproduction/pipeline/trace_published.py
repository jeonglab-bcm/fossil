"""Trace the curves of Figs 3 to 5 back into numbers, so the paper's curves can be drawn and
compared with ours as data.

Fig. 3: two density curves. Figs 4 and 5: two Kaplan-Meier step curves. In each, the solid line is
the largest connected stroke in the plot frame and the dashed line is the rest. Pixel positions map
to data through the axis ticks that paper_measure.py found.

Two checks keep the tracer honest, and the script fails if either slips:
  - each traced density in Fig. 3 must enclose an area of 1, as a density does;
  - Fig. 5 is drawn from the paper's own Table S3, so its traced curves must sit on the Kaplan-Meier
    curves of that table (mean gap under 0.02).

Usage: python3 trace_published.py <published dir> <paper_measure.json> <fig5_clinical.csv> <out.json>
"""
import csv
import json
import sys

import numpy as np
from PIL import Image

TICK_VALUES = {
    "fig3": {"x": [-1, -0.5, 0, 0.5, 1], "y": [2.5, 2, 1.5, 1, 0.5, 0]},
    "fig4": {"x": [0, 20, 40, 60, 80, 100, 120], "y": [1, 0.8, 0.6, 0.4, 0.2, 0]},
    "fig5": {"x": [0, 500, 1000, 1500], "y": [1, 0.8, 0.6, 0.4, 0.2, 0]},
}
INK = 200          # grey level below which a pixel is ink
GAP_MAX = 7        # dashes in one dashed line are at most this far apart


def axis_maps(measure, fig):
    """Least-squares linear maps from pixel index to data value, from the tick positions."""
    t = measure[fig]["ticks"]
    fx = np.polyfit(t["x"], TICK_VALUES[fig]["x"], 1)
    fy = np.polyfit(t["y"], TICK_VALUES[fig]["y"], 1)
    return (lambda p: float(np.polyval(fx, p))), (lambda p: float(np.polyval(fy, p)))


def load(path, measure, fig, pad=4):
    """Grey levels, with everything outside the plot frame (and the frame itself) blanked."""
    a = np.asarray(Image.open(path).convert("L"), dtype=float)
    f = measure[fig]["frame"]
    keep = np.zeros_like(a, dtype=bool)
    keep[int(f["top"]) + pad:int(f["bottom"]) - pad, int(f["left"]) + pad:int(f["right"]) - pad] = True
    a[~keep] = 255.0
    return a


def runs1d(mask):
    """(start, end) of consecutive True runs, end exclusive."""
    m = np.concatenate([[False], mask, [False]])
    d = np.diff(m.astype(int))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


# Kaplan-Meier curves ------------------------------------------------------------------------
#
# The solid line, with its uprights and censor marks, is one connected stroke: the largest ink
# component in the frame. The dashed line is every other component, its dashes. Away from its drops
# and censor marks, each line is horizontal and 2 or 3 pixels thick, so a pixel column cuts it as a
# short ink run. Each line is then the longest chain of its runs that never rises (a Kaplan-Meier
# curve only falls), which drops the stray runs a censor mark or a touching dash leaves.

def split_lines(mask):
    """Masks of the solid line (the largest connected stroke) and the dashed line (the rest)."""
    from scipy import ndimage
    lab, _ = ndimage.label(mask, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    solid = lab == int(np.argmax(sizes))
    return {"solid": solid, "dashed": mask & ~solid}


def flat_runs(m, ink):
    """(x, y) for each column's ink run of at most 5 pixels: a cut through a horizontal stroke."""
    out = []
    for x in range(m.shape[1]):
        for s, e in runs1d(m[:, x]):
            if e - s <= 5:
                out.append((x, float((np.arange(s, e) * ink[s:e, x]).sum() / ink[s:e, x].sum())))
    return out


def falling_chain(pts, tol=1.5):
    """Longest chain of (x, y) points with x increasing and y never rising by more than tol pixels
    on the image (pixel y grows downward, so the curve's level never rises)."""
    pts = sorted(pts)
    xs = np.array([p[0] for p in pts])
    ys = np.array([p[1] for p in pts])
    n = len(pts)
    best = np.ones(n, dtype=int)
    prev = np.full(n, -1)
    for j in range(n):
        ok = (xs[:j] < xs[j]) & (ys[:j] <= ys[j] + tol)
        if ok.any():
            i = np.where(ok)[0][np.argmax(best[:j][ok])]
            best[j], prev[j] = best[i] + 1, i
    j = int(np.argmax(best))
    chain = []
    while j >= 0:
        chain.append(pts[j])
        j = prev[j]
    return chain[::-1]


def levels(chain, jump=2.0):
    """Group a chain into flat stretches: [x_first, x_last, y]."""
    out = []
    for x, y in chain:
        if out and abs(y - out[-1][2]) <= jump:
            out[-1][1] = x
            out[-1][3].append(y)
        else:
            out.append([x, x, y, [y]])
        out[-1][2] = float(np.median(out[-1][3]))
    return [[a, b, y] for a, b, y, _ in out]


def drop_column(mask, x0, x1, y_hi, y_lo):
    """Where a line drops from row y_hi to row y_lo, between the end of one flat stretch (x0) and
    the start of the next (x1): the upright is the last stretch of columns, up to x1, inked over at
    least a third of the rows between (a dashed upright is about 60% ink). A new level starts where
    its upright stands. mask is all the ink: an upright can touch the other line's stroke."""
    lo, hi = int(round(y_hi)) + 2, int(round(y_lo)) - 1
    if hi - lo < 2:
        return x1
    cols = [x for x in range(max(x0 - 1, 0), x1 + 2) if mask[lo:hi, x].mean() >= 0.35]
    if not cols:
        return x1
    run = [cols[-1]]
    while run[-1] - 1 in cols:
        run.append(run[-1] - 1)
    return float(np.mean(run))


def staircase(m, p, l):
    """Drops between flat stretch p and the next one, l, as (column, row) pairs. Several patients
    progressing a few days apart draw a cascade of uprights with shelves too short to read. An
    upright hangs from the line's current level and reaches down to the shelf it lands on, so each
    one is a new level; its column is the middle of its stroke."""
    lo, hi = int(round(p[2])) + 2, int(round(l[2])) + 2
    out, depth, x = [], p[2], max(p[1] - 1, 0)

    def upright(x, top_max):
        rows = np.where(m[lo:hi, x])[0] + lo
        if len(rows) < 5 or rows.min() > top_max:
            return None
        bottom = rows.max()
        if (m[rows.min():bottom + 1, x]).mean() < 0.45:
            return None
        return bottom

    while x <= l[0] + 1:
        b = upright(x, depth + 6)
        if b is not None and b > depth + 10:
            cols = [x]
            while x + 1 <= l[0] + 1:
                nb = upright(x + 1, depth + 6)
                if nb is None or nb < b - 4:
                    break
                x += 1
                cols.append(x)
                b = max(b, nb)
            depth = l[2] if b > l[2] - 7 else float(b)
            out.append((float(np.mean(cols)), depth))
        x += 1
    return out


def trace_km(path, measure, fig):
    a = load(path, measure, fig)
    ink = np.clip(255.0 - a, 0, None)
    fx, fy = axis_maps(measure, fig)
    t = measure[fig]["ticks"]
    y_one = float(np.polyval(np.polyfit(TICK_VALUES[fig]["y"], t["y"], 1), 1.0))
    curves = {}
    allink = a < INK
    for kind, m in split_lines(allink).items():
        cands = flat_runs(m, ink)
        lev = levels(falling_chain(cands))
        lev = [l for l in lev if l[1] - l[0] >= 2 or l is lev[-1]]
        # Every curve starts at 1. Where the other line covers that stretch, start this one there.
        if fy(lev[0][2]) < 0.99:
            lev.insert(0, [lev[0][0] - 1, lev[0][0] - 1, y_one])
        # A step only a few pixels wide can lose to its neighbours in the chain; put back any flat
        # stretch of this line that sits between two of its levels.
        full = []
        for i, l in enumerate(lev):
            full.append(l)
            if i + 1 < len(lev):
                nxt = lev[i + 1]
                mid = [(x, y) for x, y in cands if l[1] < x < nxt[0] and l[2] + 3 < y < nxt[2] - 3]
                full.extend(s for s in levels(sorted(mid)) if s[1] - s[0] >= 1)
        steps = [(0.0, 1.0)]
        for p, l in zip(full, full[1:]):
            for x, y in staircase(m, p, l):
                steps.append((fx(x), fy(y)))
            if steps[-1][1] - fy(l[2]) > 0.004:
                steps.append((fx(drop_column(allink, p[1], l[0], p[2], l[2])), fy(l[2])))
        last = full[-1]
        # A line that ends in a drop (the last patient progressing) has no flat stretch at its
        # final level: follow the upright down from the end of the last flat stretch.
        x_end, best = last[1], None
        for x in range(last[1] - 1, min(last[1] + 8, m.shape[1])):
            col = m[int(round(last[2])):, x]
            y, gap = 0, 0
            for y in range(len(col)):
                gap = 0 if col[y] else gap + 1
                if gap > GAP_MAX:
                    break
            reach = last[2] + y - gap
            if best is None or reach > best[1]:
                best = (x, reach)
        if best and best[1] - last[2] > 10:
            x_end = best[0]
            steps.append((fx(best[0]), max(fy(best[1]), 0.0)))
        curves[kind] = {"steps": [[round(t, 3), round(v, 4)] for t, v in steps], "end": round(fx(x_end), 3)}
    return curves


# Density curves ------------------------------------------------------------------------------
#
# The solid curve is one connected stroke, the largest ink component in the frame; the dashed
# curve is every other component, its dashes. Each is read column by column (the centre of its ink)
# and the dashed curve's gaps are filled by straight lines.

def trace_density(path, measure, fig="fig3"):
    from scipy import ndimage
    a = load(path, measure, fig, pad=5)
    fx, fy = axis_maps(measure, fig)
    mask = a < INK
    ink = np.clip(255.0 - a, 0, None)
    lab, _ = ndimage.label(mask, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    solid = lab == int(np.argmax(sizes))
    dashed = mask & ~solid
    curves = {}
    for kind, m in (("solid", solid), ("dashed", dashed)):
        pts = []
        for x in range(m.shape[1]):
            rs = runs1d(m[:, x])
            if not rs:
                continue
            if len(pts) >= 3 and len(rs) > 1:
                # Where a dash touches the solid stroke, keep the run that continues the curve:
                # the one nearest the straight-line extension of the last three points.
                (xa, ya), (xb, yb) = pts[-3], pts[-1]
                pred = yb + (yb - ya) / (xb - xa) * (x - xb)
                s, e = min(rs, key=lambda r: 0 if r[0] - 1 <= pred <= r[1] else min(abs(pred - r[0]), abs(pred - r[1])))
            else:
                s, e = max(rs, key=lambda r: ink[r[0]:r[1], x].sum())
            y = float((np.arange(s, e) * ink[s:e, x]).sum() / ink[s:e, x].sum())
            pts.append((x, y))
        # Each column's centre is quantised by the dashes' rounded ends and the antialiasing; a
        # running mean over a few columns takes that out without moving the peaks.
        xs = np.array([p[0] for p in pts], dtype=float)
        ys = np.array([p[1] for p in pts])
        half = 3 if kind == "solid" else 6
        smooth = np.array([ys[np.abs(xs - x) <= half].mean() for x in xs])
        curves[kind] = [[round(fx(x), 4), round(max(fy(y), 0.0), 4)] for x, y in zip(xs, smooth)]
    return curves


# Checks ------------------------------------------------------------------------------------

def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def km_from_data(rows, time, event, group):
    """Kaplan-Meier steps (time, level) for one group, the way survfit draws them."""
    obs = sorted((float(r[time]), int(r[event])) for r in rows if r["group"] == group and r[time] not in ("", "NA"))
    n, s, steps = len(obs), 1.0, [(0.0, 1.0)]
    i = 0
    while i < len(obs):
        t = obs[i][0]
        d = sum(1 for o in obs[i:] if o[0] == t and o[1] == 1)
        c = sum(1 for o in obs[i:] if o[0] == t)
        if d:
            s *= 1 - d / n
            steps.append((t, s))
        n -= c
        i += c
    return steps, obs[-1][0]


def level_at(steps, t):
    lev = steps[0][1]
    for t0, v in steps:
        if t0 <= t:
            lev = v
    return lev


def mean_gap(a, b, t_end):
    """Mean vertical gap between two step curves over [0, t_end]."""
    grid = np.linspace(0, t_end, 4000)
    return float(np.mean([abs(level_at(a, t) - level_at(b, t)) for t in grid]))


def main():
    pub, measure_path, fig5_csv, out_path = sys.argv[1:5]
    with open(measure_path) as f:
        measure = json.load(f)
    paper = {
        "fig3": trace_density(f"{pub}/figure-3.png", measure),
        "fig4": trace_km(f"{pub}/figure-4.png", measure, "fig4"),
        "fig5": trace_km(f"{pub}/figure-5.png", measure, "fig5"),
    }
    check, ok = {}, True
    for kind, pts in paper["fig3"].items():
        p = np.array(pts)
        area = float(np.sum(np.diff(p[:, 0]) * (p[1:, 1] + p[:-1, 1]) / 2))
        check[f"fig3_{kind}_area"] = round(area, 4)
        ok &= abs(area - 1) < 0.02
    rows = read_csv(fig5_csv)
    for kind, group in (("solid", "Group1"), ("dashed", "Group2")):
        truth, t_end = km_from_data(rows, "PFS", "progression", group)
        gap = mean_gap([tuple(s) for s in paper["fig5"][kind]["steps"]], truth, t_end)
        check[f"fig5_{kind}_mean_gap_to_table_s3"] = round(gap, 4)
        ok &= gap < 0.02
    with open(out_path, "w") as f:
        json.dump({"paper": paper, "check": check}, f, indent=1)
    print(json.dumps(check, indent=1))
    if not ok:
        sys.exit("trace_published.py: a check failed")


if __name__ == "__main__":
    main()
