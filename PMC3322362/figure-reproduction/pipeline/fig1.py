"""Draw Fig. 1 (ROC curves of RPISeq-RF and RPISeq-SVM on RPI2241 and RPI369).

The published figure is a MATLAB plot, 600 x 466 px. This script draws the same plot with
matplotlib in MATLAB's default look (inward ticks on all four sides, boxed legend, bold axis
labels) on the published pixel grid: the axes box is placed at the pixels measured from the
published image (params/fig1.json). The ROC points are those of Weka's ThresholdCurve: one
point per distinct predicted probability, from the pooled cross-validation predictions.

Usage: python fig1.py PARAMS.json OUT_PREFIX RF2241.csv SVM2241.csv RF369.csv SVM369.csv
Writes OUT_PREFIX.png (published pixel size), OUT_PREFIX.pdf and OUT_PREFIX.roc.json.
"""

import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402


def roc(path):
    rows = np.genfromtxt(path, delimiter=",", names=True)
    y = rows["actual"].astype(int)
    p = rows["p_interact"]
    order = np.argsort(-p, kind="mergesort")
    p, y = p[order], y[order]
    # one point per distinct score, as Weka's ThresholdCurve
    last = np.r_[np.nonzero(np.diff(p))[0], len(p) - 1]
    tp = np.cumsum(y)[last]
    fp = np.cumsum(1 - y)[last]
    tpr = np.r_[0, tp / y.sum()]
    fpr = np.r_[0, fp / (len(y) - y.sum())]
    auc = float(np.trapezoid(tpr, fpr))
    return fpr, tpr, auc


def main(params_path, out, *csvs):
    P = json.load(open(params_path))
    have = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next(f for f in P["font"] if f in have)
    W, H = P["size_px"]
    fig = plt.figure(figsize=(W / P["dpi"], H / P["dpi"]), dpi=P["dpi"])
    x0, y0, x1, y1 = P["axes_px"]  # left, top, right, bottom in image pixels
    ax = fig.add_axes([x0 / W, 1 - y1 / H, (x1 - x0) / W, (y1 - y0) / H])
    curves = {}
    for spec, path in zip(P["curves"], csvs):
        fpr, tpr, auc = roc(path)
        curves[spec["label"]] = {"auc": auc, "points": len(fpr)}
        ax.plot(fpr, tpr, color=spec["color"], linestyle=spec["style"], linewidth=P["lw"], label=spec["label"])
        tx, ty = spec["auc_xy"]
        ax.text(tx, ty, f"AUC={auc:.2f}", fontsize=P["text_pt"], ha="left", va="center")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ticks = np.round(np.arange(0, 1.01, 0.1), 1)
    ax.set_xticks(ticks, [f"{t:g}" for t in ticks])
    ax.set_yticks(ticks, [f"{t:g}" for t in ticks])
    ax.tick_params(direction="in", top=True, right=True, length=P["tick_len"], width=P["axis_lw"],
                   labelsize=P["tick_pt"], pad=P["tick_pad"])
    for s in ax.spines.values():
        s.set_linewidth(P["axis_lw"])
    ax.set_xlabel("False positive rate", fontsize=P["label_pt"], fontweight="bold", labelpad=P["xlabel_pad"])
    ax.set_ylabel("True positive rate", fontsize=P["label_pt"], fontweight="bold", labelpad=P["ylabel_pad"])
    lx, ly = P["legend_corner_px"]  # lower-right corner of the legend frame, image pixels
    leg = ax.legend(loc="lower right", bbox_to_anchor=((lx - x0) / (x1 - x0), (y1 - ly) / (y1 - y0)),
                    fontsize=P["legend_pt"], frameon=True, fancybox=False, edgecolor="black",
                    framealpha=1, borderaxespad=0, borderpad=P["legend_borderpad"],
                    handlelength=P["legend_handle"], labelspacing=P["legend_spacing"])
    leg.get_frame().set_linewidth(P["axis_lw"])
    fig.savefig(out + ".png", dpi=P["dpi"])
    fig.savefig(out + ".pdf")
    json.dump(curves, open(out + ".roc.json", "w"), indent=2)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *sys.argv[3:7])
