"""Draw every attempted panel from our numbers and overlay it on the published panel.

figures.py PAPER_DIR OUT_DIR RUN_DIR OUTDIR

PAPER_DIR holds the published figure files (1283fig*.jpg). Each panel is drawn at three times the
published panel's pixel size (fig*_ours.png), the published panel is cropped and enlarged the same way
(published/fig*.png is the crop), and the overlay puts the published panel in the red channel and ours
in green and blue (fig*_overlay.png): cyan is ink only in the paper, red ink only in ours, black both.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from settings import CONDITIONS, LOCATIONS  # noqa: E402

SCALE = 3
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6, "axes.linewidth": 0.6,
                     "svg.hashsalt": "colp", "path.simplify": False})
JET = plt.get_cmap("jet")

# Published panels: figure file and crop box (left, top, right, bottom) in its pixels.
PANELS = {
    "fig2a": ("1283fig2.jpg", (0, 0, 163, 152)), "fig2b": ("1283fig2.jpg", (163, 0, 325, 152)),
    "fig2c": ("1283fig2.jpg", (0, 150, 163, 305)), "fig2d": ("1283fig2.jpg", (163, 150, 325, 305)),
    "fig2e": ("1283fig2.jpg", (325, 0, 481, 305)),
    "fig3a": ("1283fig3.jpg", (0, 0, 115, 375)), "fig3e": ("1283fig3.jpg", (0, 370, 115, 750)),
    "fig3i": ("1283fig3.jpg", (0, 745, 705, 985)),
    "fig4a": ("1283fig4.jpg", (0, 0, 100, 135)),
    "fig5a": ("1283fig5.jpg", (0, 0, 783, 405)), "fig5b": ("1283fig5.jpg", (0, 400, 112, 635)),
    "fig5c": ("1283fig5.jpg", (0, 632, 112, 864)),
    "fig6a": ("1283fig6.jpg", (0, 0, 100, 255)), "fig6b": ("1283fig6.jpg", (205, 0, 305, 255)),
    "fig6c": ("1283fig6.jpg", (0, 255, 100, 538)),
}
CLM_PANELS = {"fig3a": "NKX2-2", "fig3e": "CPB1", "fig4a": "KIF13A", "fig5b": "RNF138", "fig5c": "TLX3",
              "fig6a": "GFRA4", "fig6b": "PSPN", "fig6c": "RET"}


def figure_for(key):
    w, h = PANELS[key][1][2] - PANELS[key][1][0], PANELS[key][1][3] - PANELS[key][1][1]
    return plt.figure(figsize=(w / 100, h / 100), dpi=100 * SCALE)


def save(fig, key, out):
    fig.savefig(out / f"{key}_ours.png", dpi=100 * SCALE, metadata={"Software": None})
    plt.close(fig)


def overlay(key, paper, out, pub_dir):
    name, box = PANELS[key]
    pub = Image.open(paper / name).convert("L").crop(box)
    pub.save(pub_dir / f"{key}.png")
    big = pub.resize((pub.width * SCALE, pub.height * SCALE), Image.LANCZOS)
    ours = Image.open(out / f"{key}_ours.png").convert("L").resize(big.size, Image.LANCZOS)
    rgb = np.stack([np.asarray(big), np.asarray(ours), np.asarray(ours)], axis=2)
    Image.fromarray(rgb.astype(np.uint8)).save(out / f"{key}_overlay.png")


def bars(ax, values, labels, color="black"):
    ax.bar(range(len(values)), values, color=color, width=0.7)
    ax.set_xticks(range(len(values)), labels)


def fig2a(d, out):
    fig = figure_for("fig2a")
    ax = fig.add_axes([0.2, 0.12, 0.78, 0.84])
    a, p = d["all_pairs"], d["ppi"]
    vals = [a["positive"], a["none"], a["negative"], 0, p["positive"], p["none"], p["negative"], 0, d["random"]]
    ax.bar(range(9), vals, color="black", width=0.75)
    ax.axhline(d["random"], color="grey", lw=0.6)
    ax.set_xticks(range(9), ["+", "0", "−", "", "+", "0", "−", "", "Random"], fontsize=5)
    ax.set_ylim(0, 0.9)
    ax.set_ylabel("Location-sharing fraction", fontsize=5)
    ax.text(5, 0.84, f"{p['positive'] - p['negative']:.2f}", fontsize=5)
    save(fig, "fig2a", out)


def fig2b(d, out):
    fig = figure_for("fig2b")
    ax = fig.add_axes([0.18, 0.15, 0.78, 0.8])
    styles = {"single+physical+correlated": ("red", "-"), "physical+correlated": ("grey", ":"),
              "physical": ("black", "--"), "correlated": ("navy", "-.")}
    for k, (c, ls) in styles.items():
        ax.plot(d[k]["roc_fpr"], d[k]["roc_tpr"], color=c, ls=ls, lw=0.8, label=f"{d[k]['mean_auc']:.2f}")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("1-Specificity", fontsize=5)
    ax.set_ylabel("Sensitivity", fontsize=5)
    ax.legend(loc="lower right", fontsize=4, frameon=False, title="AUC value", title_fontsize=4)
    save(fig, "fig2b", out)


def fig2c(d, out):
    fig = figure_for("fig2c")
    ax = fig.add_axes([0.2, 0.18, 0.76, 0.76])
    for k, c in (("common", "black"), ("normal", "red"), ("low", "green"), ("high", "blue")):
        ax.plot(d["x"], d[k], color=c, lw=0.8, label=k.capitalize())
    ax.axhline(d["random"], color="black", ls="--", lw=0.6, label="Random expection")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1e2, 1e6)
    ax.set_ylim(1e-6, 1)
    ax.set_xlabel("No. of protein pairs with high correlation", fontsize=5)
    ax.set_ylabel("Fraction of protein pairs", fontsize=5)
    ax.legend(fontsize=4, frameon=False, loc="lower left")
    save(fig, "fig2c", out)


def fig2d(d, out):
    fig = figure_for("fig2d")
    ax = fig.add_axes([0.18, 0.15, 0.8, 0.8])
    keys = ["S", "N1", "N2", "L1", "L2", "TR"]
    vals = [d[k] for k in keys]
    ax.bar([0, 1, 2, 3, 4, 5.6], vals, color="black", width=0.7)
    for x, v in zip([0, 1, 2, 3, 4, 5.6], vals):
        ax.text(x, v + 0.02, f"{v:.2f}", ha="center", fontsize=5)
    ax.set_xticks([0, 1, 2, 3, 4, 5.6], ["S", "N¹", "N²", "L¹", "L²", "TR"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("AUC value", fontsize=5)
    ax.set_xlabel("Kinds of feature", fontsize=5)
    save(fig, "fig2d", out)


def fig2e(d, out):
    sets, locs = d["sets"], d["locations"]
    m = np.array([[d["single_auc"][s][j] for j in range(len(locs))] for s in sets])
    fig = figure_for("fig2e")
    ax = fig.add_axes([0.05, 0.1, 0.6, 0.86])
    ax.imshow(m, cmap=JET, vmin=0.5, vmax=1.0, aspect="auto", interpolation="nearest")
    for j, loc in enumerate(locs):
        for s in d["selected"][loc]:
            i = sets.index(s)
            ec = "white" if s == d["first"][loc] else "black"
            ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, ec=ec, lw=0.6))
    ax.set_yticks(range(len(sets)), sets, fontsize=3)
    ax.yaxis.tick_right()
    ax.set_xticks(range(len(locs)), locs, rotation=90, fontsize=3)
    save(fig, "fig2e", out)


def clm(rows, title, key, out):
    """A conditional location map: 13 locations x (normal, low, high), H on the top location of each column."""
    m = np.array(rows).T  # locations x conditions
    fig = figure_for(key)
    ax = fig.add_axes([0.3, 0.12, 0.62, 0.84])
    ax.imshow(m, cmap=JET, vmin=0, vmax=1, aspect="auto", interpolation="nearest")
    for c in range(m.shape[1]):
        r = int(np.argmax(m[:, c]))
        ax.text(c - 0.35, r + 0.35, "H", fontsize=3, color="black")
    ax.set_yticks(range(len(LOCATIONS)), LOCATIONS, fontsize=5)
    ax.set_xticks(range(3), ["Normal", "Low", "High"], rotation=90, fontsize=4)
    ax.set_title(title, fontsize=5)
    save(fig, key, out)


def fig3i(cells, out):
    prots = []
    for c in cells:
        if c["protein"] not in prots:
            prots.append(c["protein"])
    locs = ["CY", "ER", "GL", "NU", "PM"]
    m = np.full((5, len(prots)), np.nan)
    fig = figure_for("fig3i")
    ax = fig.add_axes([0.05, 0.08, 0.93, 0.62])
    for c in cells:
        if c["P"] is not None:
            m[locs.index(c["location"]), prots.index(c["protein"])] = c["P"]
    ax.imshow(m, cmap=JET, vmin=0, vmax=1, aspect="auto", interpolation="nearest")
    for c in cells:
        i, j = locs.index(c["location"]), prots.index(c["protein"])
        if c["predicted"]:
            ax.add_patch(plt.Rectangle((j - 0.45, i - 0.45), 0.9, 0.9, fill=False, ec="black", lw=0.8))
        right = c["predicted"] == c["actual"]
        ax.text(j, i + 0.2, "+" if c["actual"] else "−", ha="center", fontsize=6,
                color="black" if right else "white")
    ax.set_yticks(range(5), locs)
    ax.set_xticks(range(len(prots)), prots, rotation=90, fontsize=5)
    ax.xaxis.tick_top()
    save(fig, "fig3i", out)


def fig5a(d, out):
    """Shares of the mislocation kinds (from normal-brain location to glioma location), as a heat map."""
    m = np.zeros((len(LOCATIONS), len(LOCATIONS)))
    tot = max(sum(d["by_kind"].values()), 1)
    for k, v in d["by_kind"].items():
        f, t = k.split(">")
        m[LOCATIONS.index(t), LOCATIONS.index(f)] = 100.0 * v / tot
    fig = figure_for("fig5a")
    ax = fig.add_axes([0.25, 0.12, 0.5, 0.82])
    im = ax.imshow(m, cmap=JET, vmin=0, vmax=40, interpolation="nearest")
    ax.set_xticks(range(len(LOCATIONS)), LOCATIONS)
    ax.set_yticks(range(len(LOCATIONS)), LOCATIONS)
    ax.set_xlabel("Normal brain")
    ax.set_ylabel("Glioma")
    for (i, j), v in np.ndenumerate(m):
        if v > 0:
            ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=4, color="white")
    fig.colorbar(im, ax=ax, fraction=0.04)
    save(fig, "fig5a", out)


def main(paper: Path, outdir: Path, run: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    pub_dir = dest / "published"
    pub_dir.mkdir(exist_ok=True)
    f2 = json.load(open(outdir / "fig2.json"))
    cl = json.load(open(outdir / "clm.json"))
    z = np.load(run / "clm.npz")
    symbols = {}
    for line in list(open(run / "proteins.tsv"))[1:]:
        a, s = line.split("\t")[:2]
        symbols.setdefault(s.upper(), a)
    pos = {a: i for i, a in enumerate(z["accessions"])}
    fig2a(f2["fig2a"], dest)
    fig2b(f2["fig2b"], dest)
    fig2c(f2["fig2c"], dest)
    fig2d(f2["fig2d"], dest)
    fig2e(f2["fig2e"], dest)
    for key, sym in CLM_PANELS.items():
        i = pos[symbols[sym]]
        clm([z["P"][i][:, c] for c in range(len(CONDITIONS))], sym, key, dest)
    fig3i(cl["fig3i"]["cells"], dest)
    fig5a(cl["mislocations"], dest)
    made = sorted(PANELS)
    for key in made:
        overlay(key, paper, dest, pub_dir)
    json.dump({"panels": made, "scale": SCALE, "boxes": {k: v[1] for k, v in PANELS.items()}},
              open(dest / "figures.json", "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
