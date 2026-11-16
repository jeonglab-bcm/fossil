"""Our values drawn on the paper's own supplementary pages (Figs S1, S2, S3, S5).

The supplementary figures are vector PDFs. To draw ours on exactly the published axes, the page is
rebuilt from its own drawing commands and text, leaving out only the published data marks (bars,
error bars, line markers, box plots, -log(p) labels); our values are then drawn with the same
marks, colours and calibrated axes. The overlay draws our marks in black on the untouched page.
Both are rasterized with the same clip and resolution as published/figure-S<n>.png.
"""

from __future__ import annotations

import math
import re

import pymupdf

DPI = 150


def clip_of(page):
    """The drawn part of a page (drawings and text), with a small margin."""
    r = None
    for d in page.get_drawings():
        r = d["rect"] if r is None else r | d["rect"]
    for b in page.get_text("dict")["blocks"]:
        r = r | pymupdf.Rect(b["bbox"])
    return pymupdf.Rect(r.x0 - 6, r.y0 - 6, r.x1 + 6, r.y1 + 6)


def published_png(pdf_path, out_path):
    """published/figure-S<n>.png: the page's drawn part at DPI."""
    page = pymupdf.open(pdf_path)[0]
    page.get_pixmap(dpi=DPI, clip=clip_of(page)).save(out_path)


def close(c, ref, tol=0.02):
    return c is not None and len(c) == 3 and all(abs(a - b) <= tol for a, b in zip(c, ref))


def rebuild(src_page, drop_drawing, drop_span):
    """A new one-page document with the source page's drawings and text, minus the dropped ones."""
    doc = pymupdf.open()
    page = doc.new_page(width=src_page.rect.width, height=src_page.rect.height)
    for d in src_page.get_drawings():
        if drop_drawing(d):
            continue
        sh = page.new_shape()
        for it in d["items"]:
            if it[0] == "l":
                sh.draw_line(it[1], it[2])
            elif it[0] == "re":
                sh.draw_rect(it[1])
            elif it[0] == "qu":
                sh.draw_quad(it[1])
            elif it[0] == "c":
                sh.draw_bezier(it[1], it[2], it[3], it[4])
        sh.finish(color=d.get("color"), fill=d.get("fill"), width=d.get("width") or 0.25,  # PDF width 0 is a hairline
                  dashes=d.get("dashes") or None, closePath=bool(d.get("closePath")),
                  even_odd=bool(d.get("even_odd")), lineCap=max(d.get("lineCap") or (0,)) if d.get("lineCap") else 0,
                  fill_opacity=d.get("fill_opacity") or 1, stroke_opacity=d.get("stroke_opacity") or 1)
        sh.commit()
    for b in src_page.get_text("dict")["blocks"]:
        for line in b.get("lines", []):
            dx, dy = line["dir"]
            rot = int(round(math.degrees(math.atan2(-dy, dx)))) % 360
            for s in line["spans"]:
                if not s["text"].strip() or drop_span(s):
                    continue
                c = s["color"]
                page.insert_text(s["origin"], s["text"], fontsize=s["size"], fontname="helv",
                                 color=((c >> 16 & 255) / 255, (c >> 8 & 255) / 255, (c & 255) / 255), rotate=rot)
    return doc, page


def rasterize(page, clip, path):
    page.get_pixmap(dpi=DPI, clip=clip).save(path)


def y_of(axis, v):
    return (v - axis["a"]) / axis["b"]


def number_label(s):
    t = s["text"].strip().replace(" ", "")
    return re.fullmatch(r"\d+\.\d", t) is not None


# ----------------------------------------------------------------------------- shared marks

def bar(page, x0, x1, top, floor, fill, outline=None):
    sh = page.new_shape()
    sh.draw_rect(pymupdf.Rect(x0, top, x1, floor))
    sh.finish(fill=fill, color=outline, width=0.5 if outline else 0)
    sh.commit()


def errbar(page, xc, lo, hi, colour=(0.01, 0.01, 0.01), half=2.5):
    sh = page.new_shape()
    sh.draw_line((xc, lo), (xc, hi))
    sh.draw_line((xc - half, hi), (xc + half, hi))
    sh.finish(color=colour, width=0.56, closePath=False)
    sh.commit()


def tick(page, x0, x1, y, colour=(0, 0, 0), width=1.2):
    sh = page.new_shape()
    sh.draw_line((x0 - 1.5, y), (x1 + 1.5, y))
    sh.finish(color=colour, width=width, closePath=False)
    sh.commit()


def neglogp_text(test):
    if not test or not test.get("pac_better") or test.get("p", 1) >= 0.05:
        return None
    return f"{test['neglog10p']:.1f}"


