"""Draw our Figs 1-4 into the published frames, overlay them, and score them with negative controls.

Usage: figures.py FIG_DIR FIGURE_VALUES.json SIMULATION.json OUTDIR

For each figure: the published JPEG with its bars removed, our bars drawn at the published columns,
fills and border (fig*_ours.png); the overlay (fig*_overlay.png: red channel the paper, green and
blue ours, so black is ink in both, cyan ink only in the paper, red ink only in ours).

Score: the bars' top edges. In each bar column the top edge is found in both images the same way
(read_published.bar_top on single columns); the score is the share of the paper's edge points with
one of ours within 2 px, and of ours with one of the paper's; the smaller of the two counts. Sides
are left out: they sit at the published columns by construction.

Controls, scored the same way: wrong inputs (the neighbouring scenario's values; the 1000/1000 runs
in place of 5000/5000) and near misses (every bar x 1.05 and x 0.95; the empirical CI of ESR_S in
place of ESR_R). The run without the first term of eq. 10 is drawn and scored as a hypothesis test.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from read_published import GROUPS, SERIES

TOL = 2
SERIES_FROM = {"esr_s_log": ("ci_s_log", "expected_length_given_coverage"),
               "esr_r_log": ("ci_r_log", "expected_length_given_coverage"),
               "esr_r_binomial": ("ci_r_binomial", "expected_length_given_coverage"),
               "empirical": ("esr_r", "empirical_length")}
NEIGHBOUR = {1: 2, 2: 1, 3: 4, 4: 3}


def values_for(sim, scen, size="5000/5000", empirical_of="esr_r", ci_r_log=None):
    out = {}
    for rr in GROUPS:
        b = sim[f"S{scen}|{size}|{rr}"]
        for ser, (block, meas) in SERIES_FROM.items():
            if ser == "empirical":
                block = empirical_of
            src = b[block]
            if ser == "esr_r_log" and ci_r_log is not None:
                src = ci_r_log[f"S{scen}|{size}|{rr}"]
            out[f"{rr}|{ser}"] = src.get(meas)
    return out


def fill_colours(g, fv):
    """Fill and border grey of each series, sampled from the published bars (median of the interior)."""
    fills = {}
    geo = fv["geometry"]
    for ser in SERIES:
        vals = []
        for rr in GROUPS:
            bar = fv["bars"][f"{rr}|{ser}"]
            if bar["top_row"] is None:
                continue
            y0, y1 = int(bar["top_row"]) + 4, geo["axis_y"] - 3
            x0, x1 = int(np.ceil(bar["left"])) + 3, int(np.floor(bar["right"])) - 2
            if y1 > y0 and x1 > x0:
                vals.append(np.median(g[y0:y1, x0:x1]))
        fills[ser] = int(round(float(np.median(vals)))) if vals else 255
    return fills


def blank(g, fv):
    """The published figure with every bar removed (white from the plot top down to the axis)."""
    out = g.copy()
    geo = fv["geometry"]
    for bar in fv["bars"].values():
        x0, x1 = int(np.floor(bar["left"])) - 1, int(np.ceil(bar["right"])) + 1
        out[geo["plot_top"] + 2:geo["axis_y"], x0:x1 + 1] = 255
    return out


def draw(base, fv, values, fills):
    """Our bars on the blanked frame: fill, and a one-pixel black border on top and sides."""
    out = base.copy()
    geo = fv["geometry"]
    slope = -fv["value_per_px"]
    zero = fv["zero_row"]
    for key, v in values.items():
        if v is None or not np.isfinite(v) or v <= 0:
            continue
        bar = fv["bars"][key]
        ser = key.split("|")[1]
        top = int(round(zero + v / slope))  # border line centre (value 0 at the axis line's centre)
        top = max(top, geo["plot_top"] + 2)
        x0, x1 = int(round(bar["left"])), int(round(bar["right"]))
        out[top:geo["axis_y"], x0:x1 + 1] = fills[ser]
        out[top, x0:x1 + 1] = 0
        out[top:geo["axis_y"], x0] = 0
        out[top:geo["axis_y"], x1] = 0
    return out


def edge_points(g, fv):
    """(column, row) of every bar column's top edge."""
    geo = fv["geometry"]
    pts = []
    for bar in fv["bars"].values():
        for c in range(int(np.ceil(bar["left"])) + 3, int(np.floor(bar["right"])) - 2):
            prof = g[geo["plot_top"] + 2:geo["axis_y"] - 1, c].astype(float)
            idx = np.nonzero(prof < 200)[0]
            if len(idx):
                pts.append((c, geo["plot_top"] + 2 + int(idx[0])))
    return pts


