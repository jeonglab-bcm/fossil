"""Score our panels against the published ones and write the overlays.

Usage: compare.py OUTDIR

OUTDIR holds published/ (the panel crops) and figures/ (our renders and the controls). For each
panel the published and our ink pixels are compared both ways: the share of published ink within
``tolerance`` pixels of ours, and the share of ours within ``tolerance`` of the published. The
smaller of the two is the score. The same code scores each control. Writes figures/fig*_ours.png,
figures/fig*_overlay.png, figures/fig*_diff.png and comparison.json.

Our renders are drawn at the published panel's pixel size, so no alignment search is needed; the
skill's compare_figure.py looks for a grey panel fill (ggplot style) that these white matplotlib
panels do not have, and is not used here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

INK = 170  # grey level below which a pixel counts as ink
TOLERANCE_PX = 2
DPI = 399

#: Rectangles (left, top, right, bottom) left out of the score: legends, insets and the printed
#: numbers, which hold no data of ours. Coordinates are inside the published panel crop.
MASKS = {
    "fig2a": [(10, 10, 660, 190)],                      # legend box
    "fig2b": [(10, 10, 880, 130)],                      # legend box with the fit parameters
    "fig3": [(430, 60, 1000, 330)],                     # printed mean, median and standard deviation
    "fig4": [(325, 253, 1080, 815), (470, 10, 1140, 170)],  # inset histograms, legend box
}
PANELS = ("fig2a", "fig2b", "fig3", "fig4")


def ink(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("L"), dtype=float) < INK


def masked(a: np.ndarray, name: str) -> np.ndarray:
    out = a.copy()
    for left, top, right, bottom in MASKS.get(name, []):
        out[top:bottom, left:right] = False
    return out


def two_way(pub: np.ndarray, ours: np.ndarray, tol: int = TOLERANCE_PX):
    """Share of published ink within ``tol`` of ours, and of ours within ``tol`` of the published."""
    dist_to_ours = ndimage.distance_transform_edt(~ours)
    dist_to_pub = ndimage.distance_transform_edt(~pub)
    a = float(np.mean(dist_to_ours[pub] <= tol)) if pub.any() else float("nan")
    b = float(np.mean(dist_to_pub[ours] <= tol)) if ours.any() else float("nan")
    return a, b


def fit_to(a: np.ndarray, shape) -> np.ndarray:
    """Crop or pad a boolean image to ``shape`` (panels differ by at most a pixel)."""
    out = np.zeros(shape, bool)
    h, w = min(a.shape[0], shape[0]), min(a.shape[1], shape[1])
    out[:h, :w] = a[:h, :w]
    return out


def overlay(pub: np.ndarray, ours: np.ndarray) -> Image.Image:
    """Red = ours only, cyan = published only, black = both."""
    h, w = pub.shape
    rgb = np.full((h, w, 3), 255, np.uint8)
    rgb[pub] = (0, 190, 190)
    rgb[ours] = (230, 0, 0)
    rgb[pub & ours] = (0, 0, 0)
    return Image.fromarray(rgb)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    a = ap.parse_args(argv)
    out = Path(a.outdir)
    figs = out / "figures"
    report = {"tolerance_px": TOLERANCE_PX, "dpi": DPI, "ink_threshold": INK, "panels": {}}

    for name in PANELS:
        pub_img = out / "published" / f"{name}.png"
        pub = masked(ink(pub_img), name)
        shape = pub.shape
        entry = {"published": f"published/{name}.png", "controls": {}}
        for path in sorted(figs.glob(f"{name}*.png")):
            if path.stem.endswith(("_ours", "_overlay", "_diff")):
                continue
            ours = masked(fit_to(ink(path), shape), name)
            p_near_o, o_near_p = two_way(pub, ours)
            scores = {"published_near_ours": p_near_o, "ours_near_published": o_near_p,
                      "score": min(p_near_o, o_near_p)}
            if path.stem == name:
                entry.update(scores)
                Image.fromarray(np.where(ours, 0, 255).astype(np.uint8)).save(figs / f"{name}_ours.png")
                overlay(pub, ours).save(figs / f"{name}_overlay.png")
                Image.fromarray(np.where(pub ^ ours, 0, 255).astype(np.uint8)).save(figs / f"{name}_diff.png")
            else:
                kind = "near_miss" if "_near_" in path.stem else "wrong_input"
                entry["controls"][path.stem] = dict(scores, kind=kind)
        report["panels"][name] = entry

    with open(out / "comparison.json", "w") as f:
        json.dump(report, f, indent=1, sort_keys=True)
    for name, e in report["panels"].items():
        best = max((c["score"] for c in e["controls"].values()), default=float("nan"))
        print(f"{name}: ours {e['score']:.4f}  best control {best:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
