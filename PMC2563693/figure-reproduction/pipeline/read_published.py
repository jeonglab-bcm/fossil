"""Read the plotted values out of the vector supplementary figures (Figs S1, S2, S3, S5).

Usage: read_published.py SUPPLEMENT_DIR OUT.json

The supplementary figures are vector PDFs: bars, line markers and box-plot strokes are drawing
commands with exact coordinates. Each panel's y axis is calibrated from its printed tick labels
(a least-squares line through the label centres; the residual is recorded), and every bar top,
marker centre and box edge is converted to data units. The -log(p) labels above the bars are
read as text and assigned to the nearest bar group.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pymupdf

COLOURS = {
    "Gene": (0.31, 0.51, 0.75),
    "PAC": (0.76, 0.32, 0.31),
    "Mean": (0.61, 0.73, 0.35),
    "Median": (0.51, 0.4, 0.64),
    "PCA": (0.3, 0.67, 0.77),
}
WITHIN = ["NF-kB", "Leukemia", "Prostate", "Breast Netherlands", "Breast USA", "Lung Boston", "Lung Michigan"]
CROSS = ["Breast Netherlands -> Breast USA", "Breast USA -> Breast Netherlands",
         "Lung Michigan -> Lung Boston", "Lung Boston -> Lung Michigan"]


def close(c, ref, tol=0.02):
    return c is not None and len(c) == 3 and all(abs(a - b) <= tol for a, b in zip(c, ref))


def words(page):
    """Text spans as (text, x centre, y centre, x0, x1)."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                t = s["text"].strip()
                if t:
                    x0, y0, x1, y1 = s["bbox"]
                    out.append((t, (x0 + x1) / 2, (y0 + y1) / 2, x0, x1))
    return out


def number(t):
    t = t.replace(" ", "")
    return float(t) if re.fullmatch(r"-?\d+(\.\d+)?", t) else None


def axes(page, values):
    """Y axes: groups of tick labels sharing a right edge, each with a fitted y -> value map."""
    labels = [(number(t), xc, yc, x1) for t, xc, yc, x0, x1 in words(page) if number(t) is not None]
    labels = [l for l in labels if l[0] in values]
    groups = defaultdict(list)
    for v, xc, yc, x1 in labels:
        groups[round(x1 / 4)].append((v, xc, yc, x1))
    out = []
    for g in groups.values():
        g.sort(key=lambda l: l[2])
        # split a column of labels into runs with a monotone value sequence (one run per panel)
        run = [g[0]]
        runs = []
        for l in g[1:]:
            if l[0] < run[-1][0] and l[2] - run[-1][2] < 40:
                run.append(l)
            else:
                runs.append(run)
                run = [l]
        runs.append(run)
        for r in runs:
            if len(r) < 4:
                continue
            v = np.array([l[0] for l in r])
            y = np.array([l[2] for l in r])
            b, a = np.polyfit(y, v, 1)
            resid = float(np.max(np.abs(a + b * y - v)))
            out.append({"x": float(np.mean([l[3] for l in r])), "ytop": float(y.min()) - 5,
                        "ybot": float(y.max()) + 5, "a": float(a), "b": float(b), "resid": resid})
    return out


def axis_for(ax, x, y):
    cands = [a for a in ax if a["x"] < x and a["ytop"] - 3 <= y <= a["ybot"] + 3]
    return max(cands, key=lambda a: a["x"]) if cands else None


def bars(page, values, group_names_by_panel):
    """Bar heights per panel: {panel index: [{method: value}] per bar group, left to right}."""
    ax = axes(page, values)
    items = []
    for d in page.get_drawings():
        if d["type"] != "f" or not d["fill"] or len(d["items"]) != 1 or d["items"][0][0] != "re":
            continue
        r = d["rect"]
        if r.width > 20 or r.height < 0.5:
            continue
        for m, c in COLOURS.items():
            if close(d["fill"], c):
                a = axis_for(ax, r.x0, r.y1 - 1)
                if a is not None and abs(a["a"] + a["b"] * r.y1 - min(values)) < 0.03:
                    items.append((id(a), a, m, r))
    panels = defaultdict(list)
    for key, a, m, r in items:
        panels[key].append((a, m, r))
    out = []
    for key, lst in panels.items():
        a = lst[0][0]
        lst.sort(key=lambda t: t[2].x0)
        groups, cur = [], []
        for _, m, r in lst:
            if cur and (r.x0 - cur[-1][1].x1 > 3 or m in [c[0] for c in cur]):
                groups.append(cur)
                cur = []
            cur.append((m, r))
        groups.append(cur)
        out.append({
            "axis": a,
            "groups": [{"x": (g[0][1].x0 + g[-1][1].x1) / 2,
                        "values": {m: round(a["a"] + a["b"] * r.y0, 4) for m, r in g},
                        "xs": {m: [round(r.x0, 2), round(r.x1, 2)] for m, r in g}} for g in groups],
        })
    return out, ax


