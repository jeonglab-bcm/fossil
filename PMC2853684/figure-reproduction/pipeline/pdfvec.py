"""Minimal reader of vector paths in a PDF content stream.

The paper's Figures 2 and 4 and the supplement's Figures S1 and S2 are vector drawings in the
PDFs. Reading their paths gives the plotted values to the precision of the PDF coordinates
(0.001 pt), so the figures can be compared as numbers as well as pixels.
"""

from __future__ import annotations

import re

TOKEN = re.compile(rb"\[[^\]]*\]|\((?:\\.|[^\\)])*\)|/[^\s/\[\]()<>]+|[-+]?\d*\.?\d+|[A-Za-z'\"*]+")
PAINT = {b"S", b"s", b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*"}


def stream_of(pdf_path: str, page: int, xobject: str | None = None) -> bytes:
    """Content of a page, or of one of its form XObjects (name without the slash)."""
    import pypdf

    reader = pypdf.PdfReader(pdf_path)
    p = reader.pages[page]
    if xobject is None:
        return p.get_contents().get_data()
    return p["/Resources"]["/XObject"]["/" + xobject].get_object().get_data()


def paths(stream: bytes) -> list[dict]:
    """Painted paths in drawing order.

    Each path: {'op', 'stroke' (colour tuple), 'fill', 'w' (line width), 'subs' [{'v': [(x, y)],
    'closed', 'rect' (x, y, w, h) or None, 'curve'}], 'index'}. Text objects are skipped, but
    each text string is recorded as {'text', 'tm'} in drawing order, so labels can be matched to
    the series drawn before them.
    """
    stack: list[float] = []
    stroke = fill = None
    width = 1.0
    cur: list[dict] = []
    sub = None
    out: list[dict] = []
    in_text = False
    tm = None
    for t in TOKEN.findall(stream):
        if t == b"BT":
            in_text, stack = True, []
            continue
        if t == b"ET":
            in_text, stack = False, []
            continue
        if in_text:
            if t == b"Tm":
                tm = tuple(stack[-6:])
                stack = []
            elif t.startswith(b"("):
                out.append({"text": t[1:-1].decode("latin1"), "tm": tm, "index": len(out)})
            elif t.startswith(b"["):
                txt = "".join(re.findall(r"\(((?:\\.|[^\\)])*)\)", t.decode("latin1")))
                out.append({"text": txt, "tm": tm, "index": len(out)})
            else:
                try:
                    stack.append(float(t))
                except ValueError:
                    if t not in (b"Tf", b"Td", b"TD", b"Tc", b"Tw", b"TJ", b"Tj", b"Tr", b"rg", b"g", b"k", b"scn", b"cs"):
                        pass
                    stack = [] if t not in (b"Tf",) else stack
            continue
        try:
            stack.append(float(t))
            continue
        except ValueError:
            pass
        if t == b"K":
            stroke = tuple(stack[-4:])
        elif t == b"RG":
            stroke = tuple(stack[-3:])
        elif t == b"G":
            stroke = (stack[-1],)
        elif t == b"k":
            fill = tuple(stack[-4:])
        elif t == b"rg":
            fill = tuple(stack[-3:])
        elif t == b"sc":
            fill = tuple(stack)
        elif t == b"SC":
            stroke = tuple(stack)
        elif t == b"g":
            fill = (stack[-1],)
        elif t == b"w":
            width = stack[-1]
        elif t == b"m":
            sub = {"v": [(stack[-2], stack[-1])], "closed": False, "rect": None, "curve": False}
            cur.append(sub)
        elif t == b"l" and sub is not None:
            sub["v"].append((stack[-2], stack[-1]))
        elif t == b"c" and sub is not None:
            sub["v"].append((stack[-2], stack[-1]))
            sub["curve"] = True
        elif t == b"re":
            x, y, w, h = stack[-4:]
            sub = {"v": [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], "closed": True, "rect": (x, y, w, h), "curve": False}
            cur.append(sub)
        elif t == b"h":
            if sub is not None:
                sub["closed"] = True
        elif t in PAINT:
            out.append({"op": t.decode(), "stroke": stroke, "fill": fill, "w": width, "subs": cur, "index": len(out)})
            cur, sub = [], None
        elif t == b"n":
            cur, sub = [], None
        stack = []
    return out


def extent(vs) -> float:
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]
    return max(max(xs) - min(xs), max(ys) - min(ys))


def close(a, b, tol=1e-3) -> bool:
    return len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


def linear_map(p0: float, v0: float, p1: float, v1: float):
    """Map from PDF coordinate to data value through two calibration points."""
    k = (v1 - v0) / (p1 - p0)
    return lambda p: v0 + (p - p0) * k
