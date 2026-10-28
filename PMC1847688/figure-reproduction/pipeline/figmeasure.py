"""Read the published figures (the authors' original 600 dpi files) in data units.

The figures are MATLAB plots: black axes boxes with inward tick marks and pure-colour
traces. frames() finds the boxes, ticks() the tick marks on the left and bottom edges,
and Axis maps pixels to data from tick positions and the tick values printed on the figure.
"""

import numpy as np
from PIL import Image

BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)


def load(path):
    return np.array(Image.open(path).convert("RGB")).astype(int)


def mask(img, colour, tol=60):
    return np.abs(img - np.array(colour)).sum(axis=2) <= tol


def dark(img):
    return img.sum(axis=2) < 200


def _runs(line):
    """Start and end (exclusive) of each run of True."""
    d = np.diff(np.r_[0, line.astype(int), 0])
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


def frames(img, min_size=300):
    """Axes boxes as (left, top, right, bottom): the pixel rows/columns of the box lines."""
    k = dark(img)
    h_lines = []
    for y in range(k.shape[0]):
        for a, b in _runs(k[y]):
            if b - a >= min_size:
                h_lines.append((y, a, b))
    boxes = []
    used = set()
    for i, (y1, a1, b1) in enumerate(h_lines):
        for y2, a2, b2 in h_lines[i + 1 :]:
            if y2 - y1 < min_size // 2 or abs(a1 - a2) > 3 or abs(b1 - b2) > 3:
                continue
            left, right = a1, b1 - 1
            if k[y1:y2, left].mean() > 0.95 and k[y1:y2, right].mean() > 0.95:
                key = (left // 10, right // 10, y1 // 10)
                if key not in used:
                    used.add(key)
                    boxes.append((left, y1, right, y2))
                break
    # Lines are several pixels thick: keep the innermost box of each nested group.
    boxes.sort()
    merged = []
    for b in boxes:
        if merged and abs(b[0] - merged[-1][0]) <= 8 and abs(b[2] - merged[-1][2]) <= 8 and abs(b[1] - merged[-1][1]) <= 8:
            merged[-1] = b
        else:
            merged.append(b)
    return merged


def ticks(img, box, depth=(6, 14)):
    """Tick-mark centres on the left edge (y pixels) and bottom edge (x pixels)."""
    k = dark(img)
    left, top, right, bottom = box
    col = k[top + 2 : bottom - 1, left + depth[0] : left + depth[1]].any(axis=1)
    ys = [top + 2 + (a + b - 1) / 2 for a, b in _runs(col)]
    row = k[bottom - depth[1] : bottom - depth[0], left + 2 : right - 1].any(axis=0)
    xs = [left + 2 + (a + b - 1) / 2 for a, b in _runs(row)]
    return ys, xs


class Axis:
    """Linear (or log10) map from pixel to data, fitted to tick positions and values."""

    def __init__(self, pixels, values, log=False):
        v = np.log10(values) if log else np.asarray(values, float)
        self.log = log
        self.a, self.b = np.polyfit(np.asarray(pixels, float), v, 1)
        self.residual = float(np.max(np.abs(np.polyval([self.a, self.b], pixels) - v)))

    def __call__(self, p):
        v = self.a * np.asarray(p, float) + self.b
        return 10**v if self.log else v

    def inverse(self, v):
        v = np.log10(v) if self.log else np.asarray(v, float)
        return (v - self.b) / self.a


def column_extent(img, box, colour):
    """Per pixel column inside the box: lowest and highest pixel row of the colour (NaN if none)."""
    left, top, right, bottom = box
    m = mask(img[top + 1 : bottom, left + 1 : right], colour)
    has = m.any(axis=0)
    rows = np.arange(m.shape[0])[:, None]
    hi = np.where(has, np.where(m, rows, 10**9).min(axis=0), np.nan) + top + 1  # smallest row = highest value
    lo = np.where(has, np.where(m, rows, -1).max(axis=0), np.nan) + top + 1
    return np.arange(left + 1, right), hi, lo