def label_values(page, ax, out):
    """Assign -log(p) labels (numbers above bars) to the nearest bar group of their panel."""
    for t, xc, yc, x0, x1 in words(page):
        v = number(t)
        if v is None or "." not in t:
            continue
        if any(abs(x1 - a["x"]) < 3 for a in ax):  # a tick label
            continue
        best = None
        for p in out:
            a = p["axis"]
            if not (a["ytop"] - 30 <= yc <= a["ybot"]) or xc < a["x"]:
                continue
            for g in p["groups"]:
                d = abs(g["x"] - xc)
                if best is None or d < best[0]:
                    best = (d, g)
        if best and best[0] < 25:
            best[1]["neglogp"] = v


def panel_kind(p):
    return "cross" if all(set(g["values"]) == {"Gene", "PAC"} for g in p["groups"]) and len(p["groups"]) == 4 else "within"


def read_s2(path):
    page = pymupdf.open(path)[0]
    out, ax = bars(page, {0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0}, None)
    label_values(page, ax, out)
    # Panels in reading order: by row (y) then column (x); A, B, C, D each have a within and a cross plot.
    out.sort(key=lambda p: (round(p["axis"]["ytop"] / 50), p["axis"]["x"]))
    res = {}
    letters = iter("ABCD")
    pending = {}
    for p in sorted(out, key=lambda p: (p["axis"]["ytop"], p["axis"]["x"])):
        kind = panel_kind(p)
        pending.setdefault(kind, []).append(p)
    within = sorted(pending["within"], key=lambda p: p["axis"]["ytop"])
    cross = sorted(pending["cross"], key=lambda p: p["axis"]["ytop"])
    for letter, w, c in zip("ABCD", within, cross):
        res[letter] = {
            "within": {WITHIN_ORDER(page, w)[i]: g for i, g in enumerate(w["groups"])},
            "cross": {CROSS[i]: g for i, g in enumerate(c["groups"])},
            "calibration_residual": max(w["axis"]["resid"], c["axis"]["resid"]),
            "axes": {"within": w["axis"], "cross": c["axis"]},
        }
    return res


def WITHIN_ORDER(page, panel):
    """Dataset of each bar group from the category labels under the panel."""
    a = panel["axis"]
    names = []
    ws = words(page)
    for g in panel["groups"]:
        below = [w for w in ws if a["ybot"] < w[2] < a["ybot"] + 45 and abs(w[1] - g["x"]) < 18]
        text = " ".join(w[0] for w in sorted(below, key=lambda w: w[2]))
        for n in WITHIN:
            key = n.split()[-1]
            if key in text and not (key == "USA" and "Netherlands" in text):
                names.append(n)
                break
        else:
            names.append(text)
    return names


def read_s3(path):
    page = pymupdf.open(path)[0]
    cols = {"PAC_SEQ": (0.61, 0.73, 0.35), "PAC_FWD": (0.31, 0.51, 0.75),
            "Gene_SEQ": (0.51, 0.4, 0.64), "Gene_FWD": (0.76, 0.32, 0.31)}
    ax = axes(page, {0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0})
    found = []
    for d in page.get_drawings():
        if d["type"] != "f" or not d["fill"]:
            continue
        r = d["rect"]
        for m, c in cols.items():
            if close(d["fill"], c) and r.width < 20 and r.height > 0.5:
                a = axis_for(ax, r.x0, r.y1 - 1)
                if a and abs(a["a"] + a["b"] * r.y1 - 0.4) < 0.03:
                    found.append((m, r, a))
    found.sort(key=lambda t: t[1].x0)
    groups, cur = [], []
    for m, r, a in found:
        if cur and (m in [c[0] for c in cur] or r.x0 - cur[-1][1].x1 > 3):
            groups.append(cur)
            cur = []
        cur.append((m, r, a))
    groups.append(cur)
    names = ["NF-kB", "Leukemia", "Prostate", "Breast Netherlands", "Breast USA", "Lung Michigan", "Lung Boston"]
    vals = {n: {m: round(a["a"] + a["b"] * r.y0, 4) for m, r, a in g} for n, g in zip(names, groups)}
    pos = {n: {m: [round(r.x0, 2), round(r.x1, 2)] for m, r, a in g} for n, g in zip(names, groups)}
    return vals, pos, groups[0][0][2], max(a["resid"] for a in ax)


