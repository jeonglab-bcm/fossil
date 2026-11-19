"""Draw our Figs 2-6 on the published figures' pixel grids, overlay them and score them.

    python figures.py PUBLISHED_DIR CALIBRATION.json ROC.json DENSITIES.json OUT_DIR

For each figure: a copy of the published JPEG with its coloured traces removed and ours drawn in the
published colours and styles (fig*_ours.png); an overlay with the published figure in the red channel
and ours in green and blue (fig*_overlay.png: cyan is ink only in the paper, red only in ours, black
both). Scores, both ways, on the coloured trace pixels inside the axes box (legend and text masked):
the share of published trace pixels within 2 px of our trace of the same colour, and of ours within
2 px of the published. The smaller is the score. Known-wrong variants are scored with the same code:
wrong inputs (the other curve, a random predictor, the binary network) and near misses (TPR shifted
by 0.03, density amplitude x 0.95 and x 1.05, x shifted by 1% of the axis, classes swapped). The pass
mark is 0.90, or just above the best control when a control reaches it.

Writes OUT_DIR/figures/*.png and OUT_DIR/comparison.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

TOL = 2.0
BASE_MARK = 0.90
BLUE = (0, 0, 255)
RED = (255, 0, 0)


def colour_masks(a: np.ndarray):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    blue = (b > 140) & (r < 140) & (g < 140) & (b - r > 60)
    red = (r > 140) & (g < 140) & (b < 140) & (r - b > 60)
    return {"blue": blue, "red": red}


def inside(shape, box, masks_px=()):
    m = np.zeros(shape[:2], dtype=bool)
    l, t, r, b = box
    m[t + 2:b - 1, l + 2:r - 1] = True
    for (x0, y0, x1, y1) in masks_px:
        m[int(y0):int(y1) + 1, int(x0):int(x1) + 1] = False
    return m


def erase_region(shape, box, keep=()):
    """Where published traces are removed: the axes box and 3 px around it, except kept areas."""
    m = np.zeros(shape[:2], dtype=bool)
    l, t, r, b = box
    m[max(t - 3, 0):b + 4, max(l - 3, 0):r + 4] = True
    for (x0, y0, x1, y1) in keep:
        m[int(y0):int(y1) + 1, int(x0):int(x1) + 1] = False
    return m


def erase_traces(a: np.ndarray, region: np.ndarray, interior: np.ndarray | None = None) -> np.ndarray:
    """White out every coloured pixel (the traces and their anti-aliased fringe) and the light-grey JPEG
    residue around them in the region; black and dark-grey ink (axes, diagonal) stays."""
    out = a.copy()
    chroma = a.max(axis=2).astype(int) - a.min(axis=2).astype(int)
    light = a.astype(int).mean(axis=2) > 190
    interior = region if interior is None else interior
    out[region & (chroma > 30)] = 255
    out[interior & ((chroma > 6) | light)] = 255
    return out


def dashed(draw, pts, fill, width, on=6.0, off=4.0):
    pos, drawing, left = 0.0, True, on
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        seg = float(np.hypot(x1 - x0, y1 - y0))
        t = 0.0
        while t < seg - 1e-9:
            step = min(left, seg - t)
            if drawing and seg > 0:
                a, b = t / seg, (t + step) / seg
                draw.line([(x0 + a * (x1 - x0), y0 + a * (y1 - y0)), (x0 + b * (x1 - x0), y0 + b * (y1 - y0))],
                          fill=fill, width=width)
            t += step
            left -= step
            if left <= 1e-9:
                drawing = not drawing
                left = on if drawing else off


def trace_layer(size, pts, colour, style, width, marker=None, marker_pts=None):
    """One trace on its own transparent layer; returns the layer."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fill = colour + (255,)
    if style == "dashed":
        dashed(d, pts, fill, width)
    else:
        d.line(pts, fill=fill, width=width)
    for (x, y) in marker_pts or []:
        if marker == "triangle":
            d.polygon([(x, y - 4), (x - 4, y + 3), (x + 4, y + 3)], outline=fill)
        elif marker == "square":
            d.rectangle([x - 3, y - 3, x + 3, y + 3], outline=fill)
    return layer


def score(pub: dict, ours: dict, region: np.ndarray):
    """Both-way shares within TOL px over the colours present."""
    hit_p = tot_p = hit_o = tot_o = 0
    for c in ("blue", "red"):
        p = pub[c] & region
        o = ours[c] & region
        if not p.any() or not o.any():
            tot_p += int(p.sum())
            tot_o += int(o.sum())
            continue
        dist_to_o = distance_transform_edt(~o)
        dist_to_p = distance_transform_edt(~p)
        hit_p += int((dist_to_o[p] <= TOL).sum())
        tot_p += int(p.sum())
        hit_o += int((dist_to_p[o] <= TOL).sum())
        tot_o += int(o.sum())
    a = hit_p / tot_p if tot_p else 0.0
    b = hit_o / tot_o if tot_o else 0.0
    return round(a, 4), round(b, 4)


