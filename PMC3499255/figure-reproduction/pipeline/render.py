"""Render our reproduction of Figures 2, 3 and 4 from a posterior JSON, drawn to
match the published figure: the same pixel size, the same 2x2 panel layout, the
same axis ranges, and the premises ordered by inferred infection time (as the
paper orders them).

Each figure has the paper's four panels:
  top-left   dot plot of posterior pairwise-transmission probabilities
             (for the simulated Fig. 2, open circles mark the true transmissions);
  top-right  the highest-posterior transmission tree drawn in space;
  bottom     posterior histograms of the mean latency duration and the mean
             connectivity (transmission) distance, with the exponential prior,
             the posterior median and the 2.5/97.5% quantiles (and, for Fig. 2,
             the true value).

Writes ``<fig>_ours.png`` at the published figure's pixel size (so a pixel
overlay lines up) and a side-by-side ``<fig>_overlay.png``. The panels are MCMC
output, so the comparison with the paper is made on the printed medians and
intervals and the tree structure, not pixel by pixel (see results.json). For the
real-data maps the longitude axis uses the paper's un-cosine-corrected scaling
(``east_scale``), which reproduces the published east extent; the model's own
distances are cosine-corrected.
"""

from __future__ import annotations

import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# Per-figure layout matched to the published JPEG (size in px, panel axis ranges,
# and the longitude scale that recovers the paper's map east extent).
CONFIG = {
    "fig2": dict(px=(668, 677),
                 map_xlim=(-1.0, 18.5), map_xticks=[0, 5, 10, 15],
                 map_ylim=(-1.5, 15.5), map_yticks=[0, 5, 10, 15],
                 lat_xlim=(3.6, 8.3), lat_xticks=[4, 5, 6, 7, 8],
                 lat_ylim=(0, 0.95), lat_yticks=[0.0, 0.2, 0.4, 0.6, 0.8],
                 dist_xlim=(0, 105), dist_xticks=[0, 20, 40, 60, 80, 100],
                 dist_ylim=(0, 0.037), dist_yticks=[0.0, 0.01, 0.02, 0.03],
                 east_scale=1.0, show_true=True),
    "fig3": dict(px=(667, 669),
                 map_xlim=(-1.5, 21.0), map_xticks=[0, 10, 20],
                 map_ylim=(-2.0, 21.0), map_yticks=[0, 10, 20],
                 lat_xlim=(0, 215), lat_xticks=[0, 50, 100, 150, 200],
                 lat_ylim=(0, 0.082), lat_yticks=[0.0, 0.02, 0.04, 0.06, 0.08],
                 dist_xlim=(0, 155), dist_xticks=[0, 50, 100, 150],
                 dist_ylim=(0, 0.051), dist_yticks=[0.0, 0.01, 0.02, 0.03, 0.04, 0.05],
                 east_scale=1.6024, show_true=False),
    "fig4": dict(px=(668, 670),
                 map_xlim=(-1.5, 26.0), map_xticks=[0, 10, 20],
                 map_ylim=(0.0, 21.0), map_yticks=[0, 10, 20],
                 lat_xlim=(8, 70), lat_xticks=[10, 20, 30, 40, 50, 60, 70],
                 lat_ylim=(0, 0.125), lat_yticks=[0.0, 0.04, 0.08, 0.12],
                 dist_xlim=(0, 135), dist_xticks=[0, 20, 40, 60, 80, 100, 120],
                 dist_ylim=(0, 0.031), dist_yticks=[0.0, 0.01, 0.02, 0.03],
                 east_scale=1.7257, show_true=False),
}


def _order_by_infection(post):
    """Premise indices ordered by inferred infection time (earliest first)."""
    t = np.array(post["infection_time_median"])
    return list(np.argsort(t))


def _dot_panel(ax, post, order, true_tree=None):
    names = post["names"]
    I = len(names)
    tp = np.array(post["trans_prob"])             # (I, I+1); col I = external
    pos = {p: k for k, p in enumerate(order)}     # premise -> axis slot
    # x axis: external, then premises in infection order; y: premises in infection order
    for i in range(I):
        yi = pos[i]
        for j in range(I + 1):
            p = tp[i, j]
            if p <= 0.004:
                continue
            xj = 0 if j == I else pos[j] + 1
            ax.scatter(xj, yi, s=6 + 230 * p, c="black", edgecolors="none", zorder=3)
    if true_tree is not None:
        for i in range(I):
            s = true_tree[i]
            xj = 0 if s == -1 else pos[s] + 1
            ax.scatter(xj, pos[i], s=250, facecolors="none", edgecolors="black",
                       linewidths=0.8, zorder=2)
    xlabels = ["ext"] + [names[p] for p in order]
    ax.set_xticks(range(I + 1)); ax.set_xticklabels(xlabels, rotation=90, fontsize=6)
    ax.set_yticks(range(I)); ax.set_yticklabels([names[p] for p in order], fontsize=6)
    ax.set_xlabel("Source premise", fontsize=8); ax.set_ylabel("Infected premise", fontsize=8)
    ax.set_xlim(-0.8, I + 0.8); ax.set_ylim(-0.8, I - 0.2)
    ax.tick_params(length=2, pad=1)
    ax.set_facecolor("#f0f0f0")
    ax.grid(True, color="white", lw=0.6)
    for spine in ax.spines.values():
        spine.set_visible(False)
    # legend of dot sizes, in the open lower-right region as in the paper
    lx = I - 1.0
    ax.text(lx - 0.3, I * 0.46 + 0.5, "Posterior\nprobabilities\nof transmissions",
            fontsize=5, va="bottom", ha="left")
    for k, p in enumerate([1.0, 0.75, 0.5, 0.1, 0.01]):
        yy = I * 0.42 - k * (I * 0.09)
        ax.scatter(lx, yy, s=6 + 230 * p, c="black", edgecolors="none", zorder=4)
        ax.text(lx + 0.4, yy, f"{p:.2f}", fontsize=5, va="center")


