#!/usr/bin/env python3
"""Figure 1: our precision-recall curves against the published ones.

Figure 1 is vector art in the article PDF, so published.py reads its four panels as numbers and
each panel is compared two ways:

- as values: the published precision at a grid of recall points against ours. This is the only
  route to an exact figure.
- as pixels: our three curves drawn on the published panel's own pixel grid at 600 dpi, with the
  overlay and the difference image, scored both ways against the published ink.

Negative controls per panel, scored with the same code: `wrong_dataset` draws the curves of
another benchmark dataset on this panel, and the near misses shift our curves along recall by one
grid step (0.05) and scale precision by 1.05.

    figure1.py --scores scores --published figure1_published.json --page-image page.png --out-dir out
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from scipy.ndimage import distance_transform_edt  # noqa: E402

import blmdti as B  # noqa: E402

PANELS = [
    ("a", "e", "enzyme"),
    ("b", "ic", "ion channel"),
    ("c", "gpcr", "GPCR"),
    ("d", "nr", "nuclear receptor"),
]
#: The three curves of a panel, with the dash pattern the PDF draws them with, in points.
CURVES = [
    ("blmd", "BLMd", (0, ())),
    ("blmt", "BLMt", (0, (3.3149, 3.3149))),
    ("aggregate", "m(BLMd,BLMt)", (0, (0.27624, 2.2099))),
]
LEGEND_STYLES = {"blmd": "-", "blmt": "--", "aggregate": ":"}
#: Recall grid of the value comparison; the printed axis runs 0 to 1.
GRID = np.round(np.arange(0.05, 1.0001, 0.05), 2)
#: Tolerance of the value comparison, in precision units. The published curves are read from
#: vector segments about 0.005 of the axis wide, which is the reading error.
VALUE_TOLERANCE = 0.01
#: Pixel tolerance at 600 dpi, as everywhere in this repository.
TOLERANCE_PX = 2
DPI = 600
LINE_WIDTH_PT = 0.46  # the published curves' line width, from the PDF
#: Pixels within this distance of the axes box are left out of the pixel score: the frame and the
#: tick marks are drawn there in the published panel and are not part of our curves.
BORDER_BAND_PX = 25


def published_profile(points: list[list[float]]) -> tuple[np.ndarray, np.ndarray]:
    """The published path's segment endpoints, ordered by recall."""
    array = np.asarray(points, dtype=float)
    order = np.argsort(array[:, 0], kind="stable")
    return array[order, 0], array[order, 1]


def at_grid(recall: np.ndarray, precision: np.ndarray, grid: np.ndarray) -> np.ndarray:
    """Precision at each grid recall: the mean of the points within half a grid step.

    A precision-recall curve can hold several precisions at one recall (a block of tied scores),
    so a grid value is the average of the points near it; where there are none, it interpolates.
    """
    half = (grid[1] - grid[0]) / 2.0 if grid.size > 1 else 0.025
    out = np.empty(grid.shape)
    for i, r in enumerate(grid):
        near = np.abs(recall - r) <= half
        out[i] = precision[near].mean() if near.any() else np.interp(r, recall, precision)
    return out


def our_curves(scores_dir: Path, dataset: str) -> dict:
    """Our three precision-recall curves for one dataset, from the committed score matrices."""
    with np.load(scores_dir / f"{dataset}_blmd.npz", allow_pickle=False) as f:
        adjacency, blmd = f["adjacency"], f["scores"]
    with np.load(scores_dir / f"{dataset}_blmt.npz", allow_pickle=False) as f:
        blmt = f["scores"]
    labels = B.interactions(adjacency)
    curves = {}
    for name, matrix in (("blmd", blmd), ("blmt", blmt), ("aggregate", B.aggregate(blmd, blmt))):
        precision, recall = B.precision_recall(labels, matrix)
        curves[name] = (recall, precision)
    return curves


def shift_recall(curve: tuple[np.ndarray, np.ndarray], by: float) -> tuple[np.ndarray, np.ndarray]:
    recall, precision = curve
    return np.clip(recall + by, 0, 1), precision


