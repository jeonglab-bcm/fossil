"""Draw our panels on the published figures' pixel grids and measure the agreement.

For every data panel: the axes box is snapped to the published box lines, our layers
(figdata.py) are painted in drawing order onto the same pixel grid with MATLAB's line widths
at the figure's scale, and published pixels are classified by nearest palette colour. For each
colour we report the share of published pixels within TOL px of ours and of our visible pixels
within TOL px of the published ones.

Outputs: fig*_overlay.png (published faded, ours painted on top), fig*_redrawn.png (the
published figure with each compared region erased and ours painted in) and comparison.json.
"""

import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import figdata as fd
from figmeasure import load, snap_box

TOL = 4

# MATLAB colour -> published colour (the files were converted through CMYK)
BASE = {
    (0.0, 0.8, 0.0): (120, 200, 50), (0.6, 0.0, 0.6): (136, 8, 152), (1.0, 0.0, 0.0): (220, 15, 15),
    (0.0, 0.0, 1.0): (15, 15, 248), (0.5, 0.0, 0.0): (104, 8, 8), (0.0, 0.0, 0.5): (8, 8, 120),
    (0.7, 0.7, 0.7): (177, 177, 177), (0.0, 0.0, 0.0): (0, 0, 0),
    (1.0, 0.5, 0.5): (232, 120, 120), (0.5, 0.5, 1.0): (120, 120, 248),
    (1.0, 0.35, 0.0): (216, 88, 24), (1.0, 0.7, 0.0): (232, 184, 40),
}


def pub_rgb(rgb):
    """Published colour of a MATLAB colour; tints (white mixed with a base colour) are mixed
    the same way from the published base colour."""
    rgb = tuple(round(float(c), 3) for c in rgb)
    if rgb in BASE:
        return BASE[rgb]
    for base, pub in BASE.items():
        # rgb = a * white + (1 - a) * base
        a = [(r - b) / (1 - b) for r, b in zip(rgb, base) if b < 1]
        if a and max(a) - min(a) < 1e-6 and 0 < a[0] < 1:
            if all(abs(r - 1) < 1e-9 for r, b in zip(rgb, base) if b >= 1):
                return tuple(int(round(a[0] * 255 + (1 - a[0]) * p)) for p in pub)
    return tuple(int(round(255 * c)) for c in rgb)


# --------------------------------------------------------------------------- painting

