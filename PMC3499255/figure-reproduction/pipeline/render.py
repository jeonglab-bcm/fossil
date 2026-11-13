"""Render our reproduction of Figures 2, 3 and 4 from a posterior JSON.

Each figure has the paper's four panels:
  top-left   dot plot of posterior pairwise-transmission probabilities
             (for the simulated Fig. 2, open circles mark the true transmissions);
  top-right  the highest-posterior transmission tree drawn in space;
  bottom     posterior histograms of the mean latency duration and the mean
             transmission distance, with the exponential prior, the posterior
             median and the 2.5/97.5% quantiles (and, for Fig. 2, the true value).

Writes ``<fig>_ours.png`` and a side-by-side ``<fig>_overlay.png`` (published |
ours). The panels are MCMC output, so the comparison with the paper is made on
the printed medians and intervals, not pixel by pixel (see results.json).
"""

from __future__ import annotations

import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def _dot_panel(ax, post, true_tree=None):
    names = post["names"]
    I = len(names)
    tp = np.array(post["trans_prob"])            # (I, I+1); col I = external
    srcs = ["ext"] + names
    for i in range(I):
        for j in range(I + 1):
            p = tp[i, j]
            if p > 0.005:
                ax.scatter(j, i, s=8 + 420 * p, c="black", edgecolors="none")
    if true_tree is not None:
        for i in range(I):
            s = true_tree[i]
            col = 0 if s == -1 else s + 1
            ax.scatter(col, i, s=430, facecolors="none", edgecolors="black", linewidths=1.0)
    ax.set_xticks(range(I + 1)); ax.set_xticklabels(srcs, rotation=90, fontsize=7)
    ax.set_yticks(range(I)); ax.set_yticklabels(names, fontsize=7)
    ax.set_xlabel("Source premise"); ax.set_ylabel("Infected premise")
    ax.set_xlim(-0.7, I + 0.7); ax.set_ylim(-0.7, I - 0.3)
    ax.grid(True, lw=0.3, alpha=0.5)


def _map_panel(ax, post):
    names = post["names"]
    X = np.array(post["X"])
    best = post["best_tree"]
    ax.scatter(X[:, 0], X[:, 1], s=6, c="black")
    for i, nm in enumerate(names):
        ax.annotate(nm, (X[i, 0], X[i, 1]), fontsize=6,
                    xytext=(2, 2), textcoords="offset points")
    for i, s in enumerate(best):
        if s is None or s == -1:
            continue
        ax.annotate("", xy=(X[i, 0], X[i, 1]), xytext=(X[s, 0], X[s, 1]),
                    arrowprops=dict(arrowstyle="->", lw=0.8, color="black"))
    ax.set_xlabel("West-East (km)"); ax.set_ylabel("South-North (km)")


def _hist_panel(ax, samples, prior_mean, xlabel, median, lo, hi, true_val=None):
    samples = np.array(samples)
    ax.hist(samples, bins=40, density=True, color="0.7", edgecolor="none")
    xs = np.linspace(max(1e-6, samples.min()), samples.max() * 1.05, 200)
    ax.plot(xs, (1.0 / prior_mean) * np.exp(-xs / prior_mean), "k-.", lw=0.9)
    ax.axvline(median, color="black", lw=1.2)
    ax.axvline(lo, color="black", ls=":", lw=0.9)
    ax.axvline(hi, color="black", ls=":", lw=0.9)
    if true_val is not None:
        ax.axvline(true_val, color="black", ls="--", lw=1.0)
    ax.set_xlabel(xlabel); ax.set_ylabel("Density")


def render(post, out_ours, title):
    truth = post.get("truth")
    true_tree = truth["J"] if truth else None
    fig, axes = plt.subplots(2, 2, figsize=(9, 8))
    _dot_panel(axes[0, 0], post, true_tree)
    _map_panel(axes[0, 1], post)
    lat = post["mean_latency"]; dist = post["mean_distance"]
    _hist_panel(axes[1, 0], post["samples"]["mean_latency"], 100.0,
                "Mean latency duration (days)", lat["median"], lat["lo"], lat["hi"],
                true_val=(truth["mean_latency"] if truth else None))
    _hist_panel(axes[1, 1], post["samples"]["mean_distance"], 100.0,
                "Mean transmission distance (km)", dist["median"], dist["lo"], dist["hi"],
                true_val=(truth["mean_distance"] if truth else None))
    fig.suptitle(title, fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out_ours, dpi=110)
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
    ap.add_argument("--title", default="")
    args = ap.parse_args()
    post = json.load(open(args.posterior))
    render(post, args.ours, args.title)
    overlay(args.published, args.ours, args.overlay)
    print("wrote", args.ours, args.overlay)


if __name__ == "__main__":
    main()