# ----------------------------------------------------------------------------- Fig. S2

S2_COLOURS = {"Gene": (0.31, 0.51, 0.75), "PAC": (0.76, 0.32, 0.31), "Mean": (0.61, 0.73, 0.35),
              "Median": (0.51, 0.4, 0.64), "PCA": (0.3, 0.67, 0.77)}


def figs2(pdf, vec, cv, groups, kinds, out_ours, out_overlay):
    src = pymupdf.open(pdf)[0]
    clip = clip_of(src)

    floors = [y_of(vec[p]["axes"][part], 0.4) for p in kinds for part in ("within", "cross")]

    def is_bar(d):
        r = d["rect"]
        return d["type"] == "f" and any(close(d["fill"], c) for c in S2_COLOURS.values()) and r.width < 20 \
            and r.height > 0.5 and any(abs(r.y1 - f) < 1.0 for f in floors)

    def is_err(d):
        return d["type"] == "s" and len(d["items"]) >= 16 and all(i[0] == "l" for i in d["items"]) and \
            close(d.get("color"), (0.01, 0.01, 0.01), 0.03)

    axes_x = [vec[p]["axes"][part]["x"] for p in kinds for part in ("within", "cross")]
    # -log(p) labels go; the axes' tick labels (right-aligned at the axis) stay
    doc, page = rebuild(src, lambda d: is_bar(d) or is_err(d),
                        lambda s: number_label(s) and not any(abs(s["bbox"][2] - x) < 4 for x in axes_x))
    over = pymupdf.open(pdf)
    opage = over[0]
    for panel, kind in kinds.items():
        for part, names in groups:
            a = vec[panel]["axes"][part]
            floor = y_of(a, 0.4)
            for key, label in names:
                g = vec[panel][part][label]
                sc = cv[part][key]["scores"]
                for m, (x0, x1) in g["xs"].items():
                    v, se = sc[f"{m}/{kind}"]["mean"], sc[f"{m}/{kind}"]["ste"]
                    top = y_of(a, v)
                    bar(page, x0, x1, top, floor, S2_COLOURS[m])
                    errbar(page, (x0 + x1) / 2, top, y_of(a, v + se))
                    tick(opage, x0, x1, top)
                lab = neglogp_text(cv[part][key]["tests"].get(kind))
                if lab:
                    x0, x1 = g["xs"]["PAC"]
                    yt = y_of(a, sc[f"PAC/{kind}"]["mean"] + sc[f"PAC/{kind}"]["ste"]) - 2.5
                    page.insert_text(((x0 + x1) / 2 - 5, yt), lab, fontsize=6.5, fontname="helv")
    rasterize(page, clip, out_ours)
    rasterize(opage, clip, out_overlay)


# ----------------------------------------------------------------------------- Fig. S3

S3_COLOURS = {"PAC_SEQ": (0.61, 0.73, 0.35), "PAC_FWD": (0.31, 0.51, 0.75),
              "Gene_SEQ": (0.51, 0.4, 0.64), "Gene_FWD": (0.76, 0.32, 0.31)}
S3_KEYS = {"PAC_SEQ": "PAC/lr", "PAC_FWD": "PAC/fwd", "Gene_SEQ": "Gene/lr", "Gene_FWD": "Gene/fwd"}


def figs3(pdf, axis, positions, cv, names, out_ours, out_overlay):
    src = pymupdf.open(pdf)[0]
    clip = clip_of(src)
    floor = y_of(axis, 0.4)

    def data(d):
        r = d["rect"]
        on_floor = abs(r.y1 - floor) < 1.5 and r.width < 20
        if on_floor and (d["type"] == "f" or (d["type"] == "s" and len(d["items"]) == 1)):
            return True  # a bar and its outline
        return d["type"] == "s" and len(d["items"]) >= 16 and all(i[0] == "l" for i in d["items"]) and r.width < 400

    doc, page = rebuild(src, data, lambda s: False)
    over = pymupdf.open(pdf)
    opage = over[0]
    for d_, label in names:
        for m, (x0, x1) in positions[label].items():
            s = cv[d_]["scores"][S3_KEYS[m]]
            top = y_of(axis, s["mean"])
            bar(page, x0, x1, top, floor, S3_COLOURS[m], outline=(0.25, 0.25, 0.26))
            errbar(page, (x0 + x1) / 2, top, y_of(axis, s["mean"] + s["ste"]), colour=(0.25, 0.25, 0.26))
            tick(opage, x0, x1, top)
    rasterize(page, clip, out_ours)
    rasterize(opage, clip, out_overlay)


# ----------------------------------------------------------------------------- Fig. S1