def share_near(a, b):
    if not a:
        return 1.0 if not b else 0.0
    bset = {}
    for c, r in b:
        bset.setdefault(c, []).append(r)
    hit = 0
    for c, r in a:
        if any(abs(r - r2) <= TOL and abs(c - c2) <= TOL for c2 in range(c - TOL, c + TOL + 1) for r2 in bset.get(c2, [])):
            hit += 1
    return hit / len(a)


def score(pub_g, ours_g, fv):
    p, o = edge_points(pub_g, fv), edge_points(ours_g, fv)
    return {"published_near_ours": round(share_near(p, o), 4), "ours_near_published": round(share_near(o, p), 4),
            "published_points": len(p), "ours_points": len(o)}


def overlay(pub_g, ours_g):
    return np.stack([pub_g, ours_g, ours_g], axis=-1).astype(np.uint8)


def main():
    fig_dir, fv_p, sim_p, outdir = sys.argv[1:5]
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    FV = json.load(open(fv_p))
    S = json.load(open(sim_p))
    sim, var = S["main"], S["variants"]
    nofirst = {k: v["eq10_no_first_term"]["ci_r_log"] for k, v in var.items()}
    res = {"tolerance_px": TOL, "figures": {}}
    for i in range(1, 5):
        fig = f"fig{i}"
        fv = FV[fig]
        g = np.asarray(Image.open(Path(fig_dir) / f"1471-2288-11-1-{i}.jpg").convert("L")).astype(np.uint8)
        fills = fill_colours(g, fv)
        base = blank(g, fv)
        ours_vals = values_for(sim, i)
        ours = draw(base, fv, ours_vals, fills)
        Image.fromarray(ours).save(out / f"{fig}_ours.png", optimize=True)
        Image.fromarray(overlay(g, ours)).save(out / f"{fig}_overlay.png", optimize=True)
        entry = {"values": ours_vals, "fills": fills, **score(g, ours, fv), "controls": [], "hypotheses": {}}
        controls = [
            ("Scenario %d's values (wrong input)" % NEIGHBOUR[i], "wrong_input", values_for(sim, NEIGHBOUR[i])),
            ("N1/N2 1000/1000 in place of 5000/5000 (wrong input)", "wrong_input", values_for(sim, i, size="1000/1000")),
            ("every bar x 1.05 (near miss)", "near_miss", {k: (v * 1.05 if v else v) for k, v in ours_vals.items()}),
            ("every bar x 0.95 (near miss)", "near_miss", {k: (v * 0.95 if v else v) for k, v in ours_vals.items()}),
            ("empirical CI of ESR_S in place of ESR_R (near miss)", "near_miss", values_for(sim, i, empirical_of="esr_s")),
        ]
        for name, kind, vals in controls:
            sc = score(g, draw(base, fv, vals, fills), fv)
            entry["controls"].append({"name": name, "kind": kind,
                                      "score": min(sc["published_near_ours"], sc["ours_near_published"])})
        alt_vals = values_for(sim, i, ci_r_log=nofirst)
        alt = draw(base, fv, alt_vals, fills)
        Image.fromarray(alt).save(out / f"{fig}_ours_eq10_no_first_term.png", optimize=True)
        entry["hypotheses"]["eq10_no_first_term"] = score(g, alt, fv)
        res["figures"][fig] = entry
        s = min(entry["published_near_ours"], entry["ours_near_published"])
        best = max(c["score"] for c in entry["controls"])
        h = entry["hypotheses"]["eq10_no_first_term"]
        print(f"{fig}: ours {s:.3f}; best control {best:.3f}; without eq. 10's first term "
              f"{min(h['published_near_ours'], h['ours_near_published']):.3f}", file=sys.stderr)
    (out / "figures.json").write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