def compose(base: np.ndarray, layers, region: np.ndarray):
    img = Image.fromarray(base).convert("RGBA")
    masks = {}
    for name, layer in layers:
        arr = np.asarray(layer)
        m = (arr[..., 3] > 0) & region
        masks[name] = m
        clipped = arr.copy()
        clipped[~region] = 0
        img = Image.alpha_composite(img, Image.fromarray(clipped))
    return np.asarray(img.convert("RGB")), masks


def overlay(pub: np.ndarray, ours: np.ndarray) -> np.ndarray:
    lp = np.asarray(Image.fromarray(pub).convert("L"))
    lo = np.asarray(Image.fromarray(ours).convert("L"))
    return np.stack([lp, lo, lo], axis=2)


def mark(controls):
    best = max([c["score"] for c in controls], default=0.0)
    return round(max(BASE_MARK, best + 0.01), 4)


# ---------------------------------------------------------------- ROC figures (Figs 2-5)

ROC_FIGS = {
    "fig2": ("figure-2.jpg", "unlabelled20/ssl/weighted", "unlabelled20/svm/weighted", "square"),
    "fig3": ("figure-3.jpg", "unlabelled50/ssl/weighted", "unlabelled50/svm/weighted", "square"),
    "fig4": ("figure-4.jpg", "unlabelled80/ssl/weighted", "unlabelled80/svm/weighted", "square"),
    "fig5": ("figure-5.jpg", "unlabelled50/ssl/weighted", "unlabelled50/ssl/binary", "square"),
}


def roc_figure(pub_dir, cal, roc, out_dir, fig_id):
    fname, blue_key, red_key, red_marker = ROC_FIGS[fig_id]
    pub = np.asarray(Image.open(pub_dir / fname).convert("RGB"))
    l, t, r, b = cal["roc"]["box"][fname]

    def px(points):
        return [(l + x * (r - l), b - y * (b - t)) for x, y in points]

    lx0, ly0, lx1, ly1 = cal["roc"]["legend_mask_data"]
    legend = (l + lx0 * (r - l) - 2, b - ly1 * (b - t), r, b)
    region = inside(pub.shape, (l, t, r, b), [legend])
    base = erase_traces(pub, erase_region(pub.shape, (l, t, r, b), [legend]), region)
    pmask = colour_masks(pub)
    size = (pub.shape[1], pub.shape[0])

    def render(blue_pts, red_pts):
        layers = [("blue", trace_layer(size, px(blue_pts), BLUE, "solid", 1, "triangle", px(blue_pts))),
                  ("red", trace_layer(size, px(red_pts), RED, "dashed", 1, red_marker, px(red_pts)))]
        return compose(base, layers, region)

    blue_pts = roc["curves"][blue_key]["points"]
    red_pts = roc["curves"][red_key]["points"]
    img, om = render(blue_pts, red_pts)
    s_pub, s_ours = score(pmask, om, region)

    def shifted(pts, dy):
        return [[x, float(np.clip(y + dy, 0, 1))] if 0 < i < len(pts) - 1 else [x, y] for i, (x, y) in enumerate(pts)]

    diag = [[q, q] for q in np.linspace(0, 1, 26)]
    controls = []
    for name, kind, bp, rp in (
        ("curves swapped", "wrong_input", red_pts, blue_pts),
        ("random predictor (both curves on the diagonal)", "wrong_input", diag, diag),
        ("TPR + 0.03", "near_miss", shifted(blue_pts, 0.03), shifted(red_pts, 0.03)),
        ("TPR - 0.03", "near_miss", shifted(blue_pts, -0.03), shifted(red_pts, -0.03)),
    ):
        _, m = render(bp, rp)
        controls.append({"name": name, "kind": kind, "score": min(score(pmask, m, region))})
    Image.fromarray(img).save(out_dir / f"{fig_id}_ours.png")
    Image.fromarray(overlay(pub, img)).save(out_dir / f"{fig_id}_overlay.png")
    # area under each published curve, read from the figure: the top-most trace pixel of the colour in
    # each pixel column of the box (legend masked), linearly filled across empty columns
    pub_auc = {}
    for c in ("blue", "red"):
        m = pmask[c] & region
        xs, ys = [], []
        for col in range(l + 1, r):
            rows = np.where(m[:, col])[0]
            if len(rows):
                xs.append((col - l) / (r - l))
                ys.append((b - rows.min()) / (b - t))
        xs, ys = np.r_[0.0, xs, 1.0], np.r_[0.0, ys, 1.0]
        pub_auc[c] = round(float(np.trapezoid(np.maximum.accumulate(ys), xs)), 3)
    return {"tolerance_px": TOL, "published_near_ours": s_pub, "ours_near_published": s_ours,
            "threshold": mark(controls), "controls": controls, "published_auc_read": pub_auc,
            "curves": {"blue": blue_key, "red": red_key}, "size": [pub.shape[1], pub.shape[0]]}


# ---------------------------------------------------------------- Fig. 6