class Canvas:
    def __init__(self, shape, box, panel, scale):
        self.shape = shape
        self.L, self.T, self.R, self.B = box
        self.p = panel
        self.scale = scale
        self.labels = np.zeros(shape[:2], np.int32)
        self.colour_of = {}
        self.n = 0

    def _x(self, x):
        x = np.asarray(x, float)
        lo, hi = self.p["xlim"]
        if self.p.get("xlog"):
            x = np.log10(np.maximum(x, 1e-300))
            lo, hi = np.log10(lo), np.log10(hi)
        return self.L + (x - lo) / (hi - lo) * (self.R - self.L)

    def _y(self, y):
        y = np.asarray(y, float)
        lo, hi = self.p["ylim"]
        if self.p.get("ylog"):
            y = np.log10(np.maximum(y, 1e-300))
            lo, hi = np.log10(lo), np.log10(hi)
        return self.B - (y - lo) / (hi - lo) * (self.B - self.T)

    def paint(self, layer):
        im = Image.new("1", (self.shape[1], self.shape[0]), 0)
        d = ImageDraw.Draw(im)
        kind = layer["kind"]
        if kind == "line":
            X, Y = self._x(layer["x"]), self._y(layer["y"])
            Y = np.clip(Y, self.T - 50, self.B + 50)
            w = max(1, int(round(layer["lw"] * self.scale)))
            pts = [(a, b) for a, b in zip(X, Y) if np.isfinite(a) and np.isfinite(b)]
            if layer.get("style") == "--":
                pts = _dash(pts, 6 * self.scale, 3 * self.scale)
                for seg in pts:
                    d.line(seg, fill=1, width=w)
            elif len(pts) > 1:
                d.line(pts, fill=1, width=w, joint="curve")
        elif kind == "fill":
            X, Y = self._x(layer["x"]), self._y(layer["y"])
            Y = np.clip(Y, self.T - 5, self.B + 5)
            d.polygon(list(zip(X, Y)), fill=1)
        elif kind == "rect":
            x0, x1 = self._x(np.clip(layer["x"], *_lim(self.p["xlim"], self.p.get("xlog"))))
            y0, y1 = self._y(layer["y"])
            d.rectangle([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)], fill=1)
        elif kind == "markers":
            # MATLAB: a "." dot is about a third of its MarkerSize across, an "o" its full size
            r = layer["size"] * self.scale / (6.0 if not layer.get("open") else 2.0)
            for a, b in zip(self._x(layer["x"]), self._y(layer["y"])):
                if layer.get("open"):
                    w = max(1, int(round(self.scale)))
                    d.ellipse([a - r, b - r, a + r, b + r], outline=1, width=w)
                else:
                    d.ellipse([a - r, b - r, a + r, b + r], fill=1)
        elif kind == "errorbar":
            w = max(1, int(round(layer["lw"] * self.scale)))
            for a, b, e in zip(self._x(layer["x"]), layer["y"], layer["err"]):
                d.line([(a, self._y(b - e)), (a, self._y(b + e))], fill=1, width=w)
        m = np.array(im, bool)
        self.n += 1
        self.labels[m] = self.n
        self.colour_of[self.n] = (tuple(round(float(c), 3) for c in layer["rgb"]),
                                  layer.get("compare", True))
        if kind in ("fill", "rect") and layer.get("edge", True):
            # MATLAB fill() and bar() draw a black 0.5 pt edge by default
            e = Image.new("1", (self.shape[1], self.shape[0]), 0)
            de = ImageDraw.Draw(e)
            w = max(1, int(round(0.5 * self.scale)))
            if kind == "fill":
                X, Y = self._x(layer["x"]), np.clip(self._y(layer["y"]), self.T - 5, self.B + 5)
                pts = list(zip(X, Y))
                de.line(pts + pts[:1], fill=1, width=w)
            else:
                x0, x1 = self._x(layer["x"])
                y0, y1 = self._y(layer["y"])
                de.rectangle([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)], outline=1, width=w)
            em = np.array(e, bool)
            self.n += 1
            self.labels[em] = self.n
            self.colour_of[self.n] = ((0.0, 0.0, 0.0), layer.get("compare", True))

    def region(self, inset=6):
        m = np.zeros(self.shape[:2], bool)
        m[int(self.T) + inset:int(self.B) - inset + 1, int(self.L) + inset:int(self.R) - inset + 1] = True
        return m


def _lim(lim, log):
    return (lim[0], lim[1])


def _dash(pts, on, off):
    segs, cur, budget, drawing = [], [pts[0]], on, True
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        L = np.hypot(x1 - x0, y1 - y0)
        pos = 0.0
        while L - pos > budget:
            pos += budget
            p = (x0 + (x1 - x0) * pos / L, y0 + (y1 - y0) * pos / L)
            if drawing:
                cur.append(p)
                segs.append(cur)
            cur = [p]
            drawing = not drawing
            budget = on if drawing else off
        budget -= L - pos
        if drawing:
            cur.append((x1, y1))
        else:
            cur = [(x1, y1)]
    if drawing and len(cur) > 1:
        segs.append(cur)
    return segs