def read_s1(path):
    page = pymupdf.open(path)[0]
    ax = axes(page, {0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8})
    series = {"Pathways": ((0.16, 0.16, 0.45), 4), "CORGs": ((0.73, 0.33, 0.62), 1), "Genes": ((0.96, 0.92, 0.09), 3)}
    pts = defaultdict(lambda: defaultdict(list))
    for d in page.get_drawings():
        if d["type"] != "f" or not d["fill"]:
            continue
        r = d["rect"]
        for s, (c, n) in series.items():
            if close(d["fill"], c) and len(d["items"]) == n and r.width < 8 and r.height < 8:
                x, y = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
                a = axis_for(ax, x, y)
                if a:
                    pts[(a["x"], a["ytop"])][s].append((x, a["a"] + a["b"] * y))
    names = {"A": "NF-kB", "B": "Leukemia", "C": "Prostate", "D": "Breast Netherlands", "E": "Breast USA",
             "F": "Lung Michigan", "G": "Lung Boston"}
    ws = words(page)
    keys = sorted(pts, key=lambda k: (round(k[1] / 100), k[0]))
    out = {}
    for letter, k in zip("ABCDEFG", keys):
        a = next(a for a in ax if (a["x"], a["ytop"]) == k)
        ticks = sorted(w[1] for w in ws if re.fullmatch(r"\d+%", w[0]) and a["ybot"] < w[2] < a["ybot"] + 30
                       and a["x"] < w[1] < a["x"] + 220)
        out[names[letter]] = {}
        for s_, p_ in pts[k].items():
            vals = []
            for tx in ticks:
                near = [v for x, v in p_ if abs(x - tx) < 5]
                vals.append(round(float(np.mean(near)), 4) if near else None)
            out[names[letter]][s_] = vals
        out[names[letter]]["_x"] = [round(x, 2) for x in ticks]
        out[names[letter]]["_axis"] = a
    return out, max(a["resid"] for a in ax)


def segments(d):
    """Line segments of a drawing as (x0, y0, x1, y1)."""
    out = []
    for it in d["items"]:
        if it[0] == "l":
            out.append((it[1].x, it[1].y, it[2].x, it[2].y))
        elif it[0] in ("re", "qu"):
            r = it[1] if it[0] == "re" else it[1].rect
            out += [(r.x0, r.y0, r.x1, r.y0), (r.x0, r.y1, r.x1, r.y1), (r.x0, r.y0, r.x0, r.y1), (r.x1, r.y0, r.x1, r.y1)]
    return out


def read_s5(path):
    """Box plots: box edges (blue), medians (red, long), outliers (red '+'), whisker caps (black)."""
    page = pymupdf.open(path)[0]
    ax = axes(page, {2, 4, 6, 8, 10, 12, 14})
    a = ax[0]
    val = lambda y: round(2 * (a["a"] + a["b"] * y)) / 2  # counts are integers (medians may be halves)
    blue, red, black = [], [], []
    for d in page.get_drawings():
        c = tuple(round(v, 2) for v in (d["color"] or ()))
        segs = segments(d)
        {(0.0, 0.0, 1.0): blue, (1.0, 0.0, 0.0): red, (0.0, 0.0, 0.0): black}.get(c, []).extend(segs)
    hblue = [s for s in blue if abs(s[1] - s[3]) < 0.1 and abs(s[2] - s[0]) > 5]
    centres = sorted({round((s[0] + s[2]) / 2) for s in hblue})
    merged = []
    for x in centres:
        if not merged or x - merged[-1] > 5:
            merged.append(x)
    names = ["NF-kB", "Leukemia", "Prostate", "Breast Netherlands", "Breast USA", "Lung Michigan", "Lung Boston"]
    res = {}
    for n, xc in zip(names, merged):
        near = lambda s: abs((s[0] + s[2]) / 2 - xc) < 6
        box = sorted(val(s[1]) for s in hblue if near(s))
        med = [val(s[1]) for s in red if near(s) and abs(s[1] - s[3]) < 0.1 and abs(s[2] - s[0]) > 10]
        plus = sorted({val((s[1] + s[3]) / 2) for s in red if near(s) and abs(s[2] - s[0]) <= 5 and abs(s[3] - s[1]) > 1})
        caps = sorted(val(s[1]) for s in black if near(s) and abs(s[1] - s[3]) < 0.1 and 2 < abs(s[2] - s[0]) < 15)
        res[n] = {"x": xc, "q1": box[0], "q3": box[-1], "median": med[0] if med else None,
                  "whisker_low": caps[0] if caps else None, "whisker_high": caps[-1] if caps else None,
                  "outliers": plus}
    res["_axis"] = a
    return res, a["resid"]


def main(supp: Path, out: Path):
    s1, r1 = read_s1(supp / "pcbi.1000217.s003.pdf")
    s2 = read_s2(supp / "pcbi.1000217.s004.pdf")
    s3, s3pos, s3axis, r3 = read_s3(supp / "pcbi.1000217.s005.pdf")
    s5, r5 = read_s5(supp / "pcbi.1000217.s007.pdf")
    res = {"figS1": s1, "figS1_residual": r1, "figS2": s2, "figS3": s3, "figS3_positions": s3pos,
           "figS3_axis": s3axis, "figS3_residual": r3,
           "figS5": s5, "figS5_residual": r5}
    out.write_text(json.dumps(res, indent=1, default=float))
    return res


if __name__ == "__main__":
    r = main(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(r, indent=1, default=float)[:6000])