def _map_panel(ax, post, cfg):
    names = post["names"]
    X = np.array(post["X"], dtype=float).copy()
    X[:, 0] *= cfg["east_scale"]                   # recover the paper's map east scaling
    X[:, 0] -= X[:, 0].min(); X[:, 1] -= X[:, 1].min()   # southwest corner at the origin
    best = post["best_tree"]
    for i, s in enumerate(best):
        if s is None or s == -1:
            continue
        ax.annotate("", xy=(X[i, 0], X[i, 1]), xytext=(X[s, 0], X[s, 1]),
                    arrowprops=dict(arrowstyle="->", lw=0.8, color="black"))
    for i, nm in enumerate(names):
        ax.annotate(nm, (X[i, 0], X[i, 1]), fontsize=6,
                    xytext=(2, 2), textcoords="offset points")
    ax.set_xlim(*cfg["map_xlim"]); ax.set_ylim(*cfg["map_ylim"])
    ax.set_xticks(cfg["map_xticks"]); ax.set_yticks(cfg["map_yticks"])
    ax.set_xlabel("West-East (km)", fontsize=8); ax.set_ylabel("South-North (km)", fontsize=8)
    ax.tick_params(length=2, labelsize=7)


def _hist_panel(ax, samples, xlim, xticks, ylim, yticks, xlabel, median, lo, hi,
                prior_mean=100.0, true_val=None):
    samples = np.array(samples)
    bins = np.linspace(xlim[0], xlim[1], 56)
    ax.hist(samples, bins=bins, range=xlim, density=True, color="0.72", edgecolor="none")
    xs = np.linspace(max(1e-6, xlim[0]), xlim[1], 200)
    ax.plot(xs, (1.0 / prior_mean) * np.exp(-xs / prior_mean), "k-.", lw=0.9)
    if true_val is not None:
        ax.axvline(true_val, color="black", ls="--", lw=1.0)
    ax.axvline(median, color="black", lw=1.3)
    ax.axvline(lo, color="black", ls=":", lw=0.9)
    ax.axvline(hi, color="black", ls=":", lw=0.9)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_xticks(xticks); ax.set_yticks(yticks)
    ax.set_xlabel(xlabel, fontsize=8); ax.set_ylabel("Density", fontsize=8)
    ax.tick_params(length=2, labelsize=7)


def render(post, out_ours, key):
    cfg = CONFIG[key]
    truth = post.get("truth")
    true_tree = truth["J"] if truth else None
    order = _order_by_infection(post)
    w, h = cfg["px"]
    dpi = 100.0
    fig, axes = plt.subplots(2, 2, figsize=(w / dpi, h / dpi), dpi=dpi)
    _dot_panel(axes[0, 0], post, order, true_tree)
    _map_panel(axes[0, 1], post, cfg)
    lat = post["mean_latency"]; dist = post["mean_distance"]
    _hist_panel(axes[1, 0], post["samples"]["mean_latency"],
                cfg["lat_xlim"], cfg["lat_xticks"], cfg["lat_ylim"], cfg["lat_yticks"],
                "Mean latency duration (days)", lat["median"], lat["lo"], lat["hi"],
                true_val=(truth["mean_latency"] if (truth and cfg["show_true"]) else None))
    _hist_panel(axes[1, 1], post["samples"]["mean_distance"],
                cfg["dist_xlim"], cfg["dist_xticks"], cfg["dist_ylim"], cfg["dist_yticks"],
                "Mean connectivity distance (km)", dist["median"], dist["lo"], dist["hi"],
                true_val=(truth["mean_distance"] if (truth and cfg["show_true"]) else None))
    fig.subplots_adjust(left=0.10, right=0.975, top=0.975, bottom=0.11,
                        wspace=0.32, hspace=0.42)
    fig.savefig(out_ours, dpi=dpi)
    plt.close(fig)


def overlay(published_path, ours_path, out_path):
    pub = Image.open(published_path).convert("RGB")
    ours = Image.open(ours_path).convert("RGB")
    h = 520
    pub = pub.resize((int(pub.width * h / pub.height), h))
    ours = ours.resize((int(ours.width * h / ours.height), h))
    canvas = Image.new("RGB", (pub.width + ours.width + 20, h + 26), "white")
    canvas.paste(pub, (0, 26)); canvas.paste(ours, (pub.width + 20, 26))
    from PIL import ImageDraw
    d = ImageDraw.Draw(canvas)
    d.text((4, 6), "Published", fill="black")
    d.text((pub.width + 24, 6), "Reproduced", fill="black")
    canvas.save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("posterior")
    ap.add_argument("--published", required=True)
    ap.add_argument("--ours", required=True)
    ap.add_argument("--overlay", required=True)
    ap.add_argument("--key", required=True, choices=list(CONFIG))
    args = ap.parse_args()
    post = json.load(open(args.posterior))
    render(post, args.ours, args.key)
    overlay(args.published, args.ours, args.overlay)
    print("wrote", args.ours, args.overlay)


if __name__ == "__main__":
    main()