def _save_half(arr, path):
    """Overlays are written at half the published resolution to keep the repository small."""
    im = Image.fromarray(arr)
    im.resize((im.width // 2, im.height // 2), Image.LANCZOS).save(path, optimize=True)


def classify(img, region, colours):
    """Published pixels assigned to the nearest palette colour (with white as background)."""
    pal = [(255, 255, 255)] + [pub_rgb(c) for c in colours]
    sub = img[region]
    d = np.stack([np.abs(sub - np.array(p)).sum(1) for p in pal], 1)
    lab = d.argmin(1)
    near = d.min(1) <= 90
    out = {}
    for i, c in enumerate(colours, start=1):
        m = np.zeros(img.shape[:2], bool)
        m[region] = (lab == i) & near
        out[c] = m
    return out


def measure(img, box, panel, scale):
    cv = Canvas(img.shape, box, panel, scale)
    for layer in panel["layers"]:
        cv.paint(layer)
    region = cv.region()
    for fx0, fy0, fx1, fy1 in panel.get("exclude", []):
        # text and legends inside the box, as fractions of the box (x right, y up)
        L, T, R, B = box
        region[int(B - fy1 * (B - T)):int(B - fy0 * (B - T)) + 1,
               int(L + fx0 * (R - L)):int(L + fx1 * (R - L)) + 1] = False
    colours = sorted({c for c, _ in cv.colour_of.values()})
    pub = classify(img, region, colours)
    res = {}
    for c in colours:
        ids = [i for i, (cc, cmp) in cv.colour_of.items() if cc == c and cmp]
        if not ids:
            continue
        ours = np.isin(cv.labels, ids) & region
        p = pub[c]
        if c in ((0.7, 1.0, 0.7), (1.0, 0.7, 1.0)):
            continue
        if c == (0.0, 0.0, 0.0):
            # black also covers text, ticks and legends inside the box: count only the
            # published black pixels near our black elements' bounding area
            near = ndimage.binary_dilation(ours, iterations=int(4 * scale))
            p = p & near
        if ours.sum() == 0 and p.sum() == 0:
            continue
        r = {"published_px": int(p.sum()), "ours_px": int(ours.sum())}
        if ours.sum() and p.sum():
            d_our = ndimage.distance_transform_edt(~ours)
            d_pub = ndimage.distance_transform_edt(~p)
            r["published_matched"] = round(float((d_our[p] <= TOL).mean()), 4)
            r["ours_matched"] = round(float((d_pub[ours] <= TOL).mean()), 4)
        res[str(c)] = r
    # all coloured traces together, whatever their colour (thin overlapping curves blend in
    # the published raster, so their individual colours cannot always be told apart)
    traces = [c for c in colours if c not in ((0.0, 0.0, 0.0), (0.7, 0.7, 0.7), (0.7, 1.0, 0.7),
                                              (1.0, 0.7, 1.0))]
    if traces:
        ids = [i for i, (cc, cmp) in cv.colour_of.items() if cc in traces and cmp]
        ours = np.isin(cv.labels, ids) & region
        p = np.zeros_like(ours)
        for c in traces:
            p |= pub[c]
        if ours.sum() and p.sum():
            d_our = ndimage.distance_transform_edt(~ours)
            d_pub = ndimage.distance_transform_edt(~p)
            res["all_traces"] = {"published_px": int(p.sum()), "ours_px": int(ours.sum()),
                                 "published_matched": round(float((d_our[p] <= TOL).mean()), 4),
                                 "ours_matched": round(float((d_pub[ours] <= TOL).mean()), 4)}
    return cv, region, res


def paint_overlay(out, cv, region, fade=0.3):
    """Our layers over the published pixels of the region, faded to `fade` (0: erased)."""
    faded = out[region].astype(float)
    out[region] = (255 - (255 - faded) * fade).astype(np.uint8)
    for i, (c, _) in cv.colour_of.items():
        m = (cv.labels == i) & region
        out[m] = pub_rgb(c)


def paint_both(ov, rd, cv, region):
    paint_overlay(ov, cv, region)
    paint_overlay(rd, cv, region, fade=0)


# --------------------------------------------------------------------------- layouts

def boxes_fig2(img):
    B = {}
    for off, (b, c, d) in [(0, ("B", "C", "D")), (1, ("E", "F", "G"))]:
        x0 = [0, 2069][off]
        B[b] = snap_box(img, ([1156, 2348][off], 290, [1930, 3121][off], 988))
        for k in range(6):
            col, row = k % 3, k // 3
            L = [284, 853, 1422][col] + x0 - (1 if off and col == 0 else 0)
            T = [1224, 1638][row]
            B[(c, k)] = snap_box(img, (L, T, L + 510, T + 365))
        xs = [279, 1243] if off == 0 else [2352, 3318]
        B[(d, "k1_density")] = snap_box(img, (xs[0], 2466, xs[0] + 675, 2866))
        B[(d, "k1_s1_estimate")] = snap_box(img, (xs[0], 2881, xs[0] + 675, 2943), search=10)
        B[(d, "k1_s2_estimate")] = snap_box(img, (xs[0], 2959, xs[0] + 675, 3020), search=10)
        B[(d, "k2_density")] = snap_box(img, (xs[1], 2466, xs[1] + 676, 2866))
        B[(d, "k2_estimate")] = snap_box(img, (xs[1], 2882, xs[1] + 676, 3020), search=10)
        B[(d, "k3_density")] = snap_box(img, (xs[0], 3205, xs[0] + 675, 3605))
        B[(d, "k3_estimate")] = snap_box(img, (xs[0], 3620, xs[0] + 675, 3759), search=10)
        B[(d, "w1_density")] = snap_box(img, (xs[1], 3206, xs[1] + 676, 3605))
        B[(d, "w1_estimate")] = snap_box(img, (xs[1], 3620, xs[1] + 676, 3759), search=10)
    return B


def boxes_fig34(img, which):
    B = {}
    if which == "H1":
        kin = [1477, 1802, 2126, 2450, 2774]
        dose = [1476, 1801, 2125, 2449, 2773, 3098]
        xk, xd, h = (223, 849), (1092, 1718), 271
        B["B", "kinetic_0"] = snap_box(img, (2469, 211, 3216, 842))
        B["B", "kinetic_1"] = snap_box(img, (2469, 907, 3216, 1538))
        B["B", "dose_0"] = snap_box(img, (3251, 212, 3999, 842))
        B["B", "dose_1"] = snap_box(img, (3252, 907, 3998, 1538))
        B["D", "rates"] = snap_box(img, (2694, 1942, 3997, 2875))
    else:
        kin = [1840, 2165, 2491, 2816, 3142]
        dose = [1840, 2165, 2491, 2816, 3142, 3468]
        xk, xd, h = (244, 870), (1115, 1743), 275
        B["B", "kinetic_0"] = snap_box(img, (2475, 249, 3224, 882))
        B["B", "kinetic_1"] = snap_box(img, (2476, 947, 3224, 1580))
        B["B", "dose_0"] = snap_box(img, (3259, 250, 4010, 882))
        B["B", "dose_1"] = snap_box(img, (3259, 948, 4010, 1580))
        B["D", "rates"] = snap_box(img, (2714, 2687, 4022, 3781))
        B["D", "w1"] = snap_box(img, (2715, 3922, 4022, 4078), search=10)
    for k, T in enumerate(kin):
        B["C", f"kinetic_{k}"] = snap_box(img, (xk[0], T, xk[1], T + h))
    for k, T in enumerate(dose):
        B["C", f"dose_{k}"] = snap_box(img, (xd[0], T, xd[1], T + h))
    return B


def run(sources, published, out, fits="saved", refit_dir=None, figs=(2, 3, 4, 5, 6), tag=""):
    os.makedirs(out, exist_ok=True)
    result = {}

    if 2 in figs:
        result["fig2"] = fig2_compare(sources, published, out, fits, refit_dir, tag)
    if 3 in figs or 4 in figs:
        result.update(fig34_compare(sources, published, out, fits, refit_dir, figs))
    if 5 in figs:
        result["fig5"] = fig5_compare(sources, published, out, fits, refit_dir)
    if 6 in figs:
        result["fig6"] = fig6_compare(sources, published, out)
    json.dump(result, open(os.path.join(out, f"comparison{tag}.json"), "w"), indent=1)
    return result


def fig2_compare(sources, published, out, fits, refit_dir, tag):
    img = load(os.path.join(published, "figure-2.png"))
    boxes = boxes_fig2(img)
    ov = img.astype(np.uint8).copy()
    rd = ov.copy()
    res = {}
    for scen in (1, 2):
        P = fd.fig2(sources, scen, fits, refit_dir)
        for key, box in boxes.items():
            if isinstance(key, str):
                if key not in P:
                    continue
                panel = P[key]
                name = key
            else:
                if key[0] not in P:
                    continue
                panel = P[key[0]][key[1]]
                name = f"{key[0]}:{key[1]}"
            cv, region, r = measure(img, box, panel, 7.15)
            paint_both(ov, rd, cv, region)
            res[name] = {"box": [round(float(v), 1) for v in box], "colours": r}
    _save_half(ov, os.path.join(out, f"fig2_overlay{tag}.png"))
    _save_half(rd, os.path.join(out, f"fig2_redrawn{tag}.png"))
    return res


def fig34_compare(sources, published, out, fits, refit_dir, figs):
    result = {}
    for fig, which in [(3, "H1"), (4, "H3")]:
        if fig not in figs:
            continue
        img = load(os.path.join(published, f"figure-{fig}.png"))
        boxes = boxes_fig34(img, which)
        P = fd.fig34(sources, which, fits, refit_dir)
        ov = img.astype(np.uint8).copy()
        rd = ov.copy()
        res = {}
        for key, box in boxes.items():
            panel = P[key[0]][key[1]]
            if which == "H3" and key[0] == "B":
                # the "w1 = ..%" / "w2 = ..%" labels (text, not traces)
                panel["exclude"] = [(0.55, 0.62, 1.0, 0.82), (0.55, 0.12, 1.0, 0.30)]
            cv, region, r = measure(img, box, panel, 7.25)
            paint_both(ov, rd, cv, region)
            res[f"{key[0]}:{key[1]}"] = {"box": [round(float(v), 1) for v in box], "colours": r}
        res["weights"] = [[round(float(w), 4) for w in ws] for ws in P["weights"]]
        _save_half(ov, os.path.join(out, f"fig{fig}_overlay.png"))
        _save_half(rd, os.path.join(out, f"fig{fig}_redrawn.png"))
        result[f"fig{fig}"] = res
    return result


def fig5_compare(sources, published, out, fits, refit_dir):
    img = load(os.path.join(published, "figure-5.png"))
    F5 = fd.fig5(sources, fits, refit_dir)
    box = snap_box(img, (453, 1668, 3075, 2661))
    cols = [(1.0, 0.0, 0.0), (1.0, 0.35, 0.0), (1.0, 0.7, 0.0)]
    layers = []
    for i in range(9):
        for j in range(3):
            x = i + 1 + (j - 1) * 0.2222   # MATLAB grouped bar: width 0.8/3 of a group of 0.8
            layers.append({"kind": "rect", "rgb": cols[j], "x": (x - 0.0889, x + 0.0889),
                           "y": (0, F5["BIC"][i, j])})
    panel = {"xlim": (0.5, 9.5), "ylim": (np.exp(11.15), np.exp(11.65)), "layers": layers}
    cv, region, r = measure(img, box, panel, 7.27)
    ov = img.astype(np.uint8).copy()
    rd = ov.copy()
    paint_both(ov, rd, cv, region)
    _save_half(ov, os.path.join(out, "fig5_overlay.png"))
    _save_half(rd, os.path.join(out, "fig5_redrawn.png"))
    return {"B": {"box": [round(float(v), 1) for v in box], "colours": r},
            "BIC": F5["BIC"].round(4).tolist(),
            "C_w1_percent": [round(100 * w[0], 1) for w in F5["w_H33"]],
            "C_published_percent": [68.8, 71.5, 70.0]}


def fig6_compare(sources, published, out):
    img = load(os.path.join(published, "figure-6.png"))
    F6 = fd.fig6(sources)
    ov = img.astype(np.uint8).copy()
    rd = ov.copy()
    res = {"rho_control": round(F6["rho_control"], 4), "rho_stimulated": round(F6["rho_stimulated"], 4),
           "published_rho": [0.895, 0.696],
           "w_percent": [round(100 * float(p), 2) for p in F6["gm"]["p"]],
           "published_w_percent": [68.0, 32.0], "gm_mu": F6["gm"]["mu"].round(4).tolist(),
           "n_cells_used": 1500, "n_control": F6["n_control_total"], "n_stimulated": F6["n_stim_total"]}
    # scatter panels: published black dots vs ours
    y_hist = np.linspace(-1, 1, 40)
    n = 1500

    def hist_of(v):
        # histc with edges y_hist; its last bin (values equal to the last edge) is dropped
        h = np.histogram(v, np.r_[y_hist, np.inf])[0][:-1].astype(float)
        return h / n
    ctrl, stim, i1, i2 = F6["control"], F6["stimulated"], F6["ind1"], F6["ind2"]
    both = np.r_[i1, i2]
    h_pc = hist_of(ctrl[both, 1])
    specs = {
        "A:scatter": ((444, 197, 1183, 938), [{"kind": "markers", "rgb": (0, 0, 0), "size": 1.5,
                                               "x": 10 ** ctrl[:, 0], "y": 10 ** ctrl[:, 1]}]),
        "B:scatter": ((1925, 197, 2664, 938), [
            {"kind": "markers", "rgb": (0, 0, 0), "size": 1.5, "x": 10 ** np.r_[ctrl[:, 0], stim[:, 0]],
             "y": 10 ** np.r_[ctrl[:, 1], stim[:, 1]]}] + _ellipses(F6["gm"])),
    }
    for key, (approx, layers) in specs.items():
        box = snap_box(img, approx)
        panel = {"xlim": (0.1, 10), "ylim": (0.1, 10), "xlog": True, "ylog": True, "layers": layers,
                 # legend, and the "32.0 %" / "68.0 %" labels
                 "exclude": [(0.22, 0.0, 1.0, 0.2), (0.6, 0.83, 1.0, 0.98), (0.6, 0.43, 1.0, 0.59)]}
        cv, region, r = measure(img, box, panel, 6.16)
        paint_both(ov, rd, cv, region)
        res[key] = {"box": [round(float(v), 1) for v in box], "colours": r}
    # marginal histograms
    st = lambda h: fd.staircase(y_hist, h)   # noqa: E731
    hist_specs = {
        "A:pErk_hist": ((148, 198, 385, 939), "v", [((0.7, 0.7, 0.7), h_pc)], h_pc.max()),
        "A:Erk_hist": ((444, 998, 1183, 1205), "h", [((0.7, 0.7, 0.7), hist_of(ctrl[both, 0]))], h_pc.max()),
        "B:pErk_hist": ((1629, 197, 1864, 939), "v", [((0, 0.8, 0), hist_of(stim[both, 1])),
                                                      ((0.6, 0, 0.6), hist_of(stim[i2, 1]))], h_pc.max()),
        "B:Erk_hist": ((1925, 998, 2665, 1205), "h", [((0, 0.8, 0), hist_of(stim[both, 0])),
                                                     ((0.6, 0, 0.6), hist_of(stim[i2, 0]))], h_pc.max()),
    }
    for key, (approx, orient, fills, hmax) in hist_specs.items():
        box = snap_box(img, approx)
        layers = []
        for c, h in fills:
            x, y = st(h)
            if orient == "v":
                layers.append({"kind": "fill", "rgb": c, "x": y, "y": 10 ** x})
            else:
                layers.append({"kind": "fill", "rgb": c, "x": 10 ** x, "y": y})
        if orient == "v":
            panel = {"xlim": (0, 1.1 * hmax), "ylim": (0.1, 10), "ylog": True, "layers": layers}
        else:
            panel = {"xlim": (0.1, 10), "xlog": True, "ylim": (0, 1.1 * hmax), "layers": layers}
        cv, region, r = measure(img, box, panel, 6.16)
        paint_both(ov, rd, cv, region)
        res[key] = {"box": [round(float(v), 1) for v in box], "colours": r}
    _save_half(ov, os.path.join(out, "fig6_overlay.png"))
    _save_half(rd, os.path.join(out, "fig6_redrawn.png"))
    return res


def _ellipses(gm):
    """Contours P_k / max P_k = exp(-2): the 2-sigma ellipse of each component."""
    out = []
    th = np.linspace(0, 2 * np.pi, 400)
    for k, c in enumerate([(0, 0.8, 0), (0.6, 0, 0.6)]):
        vals, vecs = np.linalg.eigh(gm["Sigma"][k])
        pts = gm["mu"][k][:, None] + vecs @ (2 * np.sqrt(vals)[:, None] * np.vstack([np.cos(th), np.sin(th)]))
        out.append({"kind": "line", "rgb": c, "lw": 0.5, "x": 10 ** pts[0], "y": 10 ** pts[1]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", required=True)
    ap.add_argument("--published", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fits", default="saved", choices=["saved", "refit"])
    ap.add_argument("--refit-dir")
    ap.add_argument("--figs", default="2,3,4,5,6")
    ap.add_argument("--tag", default="", help="suffix for output names, e.g. _refit")
    a = ap.parse_args()
    r = run(a.sources, a.published, a.out, a.fits, a.refit_dir,
            tuple(int(f) for f in a.figs.split(",")), a.tag)
    for fig, panels in r.items():
        for name, v in panels.items():
            if isinstance(v, dict) and "colours" in v:
                cs = "  ".join(f"{c}: {x.get('published_matched')}/{x.get('ours_matched')}"
                               for c, x in v["colours"].items())
                print(f"{fig} {name:22s} {cs}")


if __name__ == "__main__":
    main()