def scale_precision(curve: tuple[np.ndarray, np.ndarray], by: float) -> tuple[np.ndarray, np.ndarray]:
    recall, precision = curve
    return recall, np.clip(precision * by, 0, 1)


def figure_render(ours: dict, path: Path) -> None:
    """Our four panels in the published layout, for the results page."""
    fig, axes = plt.subplots(2, 2, figsize=(6.6, 5.2))
    for (label, dataset, _), ax in zip(PANELS, axes.ravel()):
        for name, legend, _ in CURVES:
            recall, precision = ours[dataset][name]
            ax.plot(recall, precision, LEGEND_STYLES[name], color="black", linewidth=0.8, label=legend)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks(np.arange(0, 1.01, 0.2))
        ax.set_yticks(np.arange(0, 1.01, 0.2))
        ax.set_xlabel("Recall")
        ax.set_ylabel("Precision")
        ax.set_title(f"({label})", loc="left", fontsize=9)
        ax.tick_params(labelsize=7)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
    axes[0][0].legend(fontsize=6, frameon=False, loc="lower left")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def panel_ink(curves: dict, names: dict, width: int, height: int) -> np.ndarray:
    """Draw the given curves alone, filling a width x height pixel panel, and return the ink mask."""
    fig = plt.figure(figsize=(width / DPI, height / DPI), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    for name, _, dashes in CURVES:
        recall, precision = names[name]
        ax.plot(
            recall, precision, linestyle=dashes, color="black", linewidth=LINE_WIDTH_PT,
            solid_capstyle="butt", dash_capstyle="butt",
        )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    canvas = fig.canvas
    canvas.draw()
    image = np.asarray(canvas.buffer_rgba())[:, :, :3].mean(axis=2)
    plt.close(fig)
    return image < 128


def published_panel_ink(page: Image.Image, box_points: tuple, page_box: tuple) -> np.ndarray:
    """Crop one panel's axes box out of the 600 dpi page render and return its ink mask."""
    scale = DPI / 72.0
    x0, y0, x1, y1 = box_points
    px0 = int(round((x0 - page_box[0]) * scale))
    py0 = int(round((y0 - page_box[1]) * scale))
    px1 = int(round((x1 - page_box[0]) * scale))
    py1 = int(round((y1 - page_box[1]) * scale))
    crop = page.convert("L").crop((px0, py0, px1, py1))
    return np.asarray(crop) < 128


def without_border(mask: np.ndarray, band: int = BORDER_BAND_PX) -> np.ndarray:
    """Drop the band along the axes box, where the published panel draws its frame and ticks."""
    out = mask.copy()
    out[:band, :] = False
    out[-band:, :] = False
    out[:, :band] = False
    out[:, -band:] = False
    return out


def two_way(ours: np.ndarray, theirs: np.ndarray, tolerance: int) -> dict:
    """Share of published ink near ours and of ours near the published, and the smaller of the two."""
    if not ours.any() or not theirs.any():
        return {"published_near_ours": 0.0, "ours_near_published": 0.0, "score": 0.0}
    to_ours = distance_transform_edt(~ours)
    to_theirs = distance_transform_edt(~theirs)
    published_near_ours = float((to_ours[theirs] <= tolerance).mean())
    ours_near_published = float((to_theirs[ours] <= tolerance).mean())
    return {
        "published_near_ours": round(published_near_ours, 4),
        "ours_near_published": round(ours_near_published, 4),
        "score": round(min(published_near_ours, ours_near_published), 4),
    }


def save_overlay(ours: np.ndarray, theirs: np.ndarray, path: Path) -> None:
    """Published ink in dark grey, ours in green, agreement in light grey."""
    height, width = theirs.shape
    image = np.full((height, width, 3), 255, dtype=np.uint8)
    both = ours & theirs
    image[theirs & ~ours] = (40, 40, 45)
    image[ours & ~theirs] = (20, 150, 90)
    image[both] = (190, 190, 190)
    Image.fromarray(image).save(path)


def save_render(ink: np.ndarray, path: Path) -> None:
    Image.fromarray(np.where(ink, 0, 255).astype(np.uint8)).save(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scores", type=Path, required=True)
    ap.add_argument("--published", type=Path, required=True)
    ap.add_argument("--page-image", type=Path, required=True, help="600 dpi render of the figure")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    published = json.loads(args.published.read_text())
    page_box = tuple(published["figure_box_pdf_points"])
    page = Image.open(args.page_image)
    ours = {dataset: our_curves(args.scores, dataset) for _, dataset, _ in PANELS}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    figure_render(ours, args.out_dir / "fig1_ours.png")

    datasets = [dataset for _, dataset, _ in PANELS]
    report = {
        "value_tolerance": VALUE_TOLERANCE,
        "tolerance_px": TOLERANCE_PX,
        "dpi": DPI,
        "recall_grid": GRID.tolist(),
        "panels": {},
    }
    for index, (label, dataset, name) in enumerate(PANELS):
        panel = published["panels"][label]
        box = published["panel_boxes_pdf_points"][label]
        theirs_ink = published_panel_ink(page, box, page_box)
        height, width = theirs_ink.shape
        wrong = datasets[(index + 1) % len(datasets)]

        values = {}
        for curve, legend, _ in CURVES:
            recall, precision = published_profile(panel["curves"][curve])
            theirs = at_grid(recall, precision, GRID)
            mine = at_grid(*ours[dataset][curve], GRID)
            control = at_grid(*ours[wrong][curve], GRID)
            difference = np.abs(mine - theirs)
            values[curve] = {
                "legend": legend,
                "published": [round(float(x), 4) for x in theirs],
                "ours": [round(float(x), 4) for x in mine],
                "max_difference": round(float(difference.max()), 4),
                "median_difference": round(float(np.median(difference)), 4),
                "points_within_tolerance": int((difference <= VALUE_TOLERANCE).sum()),
                "points": int(difference.size),
                "wrong_dataset_control": {
                    "dataset": wrong,
                    "points_within_tolerance": int(
                        (np.abs(control - theirs) <= VALUE_TOLERANCE).sum()
                    ),
                },
            }

        ours_ink = panel_ink(CURVES, ours[dataset], width, height)
        save_render(ours_ink, args.out_dir / f"fig1{label}_ours.png")
        save_render(theirs_ink, args.out_dir / f"fig1{label}_published.png")
        save_overlay(ours_ink, theirs_ink, args.out_dir / f"fig1{label}_overlay.png")
        save_render(ours_ink ^ theirs_ink, args.out_dir / f"fig1{label}_diff.png")
        scored_ours, scored_theirs = without_border(ours_ink), without_border(theirs_ink)
        pixels = two_way(scored_ours, scored_theirs, TOLERANCE_PX)
        controls = []
        for control_name, kind, curves in (
            (f"wrong dataset ({wrong})", "wrong_input", ours[wrong]),
            ("recall shifted by 0.05", "near_miss", {k: shift_recall(v, 0.05) for k, v in ours[dataset].items()}),
            ("precision scaled by 1.05", "near_miss", {k: scale_precision(v, 1.05) for k, v in ours[dataset].items()}),
        ):
            mask = without_border(panel_ink(CURVES, curves, width, height))
            controls.append(
                {
                    "name": control_name,
                    "kind": kind,
                    "score": two_way(mask, scored_theirs, TOLERANCE_PX)["score"],
                }
            )

        report["panels"][label] = {
            "dataset": dataset,
            "name": name,
            "panel_px": [int(width), int(height)],
            "border_band_px": BORDER_BAND_PX,
            "curves": values,
            "pixels": pixels,
            "controls": controls,
            "outputs": [
                f"figure-reproduction/output/fig1{label}_ours.png",
                f"figure-reproduction/output/fig1{label}_overlay.png",
            ],
        }
        print(
            f"panel {label} ({name}): pixels {pixels['score']:.3f}"
            f" (controls {', '.join(f'{c['name']} {c['score']:.3f}' for c in controls)});"
            + "; ".join(
                f" {v['legend']} {v['points_within_tolerance']}/{v['points']} within"
                f" {VALUE_TOLERANCE} (wrong dataset {v['wrong_dataset_control']['points_within_tolerance']})"
                for v in values.values()
            ),
            flush=True,
        )
    (args.out_dir / "figure1_comparison.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
