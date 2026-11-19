"""Read plotted points out of the vector figures of PMC3098087 (R base graphics in PDF).

Each panel is a black stroked rectangle. Its tick marks are short black lines outside the box;
the tick labels are the words next to them. The figure text is outlined (glyphs drawn as
paths), so the tick values are given per figure, read from the printed tick labels; the
pixel-to-data map of each axis is a straight line fitted to the ticks and those values (the
residual is reported). Every circle marker inside a box
is a point; legend markers (a word right next to them) are left out.
"""

import math
import re

import pymupdf

NUM = re.compile(r"^-?\d+(\.\d+)?$")


def _rgb(c):
    return tuple(round(v, 3) for v in c) if c else None


def _is_circle(d):
    """A marker: a small square-bounded path of 4 Bezier arcs (a disc) or 8 arcs and joining
    lines (a ring, an open circle)."""
    its = d["items"]
    r = d["rect"]
    if not its or not (1.0 < r.width < 6 and abs(r.width - r.height) < 0.6):
        return False
    kinds = [i[0] for i in its]
    if not all(k in "cl" for k in kinds):
        return False
    return kinds.count("c") in (4, 8)


def _ring(d):
    """Open circles are drawn as a filled ring (an outer and an inner circle)."""
    return d["type"] == "f" and len(d["items"]) > 6


def panels(page, min_size=40):
    """Black stroked rectangles larger than min_size points."""
    out = []
    for d in page.get_drawings():
        if d["type"] not in ("s", "fs") or _rgb(d.get("color")) != (0.0, 0.0, 0.0):
            continue
        for it in d["items"]:
            if it[0] == "re" and it[1].width > min_size and it[1].height > min_size:
                out.append(pymupdf.Rect(it[1]))
            if it[0] == "qu":
                r = it[1].rect
                if r.width > min_size and r.height > min_size:
                    out.append(pymupdf.Rect(r))
    uniq = []
    for r in out:
        if not any(abs(r.x0 - u.x0) < 0.5 and abs(r.y0 - u.y0) < 0.5 and abs(r.x1 - u.x1) < 0.5 for u in uniq):
            uniq.append(r)
    return sorted(uniq, key=lambda r: (round(r.y0 / 20), r.x0))


def _black_lines(page):
    lines = []
    for d in page.get_drawings():
        if d["type"] != "s" or _rgb(d.get("color")) != (0.0, 0.0, 0.0) or d.get("dashes") not in (None, "[] 0"):
            continue
        for it in d["items"]:
            if it[0] == "l":
                lines.append((it[1].x, it[1].y, it[2].x, it[2].y))
    return lines


def _fit(pairs):
    """Least-squares line value = a + b * position; returns a, b and the largest residual."""
    n = len(pairs)
    if n < 2:
        raise ValueError("fewer than two labelled ticks")
    mx = sum(p for p, _ in pairs) / n
    mv = sum(v for _, v in pairs) / n
    sxx = sum((p - mx) ** 2 for p, _ in pairs)
    b = sum((p - mx) * (v - mv) for p, v in pairs) / sxx
    a = mv - b * mx
    res = max(abs(a + b * p - v) for p, v in pairs)
    return a, b, res


def ticks(box, lines, tick_len=(1.0, 8.0)):
    """Positions of the y ticks (left of the box) and x ticks (below the box)."""
    yt, xt = [], []
    for x0, y0, x1, y1 in lines:
        if abs(y0 - y1) < 0.05 and tick_len[0] <= abs(x1 - x0) <= tick_len[1]:
            if max(x0, x1) <= box.x0 + 0.6 and min(x0, x1) >= box.x0 - 12 and box.y0 - 1 <= y0 <= box.y1 + 1:
                yt.append(y0)
        if abs(x0 - x1) < 0.05 and tick_len[0] <= abs(y1 - y0) <= tick_len[1]:
            if min(y0, y1) >= box.y1 - 0.6 and max(y0, y1) <= box.y1 + 12 and box.x0 - 1 <= x0 <= box.x1 + 1:
                xt.append(x0)
    yt = sorted(set(round(v, 3) for v in yt), reverse=True)  # bottom (smallest value) first
    xt = sorted(set(round(v, 3) for v in xt))
    return xt, yt


