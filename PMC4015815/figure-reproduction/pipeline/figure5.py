"""Figure 5: our discriminant weights of (G,G) and (L,L) as bars on the published grid.

usage: figure5.py PUBLISHED_PNG PUBLISHED_BARS_JSON DT_WEIGHTS_JSON|- DR_WEIGHTS_JSON OUTDIR

Published bars are read by figure5_read.py. Their x position is d + 1: the bar at x shows our
weight at distance x - 1 (x = 1 is the composition weight T0). This offset is read from the
figure (see fig5_scores.json "offset_test": correlations of every panel at offsets -2..2), as
if the 151 values had been plotted against their row numbers 1..151; the bar at x = 151 falls
outside the axis.

Ours: the published panel with its bars erased (inside the axes, clear of the ticks), and our
bars drawn 2 px wide (measured) from the zero row. Scores per panel: the share of the 148 published
bars at x = 2..149 whose end is within 2 px of ours (primary; the bars are 2 px wide and most are
short, so the two-way ink trace score at 2 px, also reported, cannot tell ours from ours x 1.05),
and the correlation of the bar values. Controls: the other pair's weights (wrong
input), our bars at x = d (offset near miss), and ours times 1.05 and 0.95 (amplitude near
misses). The least-squares scale of the published bars on ours is reported, not applied.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

from trace_score import two_way

PAIR = {"A": ("SVM-DT", "G,G", "B"), "B": ("SVM-DT", "L,L", "A"),
        "C": ("SVM-DR", "G,G", "D"), "D": ("SVM-DR", "L,L", "C")}
BAR_W = 2.0
SS = 4


def region(p):
    x0, x1, y0, y1 = p["box"]
    m = (slice(y0 + 2, y1 - 1), slice(x0 + 2, x1 - 1))
    return m


def erase(g, p):
    out = g.copy()
    x0, x1, y0, y1 = p["box"]
    sub = out[y0 + 2:y1 - 1, x0 + 2:x1 - 1]
    # keep the tick stubs: 7 px along the left and bottom axes at tick rows/columns
    keep = np.zeros_like(sub, bool)
    keep[:, :7] = True
    keep[-8:, :] = True
    keep[:7, :] = False
    sub[~keep & (sub < 200)] = 255
    # tick stubs are rows/cols where the published stub is drawn; restore them from the original
    return out


def draw(g, p, values, offset=1):
    """values[d] for d = 0..150 drawn at x = d + offset."""
    x0, x1, y0, y1 = p["box"]
    ay, by = p["y_px"]
    ax, bx = p["x_px"]
    H, W = g.shape
    layer = Image.new("L", (W * SS, H * SS), 0)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(layer)
    for d, v in enumerate(values):
        x = ax + bx * (d + offset)
        if not (x0 + 1 < x < x1 - 1):
            continue
        ytop, ybot = sorted([ay, ay + by * v])
        ytop = max(ytop, y0 + 1)
        ybot = min(ybot, y1 - 1)
        dr.rectangle([(x - BAR_W / 2) * SS, ytop * SS, (x + BAR_W / 2) * SS, ybot * SS], fill=255)
    a = np.asarray(layer.resize((W, H), Image.LANCZOS)).astype(float) / 255.0
    return g * (1 - a)


def bar_mask(g, p):
    x0, x1, y0, y1 = p["box"]
    m = np.zeros(g.shape, bool)
    m[y0 + 3:y1 - 2, x0 + 8:x1 - 2] = g[y0 + 3:y1 - 2, x0 + 8:x1 - 2] < 140
    return m


def score(pub_g, p, values, offset=1):
    base = erase(pub_g, p)
    ours = draw(base, p, values, offset)
    return two_way(bar_mask(pub_g, p), bar_mask(ours, p))


def bar_ends(pub_vals, values, p, offset=1, tol_px=2.0):
    """Share of published bars (x = 2..149) whose end lies within tol_px of ours, in pixels."""
    by = abs(p["y_px"][1])
    xs = np.arange(2, 150)
    ours = np.array([values[x - offset] if 0 <= x - offset < len(values) else 0.0 for x in xs])
    return float(np.mean(np.abs(ours - np.array(pub_vals)[xs]) * by <= tol_px))


def main(published, bars_json, dt_json, dr_json, outdir):
    os.makedirs(outdir, exist_ok=True)
    g = np.asarray(Image.open(published).convert("L")).astype(float)
    pub = json.load(open(bars_json))
    ours = {"SVM-DT": json.load(open(dt_json)) if dt_json != "-" else None,
            "SVM-DR": json.load(open(dr_json))}
    render = g.copy()
    overlay = np.stack([g * 0.35 + 165] * 3, -1)
    res = {"tolerance_px": 2, "panels": {}}
    for k, (method, pair, other) in PAIR.items():
        p = pub[k]
        pv = np.array(p["values"])
        entry = {"method": method, "pair": pair, "published_values_x0_150": pv.tolist()}
        o = ours[method]
        if o is None:
            entry["ours"] = None
            res["panels"][k] = entry
            continue
        ov = np.array(o["weights"][pair])
        oo = np.array(o["weights"][PAIR[other][1]])
        a, b = pv[2:150], ov[1:149]
        entry["offset_test"] = {str(s): round(float(np.corrcoef(pv[2:149], ov[2 - s:149 - s])[0, 1]), 3)
                                for s in (-2, -1, 0, 1, 2)}
        entry["correlation_x2_149"] = round(float(np.corrcoef(a, b)[0, 1]), 4)
        entry["sign_agreement_x2_149"] = round(float(np.mean(np.sign(a) == np.sign(b))), 4)
        entry["published_scale_on_ours"] = round(float(np.dot(a, b) / np.dot(b, b)), 4)
        entry["share_negative_d1_150"] = {"published_x2_151": round(float(np.mean(pv[2:] < 0)), 4),
                                          "ours": round(float(np.mean(ov[1:] < 0)), 4)}
        entry["first_bar"] = {"published_x1": float(pv[1]), "ours_d0": round(float(ov[0]), 2)}
        # Primary score: bar ends within 2 px of the published bar ends (x = 2..149). The ink
        # trace score is kept too, but it cannot tell ours from ours x 1.05 (most bars are short).
        be = bar_ends(pv, ov, p)
        entry["ours"] = {"bar_ends_within_2px": round(be, 4), "trace": score(g, p, ov)}
        entry["controls"] = [
            {"name": f"({PAIR[other][1]}) weights in place of ({pair})", "kind": "wrong_input",
             "score": round(bar_ends(pv, oo, p), 4), "trace": score(g, p, oo)["score"]},
            {"name": "ours at x = d (no offset)", "kind": "near_miss",
             "score": round(bar_ends(pv, ov, p, offset=0), 4),
             "trace": score(g, p, ov, offset=0)["score"]},
            {"name": "ours x 1.05", "kind": "near_miss", "score": round(bar_ends(pv, ov * 1.05, p), 4),
             "trace": score(g, p, ov * 1.05)["score"]},
            {"name": "ours x 0.95", "kind": "near_miss", "score": round(bar_ends(pv, ov * 0.95, p), 4),
             "trace": score(g, p, ov * 0.95)["score"]},
        ]
        entry["published_redrawn"] = score(g, p, np.concatenate([pv[1:], [0.0]]))["score"]
        ys, xs = region(p)
        drawn = draw(erase(g, p), p, ov)
        render[ys, xs] = drawn[ys, xs]
        om = bar_mask(drawn, p)
        overlay[om] = (0, 90, 255)
        res["panels"][k] = entry
    Image.fromarray(np.clip(render, 0, 255).astype(np.uint8)).save(
        os.path.join(outdir, "fig5_ours.png"))
    Image.fromarray(overlay.astype(np.uint8)).save(os.path.join(outdir, "fig5_overlay.png"))
    json.dump(res, open(os.path.join(outdir, "fig5_scores.json"), "w"), indent=1)
    for k, e in res["panels"].items():
        if e.get("ours"):
            print(k, e["pair"], e["method"], "score", e["ours"], "redrawn", e["published_redrawn"],
                  "r", e["correlation_x2_149"], "scale", e["published_scale_on_ours"],
                  "offsets", e["offset_test"])
            for c in e["controls"]:
                print("    ", c)


if __name__ == "__main__":
    main(*sys.argv[1:6])
