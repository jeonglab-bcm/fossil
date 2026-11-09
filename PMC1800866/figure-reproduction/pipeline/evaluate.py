#!/usr/bin/env python3
"""Figs 3-6 and the evaluation numbers of the text, from our predictions.

Residue level (Figs 3, 4): recall-precision of the local and gated SPCH-SVM over the C and H
residues of the LOO set (Fig. 3) and of the five CV folds pooled (Fig. 4); AURPC and AUC with its
Wilcoxon-Mann-Whitney (Hanley-McNeil) standard error. D and E AUCs from the SPCHDE-SVM.

Protein level (Figs 5, 6): a chain's score is its third-highest gated probability (it is called
zinc-binding at threshold t when at least three residues exceed t). (a) all chains; (b) positives
are the zinc chains with a site of the given type, negatives all non-zinc chains; (c) Zn3 with
SPCH against SPCHDE.

Curves are compared with the published ones read from the PDF (extract_published_curves.py): both
are drawn as 2 px lines on the 600 dpi grid of the published axes box and scored both ways
within 2 px, with controls.

Usage: evaluate.py PRED_DIR SITES_TSV PUBLISHED_CURVES_JSON PAPER_PDF OUT_DIR
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

import pixels
import spsvm

DPI = 600
RNG_SEED = 1


def read_pred(path):
    rows = list(csv.DictReader(open(path), delimiter="\t"))
    for r in rows:
        r["label"] = int(r["label"])
        for k in ("p_local", "p_semipattern", "p_gated"):
            r[k] = float(r[k])
    return rows


def chain_types(sites_tsv):
    t = defaultdict(set)
    for r in csv.DictReader(open(sites_tsv), delimiter="\t"):
        t[r["chain"]].add(r["type"])
    return t


def residue_metrics(rows, score):
    s = [r[score] for r in rows]
    y = [r["label"] for r in rows]
    auc, se = spsvm.auc_with_se(s, y)
    return {"aurpc_ap": spsvm.aurpc(s, y, "average_precision"), "aurpc_trapezoid": spsvm.aurpc(s, y, "trapezoid"),
            "auc": auc, "auc_se": se, "n": len(y), "positives": int(sum(y))}


def residue_curve(rows, score):
    r, p = spsvm.pr_curve([x[score] for x in rows], [x["label"] for x in rows])
    return np.c_[r, p]


def protein_data(rows):
    probs = defaultdict(dict)
    labels = defaultdict(int)
    for r in rows:
        probs[r["chain"]][int(r["pos"])] = {"gated": r["p_gated"]}
        labels[r["chain"]] |= r["label"]
    return spsvm.protein_scores(probs), dict(labels)


def protein_curve(scores, labels, keep=None):
    names = [n for n in sorted(labels) if keep is None or keep(n)]
    r, p = spsvm.pr_curve([scores[n] for n in names], [labels[n] for n in names])
    return np.c_[r, p]


# ----------------------------------------------------------------------------- drawing and scoring

def box_px(box):
    x0, y0, x1, y1 = box
    return int(round((x1 - x0) * DPI / 72)), int(round((y1 - y0) * DPI / 72))


def to_px(curve, axes, size):
    (xlo, xhi), (ylo, yhi) = axes["x"], axes["y"]
    w, h = size
    c = np.asarray(curve, dtype=float)
    return np.c_[(c[:, 0] - xlo) / (xhi - xlo) * (w - 1), (yhi - c[:, 1]) / (yhi - ylo) * (h - 1)]


def mask_of(curves, axes, size):
    m = np.zeros((size[1], size[0]), bool)
    for c in curves:
        m |= pixels.line_mask((size[1], size[0]), to_px(c, axes, size), width=2)
    return m


def step_curve(c):
    """The curve as gnuplot draws it from the points: straight lines between them."""
    return np.asarray(c)


def scale_precision(c, f):
    c = np.array(c, dtype=float)
    c[:, 1] = np.clip(c[:, 1] * f, 0, 1)
    return c


def render_page_crop(pdf, page, rect, dpi=300):
    doc = pymupdf.open(pdf)
    pix = doc[page - 1].get_pixmap(dpi=dpi, clip=pymupdf.Rect(*rect))
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


WIDTH_PT = {"Local": 0.7, "Gated": 0.233, "All": 0.35, "Zn4": 0.7, "Zn3": 0.233, "Zn2": 0.233, "Zn1": 0.233,
            "CH Zn3": 0.7, "CHDE Zn3": 0.233}


def draw_figure(fig, panels, ours, published, pdf, out, dpi=300):
    """fig*_ours.png: the published figure region (published.py's frame) with the published curves
    erased and ours drawn in black at the published line widths; fig*_overlay.png: the published
    region in grey with our curves in red."""
    from published import VECTOR

    page, rect = VECTOR[int(fig[3:])]
    base = render_page_crop(pdf, page, rect, dpi)
    arr = np.array(base.convert("L"))
    scale = dpi / 72
    ours_arr = arr.copy()
    over = np.zeros_like(arr, dtype=bool)
    for p in panels:
        k = f"{fig}.{p}"
        x0, y0, x1, y1 = published[k]["box"]
        size = (int(round((x1 - x0) * scale)), int(round((y1 - y0) * scale)))
        off = np.array([(x0 - rect[0]) * scale, (y0 - rect[1]) * scale])
        for name, s in published[k]["series"].items():
            m = pixels.line_mask(arr.shape, to_px(np.array(s["points"]), published[k]["axes"], size) + off,
                                 width=max(2, int(round(s["style"]["width"] * scale)) + 5))
            ours_arr[m & (arr < 250)] = 255
        for name, c in ours[k].items():
            pts = to_px(c, published[k]["axes"], size) + off
            ours_arr[pixels.line_mask(arr.shape, pts, width=max(1, int(round(WIDTH_PT.get(name, 0.35) * scale))))] = 0
            over |= pixels.line_mask(arr.shape, pts, width=2)
    Image.fromarray(ours_arr).save(out / f"{fig}_ours.png")
    pixels.overlay(arr, over).save(out / f"{fig}_overlay.png")


def score_panel(key, ours_curves, published, controls):
    pub = published[key]
    size = box_px(pub["box"])
    pub_mask = mask_of([np.array(s["points"]) for s in pub["series"].values()], pub["axes"], size)
    ours_mask = mask_of(list(ours_curves.values()), pub["axes"], size)
    s, both = pixels.score(pub_mask, ours_mask)
    ctl = []
    for name, kind, curves in controls:
        ctl.append({"name": name, "kind": kind, "score": round(pixels.score(pub_mask, mask_of(curves, pub["axes"], size))[0], 4)})
    return {"tolerance_px": pixels.TOL_PX, "dpi": DPI, "published_near_ours": round(both["published_near_ours"], 4),
            "ours_near_published": round(both["ours_near_published"], 4), "score": round(s, 4), "controls": ctl}


def published_area(curve):
    """Area under a published curve as drawn: its upper envelope, extended to recall 0."""
    c = np.asarray(curve)
    g = np.linspace(0, 1, 4001)
    env = [c[c[:, 0] >= x, 1].max() if (c[:, 0] >= x).any() else 0.0 for x in g]
    return float(np.trapezoid(env, g))


def main(pred, sites_tsv, pub_json, pdf, out):
    pred, out = Path(pred), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    published = json.load(open(pub_json))
    types = chain_types(sites_tsv)
    rng = np.random.default_rng(RNG_SEED)
    res = {"residue": {}, "protein": {}, "published_curve_area": {}, "panels": {}}
    rows = {(v, s): read_pred(pred / f"{s}_{v}.tsv") for v in ("CH", "CHDE") for s in ("loo", "cv")}

    curves = {}
    for s, fig in (("loo", "fig3"), ("cv", "fig4")):
        R = rows[("CH", s)]
        sub = {"a": R, "b": [r for r in R if r["aa"] == "C"], "c": [r for r in R if r["aa"] == "H"]}
        for p, rr in sub.items():
            res["residue"][f"CH_{s}_{p}"] = {"local": residue_metrics(rr, "p_local"), "gated": residue_metrics(rr, "p_gated")}
            curves[f"{fig}.{p}"] = {"Local": residue_curve(rr, "p_local"), "Gated": residue_curve(rr, "p_gated")}
        D = rows[("CHDE", s)]
        for aa in "DE":
            rr = [r for r in D if r["aa"] == aa]
            res["residue"][f"CHDE_{s}_{aa}"] = {"gated": residue_metrics(rr, "p_gated"), "local": residue_metrics(rr, "p_local")}
        res["residue"][f"CHDE_{s}_all"] = {"gated": residue_metrics(D, "p_gated"), "local": residue_metrics(D, "p_local")}

    for s, fig in (("loo", "fig5"), ("cv", "fig6")):
        sc, lab = protein_data(rows[("CH", s)])
        scd, labd = protein_data(rows[("CHDE", s)])
        curves[f"{fig}.a"] = {"All": protein_curve(sc, lab)}
        curves[f"{fig}.b"] = {}
        for t in ("Zn4", "Zn3", "Zn2", "Zn1"):
            keep = lambda n, t=t: lab[n] == 0 or t in types.get(n, ())
            curves[f"{fig}.b"][t] = protein_curve(sc, lab, keep)
            res["protein"][f"{s}_{t}_chains"] = int(sum(1 for n in lab if lab[n] and t in types.get(n, ())))
        keep3 = lambda n: lab.get(n, 0) == 0 or "Zn3" in types.get(n, ())
        keep3d = lambda n: labd.get(n, 0) == 0 or "Zn3" in types.get(n, ())
        curves[f"{fig}.c"] = {"CH Zn3": protein_curve(sc, lab, keep3), "CHDE Zn3": protein_curve(scd, labd, keep3d)}
        for k in ("a", "b", "c"):
            for name, c in curves[f"{fig}.{k}"].items():
                res["protein"][f"{fig}.{k}.{name}.area"] = float(np.trapezoid(c[:, 1], c[:, 0])) if len(c) > 1 else 0.0  # recall rises along c
        res["protein"][f"{s}_chains"] = len(lab)
        res["protein"][f"{s}_zinc_chains"] = int(sum(lab.values()))

    for k, v in published.items():
        res["published_curve_area"][k] = {n: round(published_area(s["points"]), 4) for n, s in v["series"].items()}
    for k, v in curves.items():
        res.setdefault("our_curve_area", {})[k] = {n: round(published_area(c), 4) for n, c in v.items()}

    # The text's comparisons, computed on our run ("yes"/"no").
    yn = lambda b: "yes" if b else "no"
    claims = {}
    for s_ in ("loo", "cv"):
        m = res["residue"][f"CH_{s_}_a"]
        claims[f"{s_}_gated_aurpc_above_local"] = yn(m["gated"]["aurpc_ap"] > m["local"]["aurpc_ap"])
        claims[f"{s_}_gated_auc_above_local"] = yn(m["gated"]["auc"] > m["local"]["auc"])
        # "significant": the two AUCs are further apart than the sum of their standard errors
        claims[f"{s_}_auc_difference_significant"] = yn(m["gated"]["auc"] - m["local"]["auc"] > m["gated"]["auc_se"] + m["local"]["auc_se"])
        for aa in "CH":
            k = "b" if aa == "C" else "c"
            mm = res["residue"][f"CH_{s_}_{k}"]
            claims[f"{s_}_gated_above_local_on_{aa}"] = yn(mm["gated"]["aurpc_ap"] > mm["local"]["aurpc_ap"])
        claims[f"{s_}_cysteines_better_than_histidines"] = yn(res["residue"][f"CH_{s_}_b"]["gated"]["aurpc_ap"] > res["residue"][f"CH_{s_}_c"]["gated"]["aurpc_ap"])
        fig = "fig5" if s_ == "loo" else "fig6"
        areas = {t: res["protein"][f"{fig}.b.{t}.area"] for t in ("Zn4", "Zn3", "Zn2", "Zn1")}
        claims[f"{s_}_zn4_easiest"] = yn(max(areas, key=areas.get) == "Zn4")
        claims[f"{s_}_chde_better_on_zn3"] = yn(res["protein"][f"{fig}.c.CHDE Zn3.area"] > res["protein"][f"{fig}.c.CH Zn3.area"])
        for aa in "DE":
            m3 = res["residue"][f"CHDE_{s_}_{aa}"]["gated"]
            claims[f"{s_}_{aa}_better_than_random"] = yn(m3["auc"] - 2 * m3["auc_se"] > 0.5)
    res["claims"] = claims

    # Scores with controls. Wrong input: the other evaluation (CV curves on a LOO panel and back),
    # and labels shuffled within the set. Near miss: precision scaled by 0.95 and 1.05.
    other = {"fig3": "fig4", "fig4": "fig3", "fig5": "fig6", "fig6": "fig5"}
    for key, ours in curves.items():
        fig, p = key.split(".")
        ctl = [(f"{other[fig].replace('fig', 'Fig. ')}{p} curves in place of these", "wrong_input", list(curves[f"{other[fig]}.{p}"].values()))]
        shuffled = []
        for c in ours.values():
            prev = c[-1, 1]  # final precision = share of positives
            y = rng.permutation(np.r_[np.ones(int(round(prev * 1000))), np.zeros(1000 - int(round(prev * 1000)))])
            r_, p_ = spsvm.pr_curve(rng.random(len(y)), y)
            shuffled.append(np.c_[r_, p_])
        ctl.append(("random scores at the same share of positives", "wrong_input", shuffled))
        shifted = []
        for c in ours.values():
            c2 = np.array(c, dtype=float)
            c2[:, 0] = np.clip(c2[:, 0] + 0.02, 0, 1)
            shifted.append(c2)
        ctl.append(("recall shifted by 0.02", "near_miss", shifted))
        for f in (0.95, 1.05):
            ctl.append((f"precision x {f:.2f}", "near_miss", [scale_precision(c, f) for c in ours.values()]))
        res["panels"][key] = score_panel(key, ours, published, ctl)

    for fig, panels in (("fig3", "abc"), ("fig4", "abc"), ("fig5", "abc"), ("fig6", "abc")):
        draw_figure(fig, panels, curves, published, pdf, out)
    with open(out / "curves.json", "w") as f:
        json.dump({k: {n: np.round(c, 5).tolist() for n, c in v.items()} for k, v in curves.items()}, f)
    json.dump(res, open(out / "evaluation.json", "w"), indent=1)
    for k, v in res["residue"].items():
        print(k, {m: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in x.items()} for m, x in v.items()})
    for k, v in res["panels"].items():
        print(k, v["score"], [(c["name"][:30], c["score"]) for c in v["controls"]])


if __name__ == "__main__":
    main(*sys.argv[1:6])
