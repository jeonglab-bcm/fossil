"""Render our reproduction of Figures 2, 3 and 4 the way the paper drew them.

The published figures are R base graphics (``par(mfrow = c(2, 2))``): a dot plot
of pairwise-transmission probabilities, the highest-posterior tree drawn in space
with ``asp = 1``, and two ``hist(freq = FALSE)`` panels. This module redraws them
on the published JPEG's own pixel grid, with R's rules for everything that depends
on the data, so that ours and the published figure overlay:

* panel boxes        measured from the published JPEG (pixel rows and columns of
                     the box lines and axis lines), per figure;
* dot plot           x = 1..I+1 (``ext`` first), y = 1..I, ``usr`` from xlim
                     (1, I+1) and ylim (0, I) with R's 4% extension; light grey
                     grid at every row and column; dot diameter = 10.9 px * p^(1/4)
                     (measured from the published legend); a fixed legend box
                     (42 x 59 px) 3 px from the right and 10 px from the bottom;
                     open 16 px circles for the true transmissions (Fig. 2);
* map                ``plot(x, y, asp = 1)``: the larger data range sets the
                     scale, the other axis is centred; light grey points, solid
                     arrows for the highest-posterior tree, a dashed arrow for a
                     true transmission the tree misses (Fig. 2 caption);
* histograms         the paper's breaks (read from the published axes: R's
                     ``pretty(range(x), 50)`` on their samples); densities over all
                     our samples, and the samples outside the paper's axis counted
                     and printed, not drawn; ``xlim = range(breaks)``,
                     ``ylim = c(0, max(density))`` (the published height unless
                     ours is taller), R's 4% extension, axis ticks
                     from R's axis code (GEPretty on usr) with R's label
                     formatting, a label skipped within one "m" of the last; the exponential
                     priors: mean latency beta1 ~ Exp(mean 100) and mean distance
                     2 * alpha2 with alpha2 ~ Exp(mean 100), i.e. Exp(mean 200).

The paper's map coordinates are uncorrected longitude and latitude times a
constant (109.8 km per degree, read from the published tick spacing) about an
origin read from the published ticks; the model's own distances stay
cosine-corrected (that is what reproduces the 18.2 km IP5-IP1b). These, the row
order of the 2007 dot plot and the side each map label sits on (R's ``pos``,
with a pixel nudge where the paper moved one) are read from the
published figures and recorded in CONFIG.

Writes ``<fig>_ours.png`` at the published pixel size and ``<fig>_overlay.png``,
the published figure and ours on top of each other (red channel = published,
green and blue = ours). The panels are MCMC output, so the
verdicts are computed from the printed medians, intervals and tree structure,
not pixel by pixel (see results.json).
"""

from __future__ import annotations

import argparse
import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle
from PIL import Image

