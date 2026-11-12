"""Draw our series on the published figures and score them.

Usage: python compare.py <sources> <published_values.json> <results dir> <out dir>

For every figure:
  fig*_ours.png     the published figure with its plotted series painted out and
                    ours drawn in their place, in the published style
  fig*_overlay.png  the published figure with ours drawn on top in red
For every panel, the two-way pixel score: the share of the published series'
ink within TOL px of ours, and of ours within TOL px of the published, at DPI;
both series are drawn solid at the published line width on a blank page with
the panel's own axis map, so only the plotted values differ. The same score is
computed for the negative controls (series.controls). Writes comparison.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pymupdf
from scipy import ndimage

import series as S

DPI = 300
TOL = 2
PASS_FLOOR = 0.95          # pass mark: the larger of this and the best control + 0.01

FIGFILES = {"fig1": ("MOESM2.pdf", 0), "fig2": ("MOESM3.pdf", 0), "fig3": ("MOESM4.pdf", 0),
            "fig4": ("MOESM5.pdf", 0), "fig5": ("MOESM6.pdf", 0), "fig6": ("MOESM7.pdf", 0),
            "fig7": ("MOESM8.pdf", 0), "figS2": ("MOESM1.PDF", 10), "figS3": ("MOESM1.PDF", 11),
            "figS4": ("MOESM1.PDF", 13), "figS5": ("MOESM1.PDF", 14), "figS6": ("MOESM1.PDF", 15),
            "figS8": ("MOESM1.PDF", 18), "figS9": ("MOESM1.PDF", 18)}
CLIPS = {"figS2": (150, 120, 470, 420), "figS3": (150, 125, 470, 262), "figS4": (135, 100, 480, 470),
         "figS5": (120, 140, 470, 420), "figS6": (150, 120, 470, 262), "figS8": (150, 125, 470, 262),
         "figS9": (150, 360, 470, 496)}


def to_px(p, x, y):
    xm, ym = p["x_map"], p["y_map"]
    if xm.get("categories") is not None:
        # categorical axes: a fraction removed (<= 1) names its category; larger x is already in points
        px = xm["categories"][f"{round(x, 2) + 0.0:g}"] if x <= 1.0 else x
    else:
        px = (x - xm["intercept"]) / xm["slope"]
    return px, (y - ym["intercept"]) / ym["slope"]


def polylines(p, ser):
    """Series (data units) -> list of point lists in PDF points."""
    out = []
    if "lines" in ser:
        for nm, l in ser["lines"].items():
            pl = p["lines"].get(nm)
            if pl is None:
                continue
            xa, xb = pl["x"]
            out.append([to_px(p, xa, l["intercept"] + l["slope"] * xa), to_px(p, xb, l["intercept"] + l["slope"] * xb)])
        return out
    for nm, pts in ser.items():
        pts = [q for q in pts if q[1] is not None and np.isfinite(q[1])]
        if len(pts) >= 2:
            out.append([to_px(p, x, y) for x, y in pts])
    return out


def published_series(fig, p):
    if fig in ("figS8", "figS9"):
        return {"lines": p["lines"]}
    ser = dict(p["series"])
    if fig == "fig6":
        ser.update(S.box_series(p["x_map"]["categories"], p["boxplots"]))
    if fig == "figS4":
        cats = p["x_map"]["categories"]
        for f, y in p["medians"].items():
            ser[f"median{f}"] = [[cats[f] - 2.8, y], [cats[f] + 2.8, y]]
    return ser


def width_of(fig, p):
    ws = [st["width"] for st in p.get("style", {}).values() if st.get("width")]
    return max(ws) if ws else 0.75


def mask(size, box, lines, width):
    doc = pymupdf.open()
    page = doc.new_page(width=size[0], height=size[1])
    sh = page.new_shape()
    for pl in lines:
        sh.draw_polyline(pl)
    sh.finish(color=(0, 0, 0), width=width, closePath=False)
    sh.commit()
    clip = pymupdf.Rect(*box)
    pix = page.get_pixmap(dpi=DPI, clip=clip, colorspace=pymupdf.csGRAY)
    a = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
    return a < 160


def score(m_pub, m_ours):
    if m_pub.sum() == 0 or m_ours.sum() == 0:
        return 0.0, 0.0
    d_ours = ndimage.distance_transform_edt(~m_ours)
    d_pub = ndimage.distance_transform_edt(~m_pub)
    return float((d_ours[m_pub] <= TOL).mean()), float((d_pub[m_ours] <= TOL).mean())


def draw(page, lines, color, width, dashes=None):
    sh = page.new_shape()
    for pl in lines:
        sh.draw_polyline(pl)
    sh.finish(color=color, width=width, closePath=False, dashes=dashes)
    sh.commit()


def render(src, fig, P, our, out_dir):
    fn, pg = FIGFILES[fig]
    clip = CLIPS.get(fig)
    dpi = DPI if not fig.startswith("figS") else 200
    doc = pymupdf.open(Path(src) / fn)
    doc[pg].get_pixmap(dpi=dpi, clip=pymupdf.Rect(*clip) if clip else None).save(str(Path(out_dir) / f"{fig}_published.png"))
    for kind in ("ours", "overlay"):
        doc = pymupdf.open(Path(src) / fn)
        page = doc[pg]
        for pn, p in P.items():
            pub_lines = polylines(p, published_series(fig, p))
            w = width_of(fig, p)
            if kind == "ours":
                # paint out the published series and the markers inside the panel
                draw(page, pub_lines, (1, 1, 1), w + 1.6)
                if fig not in ("fig2",):
                    for g in page.get_drawings():
                        r = g["rect"]
                        bx = p["box"]
                        if r.width < 8 and r.height < 8 and bx[0] < r.x0 and r.x1 < bx[2] and bx[1] < r.y0 and r.y1 < bx[3]:
                            page.draw_rect(r + (-0.6, -0.6, 0.6, 0.6), color=None, fill=(1, 1, 1))
                    if fig in ("fig7", "figS5", "fig3", "fig4", "fig6", "figS2", "figS4", "figS6"):
                        for w_ in page.get_text("words"):
                            r = pymupdf.Rect(w_[:4])
                            bx = p["box"]
                            if w_[4].strip("G") == "" and bx[0] < r.x0 and r.x1 < bx[2] and bx[1] < r.y0 and r.y1 < bx[3]:
                                page.draw_rect(r, color=None, fill=(1, 1, 1))
                for nm, pts in our[pn].items() if "lines" not in our[pn] else []:
                    st = p.get("style", {}).get(nm) or {}
                    col = tuple(st.get("color") or (0, 0, 0))
                    dsh = st.get("dashes")
                    dsh = None if not dsh or dsh == "[] 0" else dsh
                    draw(page, polylines(p, {nm: pts}), col, st.get("width") or w, dsh)
                if "lines" in our[pn]:
                    for nm, l in our[pn]["lines"].items():
                        col = {"B25": (1, 0, 0), "B50": (0, 1, 0), "C10": (0, 0, 1), "C20": (0, 0, 0)}[nm]
                        draw(page, polylines(p, {"lines": {nm: l}}), col, w)
            else:
                draw(page, polylines(p, our[pn]), (0.9, 0.1, 0.1), w)
        pix = page.get_pixmap(dpi=dpi, clip=pymupdf.Rect(*clip) if clip else None)
        pix.save(str(Path(out_dir) / f"{fig}_{kind}.png"))


def main(src, pubfile, res_dir, out_dir):
    pub = json.loads(Path(pubfile).read_text())
    R = {"sim": "sim_sd0.1.json", "sim_sd001": "sim_sd0.01.json", "one": "one_sd0.1.json",
         "one_sd001": "one_sd0.01.json", "one_sd0": "one_sd0.json", "fig1": "fig1.json", "leuk": "leukemia.json", "pi0_07": "sim_pi0.7.json"}
    R = {k: json.loads((Path(res_dir) / v).read_text()) for k, v in R.items()}
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    comp = {"dpi": DPI, "tolerance_px": TOL, "pass_floor": PASS_FLOOR, "figures": {}}
    for fig in FIGFILES:
        P = pub[fig]["panels"]
        our = {pn: S.ours(fig, pn, R, "ours", p) for pn, p in P.items()}
        render(src, fig, P, our, out_dir)
        fc = {}
        for pn, p in P.items():
            size = pub[fig]["size"]
            if fig.startswith("figS"):
                size = [612, 792]
            box = p["box"]
            w = width_of(fig, p)
            m_pub = mask(size, box, polylines(p, published_series(fig, p)), w)
            a, b = score(m_pub, mask(size, box, polylines(p, our[pn]), w))
            ctrl = []
            for v, kind, desc in S.controls(fig):
                try:
                    cs = S.ours(fig, pn, R, v, p)
                except (KeyError, IndexError, TypeError):
                    continue
                if cs == our[pn]:
                    continue                 # identical to ours on this panel: not a control
                ca, cb = score(m_pub, mask(size, box, polylines(p, cs), w))
                ctrl.append({"name": f"{v}: {desc}", "kind": kind, "score": round(min(ca, cb), 4)})
            best = max(c["score"] for c in ctrl)
            fc[pn] = {"published_near_ours": round(a, 4), "ours_near_published": round(b, 4),
                      "score": round(min(a, b), 4), "controls": ctrl,
                      "threshold": round(max(PASS_FLOOR, best + 0.01), 4),
                      "values": value_diffs(fig, p, our[pn], R, pn)}
            if fig in ("fig4", "figS2", "figS6"):
                # the same score with the points up to x = 0.9 only (a hypothesis test for the x = 0.99 point)
                cut = lambda ser: {n: [q for q in pts if q[0] < 0.95] for n, pts in ser.items()}
                ca, cb = score(mask(size, box, polylines(p, cut(published_series(fig, p))), w),
                               mask(size, box, polylines(p, cut(our[pn])), w))
                fc[pn]["score_x_up_to_0.9"] = round(min(ca, cb), 4)
        comp["figures"][fig] = {"panels": fc, "outputs": [f"{fig}_ours.png", f"{fig}_overlay.png", f"{fig}_published.png"]}
        print(fig, {pn: (v["score"], max(c["score"] for c in v["controls"]), v["values"].get("max_abs"))
                    for pn, v in fc.items()})
    (Path(out_dir) / "comparison.json").write_text(json.dumps(comp, indent=1))


def value_diffs(fig, p, ours, R=None, panel=None):
    """Differences in data units at the published points (series drawn at
    discrete x only): mean and largest absolute difference."""
    if "lines" in ours:
        d = []
        for nm, l in ours["lines"].items():
            pl = p["lines"].get(nm)
            if pl:
                for x in pl["x"]:
                    d.append(abs((l["intercept"] + l["slope"] * x) - (pl["intercept"] + pl["slope"] * x)))
        return {"points": len(d), "mean_abs": float(np.mean(d)) if d else None, "max_abs": float(np.max(d)) if d else None}
    if fig in ("fig1", "fig2", "fig6"):
        return {}
    d, d_inner = [], []
    for nm, pts in p["series"].items():
        o = {round(x, 2): y for x, y in ours.get(nm, [])}
        for x, y in pts:
            if round(x, 2) in o and o[round(x, 2)] is not None:
                d.append(abs(o[round(x, 2)] - y))
                if round(x, 2) < 0.95:
                    d_inner.append(d[-1])
    out = {"points": len(d), "mean_abs": float(np.mean(d)) if d else None, "max_abs": float(np.max(d)) if d else None}
    if fig in ("fig3", "fig4", "figS2", "figS6") and d_inner:
        out["max_abs_below_0.95"] = float(np.max(d_inner))      # without the x = 0.99 and x = 1 points
    if fig == "fig3":
        # the caption's labels of the signal and variance curves swapped
        sw = {"signal": "variance", "variance": "signal"}
        e = []
        for nm, pts in p["series"].items():
            if nm not in sw:
                continue
            o = {round(x, 2): y for x, y in ours.get(sw[nm], [])}
            e += [abs(o[round(x, 2)] - y) for x, y in pts if round(x, 2) in o and round(x, 2) < 0.995]
        out["max_abs_signal_variance_swapped"] = float(np.max(e))
        out["max_abs_signal_variance_as_labelled"] = float(np.max(
            [abs({round(x, 2): y for x, y in ours[nm]}[round(x, 2)] - y) for nm in sw for x, y in p["series"][nm]
             if round(x, 2) < 0.995]))
    if fig in ("fig7", "figS5") and R is not None:
        # the published points against the range of our 20 other random subsets of each size
        col = 1 if fig == "fig7" else 2
        inside, total = 0, 0
        for nm, pts in p["series"].items():
            filt, n = nm.split(".")
            draws = R["leuk"]["draws"][n]
            for x, y in pts:
                i = int(round(x * 10))
                vals = [d[filt][i][col] for d in draws]
                total += 1
                inside += min(vals) <= y <= max(vals)
        out["published_within_20_draws"] = f"{inside} of {total}"
        out["share_within_20_draws"] = inside / total
    return out


if __name__ == "__main__":
    main(*sys.argv[1:5])
