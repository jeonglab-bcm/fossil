"""Draw our results: each figure as ours (fig*_ours.png) and over the published one (fig*_overlay.png).

Usage: render.py RUN_DIR PUBLISHED_DIR SUPPLEMENT_DIR OUTDIR

Raster figures (Figs 2 and 3): ours is drawn on a copy of the published figure with the
published series removed, through the same axis calibration that read the published values,
in the published colours; the overlay draws ours in black on the untouched figure.
Vector figures (Figs S1, S2, S3, S5): the PDF page is rasterized at 200 dpi and ours is drawn
in black over it through the calibration read from the PDF; ours alone is re-plotted with
matplotlib in the published colours. Figs 4 and S4 are heatmaps without printed values: ours is
drawn as a heatmap, and the overlay puts the published figure above it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pymupdf  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import digitize as DG  # noqa: E402
from common import LABELS  # noqa: E402
from compare import CROSS_ORDER, WITHIN_ORDER, cross_label  # noqa: E402

ZOOM = 200 / 72
BLACK = (0, 0, 0)


def save(im, path):
    im.save(path, optimize=True)


def cross_mark(d, x, y, r, colour, w):
    d.line([(x - r, y - r), (x + r, y + r)], fill=colour, width=w)
    d.line([(x - r, y + r), (x + r, y - r)], fill=colour, width=w)


# ----------------------------------------------------------------------------- Fig. 2

def fig2(run, pub, out):
    dig = json.loads((run / "digitized.json").read_text())["fig2"]
    ours = json.loads((run / "fig2.json").read_text())
    base = DG.load(pub / "figure-2.png")
    lab = DG.nearest(base, DG.FIG2_COLOURS, 40)
    clean = base.copy()
    for p in dig.values():
        x0, y0, x1, y1 = p["box"]
        sub = lab[y0 - 10 : y1 + 10, x0 - 10 : x1 + 12]
        clean[y0 - 10 : y1 + 10, x0 - 10 : x1 + 12][sub >= 0] = 255
    im_ours = Image.fromarray(clean.astype(np.uint8))
    im_over = Image.fromarray(base.astype(np.uint8))
    do, dv = ImageDraw.Draw(im_ours), ImageDraw.Draw(im_over)
    outputs = {}
    for panel, p in dig.items():
        row = lambda v: (v - p["a"]) / p["b"]
        for s, c in DG.FIG2_COLOURS.items():
            pts = [(x, row(v)) for x, v in zip(p["x"], ours[panel]["series"][s])]
            do.line(pts, fill=tuple(c), width=5)
            dv.line(pts, fill=BLACK, width=2)
            for x, y in pts:
                cross_mark(do, x, y, 8, tuple(c), 3)
                cross_mark(dv, x, y, 6, BLACK, 2)
    save(im_ours, out / "fig2_ours.png")
    save(im_over, out / "fig2_overlay.png")
    for panel, p in dig.items():
        x0, y0, x1, y1 = p["box"]
        crop = (max(x0 - 130, 0), max(y0 - 110, 0), min(x1 + 40, base.shape[1]), min(y1 + 130, base.shape[0]))
        for kind, im in (("ours", im_ours), ("overlay", im_over)):
            name = f"fig2{panel.lower()}_{kind}.png"
            save(im.crop(crop), out / name)
            outputs.setdefault(f"fig2.{panel.lower()}", []).append(f"figure-reproduction/output/figures/{name}")
    return outputs


# ----------------------------------------------------------------------------- Fig. 3

def fig3(run, pub, out):
    dig = json.loads((run / "digitized.json").read_text())["fig3"]
    cv = json.loads((run / "cv_summary.json").read_text())
    base = DG.load(pub / "figure-3.png")
    im_ours = Image.fromarray(base.astype(np.uint8))
    im_over = Image.fromarray(base.astype(np.uint8))
    do, dv = ImageDraw.Draw(im_ours), ImageDraw.Draw(im_over)
    for panel, names in (("A", [(d, LABELS[d], f"within", d) for d in WITHIN_ORDER]),
                         ("B", [(f"{s}__{t}", cross_label(s, t), "cross", None) for s, t in CROSS_ORDER])):
        p = dig[panel]
        row = lambda v: (v - p["a"]) / p["b"]
        floor = row(0.4)
        for key, label, kind, _ in names:
            sc = cv[kind][key]["scores"]
            for m, (xa, xb) in p["extent"][label].items():
                top = row(sc[f"{m}/lr"]["mean"])
                # remove the published bar (and its error bar) and draw ours
                do.rectangle([xa - 1, row(1.0) - 30, xb + 1, floor - 1], fill=(255, 255, 255))
                do.rectangle([xa, top, xb, floor - 1], fill=DG.FIG3_COLOURS[m])
                dv.line([(xa - 3, top), (xb + 3, top)], fill=BLACK, width=3)
    save(im_ours, out / "fig3_ours.png")
    save(im_over, out / "fig3_overlay.png")
    h = base.shape[0]
    outputs = {}
    for panel, crop in (("a", (0, 0, base.shape[1], 590)), ("b", (0, 590, base.shape[1], h))):
        for kind, im in (("ours", im_ours), ("overlay", im_over)):
            name = f"fig3{panel}_{kind}.png"
            save(im.crop(crop), out / name)
            outputs.setdefault(f"fig3.{panel}", []).append(f"figure-reproduction/output/figures/{name}")
    outputs["fig3.pvalues"] = list(outputs["fig3.a"]) + list(outputs["fig3.b"])
    return outputs


# ----------------------------------------------------------------------------- vector figures

def page_image(path):
    pix = pymupdf.open(path)[0].get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM))
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def ypx(axis, v):
    return (v - axis["a"]) / axis["b"] * ZOOM


def fig_s1(run, supp, out):
    vec = json.loads((run / "published_vector.json").read_text())["figS1"]
    rob = json.loads((run / "robustness.json").read_text())["figS1"]
    im = page_image(supp / "pcbi.1000217.s003.pdf")
    d = ImageDraw.Draw(im)
    colours = {"Pathways": (40, 40, 115), "CORGs": (186, 84, 158), "Genes": (245, 235, 23)}
    for L, pub in vec.items():
        a = pub["_axis"]
        xs = [x * ZOOM for x in pub["_x"]]
        for s in colours:
            pts = [(x, ypx(a, v)) for x, v in zip(xs, rob[L][s])]
            d.line(pts, fill=BLACK, width=3)
            for x, y in pts:
                d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=BLACK, width=2)
    save(im, out / "figS1_overlay.png")
    fig, axs = plt.subplots(4, 2, figsize=(8, 11))
    for ax, d_ in zip(axs.flat, WITHIN_ORDER):
        for s, c in colours.items():
            ax.plot(range(6), rob[LABELS[d_]][s], marker="o", color=np.array(c) / 255, label=s)
        ax.set_title(LABELS[d_].replace(" ", "_"), fontsize=10)
        ax.set_ylim(0, 0.8)
        ax.set_xticks(range(6), ["1%", "2%", "3%", "5%", "10%", "20%"])
        ax.set_ylabel("Overlap")
    axs.flat[-1].axis("off")
    axs.flat[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "figS1_ours.png", dpi=110)
    plt.close(fig)
    return {f"fig_s1.{d_}": ["figure-reproduction/output/figures/figS1_ours.png",
                             "figure-reproduction/output/figures/figS1_overlay.png"] for d_ in WITHIN_ORDER}


def fig_s2(run, supp, out):
    vec = json.loads((run / "published_vector.json").read_text())["figS2"]
    cv = json.loads((run / "cv_summary.json").read_text())
    kinds = {"A": "knn3", "B": "knn5", "C": "nb", "D": "lda"}
    im = page_image(supp / "pcbi.1000217.s004.pdf")
    d = ImageDraw.Draw(im)
    colours = {"Gene": (79, 129, 189), "PAC": (192, 80, 77), "Mean": (155, 187, 89), "Median": (128, 100, 162), "PCA": (75, 172, 198)}
    for panel, kind in kinds.items():
        for part, names in (("within", [(d_, LABELS[d_]) for d_ in WITHIN_ORDER]),
                            ("cross", [(f"{s}__{t}", cross_label(s, t)) for s, t in CROSS_ORDER])):
            a = vec[panel]["axes"][part]
            for key, label in names:
                g = vec[panel][part][label]
                sc = cv[part][key]["scores"]
                for m, (x0, x1) in g["xs"].items():
                    y = ypx(a, sc[f"{m}/{kind}"]["mean"])
                    d.line([(x0 * ZOOM - 3, y), (x1 * ZOOM + 3, y)], fill=BLACK, width=3)
    save(im, out / "figS2_overlay.png")
    fig, axs = plt.subplots(4, 2, figsize=(11, 12), gridspec_kw={"width_ratios": [7, 4]})
    for row, (panel, kind) in enumerate(kinds.items()):
        for col, (part, keys, labels, methods) in enumerate((
                ("within", WITHIN_ORDER, [LABELS[x] for x in WITHIN_ORDER], list(colours)),
                ("cross", [f"{s}__{t}" for s, t in CROSS_ORDER], [cross_label(s, t).replace(" -> ", "\n-> ") for s, t in CROSS_ORDER], ["Gene", "PAC"]))):
            ax = axs[row, col]
            w = 0.8 / len(methods)
            for i, m in enumerate(methods):
                vals = [cv[part][k]["scores"][f"{m}/{kind}"]["mean"] for k in keys]
                ax.bar(np.arange(len(keys)) + i * w, vals, w, color=np.array(colours[m]) / 255, label=m, bottom=0)
            ax.set_ylim(0.4, 1)
            ax.set_xticks(np.arange(len(keys)) + 0.4 - w / 2, labels, fontsize=7)
            ax.set_ylabel("Accuracy" if kind.startswith("knn") else "AUC")
            if col == 0:
                ax.set_title(panel, loc="left")
    axs[0, 0].legend(fontsize=7, ncol=5)
    fig.tight_layout()
    fig.savefig(out / "figS2_ours.png", dpi=100)
    plt.close(fig)
    files = ["figure-reproduction/output/figures/figS2_ours.png", "figure-reproduction/output/figures/figS2_overlay.png"]
    return {**{f"fig_s2.{p.lower()}": files for p in kinds}, **{f"fig_s2.{p.lower()}.pvalues": files for p in kinds}}


def fig_s3(run, supp, out):
    vec = json.loads((run / "published_vector.json").read_text())
    cv = json.loads((run / "cv_summary.json").read_text())["within"]
    a = vec["figS3_axis"]
    im = page_image(supp / "pcbi.1000217.s005.pdf")
    d = ImageDraw.Draw(im)
    keys = {"PAC_SEQ": "PAC/lr", "PAC_FWD": "PAC/fwd", "Gene_SEQ": "Gene/lr", "Gene_FWD": "Gene/fwd"}
    colours = {"PAC_SEQ": (155, 187, 89), "PAC_FWD": (79, 129, 189), "Gene_SEQ": (128, 100, 162), "Gene_FWD": (192, 80, 77)}
    for d_ in WITHIN_ORDER:
        for m, (x0, x1) in vec["figS3_positions"][LABELS[d_]].items():
            y = ypx(a, cv[d_]["scores"][keys[m]]["mean"])
            d.line([(x0 * ZOOM - 3, y), (x1 * ZOOM + 3, y)], fill=BLACK, width=3)
    save(im, out / "figS3_overlay.png")
    fig, ax = plt.subplots(figsize=(8, 3.5))
    w = 0.2
    for i, m in enumerate(keys):
        ax.bar(np.arange(7) + i * w, [cv[d_]["scores"][keys[m]]["mean"] for d_ in WITHIN_ORDER], w,
               color=np.array(colours[m]) / 255, label=m)
    ax.set_xticks(np.arange(7) + 0.3, [LABELS[d_].replace(" ", "\n") for d_ in WITHIN_ORDER], fontsize=8)
    ax.set_ylim(0.4, 1)
    ax.set_ylabel("AUC")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out / "figS3_ours.png", dpi=110)
    plt.close(fig)
    return {"fig_s3": ["figure-reproduction/output/figures/figS3_ours.png", "figure-reproduction/output/figures/figS3_overlay.png"]}


def fig_s5(run, supp, out):
    vec = json.loads((run / "published_vector.json").read_text())["figS5"]
    rob = json.loads((run / "robustness.json").read_text())
    a = vec["_axis"]
    im = page_image(supp / "pcbi.1000217.s007.pdf")
    d = ImageDraw.Draw(im)
    for d_ in WITHIN_ORDER:
        L = LABELS[d_]
        x = vec[L]["x"] * ZOOM
        s = rob["figS5"][L]
        for k in ("q1", "q3"):
            d.line([(x - 22, ypx(a, s[k])), (x + 22, ypx(a, s[k]))], fill=BLACK, width=3)
        d.line([(x - 22, ypx(a, s["median"])), (x + 22, ypx(a, s["median"]))], fill=(0, 160, 0), width=3)
        d.line([(x, ypx(a, s["whisker_low"])), (x, ypx(a, s["whisker_high"]))], fill=BLACK, width=1)
        for o in s["outliers"]:
            d.ellipse([x + 8 - 5, ypx(a, o) - 5, x + 8 + 5, ypx(a, o) + 5], outline=BLACK, width=2)
    save(im, out / "figS5_overlay.png")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.boxplot([rob["figS5_sizes"][LABELS[d_]] for d_ in WITHIN_ORDER], whis=1.5,
               tick_labels=[LABELS[d_].replace(" ", "\n") for d_ in WITHIN_ORDER])
    ax.set_ylabel("number of CORGs")
    fig.tight_layout()
    fig.savefig(out / "figS5_ours.png", dpi=110)
    plt.close(fig)
    return {"fig_s5": ["figure-reproduction/output/figures/figS5_ours.png", "figure-reproduction/output/figures/figS5_overlay.png"]}


def heatmaps(run, pub, supp, out):
    f4 = json.loads((run / "figure4.json").read_text())["heatmap"]
    outputs = {}
    for tid, title, published in (("fig4", "Lung", pub / "figure-4.png"), ("fig_s4", "Breast", None)):
        parts = f4[tid]
        fig, axs = plt.subplots(1, len(parts), figsize=(12, 3.2))
        for ax, (d_, h) in zip(np.atleast_1d(axs), parts.items()):
            A = np.array(h["activity"])
            ax.imshow(np.clip(A, -2.5, 2.5), aspect="auto", cmap="RdYlGn_r", vmin=-2.5, vmax=2.5,
                      interpolation="nearest")
            ax.axvline(h["cases"] - 0.5, color="k", lw=1)
            ax.set_yticks(range(len(h["pathways"])), h["pathways"], fontsize=6)
            ax.set_xticks([])
            ax.set_title(f"{LABELS[d_]} (cases left of the line)", fontsize=8)
        fig.tight_layout()
        fig.savefig(out / f"{tid}_ours.png", dpi=110)
        plt.close(fig)
        ours = Image.open(out / f"{tid}_ours.png").convert("RGB")
        if published is None:
            p = page_image(supp / "pcbi.1000217.s006.pdf")
        else:
            p = Image.open(published).convert("RGB")
        p = p.resize((ours.width, int(p.height * ours.width / p.width)))
        both = Image.new("RGB", (ours.width, p.height + ours.height), "white")
        both.paste(p, (0, 0))
        both.paste(ours, (0, p.height))
        save(both, out / f"{tid}_overlay.png")
        outputs[tid] = [f"figure-reproduction/output/figures/{tid}_ours.png", f"figure-reproduction/output/figures/{tid}_overlay.png"]
    return outputs


def main(run: Path, pub: Path, supp: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for f in (lambda: fig2(run, pub, out), lambda: fig3(run, pub, out), lambda: fig_s1(run, supp, out),
              lambda: fig_s2(run, supp, out), lambda: fig_s3(run, supp, out), lambda: fig_s5(run, supp, out),
              lambda: heatmaps(run, pub, supp, out)):
        outputs.update(f())
    (out / "outputs.json").write_text(json.dumps(outputs, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