# R draws in Helvetica; Liberation Sans and Arial share its metrics.
FONTS = ["Helvetica", "Arial", "Liberation Sans", "Nimbus Sans", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = FONTS

# Sizes in device pixels, measured on the published JPEGs (the figure is drawn at
# 72 dpi, so a font size in points is its em in pixels).
EM = 16.8            # axis titles and tick labels (digit height 12 px)
EM_DOT = 8.8         # dot-plot tick labels
EM_LEG = 9.8         # legend
EM_MAP = 13.5        # map labels
LW = 1.3             # lwd = 1
TICK = 7.0           # tick length
GRID = "#d0d0d0"     # dot-plot grid
BAR = "#bebebe"      # R "grey"
LEG = "#bebebe"
POINT = "#c8c8c8"    # map points
LINE_TICKLAB = 30.5  # side 1: tick-label baseline below the axis line
LINE_TITLE = 63.0    # side 1: title baseline below the axis line
SIDE2_TICKLAB = 19.5  # side 2: tick-label baseline left of the axis line
SIDE2_TITLE = 52.0   # side 2: title baseline left of the axis line
DOT_LAB = 17.0       # dot plot: distance from the axis line to the end of a tick label
KM_PER_DEG = 109.8   # paper map scale (read from the published tick spacing)

# Per figure: the published pixel size, the panel boxes (pixel index of the box or
# axis line: x0, x1, y0, y1), and what is read from the figure.
CONFIG = {
    "fig2": dict(
        px=(668, 677),
        TL=(67, 323, 10, 266), TR=(409, 664, 10, 266),
        BL=(67, 323, 352, 607), BR=(409, 664, 352, 607),
        order=None,                      # F1..F20, as the data
        map=dict(kind="km"),             # simulated: coordinates are already km
        label_pos=None,                  # below every point
        # histogram breaks (lo, hi, width) and max density, read from the published axes
        hist=dict(lat=(3.7, 8.3, 0.1), dist=(4.0, 104.0, 2.0)),
        # axis limits (usr: xmin, xmax, ymin, ymax) of the map and the two histograms
        usr=dict(TR=(-0.7234, 18.693, -4.466, 15.076), BL=(3.504, 8.487, -0.0364, 0.9397),
                 BR=(0.0, 107.822, -0.0015, 0.0399)),
        show_true=True,
    ),
    "fig3": dict(
        px=(667, 669),
        TL=(67, 322, 3, 258), TR=(408, 663, 3, 258),
        BL=(67, 322, 345, 599), BR=(408, 663, 345, 599),
        order=["IP1b", "IP2b", "IP5", "IP4b", "IP3b", "IP3c", "IP6b", "IP7", "IP8"],
        # first premise (IP1b) in the paper's map km, and 1/cos(mean latitude)
        map=dict(kind="lonlat", first=(0.685, -1.339), east_scale=1.60236,
                 xlabel_every=2, ylabel_every=2),
        label_pos={"IP1b": (3, -8.0), "IP2b": 4, "IP3b": 4, "IP3c": 4, "IP4b": 1,
                   "IP5": 4, "IP6b": 2, "IP7": 2, "IP8": 4},
        hist=dict(lat=(0.0, 220.0, 5.0), dist=(0.0, 155.0, 5.0)),
        usr=dict(TR=(-2.258, 21.244, -2.207, 21.241), BL=(-9.324, 228.438, -0.003, 0.081),
                 BR=(-6.565, 160.832, -0.0019, 0.0518)),
        show_true=False,
    ),
    "fig4": dict(
        px=(668, 670),
        TL=(68, 323, 3, 259), TR=(409, 664, 3, 259),
        BL=(68, 323, 345, 600), BR=(409, 664, 345, 600),
        order=None,                      # K, L, O, F, E, C, P, M, G, D, I, J, as the data
        map=dict(kind="lonlat", first=(2.842, 13.445), east_scale=1.72567,
                 xlabel_every=2, ylabel_every=2),
        label_pos={"K": 3, "L": 4, "D": 4, "M": 1, "O": 1, "F": 3, "G": 2,
                   "I": 1, "J": 1, "E": 1, "C": 1, "P": 1},
        hist=dict(lat=(10.0, 68.0, 1.0), dist=(4.0, 142.0, 2.0)),
        usr=dict(TR=(-1.171, 23.707, -4.254, 20.782), BL=(7.791, 70.368, -0.0046, 0.1251),
                 BR=(-1.754, 147.307, -0.0011, 0.0305)),
        show_true=False,
    ),
}


# ------------------------------------------------------------------ R rules

def r_pretty(lo: float, hi: float, n: int = 5, min_n: int | None = None,
             h: float = 1.5, h5: float = 0.5 + 1.5 * 1.5) -> np.ndarray:
    """R's pretty(): about n+1 equally spaced round values covering [lo, hi].

    h and h5 are its rounding biases: pretty() uses 1.5 and 2.75; the axis code
    (GEPretty, which places the tick marks) uses 0.8 and 1.7.
    """
    if min_n is None:
        min_n = n // 3
    dx = hi - lo
    if dx == 0 and hi == 0:
        cell, i_small = 1.0, True
    else:
        cell = max(abs(lo), abs(hi))
        U = 1 + (1 / (1 + h) if h5 >= 1.5 * h + 0.5 else 1.5 / (1 + h5))
        U *= max(1, n) * np.finfo(float).eps
        i_small = dx < cell * U * 3
    if i_small:
        if cell > 10:
            cell = 9 + cell / 10
        cell *= 1.0
        if min_n > 1:
            cell /= min_n
    else:
        cell = dx
        if n > 1:
            cell /= n
    base = 10.0 ** math.floor(math.log10(cell))
    unit = base
    if 2 * base - cell < h * (cell - unit):
        unit = 2 * base
        if 5 * base - cell < h5 * (cell - unit):
            unit = 5 * base
            if 10 * base - cell < h * (cell - unit):
                unit = 10 * base
    ns = math.floor(lo / unit + 1e-7)
    nu = math.ceil(hi / unit - 1e-7)
    while ns * unit > lo + 1e-7 * unit:
        ns -= 1
    while nu * unit < hi - 1e-7 * unit:
        nu += 1
    k = int(0.5 + nu - ns)
    if k < min_n:
        k = min_n - k
        if ns >= 0:
            nu += k / 2
            ns -= k / 2 + k % 2
        else:
            ns -= k / 2
            nu += k / 2 + k % 2
    return np.arange(ns, nu + 0.5) * unit


def r_extend(lo: float, hi: float) -> tuple[float, float]:
    """xaxs = "r": the axis range extended by 4% on each side."""
    d = 0.04 * (hi - lo)
    return lo - d, hi + d


def r_axticks(u0: float, u1: float) -> np.ndarray:
    """The tick marks R's axis() draws: GEPretty on usr, kept inside usr."""
    t = r_pretty(u0, u1, 5, min_n=1, h=0.8, h5=1.7)
    fuzz = 1e-7 * (u1 - u0)
    return t[(t >= u0 - fuzz) & (t <= u1 + fuzz)]


def r_labels(ticks: np.ndarray) -> list[str]:
    """R formats the labels of one axis with a common number of decimals."""
    dec = 0
    for t in ticks:
        s = f"{t:.10f}".rstrip("0").rstrip(".")
        if "." in s:
            dec = max(dec, len(s.split(".")[1]))
    return [f"{t:.{dec}f}" for t in ticks]


# ------------------------------------------------------------------ device

class Panel:
    """A plot region on the device: pixel box and user coordinates."""

    def __init__(self, ax, box, usr):
        self.ax = ax
        self.x0, self.x1, self.y0, self.y1 = (b + 0.5 for b in box)  # line centres
        self.u = usr  # (xmin, xmax, ymin, ymax)

    def px(self, x):
        u0, u1 = self.u[0], self.u[1]
        return self.x0 + (np.asarray(x, float) - u0) / (u1 - u0) * (self.x1 - self.x0)

    def py(self, y):
        u2, u3 = self.u[2], self.u[3]
        return self.y1 - (np.asarray(y, float) - u2) / (u3 - u2) * (self.y1 - self.y0)

    def clip(self):
        return Rectangle((self.x0, self.y0), self.x1 - self.x0, self.y1 - self.y0,
                         transform=self.ax.transData)


def _text(ax, x, y, s, size, **kw):
    kw.setdefault("rotation_mode", "anchor")
    ax.text(x, y, s, fontsize=size, color="black", **kw)


def _line(ax, xs, ys, lw=LW, ls="-", color="black", clip=None, **kw):
    (ln,) = ax.plot(xs, ys, color=color, lw=lw, ls=ls, solid_capstyle="butt",
                    dash_capstyle="butt", **kw)
    if clip is not None:
        ln.set_clip_path(clip)
    return ln


def _label_width(s: str, size: float) -> float:
    """Approximate Helvetica width of a numeric label, in pixels."""
    w = {".": 0.278, "-": 0.333}
    return sum(w.get(c, 0.556) for c in s) * size


# R skips an axis label that comes closer than the width of one "m" to the last label it drew
GAP = 0.833 * EM


def _side1(p: Panel, at, labels, title, gap=GAP, size=EM, every=1):
    ax = p.ax
    xs = p.px(at)
    _line(ax, [xs[0], xs[-1]], [p.y1, p.y1])
    last = -1e9
    for i, (x, lab) in enumerate(zip(xs, labels)):
        _line(ax, [x, x], [p.y1, p.y1 + TICK])
        if i % every:
            continue
        w = _label_width(lab, size)
        if x - w / 2 < last + gap:
            continue
        _text(ax, x, p.y1 + LINE_TICKLAB, lab, size, ha="center", va="baseline")
        last = x + w / 2
    _text(ax, (p.x0 + p.x1) / 2, p.y1 + LINE_TITLE, title, size, ha="center", va="baseline")


def _side2(p: Panel, at, labels, title, gap=GAP, size=EM, every=1):
    ax = p.ax
    ys = p.py(at)
    _line(ax, [p.x0, p.x0], [ys[0], ys[-1]])
    last = 1e9
    for i, (y, lab) in enumerate(zip(ys, labels)):
        _line(ax, [p.x0 - TICK, p.x0], [y, y])
        if i % every:
            continue
        w = _label_width(lab, size)
        if y + w / 2 > last - gap:
            continue
        _text(ax, p.x0 - SIDE2_TICKLAB, y, lab, size, ha="center", va="baseline", rotation=90)
        last = y - w / 2
    _text(ax, p.x0 - SIDE2_TITLE, (p.y0 + p.y1) / 2, title, size, ha="center", va="baseline",
          rotation=90)


def _box(p: Panel):
    p.ax.add_patch(Rectangle((p.x0, p.y0), p.x1 - p.x0, p.y1 - p.y0, fill=False,
                             lw=LW, edgecolor="black", zorder=5))


# ------------------------------------------------------------------ panels

def _dot_panel(ax, box, post, order, true_tree):
    names = post["names"]
    I = len(names)
    slot = {n: k + 1 for k, n in enumerate(order)}          # premise name -> 1..I
    p = Panel(ax, box, (*r_extend(1, I + 1), *r_extend(0, I)))
    clip = p.clip()
    for v in range(1, I + 2):
        _line(ax, [p.px(v)] * 2, [p.y0, p.y1], lw=1.0, color=GRID, clip=clip)
    for v in range(0, I + 1):
        _line(ax, [p.x0, p.x1], [p.py(v)] * 2, lw=1.0, color=GRID, clip=clip)
    tp = np.array(post["trans_prob"])                         # (I, I+1); column I = external
    for i in range(I):
        yi = p.py(slot[names[i]])
        for j in range(I + 1):
            pr = tp[i, j]
            if pr < 0.005:
                continue
            xj = p.px(1 if j == I else slot[names[j]] + 1)
            ax.add_patch(Circle((xj, yi), 10.9 * pr ** 0.25 / 2, color="black", lw=0, zorder=3))
    if true_tree is not None:
        for i in range(I):
            s = true_tree[i]
            xj = p.px(1 if s == -1 else slot[names[s]] + 1)
            ax.add_patch(Circle((xj, p.py(slot[names[i]])), 8.0, fill=False, lw=LW,
                                edgecolor="black", zorder=3))
    # legend: a grey box in the lower right, the title written upwards to its left
    lx1, ly1 = p.x1 - 3.0, p.y1 - 10.0
    lx0, ly0 = lx1 - 42.0, ly1 - 59.0
    ax.add_patch(Rectangle((lx0, ly0), 42.0, 59.0, color=LEG, lw=0, zorder=4))
    for k, pr in enumerate([1.0, 0.75, 0.5, 0.1, 0.01]):
        cy = ly0 + 6.0 + 11.75 * k
        ax.add_patch(Circle((lx0 + 8.5, cy), 10.9 * pr ** 0.25 / 2, color="black", lw=0, zorder=5))
        _text(ax, lx0 + 14.5, cy + 3.5, f"{pr:.2f}", EM_LEG, ha="left", va="baseline", zorder=5)
    for k, s in enumerate(["Posterior", "probabilities", "of transmissions"]):
        _text(ax, lx0 - 25.0 + 11.75 * k, ly1 + 6.0, s, EM_LEG, ha="left", va="baseline",
              rotation=90, zorder=5)
    _box(p)
    # axes: every slot labelled, x labels written upwards (las = 2)
    for k, lab in enumerate(["ext"] + list(order)):
        x = p.px(k + 1)
        _line(ax, [x, x], [p.y1, p.y1 + TICK])
        _text(ax, x + 3.0, p.y1 + DOT_LAB, lab, EM_DOT, ha="right", va="baseline", rotation=90)
    for k, lab in enumerate(order):
        y = p.py(k + 1)
        _line(ax, [p.x0 - TICK, p.x0], [y, y])
        _text(ax, p.x0 - DOT_LAB, y + 3.0, lab, EM_DOT, ha="right", va="baseline")
    _text(ax, (p.x0 + p.x1) / 2, p.y1 + LINE_TITLE, "Source premise", EM, ha="center", va="baseline")
    _text(ax, p.x0 - SIDE2_TITLE, (p.y0 + p.y1) / 2, "Infected premise", EM, ha="center",
          va="baseline", rotation=90)


def _map_xy(post, mcfg):
    X = np.array(post["X"], float)
    if mcfg["kind"] == "km":
        return X[:, 0].copy(), X[:, 1].copy()
    # back to uncorrected degrees about the first premise, then the paper's km
    s = KM_PER_DEG / 111.19493
    return (mcfg["first"][0] + X[:, 0] * mcfg["east_scale"] * s,
            mcfg["first"][1] + X[:, 1] * s)


def _arrow(ax, x0, y0, x1, y1, ls="-", clip=None):
    _line(ax, [x0, x1], [y0, y1], ls=ls, clip=clip, zorder=3)
    L, ang = 9.0, math.radians(30)
    th = math.atan2(y1 - y0, x1 - x0)
    for s in (-1, 1):
        _line(ax, [x1, x1 - L * math.cos(th + s * ang)], [y1, y1 - L * math.sin(th + s * ang)],
              clip=clip, zorder=3)


def _map_panel(ax, box, post, cfg, true_tree):
    names = post["names"]
    mcfg = cfg["map"]
    x, y = _map_xy(post, mcfg)
    # plot(x, y, asp = 1): the larger range sets the scale, the other is centred
    p0 = Panel(ax, box, (0, 1, 0, 1))
    w, h = p0.x1 - p0.x0, p0.y1 - p0.y0
    xmin, xmax, ymin, ymax = x.min(), x.max(), y.min(), y.max()
    scale = min(w / (xmax - xmin), h / (ymax - ymin))
    xadd = 0.5 * (w / scale - (xmax - xmin))
    yadd = 0.5 * (h / scale - (ymax - ymin))
    usr = (*r_extend(xmin - xadd, xmax + xadd), *r_extend(ymin - yadd, ymax + yadd))
    usr = cfg["usr"]["TR"] if "usr" in cfg else usr      # the paper's axes
    p = Panel(ax, box, usr)
    clip = p.clip()
    X, Y = p.px(x), p.py(y)
    outside = [nm for nm, xi, yi in zip(names, x, y)
               if not (usr[0] <= xi <= usr[1] and usr[2] <= yi <= usr[3])]
    for i in range(len(names)):
        if names[i] in outside:
            continue
        ax.add_patch(Circle((X[i], Y[i]), 2.5, color=POINT, lw=0, zorder=2))
    best = post["best_tree"]
    for i, s in enumerate(best):
        if s is not None and s >= 0:
            _arrow(ax, X[s], Y[s], X[i], Y[i], clip=clip)
    if true_tree is not None:
        for i, s in enumerate(true_tree):
            if s >= 0 and best[i] != s:
                _arrow(ax, X[s], Y[s], X[i], Y[i], ls=(0, (4, 3)), clip=clip)
    off = 0.3 * EM_MAP
    for i, nm in enumerate(names):
        if nm in outside:
            continue
        pos = (cfg["label_pos"] or {}).get(nm, 1)
        pos, dx = pos if isinstance(pos, tuple) else (pos, 0.0)   # (R pos, pixel nudge)
        X_i = X[i] + dx
        if pos == 1:
            _text(ax, X_i, Y[i] + off + 0.72 * EM_MAP, nm, EM_MAP, ha="center", va="baseline")
        elif pos == 3:
            _text(ax, X_i, Y[i] - off, nm, EM_MAP, ha="center", va="baseline")
        elif pos == 2:
            _text(ax, X_i - off, Y[i] + 0.36 * EM_MAP, nm, EM_MAP, ha="right", va="baseline")
        else:
            _text(ax, X_i + off, Y[i] + 0.36 * EM_MAP, nm, EM_MAP, ha="left", va="baseline")
    _box(p)
    xt, yt = r_axticks(p.u[0], p.u[1]), r_axticks(p.u[2], p.u[3])
    _side1(p, xt, r_labels(xt), "West–East (km)", every=mcfg.get("xlabel_every", 1))
    _side2(p, yt, r_labels(yt), "South–North (km)", every=mcfg.get("ylabel_every", 1))
    return dict(outside=outside, n=len(names))


def _breaks(s, pub):
    """The paper's breaks; without them R's default here, pretty(range(x), 50)."""
    if pub is None:
        return r_pretty(s.min(), s.max(), 50, min_n=1)
    lo, hi, w = pub
    return lo + w * np.arange(round((hi - lo) / w) + 1)


def _hist_panel(ax, box, samples, xlabel, median, lo, hi, prior_mean, pub=None, usr=None,
                true_val=None):
    s = np.asarray(samples, float)
    br = _breaks(s, pub)
    # densities over all our samples; samples outside the paper's breaks and bars above the
    # paper's axis are counted (and printed), not drawn
    counts, _ = np.histogram(s, bins=br)
    dens = counts / (len(s) * np.diff(br))
    outside = int(np.sum((s < br[0]) | (s > br[-1])))
    if usr is None:   # R's own limits: xlim = range(breaks), ylim = c(0, max(density))
        usr = (*r_extend(br[0], br[-1]), *r_extend(0.0, dens.max()))
    p = Panel(ax, box, usr)
    clip = p.clip()
    for a, b, d in zip(br[:-1], br[1:], dens):
        if d > 0:
            r = Rectangle((p.px(a), p.py(d)), p.px(b) - p.px(a), p.py(0) - p.py(d),
                          color=BAR, lw=0, zorder=1)
            r.set_clip_path(clip)
            ax.add_patch(r)
    xs = np.linspace(p.u[0], p.u[1], 400)
    xs = xs[xs >= 0]
    _line(ax, p.px(xs), p.py(np.exp(-xs / prior_mean) / prior_mean), lw=2.0,
          ls=(0, (1.5, 3.0, 6.0, 3.0)), clip=clip, zorder=2)
    for v, ls, lw in [(median, "-", 2.0), (lo, (0, (1.5, 3.5)), 2.0), (hi, (0, (1.5, 3.5)), 2.0)] + (
            [(true_val, (0, (6.0, 4.0)), 2.0)] if true_val is not None else []):
        _line(ax, [p.px(v)] * 2, [p.y0, p.y1], lw=lw, ls=ls, clip=clip, zorder=3)
    xt, yt = r_axticks(p.u[0], p.u[1]), r_axticks(p.u[2], p.u[3])
    _side1(p, xt, r_labels(xt), xlabel)
    _side2(p, yt, r_labels(yt), "Density")
    return dict(outside=outside, n=len(s), axis=[float(br[0]), float(br[-1])],
                ymax=float(usr[3]), ours_max_density=float(dens.max()),
                bars_above=int(np.sum(dens > usr[3])))


def render(post, out_ours, key):
    cfg = CONFIG[key]
    truth = post.get("truth")
    true_tree = truth["J"] if (truth and cfg["show_true"]) else None
    order = cfg["order"] or list(post["names"])
    assert sorted(order) == sorted(post["names"]), "dot-plot order must list every premise"
    W, H = cfg["px"]
    fig = plt.figure(figsize=(W / 72.0, H / 72.0), dpi=72)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    _dot_panel(ax, cfg["TL"], post, order, true_tree)
    notes = {"map": _map_panel(ax, cfg["TR"], post, cfg, true_tree)}
    lat, dist = post["mean_latency"], post["mean_distance"]
    notes["mean_latency"] = _hist_panel(ax, cfg["BL"], post["samples"]["mean_latency"], "Mean latency duration (days)",
                lat["median"], lat["lo"], lat["hi"], 100.0, cfg["hist"]["lat"], cfg["usr"]["BL"],
                true_val=truth["mean_latency"] if true_tree is not None else None)
    notes["mean_distance"] = _hist_panel(ax, cfg["BR"], post["samples"]["mean_distance"], "Mean connectivity distance (km)",
                dist["median"], dist["lo"], dist["hi"], 200.0, cfg["hist"]["dist"], cfg["usr"]["BR"],
                true_val=truth["mean_distance"] if true_tree is not None else None)
    fig.savefig(out_ours, dpi=72, facecolor="white")
    plt.close(fig)
    return notes


def overlay(published_path, ours_path, out_path):
    """The two figures on top of each other, on the published pixel grid.

    Red channel = the published figure, green and blue = ours: black is ink in
    both, cyan is ink only in the paper, red is ink only in ours.
    """
    pub = Image.open(published_path).convert("L")
    ours = Image.open(ours_path).convert("L")
    if ours.size != pub.size:
        raise SystemExit(f"{ours_path} is {ours.size}, the published figure {pub.size}")
    Image.merge("RGB", (pub, ours, ours)).save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("posterior")
    ap.add_argument("--published", required=True)
    ap.add_argument("--ours", required=True)
    ap.add_argument("--overlay", required=True)
    ap.add_argument("--key", required=True, choices=list(CONFIG))
    args = ap.parse_args()
    post = json.load(open(args.posterior))
    for k, v in render(post, args.ours, args.key).items():
        if k == "map":
            print(f"{args.key} map: {len(v['outside'])} of {v['n']} premises outside the paper's axes"
                  + (f" ({', '.join(v['outside'])})" if v["outside"] else ""))
            continue
        print(f"{args.key} {k}: {v['outside']} of {v['n']} samples outside the paper's axis "
              f"{v['axis'][0]:g}-{v['axis'][1]:g}; {v['bars_above']} bars above its height "
              f"{v['ymax']:.4g} (our tallest {v['ours_max_density']:.4g})")
    overlay(args.published, args.ours, args.overlay)
    print("wrote", args.ours, args.overlay)


if __name__ == "__main__":
    main()
