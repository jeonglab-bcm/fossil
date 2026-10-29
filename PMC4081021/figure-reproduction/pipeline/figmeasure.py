"""Load the published figures (PLOS original-size TIFFs, converted to PNG) and find their axes
boxes.

The published files are MATLAB plots that were rasterised, scaled up to 600 dpi and colour
converted, so lines are 5 to 12 px wide with soft edges and colours are shifted (MATLAB's
[0, 0.8, 0] green is printed as about (115, 203, 48)). Panels are located by snapping an
approximate axes box to the dark box lines; data map to pixels linearly (or log10) between
the axis limits that the authors' plotting scripts set.
"""

import numpy as np
from PIL import Image


def load(path):
    return np.array(Image.open(path).convert("RGB")).astype(int)


def dark(img, thr=250):
    return img.sum(axis=2) < thr


def snap_box(img, approx, search=25, thr=250):
    """Snap an approximate (left, top, right, bottom) box to the dark axes lines: for each edge,
    the row/column within +-search px with the most dark pixels along that edge. Returns the
    centre line of each edge."""
    k = dark(img, thr)
    L, T, R, B = approx

    def best(profile, centre):
        lo = max(centre - search, 0)
        seg = profile[lo:centre + search + 1]
        m = seg.max()
        idx = np.flatnonzero(seg >= 0.8 * m) + lo
        # centre of the run containing the maximum
        j = lo + int(np.argmax(seg))
        run = idx[np.abs(idx - j) <= 6]
        return (run.min() + run.max()) / 2

    rows = k[:, L + 10:R - 10].sum(axis=1)
    cols = k[T + 10:B - 10, :].sum(axis=0)
    return (best(cols, L), best(rows, T), best(cols, R), best(rows, B))
