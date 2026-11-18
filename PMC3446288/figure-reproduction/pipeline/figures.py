#!/usr/bin/env python3
"""Renders, overlays and scores of the figures.

Pixel-scored (our curves drawn on the published pixel grid, with negative controls): Fig. 5a and 5b
(liver SES conservation), Fig. 6 (PTC+ fraction by junction RPKM) and Fig. 7a (conservation at
stops). Values read off the figure (bar heights): Fig. 7b and Figs S2a and S2b. Figures that are
tables or carry printed numbers (Figs 1a, 2a, 3a, 3b) are compared as values in compare.py; here
they get a render of ours next to the published panel.

Usage: figures.py ANALYSIS.json FIGURE_DATA.json CONSERVATION.json REFSEQ_STOPS.json PUBLISHED_DIR OUTDIR
Writes OUTDIR/fig*_ours.png, OUTDIR/fig*_overlay.png and OUTDIR/figures.json.
"""

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.interpolate import make_smoothing_spline

import pixel_score as ps

SAMPLES = ["BMM_WT", "BMM_KO", "Liver_WT", "Liver_KO"]


def smooth(y, df):
    """Cubic smoothing spline with about ``df`` degrees of freedom (as R's smooth.spline(df=))."""
    y = np.asarray(y, float)
    x = np.arange(len(y), dtype=float)
    ok = np.isfinite(y)
    if ok.sum() < 5:
        return y
    xs, ys = x[ok], y[ok]

    def trace(lam):
        n = len(xs)
        tr = 0.0
        for i in range(0, n, max(1, n // 25)):
            e = np.zeros(n)
            e[i] = 1
            tr += make_smoothing_spline(xs, e, lam=lam)(xs[i])
        return tr * (n / len(range(0, n, max(1, n // 25))))

    lo, hi = -6.0, 6.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if trace(10 ** mid) > df:
            lo = mid
        else:
            hi = mid
    f = make_smoothing_spline(xs, ys, lam=10 ** ((lo + hi) / 2))
    out = np.full(len(y), np.nan)
    out[ok] = f(xs)
    return out


def smooth_pieces(v, pieces=((0, 100), (100, 200), (200, 300), (300, 400)), df_per_100=33):
    v = np.asarray(v, float)
    out = np.full(len(v), np.nan)
    for a, b in pieces:
        seg = v[a:b]
        if np.isfinite(seg).sum() >= 5:
            out[a:b] = smooth(seg, df_per_100 * (b - a) / 100)
    return out


# ------------------------------------------------------------------ configurations
FIG6 = dict(file="fig6.png", box=(144, 18, 1194, 959), exclude=[(930, 36, 1168, 224)], width=5,
            colours={"BMM_WT": (178, 226, 236), "BMM_KO": (98, 155, 154), "Liver_WT": (235, 95, 33), "Liver_KO": (153, 58, 36)},
            dist=45, x=lambda v: 181 + 609 * np.log10(v), y=lambda v: 925.5 - v / 0.05 * 145.58)
FIG7A = dict(file="fig7.png", box=(157, 103, 1131, 1145), exclude=[(730, 985, 1122, 1135), (630, 103, 645, 1145)], width=3,
             colours={"BMM": (42, 54, 136), "Liver": (239, 57, 35), "RefSeq": (146, 199, 59)}, dist=60,
             x=lambda i: 182 + 9.145 * i, y=lambda v: 416.5 - v / 0.05 * 138.0)
FIG5 = dict(file="fig5.png", width=3, dist=40,
            colours={"ptc": (239, 84, 72), "noptc": (130, 154, 79), "unregulated": (198, 198, 198), "refseq": (224, 181, 48)},
            panels={"a": dict(box=(55, 76, 590, 403), x0=71, y0=391.5), "b": dict(box=(650, 76, 1186, 403), x0=667, y0=392.0)},
            xscale=1.25, yscale=305.0)


def curve_pieces(xs, ys, fx, fy, breaks=()):
    pts = [(fx(x), fy(y)) for x, y in zip(xs, ys) if np.isfinite(y)]
    if not breaks:
        return [pts]
    out, cur = [], []
    for (x, y), (px, py) in zip([(x, y) for x, y in zip(xs, ys) if np.isfinite(y)], pts):
        if cur and any(prev < b <= x for b in breaks for prev in [cur[-1][2]]):
            out.append([(a, b) for a, b, _ in cur])
            cur = []
        cur.append((px, py, x))
    if cur:
        out.append([(a, b) for a, b, _ in cur])
    return out


def score_panel(img, cfg, series, box, exclude, draw):
    """series: {key: our data}; draw(key, data) -> list of polylines in pixels."""
    pub = {k: ps.colour_mask(img, cfg["colours"][k], cfg["dist"], box, exclude) for k in series}
    ours = {k: ps.polyline_mask(img.shape[:2], draw(k, v), cfg["width"], box) for k, v in series.items()}
    a, b = ps.score(pub, ours)
    return pub, ours, a, b


def fig6(img, fd, out):
    cfg = FIG6
    data = {s: (np.array(fd["fig6"][s]["rpkm_bin"], float), np.array(fd["fig6"][s]["ptc_ratio"], float)) for s in SAMPLES}

    def draw_with(transform):
        def draw(k, v):
            x, y = transform(k, v)
            keep = x <= 46
            return [list(zip(cfg["x"](x[keep]), cfg["y"](y[keep])))]
        return draw

    ident = lambda k, v: v
    pub, ours, a, b = score_panel(img, cfg, data, cfg["box"], cfg["exclude"], draw_with(ident))
    ps.render(img, pub, ours, cfg["colours"], f"{out}/fig6_ours.png", f"{out}/fig6_overlay.png")
    controls = []
    swaps = {"WT and KO swapped within each tissue": {"BMM_WT": "BMM_KO", "BMM_KO": "BMM_WT", "Liver_WT": "Liver_KO", "Liver_KO": "Liver_WT"},
             "BMM and liver swapped": {"BMM_WT": "Liver_WT", "BMM_KO": "Liver_KO", "Liver_WT": "BMM_WT", "Liver_KO": "BMM_KO"}}
    for name, m in swaps.items():
        swapped = {k: data[m[k]] for k in data}
        _, _, ca, cb = score_panel(img, cfg, swapped, cfg["box"], cfg["exclude"], draw_with(ident))
        controls.append({"name": name, "kind": "wrong_input", "score": round(min(ca, cb), 4)})
    for name, tr in (("PTC+ fraction x1.05", lambda k, v: (v[0], v[1] * 1.05)),
                     ("PTC+ fraction x0.95", lambda k, v: (v[0], v[1] * 0.95)),
                     ("RPKM bins shifted by one", lambda k, v: (v[0] + 1, v[1]))):
        _, _, ca, cb = score_panel(img, cfg, data, cfg["box"], cfg["exclude"], draw_with(tr))
        controls.append({"name": name, "kind": "near_miss", "score": round(min(ca, cb), 4)})
    return {"published_near_ours": round(a, 4), "ours_near_published": round(b, 4), "controls": controls}


def fig7a(img, cons, out):
    cfg = FIG7A
    c = cons["fig7a"]

    def series_of(swap=False):
        bmm = np.array(c["BMM"]["mean"], float) - np.array(c["random_BMM"]["mean"], float)
        liv = np.array(c["Liver"]["mean"], float) - np.array(c["random_Liver"]["mean"], float)
        ref = np.array(c["RefSeq_STOP"]["mean"], float) - np.array(c["random_RefSeq"]["mean"], float)
        return {"BMM": liv if swap else bmm, "Liver": bmm if swap else liv, "RefSeq": ref}

    def draw_with(tr):
        def draw(k, v):
            i, y = tr(np.arange(len(v), dtype=float), np.asarray(v, float))
            return curve_pieces(i, y, cfg["x"], cfg["y"])
        return draw

    ident = lambda i, y: (i, y)
    data = series_of()
    pub, ours, a, b = score_panel(img, cfg, data, cfg["box"], cfg["exclude"], draw_with(ident))
    ps.render(img, pub, ours, cfg["colours"], f"{out}/fig7a_ours.png", f"{out}/fig7a_overlay.png")
    controls = []
    _, _, ca, cb = score_panel(img, cfg, series_of(True), cfg["box"], cfg["exclude"], draw_with(ident))
    controls.append({"name": "BMM and liver PTC+ swapped", "kind": "wrong_input", "score": round(min(ca, cb), 4)})
    flat = {k: np.zeros(len(v)) for k, v in data.items()}
    _, _, ca, cb = score_panel(img, cfg, flat, cfg["box"], cfg["exclude"], draw_with(ident))
    controls.append({"name": "no difference from random exons (all curves at zero)", "kind": "wrong_input", "score": round(min(ca, cb), 4)})
    for name, tr in (("scores x1.05", lambda i, y: (i, y * 1.05)), ("scores x0.95", lambda i, y: (i, y * 0.95)),
                     ("window shifted by 1 nt", lambda i, y: (i + 1, y))):
        _, _, ca, cb = score_panel(img, cfg, data, cfg["box"], cfg["exclude"], draw_with(tr))
        controls.append({"name": name, "kind": "near_miss", "score": round(min(ca, cb), 4)})
    return {"published_near_ours": round(a, 4), "ours_near_published": round(b, 4), "controls": controls}


def fig5(img, cons, out, tissue="Liver"):
    cfg = FIG5
    f5 = cons["fig5"]
    res = {}
    for panel, mode in (("a", "exclusion"), ("b", "inclusion")):
        p = cfg["panels"][panel]

        def series(m):
            s = {"ptc": f5[f"{tissue}:{m}_ptc"]["mean"], "noptc": f5[f"{tissue}:{m}_noptc"]["mean"],
                 "unregulated": f5[f"{tissue}:unregulated"]["mean"]}
            ref = np.array(f5["all:refseq"]["mean"], float)
            ref[:150] = np.nan  # drawn 25 nt into the introns, as in the published panels (see README)
            ref[250:] = np.nan
            s["refseq"] = ref
            return {k: smooth_pieces(np.array(v, float)) for k, v in s.items()}

        def draw_with(tr):
            def draw(k, v):
                i, y = tr(np.arange(400, dtype=float), np.asarray(v, float))
                return curve_pieces(i, y, lambda x: p["x0"] + cfg["xscale"] * x, lambda y: p["y0"] - cfg["yscale"] * y,
                                    breaks=(100, 200, 300))
            return draw

        ident = lambda i, y: (i, y)
        data = series(mode)
        excl = [(p["box"][0], p["box"][1], p["box"][2], p["box"][1] + 2)]
        pub, ours, a, b = score_panel(img, cfg, data, p["box"], excl, draw_with(ident))
        ps.render(img, pub, ours, cfg["colours"], f"{out}/fig5{panel}_ours.png", f"{out}/fig5{panel}_overlay.png")
        controls = []
        other = series("inclusion" if mode == "exclusion" else "exclusion")
        _, _, ca, cb = score_panel(img, cfg, other, p["box"], excl, draw_with(ident))
        controls.append({"name": f"{'inclusion' if mode == 'exclusion' else 'exclusion'} events drawn in place of {mode} events",
                         "kind": "wrong_input", "score": round(min(ca, cb), 4)})
        sw = dict(data)
        sw["ptc"], sw["noptc"] = data["noptc"], data["ptc"]
        _, _, ca, cb = score_panel(img, cfg, sw, p["box"], excl, draw_with(ident))
        controls.append({"name": "PTC+ and PTC- groups swapped", "kind": "wrong_input", "score": round(min(ca, cb), 4)})
        for name, tr in (("scores x1.05", lambda i, y: (i, y * 1.05)), ("scores x0.95", lambda i, y: (i, y * 0.95)),
                         ("positions shifted by 3 nt", lambda i, y: (i + 3, y))):
            _, _, ca, cb = score_panel(img, cfg, data, p["box"], excl, draw_with(tr))
            controls.append({"name": name, "kind": "near_miss", "score": round(min(ca, cb), 4)})
        res[panel] = {"published_near_ours": round(a, 4), "ours_near_published": round(b, 4), "controls": controls}
    return res


# ------------------------------------------------------------------ bar charts read off the figure
def read_bars(img, x_centres, y_zero, px_per_unit, top_search, colour_test, half=6):
    """Height of each bar: the topmost filled row above the axis at the bar's centre."""
    out = []
    for xc in x_centres:
        y = int(y_zero) - 3
        while y > top_search and colour_test(img[y, xc - half : xc + half + 1]).all():
            y -= 1
        out.append(round((y_zero - (y + 1)) / px_per_unit, 4))
    return out


def figS2(img, stops, out):
    """Fig. S2 (EPS rendered at 300 dpi): bar heights, (A) 50-nt bins to 2,100, (B) 2-nt bins to 104."""
    blue = lambda c: (c[..., 2] > 150) & (c[..., 0] < 120)
    # calibrations measured on figS2.png (tick marks): A x 0 -> 131, 2000 -> 901; y 0 -> 653, 1200 -> 140
    ax0, ax1, ay0, ay1 = 131.0, 901.0, 653.0, 140.0
    a_bins = np.arange(0, 2101, 50)
    a_cent = [int(round(ax0 + (b + 25) / 2000 * (ax1 - ax0))) for b in a_bins[:-1]]
    pub_a = read_bars(img, a_cent, ay0, (ay0 - ay1) / 1200, 100, blue, half=3)
    bx0, bx1, by0, by1 = 1108.0, 1886.0, 653.0, 178.0  # B: x 0 -> 1108, 100 -> 1886; y 0 -> 653, 100 -> 178
    b_bins = np.arange(0, 105, 2)
    b_cent = [int(round(bx0 + (b + 1) / 100 * (bx1 - bx0))) for b in b_bins[:-1]]
    pub_b = read_bars(img, b_cent, by0, (by0 - by1) / 100, 100, blue, half=2)
    ours_a = np.histogram(np.minimum(stops["figS2a_last_exon_distance"], 10 ** 9), bins=a_bins)[0].tolist()
    ours_b = np.histogram(stops["figS2b_penultimate_distance"], bins=b_bins)[0].tolist()
    fig, axs = plt.subplots(1, 2, figsize=(13, 5))
    axs[0].bar(a_bins[:-1], ours_a, width=50, align="edge", color="#4f8fc0", edgecolor="black")
    axs[0].step(a_bins[:-1], pub_a, where="post", color="red", label="published (read off)")
    axs[0].set_title("RefSeq genes with STOP in last exon")
    axs[0].set_xlabel("Distance from STOP codon to 3' end of mRNA")
    axs[1].bar(b_bins[:-1], ours_b, width=2, align="edge", color="#4f8fc0", edgecolor="black")
    axs[1].step(b_bins[:-1], pub_b, where="post", color="red", label="published (read off)")
    axs[1].set_title("RefSeq genes with STOP in 2nd last exon")
    axs[1].set_xlabel("Distance from STOP codon to nearest downstream exon-exon junction")
    for ax in axs:
        ax.set_ylabel("Frequency")
        ax.legend()
    fig.tight_layout()
    fig.savefig(f"{out}/figS2_ours.png", dpi=100)
    plt.close(fig)
    ps.side_by_side(f"{PUB}/figS2.png", f"{out}/figS2_ours.png", f"{out}/figS2_overlay.png", height=500)
    return {"a": {"bins": a_bins[:-1].tolist(), "published": pub_a, "ours": ours_a},
            "b": {"bins": b_bins[:-1].tolist(), "published": pub_b, "ours": ours_b}}


def fig7b(img, fd, stops, out):
    """Bar heights of Fig. 7b (codon frequency) and ours."""
    # y gridlines of fig7.png: 0.7 at 1506, 0.2 at 1992 (97.2 px per 0.1), so 0.0 at 2186.4;
    # bar centres: midpoints of the filled runs on row 2150
    ppu = (1992 - 1506) / 0.5
    y0 = 1992 + 0.2 * ppu
    centres = [182, 231, 280, 347, 396, 445, 512, 561, 610, 677, 726, 776, 842, 891, 941, 1008, 1057, 1106]
    filled = lambda c: (np.abs(c - 255).sum(axis=-1) > 60)
    pub = read_bars(img, centres, y0, ppu, 1480, filled, half=8)
    groups = ["Intronic", "Intergenic", "RefSeq STOPs", "Exonic", "BMM PTC+", "Liver PTC+"]
    tri = stops["trinucleotide_stop_counts"]
    rs = stops["refseq_stop_codons"]

    def frac(d):
        n = sum(d.get(k, 0) for k in ("TAA", "TAG", "TGA"))
        return [d.get(k, 0) / n if n else float("nan") for k in ("TAA", "TAG", "TGA")]

    ours = frac(tri["intronic"]) + frac(tri["intergenic"]) + frac(rs) + frac(tri["exonic"]) \
        + frac(fd["fig7b"]["BMM"]["codons"]) + frac(fd["fig7b"]["Liver"]["codons"])
    fig, ax = plt.subplots(figsize=(10, 5))
    cols = ["#dddddd", "#bbbbbb", "#999999"] * 3 + ["#8ac74a", "#5ea33c", "#3f8a3f", "#3b5bb0", "#2f48a0", "#283f98",
                                                    "#f03a2a", "#d9382a", "#c03a2c"]
    xs = np.arange(18) + np.repeat(np.arange(6) * 0.6, 3)
    ax.bar(xs, ours, color=cols, edgecolor="black")
    ax.scatter(xs, pub, color="black", marker="_", s=300, label="published (read off)", zorder=3)
    ax.set_xticks(xs, ["TAA", "TAG", "TGA"] * 6, rotation=90)
    for g, x in zip(groups, xs[1::3]):
        ax.text(x, -0.12, g, ha="center", transform=ax.get_xaxis_transform())
    ax.set_ylabel("Codon frequency")
    ax.set_ylim(0, 0.7)
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{out}/fig7b_ours.png", dpi=100)
    plt.close(fig)
    crop = Image.open(f"{PUB}/fig7.png").crop((0, 1380, 1200, 2304))
    crop.save(f"{out}/_fig7b_published.png")
    ps.side_by_side(f"{out}/_fig7b_published.png", f"{out}/fig7b_ours.png", f"{out}/fig7b_overlay.png", height=500)
    os.remove(f"{out}/_fig7b_published.png")
    from scipy.stats import fisher_exact
    ex = tri["exonic"]
    ex_tga, ex_other = ex.get("TGA", 0), ex.get("TAA", 0) + ex.get("TAG", 0)
    n, p = {}, {}
    for t in ("BMM", "Liver"):
        c = fd["fig7b"][t]["codons"]
        n[t] = fd["fig7b"][t]["n"]
        tga, other = c.get("TGA", 0), c.get("TAA", 0) + c.get("TAG", 0)
        p[t] = float(fisher_exact([[tga, other], [ex_tga, ex_other]], alternative="two-sided")[1]) if n[t] else 1.0
    return {"groups": groups, "published": pub, "ours": [round(x, 4) for x in ours], "n": n, "fisher_p": p}


def value_renders(an, fd, cons, out):
    """Renders of figures compared as values: Figs 1a, 2a, 3a, 3b, S4, S5."""
    # Fig. 1a
    fig, ax = plt.subplots(figsize=(8, 2.6))
    ax.axis("off")
    rows = ["exonic", "junction", "intronic", "intergenic", "total_mapped", "mapping_frequency"]
    cells = [[(f"{an['fig1a'][s][r]:,}" if r != "mapping_frequency" else f"{an['fig1a'][s][r]:.2f}") for s in SAMPLES] for r in rows]
    t = ax.table(cellText=cells, rowLabels=["Exonic", "Junction", "Intronic", "Intergenic", "Total mapped", "Mapping frequency"],
                 colLabels=[f"Reads, {s.replace('_', ' ')}" for s in SAMPLES], loc="center")
    t.scale(1, 1.4)
    fig.savefig(f"{out}/fig1a_ours.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    ps.side_by_side(f"{PUB}/fig1a.png", f"{out}/fig1a_ours.png", f"{out}/fig1a_overlay.png", height=400)
    # Fig. 2a
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    rl, cells = [], []
    for block, key in (("All junctions", "fig2a_all"), ("PTC+ junctions", "fig2a_ptc")):
        for t_ in ("BMM", "Liver", "Common"):
            src = an["common"] if t_ == "Common" else an["tissues"][t_]
            for unit in ("junctions", "genes"):
                rl.append(f"{block[:3]} {t_} {unit}")
                cells.append([f"{src[key][r][unit]:,} ({src[key][r][unit + '_pct']:.0f} %)" for r in ("up", "unregulated", "down")])
    t = ax.table(cellText=cells, rowLabels=rl, colLabels=["Upregulated", "Unregulated", "Downregulated"], loc="center")
    t.scale(1, 1.2)
    fig.savefig(f"{out}/fig2a_ours.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    ps.side_by_side(f"{PUB}/fig2a.png", f"{out}/fig2a_ours.png", f"{out}/fig2a_overlay.png", height=500)
    # Fig. 3a pies
    fig, axs = plt.subplots(2, 3, figsize=(9, 6))
    for col, t_ in enumerate(("BMM", "Liver", "Common")):
        src = an["common"]["fig3a"] if t_ == "Common" else an["tissues"][t_]["fig3a"]
        for row, kind in enumerate(("canonical", "alternative")):
            v = [src[kind][r] for r in ("up", "unregulated", "down")]
            axs[row, col].pie(v, colors=["#d6332b", "#f2b24a", "#6aa84f"], autopct="%.0f%%", startangle=90)
            axs[row, col].set_title(f"{t_} {kind}\nPTC+ of up: {src[kind]['ptc_of_up']:.0f}%", fontsize=9)
    fig.savefig(f"{out}/fig3a_ours.png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    ps.side_by_side(f"{PUB}/fig3a.png", f"{out}/fig3a_ours.png", f"{out}/fig3a_overlay.png", height=500)
    # Fig. 3b scatter
    fig, axs = plt.subplots(2, 2, figsize=(7, 7), sharex=True, sharey=True)
    for col, t_ in enumerate(("BMM", "Liver")):
        for row, (idx, lab) in enumerate(((1, "AS junctions"), (2, "PTC+ junctions"))):
            ax = axs[row, col]
            for s, c in ((f"{t_}_KO", "#b03030"), (f"{t_}_WT", "#3070c0")):
                arr = np.array(fd["fig3b_per_gene"][s], float)
                ax.scatter(arr[:, 0], arr[:, idx], s=3, color=c, alpha=0.4)
                sl = an["fig3b"][s]["slope_as" if idx == 1 else "slope_ptc"]
                ax.plot([0, 200], [0, 200 * sl], color=c)
                ax.text(150, 200 * sl + 4, f"a={sl:.2f}", color=c, fontsize=8)
            ax.plot([0, 200], [0, 200], color="black", lw=0.8)
            ax.set_xlim(0, 200)
            ax.set_ylim(0, 200)
            if row == 0:
                ax.set_title(t_)
            if col == 0:
                ax.set_ylabel(lab)
    fig.supxlabel("Number of junctions per gene")
    fig.savefig(f"{out}/fig3b_ours.png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    ps.side_by_side(f"{PUB}/fig3b.png", f"{out}/fig3b_ours.png", f"{out}/fig3b_overlay.png", height=600)
    # Fig. S4 (BMM SES conservation) and S5 (unnormalised stop conservation)
    f5 = cons["fig5"]
    fig, axs = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, mode in zip(axs, ("exclusion", "inclusion")):
        for key, c in ((f"BMM:{mode}_ptc", "#ef5448"), (f"BMM:{mode}_noptc", "#829a4f"), ("BMM:unregulated", "#c6c6c6"), ("all:refseq", "#e0b530")):
            v = np.array(f5[key]["mean"], float)
            if key == "all:refseq":
                v[:150] = np.nan
                v[250:] = np.nan
            v = smooth_pieces(v)
            for a, b in ((0, 100), (100, 200), (200, 300), (300, 400)):
                ax.plot(np.arange(a, b), v[a:b], color=c)
        ax.set_title(f"Exon {mode} events upregulated in BMM KO")
        ax.set_ylim(0, 1)
    axs[0].set_ylabel("Conservation")
    fig.savefig(f"{out}/figS4_ours.png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    ps.side_by_side(f"{PUB}/figS4.png", f"{out}/figS4_ours.png", f"{out}/figS4_overlay.png", height=500)
    c7 = cons["fig7a"]
    fig, ax = plt.subplots(figsize=(7, 5))
    for k, c, lab in (("BMM", "#2a3688", "BMM PTC+"), ("Liver", "#ef3923", "Liver PTC+"), ("RefSeq_STOP", "#92c73b", "Normal RefSeq STOP"),
                      ("random_BMM", "#999999", "Random expressed exons (BMM)")):
        ax.plot(np.array(c7[k]["mean"], float), color=c, label=lab)
    ax.axvline(50, color="red", ls=":")
    ax.set_xlabel("Position in 100bp window, STOP codon-centered")
    ax.set_ylabel("phastCons score")
    ax.legend()
    fig.savefig(f"{out}/figS5_ours.png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    ps.side_by_side(f"{PUB}/figS5.png", f"{out}/figS5_ours.png", f"{out}/figS5_overlay.png", height=500)


PUB = None


def main(analysis, figdata, conservation, stops, published, out):
    global PUB
    PUB = published
    os.makedirs(out, exist_ok=True)
    an = json.load(open(analysis))
    fd = json.load(open(figdata))
    cons = json.load(open(conservation))
    st = json.load(open(stops))
    res = {}
    res["fig6"] = fig6(ps.load(f"{published}/fig6.png"), fd, out)
    img7 = ps.load(f"{published}/fig7.png")
    res["fig7a"] = fig7a(img7, cons, out)
    res["fig5"] = fig5(ps.load(f"{published}/fig5.png"), cons, out)
    res["figS2"] = figS2(ps.load(f"{published}/figS2.png"), st, out)
    res["fig7b"] = fig7b(img7, fd, st, out)
    value_renders(an, fd, cons, out)
    with open(f"{out}/figures.json", "w") as f:
        json.dump(res, f, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:7])
