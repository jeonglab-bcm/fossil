#!/usr/bin/env python3
"""Read the published Figure 1 out of the article PDF, as curves and as a 600 dpi image.

Figure 1 is vector art in the PDF, so its four precision-recall panels can be read as numbers and
compared with ours value by value, not only pixel by pixel. Each panel holds exactly three curve
paths, told apart by their dash pattern:

| Dash pattern in the PDF | Caption | Our name |
| --- | --- | --- |
| solid | leave-one-out on potential drugs (row 2 of Tables 1-4) | BLMd |
| `[3.3149 3.3149]` dashed | leave-one-out on potential targets (row 5) | BLMt |
| `[.27624 2.2099]` dotted | the two scores aggregated (row 8) | m(BLMd,BLMt) |

The axes are read from the tick marks alone: six x ticks at recall 0, 0.2, ..., 1 and six y ticks
at precision 0, 0.2, ..., 1, as the printed labels say. Nothing inside the axes box is fitted.

    published.py --pdf PMC2735674.1.pdf --out-image published/figure-1.png --out-json figure1_published.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

#: Figure 1 sits on page 5 (index 4) of the article.
PAGE = 4
#: The four panels, in the caption's order, as (label, dataset, axes box in PDF points).
PANELS = [
    ("a", "e", (172.0, 399.0, 303.0, 498.0)),
    ("b", "ic", (344.0, 399.0, 475.0, 498.0)),
    ("c", "gpcr", (172.0, 532.0, 303.0, 632.0)),
    ("d", "nr", (344.0, 532.0, 475.0, 632.0)),
]
CURVES = {"solid": "blmd", "dashed": "blmt", "dotted": "aggregate"}
#: The figure's bounding box on the page, with room for the axis labels, in PDF points.
FIGURE_BOX = (150.0, 388.0, 490.0, 650.0)
DPI = 600


def classify(dashes: str | None) -> str | None:
    if dashes is None:
        return None
    if dashes.strip() in ("[] 0", "[]"):
        return "solid"
    if dashes.startswith("[ 3.3"):
        return "dashed"
    if dashes.startswith("[ .27"):
        return "dotted"
    return None


def panel_curves(page: pymupdf.Page) -> dict:
    """Curve points of each panel, in data coordinates (recall, precision)."""
    out = {}
    for label, dataset, (x0, y0, x1, y1) in PANELS:
        found = {}
        for drawing in page.get_drawings():
            rect = drawing["rect"]
            inside = x0 - 2 <= rect.x0 and rect.x1 <= x1 + 2 and y0 - 2 <= rect.y0 and rect.y1 <= y1 + 2
            kind = classify(drawing.get("dashes"))
            if not inside or kind not in CURVES or len(drawing["items"]) < 20:
                continue
            points = []
            for item in drawing["items"]:
                if item[0] != "l":
                    continue
                for point in item[1:3]:
                    recall = (point.x - x0) / (x1 - x0)
                    precision = (y1 - point.y) / (y1 - y0)
                    if not points or (recall, precision) != points[-1]:
                        points.append((round(recall, 6), round(precision, 6)))
            name = CURVES[kind]
            if name in found:
                raise SystemExit(f"panel {label}: two {kind} paths")
            found[name] = points
        missing = set(CURVES.values()) - set(found)
        if missing:
            raise SystemExit(f"panel {label}: no {sorted(missing)} curve found")
        out[label] = {"dataset": dataset, "curves": found}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--out-image", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    args = ap.parse_args()

    document = pymupdf.open(args.pdf)
    page = document[PAGE]
    curves = panel_curves(page)
    args.out_image.parent.mkdir(parents=True, exist_ok=True)
    page.get_pixmap(dpi=DPI, clip=pymupdf.Rect(*FIGURE_BOX)).save(args.out_image)
    payload = {
        "source": "Figure 1 of the article PDF (vector art), page %d" % (PAGE + 1),
        "dpi": DPI,
        "figure_box_pdf_points": FIGURE_BOX,
        "panels": curves,
        "panel_boxes_pdf_points": {label: box for label, _, box in PANELS},
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    for label, panel in curves.items():
        counts = {name: len(points) for name, points in panel["curves"].items()}
        print(f"panel {label} ({panel['dataset']}): {counts}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