def axis_maps(box, lines, xvalues, yvalues):
    xt, yt = ticks(box, lines)
    if len(xt) != len(xvalues) or len(yt) != len(yvalues):
        raise ValueError(f"tick count {len(xt)}x{len(yt)} does not match {len(xvalues)}x{len(yvalues)}")
    return {"x": _fit(list(zip(xt, xvalues))), "y": _fit(list(zip(yt, yvalues))), "xticks": xt, "yticks": yt}


def glyphs(page):
    """Rectangles of the outlined text: small black filled paths that are not circles."""
    out = []
    for d in page.get_drawings():
        if d["type"] == "f" and _rgb(d.get("fill")) == (0.0, 0.0, 0.0) and not _is_circle(d):
            r = d["rect"]
            if r.width < 80 and r.height < 12:
                out.append(r)
    return out


def markers(page, box, words):
    """Circle markers inside a box: centre, colour, filled or open; legend markers dropped."""
    out = []
    for d in page.get_drawings():
        if not _is_circle(d):
            continue
        r = d["rect"]
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        if not (box.x0 - 1 <= cx <= box.x1 + 1 and box.y0 - 1 <= cy <= box.y1 + 1):
            continue
        filled = d["type"] in ("f", "fs") and not _ring(d)
        if _rgb(d.get("fill") if d["type"] != "s" else d.get("color")) == (1.0, 1.0, 1.0):
            continue  # white discs mask the axis breaks
        colour = _rgb(d.get("fill") if d["type"] in ("f", "fs") else d.get("color"))
        out.append({"cx": cx, "cy": cy, "colour": colour, "filled": filled, "w": round(r.width, 1)})
    # Legend markers are drawn smaller than the plotted ones: keep, within each colour and fill,
    # the markers of the most common size.
    keep = []
    groups = {}
    for m in out:
        groups.setdefault((m["colour"], m["filled"]), []).append(m)
    for ms in groups.values():
        sizes = [m["w"] for m in ms]
        mode = max(set(sizes), key=lambda w: (sizes.count(w), w))
        keep += [m for m in ms if abs(m["w"] - mode) <= 0.2]
    return keep


def read_page(page, xvalues, yvalues, min_size=40, boxes=None):
    """Points of every panel on a page. xvalues and yvalues are the tick values, smallest first,
    either one list for all panels or a function of the panel index."""
    gl = glyphs(page)
    lines = _black_lines(page)
    res = []
    for k, box in enumerate(boxes or panels(page, min_size)):
        xv = xvalues(k) if callable(xvalues) else xvalues
        yv = yvalues(k) if callable(yvalues) else yvalues
        maps = axis_maps(box, lines, xv, yv)
        ax, bx, rx = maps["x"]
        ay, by, ry = maps["y"]
        pts = []
        for m in markers(page, box, gl):
            pts.append({"x": ax + bx * m["cx"], "y": ay + by * m["cy"], "colour": m["colour"],
                        "filled": m["filled"], "px": [round(m["cx"], 3), round(m["cy"], 3)]})
        res.append({"box": [round(v, 3) for v in box], "x_residual": rx, "y_residual": ry,
                    "map": [ax, bx, ay, by], "points": pts})
    return res


def titles(page, box, gap=30):
    """Words above a box, nearest line last (panel titles), for PDFs whose text is real text."""
    ws = [w for w in page.get_text("words") if w[3] <= box.y0 + 1 and box.y0 - w[3] < gap
          and box.x0 - 5 <= (w[0] + w[2]) / 2 <= box.x1 + 5]
    return " ".join(w[4] for w in sorted(ws, key=lambda w: (round(w[1]), w[0])))
