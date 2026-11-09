#!/usr/bin/env python3
"""Fig. 1: our curves drawn on the published raster, scored both ways with controls.

The published Fig. 1 is a 600 x 287 JPEG. The axes boxes, found from the image, span x 46-271
(a) and 362-587 (b), y 49-256. The x axis is log10 from 1 to 1000; y runs 0.1-1 (a) and 0.1-0.6
(b), from the printed tick labels. Legends and the prior line of (a) are masked out of the trace.

Usage: figure1.py PUBLISHED_JPG FIG1_TSV OUT_DIR
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

import pixels

BOX = {"a": (46, 271), "b": (362, 587)}
Y0, Y1 = 49, 256
YR = {"a": (0.1, 1.0), "b": (0.1, 0.6)}
LEGEND = {"a": (118, 271, 50, 82), "b": (440, 587, 50, 68)}  # x0, x1, y0, y1
PRIOR_ROWS = (201, 214)  # rows of the dotted prior line in (a); the curve stays above 0.36 (row 195)


def to_px(panel, d, v):
    x0, x1 = BOX[panel]
    lo, hi = YR[panel]
    return x0 + math.log10(d) / 3 * (x1 - x0), Y1 - (v - lo) / (hi - lo) * (Y1 - Y0)


def published_mask(gray, panel):
    x0, x1 = BOX[panel]
    m = np.zeros_like(gray, dtype=bool)
    m[Y0 + 2:Y1 - 1, x0 + 2:x1 - 1] = gray[Y0 + 2:Y1 - 1, x0 + 2:x1 - 1] < 110
    lx0, lx1, ly0, ly1 = LEGEND[panel]
    m[ly0:ly1, lx0:lx1] = False
    prior = np.zeros_like(m)
    if panel == "a":
        prior[PRIOR_ROWS[0]:PRIOR_ROWS[1]] = gray[PRIOR_ROWS[0]:PRIOR_ROWS[1]] < 200
        prior &= np.pad(np.ones((Y1 - Y0 - 3, x1 - x0 - 3), bool), ((Y0 + 2, gray.shape[0] - Y1 + 1), (x0 + 2, gray.shape[1] - x1 + 1)))
        m[PRIOR_ROWS[0]:PRIOR_ROWS[1]] = False
    return m, prior


def curve_px(panel, rows, col, scale=1.0):
    if col == "neighbour" and panel == "b":
        col = "correlation"
    return [to_px(panel, d, scale * r[col]) for d, r in sorted(rows.items())]


def main(pub_jpg, fig1_tsv, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    gray = np.array(Image.open(pub_jpg).convert("L"))
    data = defaultdict(dict)
    for line in open(fig1_tsv).read().splitlines()[1:]:
        name, d, prior, cond, corr, nb = line.split("\t")
        data[name][int(d)] = {"prior": float(prior), "conditional": float(cond), "correlation": float(corr), "neighbour": float(nb)}
    col = {"a": "conditional", "b": "correlation"}
    result = {}
    ours_img = Image.fromarray(gray).convert("RGB")
    ours_arr = np.array(ours_img)
    over_masks = []
    for panel in ("a", "b"):
        pub, prior_pub = published_mask(gray, panel)
        ours = pixels.line_mask(gray.shape, curve_px(panel, data["CH"], col[panel]), width=2)
        s, both = pixels.score(pub, ours)
        controls = []
        for name, kind, rows, scale in (
            ("CHDE residues (another residue set)", "wrong_input", data["CHDE"], 1.0),
            ("all residues", "wrong_input", data["all"], 1.0),
            ("separation as index difference (off by one)", "near_miss", data["CH_index_difference"], 1.0),
            ("(a) read as P(bound | a bound residue within d)", "near_miss", {d: dict(r, conditional=r["neighbour"]) for d, r in data["CH"].items()}, 1.0),
            ("ours x 1.05", "near_miss", data["CH"], 1.05),
            ("ours x 0.95", "near_miss", data["CH"], 0.95),
        ):
            if panel == "b" and name.startswith("(a)"):
                continue  # (b) does not depend on how (a) is read
            m = pixels.line_mask(gray.shape, curve_px(panel, rows, col[panel], scale), width=2)
            controls.append({"name": name, "kind": kind, "score": round(pixels.score(pub, m)[0], 4)})
        entry = {"tolerance_px": pixels.TOL_PX, "dpi": None, "published_near_ours": round(both["published_near_ours"], 4),
                 "ours_near_published": round(both["ours_near_published"], 4), "score": round(s, 4), "controls": controls}
        if panel == "a":
            pr = data["CH"][1]["prior"]
            prior_ours = pixels.line_mask(gray.shape, [to_px("a", 1, pr), to_px("a", 1000, pr)], width=1)
            entry["prior"] = {"ours": round(pr, 3), "published_row": float(np.median(np.where(prior_pub)[0])),
                              "ours_row": round(to_px("a", 1, pr)[1], 1),
                              "published_value": round(YR["a"][0] + (Y1 - np.median(np.where(prior_pub)[0])) / (Y1 - Y0) * 0.9, 3)}
            over_masks.append(prior_ours)
        result[panel] = entry
        # Ours: the published frame with the published traces removed and ours drawn in black.
        x0, x1 = BOX[panel]
        inner = np.zeros_like(pub)
        inner[Y0 + 2:Y1 - 1, x0 + 2:x1 - 1] = True
        lx0, lx1, ly0, ly1 = LEGEND[panel]
        inner[ly0:ly1, lx0:lx1] = False
        remove = inner & (gray < 200)
        ours_arr[remove] = 255
        ours_arr[ours] = 0
        over_masks.append(ours)
    if "prior" in result["a"]:
        pr = result["a"]["prior"]["ours"]
        m = pixels.line_mask(gray.shape, [to_px("a", 1, pr), to_px("a", 1000, pr)], width=1)
        ours_arr[m] = 80
    Image.fromarray(ours_arr).save(out / "fig1_ours.png")
    ov = np.zeros_like(gray, dtype=bool)
    for m in over_masks:
        ov |= m
    pixels.overlay(gray, ov).save(out / "fig1_overlay.png")
    json.dump(result, open(out / "fig1_scores.json", "w"), indent=1)
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