S1_SERIES = {"Pathways": ((0.16, 0.16, 0.45), "diamond"), "CORGs": ((0.73, 0.33, 0.62), "square"),
             "Genes": ((0.96, 0.92, 0.09), "triangle")}
GREY = (0.51, 0.5, 0.5)


def marker(page, x, y, kind, colour, r=2.3):
    sh = page.new_shape()
    if kind == "diamond":
        sh.draw_polyline([(x, y - r), (x + r, y), (x, y + r), (x - r, y), (x, y - r)])
    elif kind == "square":
        sh.draw_rect(pymupdf.Rect(x - r * 0.8, y - r * 0.8, x + r * 0.8, y + r * 0.8))
    else:
        sh.draw_polyline([(x, y - r), (x + r, y + r * 0.8), (x - r, y + r * 0.8), (x, y - r)])
    sh.finish(color=colour, fill=colour, width=0.3, closePath=True)
    sh.commit()


def figs1(pdf, vec, rob, legend_rect, out_ours, out_overlay):
    src = pymupdf.open(pdf)[0]
    clip = clip_of(src)

    def data(d):
        r = d["rect"]
        if legend_rect is not None and legend_rect.intersects(r):
            return False
        colour = d.get("fill") if d["type"] == "f" else d.get("color")
        if any(close(colour, c) for c, _ in S1_SERIES.values()):
            return True
        if close(colour, GREY):
            if d["type"] == "f":
                return r.width < 8 and r.height < 8  # shadow markers
            long_h = r.height < 0.5 and r.width > 100
            return not long_h and max(r.width, r.height) < 100  # shadow segments, not grid lines or frames
        return False

    doc, page = rebuild(src, data, lambda s: False)
    over = pymupdf.open(pdf)
    opage = over[0]
    for label, pub in vec.items():
        a = pub["_axis"]
        xs = pub["_x"]
        for s, (colour, kind) in S1_SERIES.items():
            pts = [(x, y_of(a, v)) for x, v in zip(xs, rob[label][s])]
            for P, Q in ((page, colour), (opage, (0, 0, 0))):
                sh = P.new_shape()
                sh.draw_polyline(pts)
                sh.finish(color=Q, width=1.4 if P is page else 0.8, closePath=False)
                sh.commit()
            for x, y in pts:
                marker(page, x, y, kind, colour)
                marker(opage, x, y, kind, (0, 0, 0), r=1.6)
    rasterize(page, clip, out_ours)
    rasterize(opage, clip, out_overlay)


# ----------------------------------------------------------------------------- Fig. S5

def figs5(pdf, vec, rob, names, out_ours, out_overlay, half=11.0):
    src = pymupdf.open(pdf)[0]
    clip = clip_of(src)
    a = vec["_axis"]

    def data(d):
        c = tuple(round(v, 2) for v in (d.get("color") or ()))
        r = d["rect"]
        if c in ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)):
            return True  # boxes, medians, outliers
        return c == (0.0, 0.0, 0.0) and len(d["items"]) == 2 and r.width < 15  # whiskers and caps

    doc, page = rebuild(src, data, lambda s: False)
    over = pymupdf.open(pdf)
    opage = over[0]
    for key, label in names:
        s = rob["figS5"][label]
        x = vec[label]["x"]
        for P, box_c, med_c, w in ((page, (0, 0, 1), (1, 0, 0), 0.5), (opage, (0, 0, 0), (0, 0, 0), 1.0)):
            sh = P.new_shape()
            sh.draw_rect(pymupdf.Rect(x - half, y_of(a, s["q3"]), x + half, y_of(a, s["q1"])))
            sh.finish(color=box_c, width=w)
            sh.draw_line((x - half, y_of(a, s["median"])), (x + half, y_of(a, s["median"])))
            sh.finish(color=med_c, width=w, closePath=False)
            sh.draw_line((x, y_of(a, s["q3"])), (x, y_of(a, s["whisker_high"])))
            sh.draw_line((x, y_of(a, s["q1"])), (x, y_of(a, s["whisker_low"])))
            sh.finish(color=(0, 0, 0), width=w, dashes="[3 2] 0", closePath=False)
            for v in (s["whisker_low"], s["whisker_high"]):
                sh.draw_line((x - half / 2, y_of(a, v)), (x + half / 2, y_of(a, v)))
            sh.finish(color=(0, 0, 0), width=w, closePath=False)
            for o in s["outliers"]:
                y = y_of(a, o)
                sh.draw_line((x - 2.5, y), (x + 2.5, y))
                sh.draw_line((x, y - 2.5), (x, y + 2.5))
            sh.finish(color=med_c, width=w, closePath=False)
            sh.commit()
    rasterize(page, clip, out_ours)
    rasterize(opage, clip, out_overlay)
