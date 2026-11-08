"""Figure 2: our ROC curves drawn on the published pixel grid, scored both ways, with controls.

Usage: compare_fig2.py PUBLISHED.jpg ROC_REP0.csv OUTDIR [--controls CONTROLS.csv]

The published figure (473 x 841 px, two panels) is mapped to data from its tick marks alone
(least squares over the 11 ticks of each axis; residuals recorded). Published traces are split
by grey level: the SVM curve is black (< 100), the logistic regression curve light grey
(150 to 235). The diagonal reference line, the axes and the legend are masked.

Scores, with tolerance 2 px:
  published_near_ours  share of published trace pixels within 2 px of our curve
  ours_near_published  share of our curve pixels within 2 px of the published trace
For the logistic curve, our pixels that fall under the published black SVM curve (where the grey
curve is hidden) are left out of ours_near_published.

Controls (same code, same panel):
  wrong_input  the other scheme's curve; a one-variable score (age alone) on the same test set
  near_miss    our curve with sensitivity moved by -0.03 and +0.03 (about 12 px)
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from scipy import ndimage

TOL = 2.0
# Tick pixel positions read from the published file (x ticks 0, 0.1, ..., 1 below the axis;
# y ticks 0, 0.1, ..., 1 left of the axis), and the boxes masked in each panel.
PANELS = {
    "I": {"xt": [55, 96, 137, 178, 219, 261, 302, 343, 384, 425, 466],
          "yt": [304, 275, 245, 216, 187, 158, 128, 99, 70, 40, 11],
          "legend": (232, 229, 460, 296), "box": (57, 8, 470, 302)},
    "II": {"xt": [54, 95, 137, 178, 220, 261, 302, 344, 385, 427, 468],
           "yt": [732, 702, 673, 643, 614, 584, 554, 525, 495, 466, 436],
           "legend": (232, 667, 460, 728), "box": (56, 433, 472, 730)},
}


def calib(p):
    v = np.linspace(0, 1, 11)
    ax, bx = np.polyfit(v, p["xt"], 1)
    ay, by = np.polyfit(v, p["yt"], 1)
    res = max(np.abs(np.polyval([ax, bx], v) - p["xt"]).max(),
              np.abs(np.polyval([ay, by], v) - p["yt"]).max())
    return (ax, bx, ay, by), float(res)


def to_px(c, fpr, tpr):
    ax, bx, ay, by = c
    return ax * np.asarray(fpr) + bx, ay * np.asarray(tpr) + by


def draw_curve(shape, c, fpr, tpr, width=1):
    img = Image.new("L", (shape[1], shape[0]), 0)
    x, y = to_px(c, fpr, tpr)
    ImageDraw.Draw(img).line(list(zip(x.tolist(), y.tolist())), fill=255, width=width)
    return np.asarray(img) > 0


def masks(gray, p, c):
    H, W = gray.shape
    x0, y0, x1, y1 = p["box"]
    inside = np.zeros_like(gray, dtype=bool)
    inside[y0:y1, x0:x1] = True
    lx0, ly0, lx1, ly1 = p["legend"]
    inside[ly0:ly1, lx0:lx1] = False
    diag = ndimage.binary_dilation(draw_curve(gray.shape, c, [0, 1], [0, 1]), iterations=2)
    black = inside & (gray < 100)
    grey = inside & (gray >= 150) & (gray <= 235) & ~diag
    return inside, black, grey


def score(pub, ours, inside, exclude=None):
    ours = ours & inside
    d_ours = ndimage.distance_transform_edt(~ours)
    d_pub = ndimage.distance_transform_edt(~pub)
    pn = float((d_ours[pub] <= TOL).mean()) if pub.any() else float("nan")
    keep = ours if exclude is None else ours & ~exclude
    on = float((d_pub[keep] <= TOL).mean()) if keep.any() else float("nan")
    return pn, on


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("published")
    ap.add_argument("roc")
    ap.add_argument("outdir")
    ap.add_argument("--controls", help="CSV with scheme, model, fpr, tpr of the one-variable controls")
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    rgb = np.asarray(Image.open(a.published).convert("RGB"))
    gray = np.asarray(Image.open(a.published).convert("L")).astype(int)
    roc = pd.read_csv(a.roc)
    ctrl = pd.read_csv(a.controls) if a.controls else None

    report = {"tolerance_px": TOL, "image_px": [gray.shape[1], gray.shape[0]], "panels": {}}
    ours_img = rgb.copy()
    overlay = (255 - (255 - rgb) * 0.45).astype(np.uint8)  # published, lightened
    for scheme, p in PANELS.items():
        c, resid = calib(p)
        inside, black, grey = masks(gray, p, c)
        ours_img[black | grey] = 255
        other = "II" if scheme == "I" else "I"
        panel = {"tick_fit_max_residual_px": resid, "models": {}}
        for model, pub, colour, ocol in [("svm", black, (0, 0, 0), (215, 25, 28)),
                                         ("mlr", grey, (190, 190, 190), (44, 123, 182))]:
            r = roc[(roc.scheme == scheme) & (roc.model == model)]
            ours = draw_curve(gray.shape, c, r.fpr, r.tpr)
            excl = black if model == "mlr" else None
            pn, on = score(pub, ours, inside, excl)
            ours_img[ours & inside] = colour
            overlay[ours & inside] = ocol
            controls = []
            ro = roc[(roc.scheme == other) & (roc.model == model)]
            controls.append({"name": f"scheme {other} curve", "kind": "wrong_input",
                             "score": min(score(pub, draw_curve(gray.shape, c, ro.fpr, ro.tpr), inside, excl))})
            if ctrl is not None:
                rc = ctrl[(ctrl.scheme == scheme)]
                controls.append({"name": "age alone", "kind": "wrong_input",
                                 "score": min(score(pub, draw_curve(gray.shape, c, rc.fpr, rc.tpr), inside, excl))})
            for dt in (-0.03, 0.03):
                t2 = np.clip(r.tpr + dt, 0, 1)
                t2.iloc[0] = 0.0
                controls.append({"name": f"sensitivity {dt:+.2f}", "kind": "near_miss",
                                 "score": min(score(pub, draw_curve(gray.shape, c, r.fpr, t2), inside, excl))})
            panel["models"][model] = {"published_near_ours": pn, "ours_near_published": on,
                                      "published_px": int(pub.sum()), "ours_px": int((ours & inside).sum()),
                                      "controls": controls}
        report["panels"][scheme] = panel
    Image.fromarray(ours_img).save(out / "fig2_ours.png")
    Image.fromarray(overlay).save(out / "fig2_overlay.png")
    (out / "fig2_comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