def fig6(pub_dir, cal, dens, out_dir):
    c6 = cal["fig6"]
    pub = np.asarray(Image.open(pub_dir / c6["figure"]).convert("RGB"))
    size = (pub.shape[1], pub.shape[0])
    pmask = colour_masks(pub)
    tx0, ty0, tx1, ty1 = c6["text_mask_box_fraction"]
    regions, mappers = {}, {}
    full_region = np.zeros(pub.shape[:2], dtype=bool)
    erase = np.zeros(pub.shape[:2], dtype=bool)
    for k, p in c6["panels"].items():
        l, t, r, b = p["box"]
        text = (l + tx0 * (r - l), t + ty0 * (b - t), l + tx1 * (r - l), t + ty1 * (b - t))
        regions[k] = inside(pub.shape, p["box"], [text])
        full_region |= regions[k]
        erase |= erase_region(pub.shape, p["box"], [text])
        (vx0, px0), (vx1, px1) = p["x"]
        (vy0, py0), (vy1, py1) = p["y"]
        mappers[k] = (lambda x, y, px0=px0, px1=px1, vx0=vx0, vx1=vx1, py0=py0, py1=py1, vy0=vy0, vy1=vy1:
                      (px0 + (np.asarray(x) - vx0) * (px1 - px0) / (vx1 - vx0),
                       py0 + (np.asarray(y) - vy0) * (py1 - py0) / (vy1 - vy0)))
    base = erase_traces(pub, erase, full_region)

    def layers_for(k, sgi, non):
        mp = mappers[k]
        xs, ys = mp(sgi[0], sgi[1])
        xn, yn = mp(non[0], non[1])
        return [("blue", trace_layer(size, list(zip(xs, ys)), BLUE, "solid", 2)),
                ("red", trace_layer(size, list(zip(xn, yn)), RED, "dashed", 2))]

    def curves(key, amp=1.0, dx=0.0):
        e = dens[key]
        return ((np.array(e["sgi"]["x"]) + dx, np.array(e["sgi"]["y"]) * amp),
                (np.array(e["nonsgi"]["x"]) + dx, np.array(e["nonsgi"]["y"]) * amp))

    all_layers, result = [], {}
    for k, p in c6["panels"].items():
        key = f"weighted/diff_{p['property']}"
        sgi, non = curves(key)
        lay = layers_for(k, sgi, non)
        all_layers += lay
        _, om = compose(base, lay, regions[k])
        s_pub, s_ours = score(pmask, om, regions[k])
        span = p["x"][1][0] - p["x"][0][0]
        controls = []
        bs, bn = curves(f"binary/diff_{p['property']}")
        for name, kind, cs, cn in (
            ("binary network, same property", "wrong_input", bs, bn),
            ("classes swapped", "near_miss", non, sgi),
            ("density x 1.05", "near_miss", *curves(key, amp=1.05)),
            ("density x 0.95", "near_miss", *curves(key, amp=0.95)),
            ("x shifted by 1% of the axis", "near_miss", *curves(key, dx=0.01 * span)),
        ):
            _, m = compose(base, layers_for(k, cs, cn), regions[k])
            controls.append({"name": name, "kind": kind, "score": min(score(pmask, m, regions[k]))})
        e = dens[key]
        rng_s = float(np.percentile(np.array(e["ecdf_sgi"]), 99))
        result[f"fig6.{k}"] = {"tolerance_px": TOL, "published_near_ours": s_pub, "ours_near_published": s_ours,
                               "threshold": mark(controls), "controls": controls, "density": key,
                               "axis_max_published": p["x"][1][0] if k != "a" else 460,
                               "sgi_99th_percentile_ours": rng_s}
    img, _ = compose(base, all_layers, full_region)
    Image.fromarray(img).save(out_dir / "fig6_ours.png")
    Image.fromarray(overlay(pub, img)).save(out_dir / "fig6_overlay.png")
    return result


def main(pub_dir, cal_path, roc_path, dens_path, out):
    pub_dir, od = Path(pub_dir), Path(out)
    (od / "figures").mkdir(parents=True, exist_ok=True)
    cal = json.loads(Path(cal_path).read_text())
    roc = json.loads(Path(roc_path).read_text())
    dens = json.loads(Path(dens_path).read_text())
    comp = {}
    for fid in ROC_FIGS:
        comp[fid] = roc_figure(pub_dir, cal, roc, od / "figures", fid)
    comp.update(fig6(pub_dir, cal, dens, od / "figures"))
    (od / "comparison.json").write_text(json.dumps(comp, indent=1) + "\n")
    for k, v in comp.items():
        print(f"{k:8s} {min(v['published_near_ours'], v['ours_near_published']):.3f} "
              f"(pub {v['published_near_ours']:.3f}, ours {v['ours_near_published']:.3f}) mark {v['threshold']}  "
              + "; ".join(f"{c['name']} {c['score']:.3f}" for c in v["controls"]))


if __name__ == "__main__":
    main(*sys.argv[1:6])
