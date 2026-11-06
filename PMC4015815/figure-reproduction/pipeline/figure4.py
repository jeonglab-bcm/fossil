"""Figure 4: the published L2-norm heatmaps read back as numbers, ours drawn on the same grid.

usage: figure4.py PUBLISHED_PNG DT_WEIGHTS_JSON|- DR_WEIGHTS_JSON OUTDIR [CONTROL_JSON ...]

Panels (A: SVM-DT, B: SVM-DR) are 20 x 20 grey cells, x = first letter, y = second letter, in
the order ARDCQEHIGNLKMFPSTWYV, with a colour bar from 0 (white) to the panel maximum (101 and
78, black). Published values: the median grey of the inner half of each cell, mapped through the
colour bar's own greys (each bar row is a value, linear from 0 at the bottom to the maximum at
the top). Ours: each cell filled with the bar's grey for our value on the published scale
(values above the published maximum take the darkest grey; the count is reported). Frame,
letters and bars are the published pixels.

Scores per panel: the share of the 400 cells whose grey is within 24 levels of the published
cell (cell grey tolerance, Paper2Repro figure-matching), Spearman and Pearson correlations of
the values, and the ranks of (G,G) and (L,L). Controls: the other panel's values (wrong input),
the transpose (first and second letter swapped; near miss), and any CONTROL_JSON given
(discriminant_weights.py output for another family; wrong input).
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import stats

PANELS = {"A": {"box": (57, 511, 39, 493), "bar": (541, 566), "max": 101.0, "method": "SVM-DT"},
          "B": {"box": (661, 1115, 39, 493), "bar": (1145, 1169), "max": 78.0, "method": "SVM-DR"}}
BAR_Y = (40, 491)   # inner rows of the colour bars
GREY_TOL = 24


def cell_bounds(box, i):
    x0, x1 = box
    w = (x1 - x0) / 20.0
    return x0 + i * w, x0 + (i + 1) * w


def bar_lut(g, bar, vmax):
    x0, x1 = bar
    ys = np.arange(BAR_Y[0], BAR_Y[1] + 1)
    grey = np.median(g[ys, x0 + 6:x1 - 6], axis=1)
    vals = vmax * (BAR_Y[1] - ys) / (BAR_Y[1] - BAR_Y[0])
    return grey, vals


def grey_to_value(grey, lut):
    # Many bar rows share a grey (452 rows, 245 greys). Each grey maps to the mean value of its
    # rows, so the map does not depend on how a sort orders ties (that differs between machines).
    lg, lv = lut
    ug, inv = np.unique(lg, return_inverse=True)
    uv = np.bincount(inv, weights=lv) / np.bincount(inv)
    return np.interp(grey, ug, uv)


def value_to_grey(v, lut):
    lg, lv = lut
    order = np.argsort(lv)
    return np.interp(np.clip(v, 0, lv.max()), lv[order], lg[order])


def read_panel(g, p):
    x0, x1, y0, y1 = p["box"]
    lut = bar_lut(g, p["bar"], p["max"])
    grey = np.zeros((20, 20))
    for i in range(20):          # first letter: column
        a, b = cell_bounds((x0, x1), i)
        for j in range(20):      # second letter: row
            c, d = cell_bounds((y0, y1), j)
            wa, wb = a + (b - a) / 4, b - (b - a) / 4
            wc, wd = c + (d - c) / 4, d - (d - c) / 4
            grey[i, j] = np.median(g[int(round(wc)):int(round(wd)), int(round(wa)):int(round(wb))])
    return grey, grey_to_value(grey, lut), lut


def paint(g, p, values, lut):
    x0, x1, y0, y1 = p["box"]
    out = g.copy()
    grey = value_to_grey(values, lut)
    for i in range(20):
        a, b = cell_bounds((x0, x1), i)
        for j in range(20):
            c, d = cell_bounds((y0, y1), j)
            out[int(round(c)):int(round(d)), int(round(a)):int(round(b))] = grey[i, j]
    return out, grey


def ranks(values, alphabet):
    order = np.argsort(-values.ravel())
    r = {(alphabet[k // 20], alphabet[k % 20]): n + 1 for n, k in enumerate(order)}
    return r


def compare(pub_grey, pub_vals, our_vals, lut):
    our_grey = value_to_grey(our_vals, lut)
    share = float(np.mean(np.abs(our_grey - pub_grey) <= GREY_TOL))
    return {"cells_within_24": round(share, 4),
            "spearman": round(float(stats.spearmanr(pub_vals.ravel(), our_vals.ravel())[0]), 4),
            "pearson": round(float(np.corrcoef(pub_vals.ravel(), our_vals.ravel())[0, 1]), 4)}


def main(published, dt_json, dr_json, outdir, *control_jsons):
    os.makedirs(outdir, exist_ok=True)
    img = Image.open(published).convert("L")
    g = np.asarray(img).astype(float)
    ours = {"SVM-DT": json.load(open(dt_json)) if dt_json != "-" else None,
            "SVM-DR": json.load(open(dr_json))}
    controls_extra = [json.load(open(c)) for c in control_jsons]
    A = "ARDCQEHIGNLKMFPSTWYV"
    render = g.copy()
    res = {"grey_tolerance": GREY_TOL, "panels": {}}
    pub_values = {}
    for key, p in PANELS.items():
        pub_grey, pub_vals, lut = read_panel(g, p)
        pub_values[key] = (pub_grey, pub_vals, lut)
    for key, p in PANELS.items():
        pub_grey, pub_vals, lut = pub_values[key]
        pr = ranks(pub_vals, A)
        entry = {"method": p["method"], "published_max": p["max"],
                 "published_values": np.round(pub_vals, 2).tolist(),
                 "published_top5": sorted(pr, key=pr.get)[:5],
                 "published_rank_GG": pr[("G", "G")], "published_rank_LL": pr[("L", "L")]}
        o = ours[p["method"]]
        if o is None:
            entry["ours"] = None
            res["panels"][key] = entry
            continue
        ov = np.array(o["l2_first_second"])
        assert o["alphabet"] == A
        orank = ranks(ov, A)
        render, _ = paint(render, p, ov, lut)
        entry.update({
            "our_max": round(float(ov.max()), 2),
            "our_cells_above_published_max": int((ov > p["max"]).sum()),
            "our_top5": sorted(orank, key=orank.get)[:5],
            "our_rank_GG": orank[("G", "G")], "our_rank_LL": orank[("L", "L")],
            "ours": compare(pub_grey, pub_vals, ov, lut),
            "ours_rescaled_to_published_max": compare(pub_grey, pub_vals,
                                                      ov * p["max"] / ov.max(), lut),
        })
        ctrl = []
        other = "B" if key == "A" else "A"
        ctrl.append({"name": f"panel {other} values (other method, published)",
                     "kind": "wrong_input",
                     **compare(pub_grey, pub_vals, pub_values[other][1] * p["max"] /
                               PANELS[other]["max"], lut)})
        ctrl.append({"name": "ours transposed (first and second letter swapped)",
                     "kind": "near_miss", **compare(pub_grey, pub_vals, ov.T, lut)})
        for c in controls_extra:
            if c.get("sequences", "residues").startswith("top1") == (p["method"] == "SVM-DT"):
                ctrl.append({"name": f"ours for family {c['family']}", "kind": "wrong_input",
                             **compare(pub_grey, pub_vals,
                                       np.array(c["l2_first_second"]), lut)})
        entry["controls"] = ctrl
        res["panels"][key] = entry
    Image.fromarray(np.clip(render, 0, 255).astype(np.uint8)).save(
        os.path.join(outdir, "fig4_ours.png"))
    # overlay: published left half of each cell, ours right half
    ov_img = g.copy()
    for key, p in PANELS.items():
        x0, x1, y0, y1 = p["box"]
        for i in range(20):
            a, b = cell_bounds((x0, x1), i)
            m = int(round((a + b) / 2))
            ov_img[y0:y1, m:int(round(b))] = render[y0:y1, m:int(round(b))]
    Image.fromarray(np.clip(ov_img, 0, 255).astype(np.uint8)).save(
        os.path.join(outdir, "fig4_overlay.png"))
    json.dump(res, open(os.path.join(outdir, "fig4_scores.json"), "w"), indent=1)
    for k, e in res["panels"].items():
        print(k, {x: e.get(x) for x in ["published_top5", "our_top5", "published_rank_GG",
                                        "our_rank_GG", "published_rank_LL", "our_rank_LL",
                                        "our_max", "ours", "ours_rescaled_to_published_max"]})
        for c in e.get("controls", []):
            print("   ", c)


if __name__ == "__main__":
    main(*sys.argv[1:])
