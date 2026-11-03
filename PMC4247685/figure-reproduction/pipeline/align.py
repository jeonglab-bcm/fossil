"""Map a render onto a published figure's pixel grid by matching the plot frames, then compare.

Usage: python3 align.py <render.png> <published.png> <out aligned.png> <out summary.json> [base|grid]

The scale and offset come from the frame lines alone (paper_measure.frame), so the data drawn
inside the frame are compared without any fitting to them. The summary reports, for the dark
pixels inside the frame, the share of published pixels with one of ours within 2 px and the
reverse, plus the blurred-ink correlation of the whole image.
"""
import json
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import binary_dilation

from paper_measure import frame as base_frame

TOL = 2


def grid_frame(path, frac=0.3):
    """Outer edges of a ggplot facet grid: first/last long dark column and row."""
    g = np.asarray(Image.open(path).convert("L"), float)
    rows = np.where((g < 150).mean(axis=1) > frac)[0]
    cols = np.where((g < 150).mean(axis=0) > 0.9 * (rows.max() - rows.min()) / g.shape[0])[0]
    return {"top": float(rows.min()), "bottom": float(rows.max()),
            "left": float(cols.min()), "right": float(cols.max())}


def inside(mask, box, margin=4):
    out = np.zeros_like(mask)
    t, b = int(box["top"]) + margin, int(box["bottom"]) - margin
    l, r = int(box["left"]) + margin, int(box["right"]) - margin
    out[t:b, l:r] = mask[t:b, l:r]
    return out


def ink_corr(a, b, blur=1.5):
    fa = 1 - np.asarray(a.filter(ImageFilter.GaussianBlur(blur)), float) / 255
    fb = 1 - np.asarray(b.filter(ImageFilter.GaussianBlur(blur)), float) / 255
    return float((fa * fb).sum() / np.sqrt((fa * fa).sum() * (fb * fb).sum()))


def main():
    render, published, out_png, out_json = sys.argv[1:5]
    frame = grid_frame if len(sys.argv) > 5 and sys.argv[5] == "grid" else base_frame
    pub = Image.open(published).convert("L")
    colour = Image.open(render).convert("RGB")
    ours = colour.convert("L")
    fp, fo = frame(published), frame(render)
    sx = (fp["right"] - fp["left"]) / (fo["right"] - fo["left"])
    sy = (fp["bottom"] - fp["top"]) / (fo["bottom"] - fo["top"])
    # Output pixel centre u maps to render coordinate (u - fp.left) / sx + fo.left.
    coeffs = (1 / sx, 0, fo["left"] - fp["left"] / sx, 0, 1 / sy, fo["top"] - fp["top"] / sy)
    aligned_rgb = colour.transform(pub.size, Image.Transform.AFFINE, coeffs,
                                   resample=Image.Resampling.BICUBIC, fillcolor=(255, 255, 255))
    aligned_rgb.save(out_png)
    aligned = aligned_rgb.convert("L")

    fa = frame(out_png)
    dp = inside(np.asarray(pub) < 160, fp)
    da = inside(np.asarray(aligned) < 160, fp)
    k = np.ones((2 * TOL + 1, 2 * TOL + 1), bool)
    cover_pub = float((dp & binary_dilation(da, k)).sum() / max(1, dp.sum()))
    cover_ours = float((da & binary_dilation(dp, k)).sum() / max(1, da.sum()))
    summary = {
        "published_size": list(pub.size), "render_size": list(ours.size),
        "scale": [round(sx, 4), round(sy, 4)],
        "frame_published": fp, "frame_render": fo, "frame_aligned": fa,
        "published_ink_within_2px_of_ours": round(cover_pub, 4),
        "our_ink_within_2px_of_published": round(cover_ours, 4),
        "blurred_ink_correlation": round(ink_corr(pub, aligned), 4),
    }
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
