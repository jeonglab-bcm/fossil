"""Draw Figs 1-5 and S1-S3 from our run on the published pixel grids, score them with negative
controls, and write the renders, overlays and figures.json.

Usage: figures.py YEAST.json HUMAN.json PUBLISHED_DIR OUT_DIR
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
import figtools as ft  # noqa: E402

DIMS = ["2", "3", "4", "5", "6", "7"]
EXCEL6 = [(65, 111, 166), (168, 66, 63), (134, 164, 74), (110, 84, 141), (61, 150, 174), (218, 129, 55)]
EXCEL4 = [(74, 126, 187), (190, 75, 72), (152, 185, 84), (125, 96, 160)]
FIG5_DIM = "4"
# Fig. 4 has fewer markers than Fig. 2: at these epsilons, then (1, 1) (read from the
# figures: the dimension-4 points at 0.05 ... 0.5 fall on the Fig. 4 markers)
SPARSE_GRID = [0.01, 0.03, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5]
# Fig. 5 has five markers below 2% false positives on its 1,000 and 2,000 curves: 0.01 to 0.05
# in steps of 0.01, then 0.1 to 0.5
FIG5_GRID = [0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5]
# How each published Fig. 5 curve was embedded (fig5_single_deletions.py, results.json fig5): the
# 500 to 2,000 curves match the largest component, the 3,000 curve every protein
FIG5_EMBEDDING = {500: "lcc", 1000: "lcc", 2000: "lcc", 3000: "whole"}


def on_grid(points, grid=SPARSE_GRID):
    keep = {round(e, 2) for e in grid}
    return [p for p in points if round(float(p["eps"]), 2) in keep]  # the dimension drawn in Fig. 5 (not stated; chosen by the score, see figures.json)


def classify(a, refs, region, tol=60):
    """Label each saturated pixel with its nearest reference colour (or -1)."""
    d = np.stack([np.sqrt(((a - np.array(c)) ** 2).sum(axis=2)) for c in refs])
    lab = d.argmin(axis=0)
    ok = (d.min(axis=0) <= tol) & ((a.max(axis=2) - a.min(axis=2)) >= 40) & region
    lab[~ok] = -1
    return lab


def pub_masks(a, refs, region, open_px=3):
    lab = classify(a, refs, region)
    out = []
    for k in range(len(refs)):
        m = lab == k
        if open_px > 1:
            m = ndimage.binary_opening(m, np.ones((open_px, open_px), bool))
        out.append(m)
    return out


def plot_region(shape, cal, legends, pad=6):
    r = np.zeros(shape[:2], bool)
    bottom = max(cal["bottom"], cal["by"])  # the y = 0 line, when no gridline marks it
    r[max(0, int(cal["top"]) - 40):int(bottom) + pad, max(0, int(cal["left"]) - pad):int(cal["right"]) + pad] = True
    for x0, y0, x1, y1 in legends:
        r[y0:y1, x0:x1] = False
    return r


def score_panel(pubs, ours_series, cal, shape, width, exclude, smooth=True, clip=None, dots=False):
    pub_any = np.zeros(shape[:2], bool)
    for m in pubs:
        pub_any |= m
    parts, masks = [], []
    for m, (x, y) in zip(pubs, ours_series):
        o = ft.draw_series(shape, cal, x, y, width, smooth=smooth, clip=clip, dots=dots)
        masks.append(o)
        parts.append(ft.shares(m, o, pub_any, exclude))
    a, b = ft.pooled_score(parts)
    return {"published_near_ours": a, "ours_near_published": b, "score": min(a, b),
            "series": [{"published_near_ours": p[0], "ours_near_published": p[1],
                        "published_px": p[2], "ours_px": p[3]} for p in parts]}, masks


def scale(series, fy=1.0, dx=0.0, ymax=None):
    out = []
    for x, y in series:
        y = np.asarray(y, float) * fy
        if ymax is not None:
            y = np.minimum(y, ymax)
        out.append((np.asarray(x, float) + dx, y))
    return out


def grid_xy(points, x="fpr", y="sens"):
    pts = [p for p in points if p[x] is not None and p[y] is not None]
    return [p[x] for p in pts], [p[y] for p in pts]


def run_panel(name, a, cal, refs, legends, ours, controls, out, smooth=True, clip=None, dots=False,
              tol=60, open_px=3, colours=None, width=None):
    region = plot_region(a.shape, cal, legends)
    lab = classify(a, refs, region, tol)
    pubs = []
    for k in range(len(refs)):
        m = lab == k
        if open_px > 1:
            m = ndimage.binary_opening(m, np.ones((open_px, open_px), bool))
        pubs.append(m)
    w = width or float(np.median([ft.line_width(m) for m in pubs if m.any()]))
    exclude = np.zeros(a.shape[:2], bool)
    if not dots:
        for m in pubs:
            exclude |= ft.marker_mask(m, w)
    res, masks = score_panel(pubs, ours, cal, a.shape, w, exclude, smooth, clip, dots)
    res["line_width_px"] = w
    res["tolerance_px"] = ft.TOL_PX
    res["calibration_residual_px"] = cal["residual_px"]
    res["controls"] = []
    for cname, kind, series in controls:
        r, _ = score_panel(pubs, series, cal, a.shape, w, exclude, smooth, clip, dots)
        res["controls"].append({"name": cname, "kind": kind, "score": r["score"]})
    ft.render(a, pubs, masks, colours or refs, out / f"{name}_ours.png", out / f"{name}_overlay.png")
    best = max(c["score"] for c in res["controls"])
    res["threshold"] = round(max(0.90, best + 0.02), 4)
    print(f"{name}: score {res['score']:.4f} (published {res['published_near_ours']:.4f}, ours "
          f"{res['ours_near_published']:.4f}); best control {best:.4f}", flush=True)
    return res


def main(yeast_json, human_json, pub_dir, out):
    Y = json.load(open(yeast_json))
    H = json.load(open(human_json))
    pub = Path(pub_dir)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    res = {}

    # ---- Fig. 1: densities after embedding in 5 dimensions
    a = ft.load(pub / "figure-1.png")
    calA = ft.excel_axes(a, (12, 12, 1030, 603), [2, 4, 6, 8, 10, 12], (0, 1.4), grey=185, tol=45, frac=0.4)
    calB = ft.excel_axes(a, (1036, 12, 2054, 603), [0, 2, 4, 6, 8, 10, 12], (0, 1.4), grey=185, tol=45, frac=0.4)
    refs1 = [(61, 116, 182), (189, 73, 70)]

    def dens(d, xmax):
        x = np.array(d["x"])
        keep = x <= xmax
        return [(x[keep], np.array(d["p_edge"])[keep]), (x[keep], np.array(d["p_nonedge"])[keep])]

    ya = dens(Y["fig1a"], Y["fig1a"]["max_distance_all_pairs"])
    hb = dens(H["fig1b"], H["max_distance"])
    clipA = (calA["top"], 1e9)
    for key, cal, ours, wrong, legend, xmax in [
        ("a", calA, ya, hb, (600, 280, 880, 410), 1.4),
        ("b", calB, hb, ya, (1685, 280, 1965, 410), 1.4),
    ]:
        top = (cal["ay"] * 12 + cal["by"], 1e9)
        controls = [("other network's densities", "wrong_input", wrong),
                    ("densities x 1.05", "near_miss", scale(ours, 1.05)),
                    ("densities x 0.95", "near_miss", scale(ours, 0.95)),
                    ("distance shifted by 0.014 (1% of the axis)", "near_miss", scale(ours, dx=0.014))]
        res[f"fig1.{key}"] = run_panel(f"fig1{key}", a, cal, refs1, [legend], ours, controls, out,
                                       smooth=False, clip=top, open_px=2)
    # one image per figure: stitch the two panel renders
    from PIL import Image
    for kind in ("ours", "overlay"):
        A = np.asarray(Image.open(out / f"fig1a_{kind}.png").convert("RGB")).copy()
        B = np.asarray(Image.open(out / f"fig1b_{kind}.png").convert("RGB"))
        A[:, 1034:] = B[:, 1034:]
        Image.fromarray(A).save(out / f"fig1_{kind}.png", optimize=True)
        (out / f"fig1a_{kind}.png").unlink()
        (out / f"fig1b_{kind}.png").unlink()

    # ---- Fig. 2 and Fig. 3: ROC and precision-recall, dimensions 2-7
    d = Y["dims"]
    wrong = Y["wrong_truth"]["dims"]
    for fig, file, ytk, legend, xk, yk in [
        ("fig2", "figure-2.png", [i / 10 for i in range(11)], (1190, 290, 1385, 645), "fpr", "sens"),
        ("fig3", "figure-3.png", [i * 0.05 for i in range(6)], (1110, 240, 1310, 590), "recall", "precision"),
    ]:
        a = ft.load(pub / file)
        cal = ft.excel_axes(a, (12, 12, a.shape[1] - 12, a.shape[0] - 12), ytk, (0, 1))
        ours = [grid_xy(d[k]["grid"], xk, yk) for k in DIMS]
        nb = {"2": "3", "3": "2", "4": "5", "5": "4", "6": "7", "7": "6"}
        ymax = 1.0 if fig == "fig2" else None
        controls = [
            ("positives = Gavin/Krogan pairs Collins discarded (BioGRID)", "wrong_input",
             [grid_xy(wrong[k]["grid"], xk, yk) for k in DIMS]),
            ("each dimension drawn with its neighbour's curve", "near_miss",
             [grid_xy(d[nb[k]]["grid"], xk, yk) for k in DIMS]),
            ("y x 1.05", "near_miss", scale(ours, 1.05, ymax=ymax)),
            ("y x 0.95", "near_miss", scale(ours, 0.95)),
            ("x shifted by 0.01 (1% of the axis)", "near_miss", scale(ours, dx=0.01)),
        ]
        res[fig] = run_panel(fig, a, cal, EXCEL6, [legend], ours, controls, out)

    # ---- Fig. 4: dimension 4, one iteration against iterating to convergence
    a = ft.load(pub / "figure-4.png")
    cal = ft.excel_axes(a, (12, 12, a.shape[1] - 12, a.shape[0] - 12), [i / 10 for i in range(11)], (0, 1))

    def with_end(xy):
        x, y = xy
        if x[-1] < 0.999:
            x, y = list(x) + [1.0], list(y) + [1.0]
        return x, y

    one = with_end(grid_xy(on_grid(Y["fig4"]["one_iteration"])))
    conv = with_end(grid_xy(on_grid(Y["fig4"]["converged"])))
    ours = [one, conv]
    controls = [("dimension 2, one iteration, for both curves", "wrong_input",
                 [with_end(grid_xy(on_grid(d["2"]["grid"])))] * 2),
                ("curves swapped", "near_miss", [conv, one]),
                ("y x 1.05", "near_miss", scale(ours, 1.05, ymax=1.0)),
                ("y x 0.95", "near_miss", scale(ours, 0.95)),
                ("x shifted by 0.01 (1% of the axis)", "near_miss", scale(ours, dx=0.01))]
    res["fig4"] = run_panel("fig4", a, cal, EXCEL4[:2], [(675, 310, 1150, 495)], ours, controls, out)

    # ---- Fig. 5: deleting 500 ... 3000 edges and recovering them
    a = ft.load(pub / "figure-5.png")
    cal = ft.excel_axes(a, (12, 12, a.shape[1] - 12, a.shape[0] - 12), [i / 10 for i in range(11)], (0, 1))

    n_all = Y["network"]["proteins"] * (Y["network"]["proteins"] - 1) // 2 - Y["network"]["interactions"]

    def mean_curve(dim, k, all_deleted=True, embedding=None):
        """Mean over the repeats. With all_deleted, every deleted edge is a positive and every
        non-edge of Yhigh a negative, so edges cut off from the largest component stay false
        negatives until the last point (the published curves level off below 1). embedding is
        "lcc" (the largest component) or "whole" (every protein), by default as FIG5_EMBEDDING."""
        emb = embedding or FIG5_EMBEDDING[k]
        runs = [on_grid((r if emb == "lcc" else r["whole"])["grid"], FIG5_GRID) for r in Y["fig5"][f"{dim}:{k}"]]
        n = min(len(r) for r in runs)
        if all_deleted:
            x = [float(np.mean([r[i]["fp"] / n_all for r in runs])) for i in range(n)]
            y = [float(np.mean([r[i]["tp"] / k for r in runs])) for i in range(n)]
        else:
            x = [float(np.mean([r[i]["fpr"] for r in runs])) for i in range(n)]
            y = [float(np.mean([r[i]["sens"] for r in runs])) for i in range(n)]
        return with_end((x, y))

    ks = [500, 1000, 2000, 3000]
    fig5 = {dim: [mean_curve(dim, k) for k in ks] for dim in ("4", "5", "7")}
    # The dimension of Fig. 5 is not stated: draw each candidate and keep the best (a search,
    # recorded as such); the others are near-miss controls.
    region = plot_region(a.shape, cal, [(745, 285, 1220, 535)])
    pubs = pub_masks(a, EXCEL4, region)
    w = float(np.median([ft.line_width(m) for m in pubs if m.any()]))
    ex = np.zeros(a.shape[:2], bool)
    for m in pubs:
        ex |= ft.marker_mask(m, w)
    search = {dim: score_panel(pubs, series, cal, a.shape, w, ex)[0]["score"] for dim, series in fig5.items()}
    best = max(search, key=search.get)
    ours = fig5[best]
    all_lcc = [mean_curve(best, k, embedding="lcc") for k in ks]
    all_whole = [mean_curve(best, k, embedding="whole") for k in ks]
    controls = [("deletion sizes in reverse order (3000 drawn as 500)", "wrong_input", ours[::-1]),
                ("every curve from the largest component (3,000 too)", "near_miss", all_lcc),
                ("every curve from every protein (500 to 2,000 too)", "near_miss", all_whole),
                ("positives and negatives within the embedded proteins only", "near_miss",
                 [mean_curve(best, k, all_deleted=False) for k in ks])]
    controls += [(f"dimension {d} instead of {best}", "near_miss", fig5[d]) for d in fig5 if d != best]
    controls += [("y x 1.05", "near_miss", scale(ours, 1.05, ymax=1.0)),
                 ("y x 0.95", "near_miss", scale(ours, 0.95)),
                 ("x shifted by 0.01 (1% of the axis)", "near_miss", scale(ours, dx=0.01))]
    res["fig5"] = run_panel("fig5", a, cal, EXCEL4, [(745, 285, 1220, 535)], ours, controls, out)
    res["fig5"]["dimension_search"] = search
    res["fig5"]["embedding"] = {str(k): v for k, v in FIG5_EMBEDDING.items()}
    res["fig5"]["series_scores_all_lcc"] = [
        round(min(x["published_near_ours"], x["ours_near_published"]), 4)
        for x in score_panel(pubs, all_lcc, cal, a.shape, w, ex)[0]["series"]]
    res["fig5"]["series_scores_all_whole"] = [
        round(min(x["published_near_ours"], x["ours_near_published"]), 4)
        for x in score_panel(pubs, all_whole, cal, a.shape, w, ex)[0]["series"]]
    res["fig5"]["auc_range_over_repeats"] = {
        f"{k}": [min(r["auc"] for r in Y["fig5"][f"{best}:{k}"]),
                 max(r["auc"] for r in Y["fig5"][f"{best}:{k}"])] for k in ks}
    res["fig5"]["auc_range_over_repeats_every_protein"] = {
        f"{k}": [min(r["whole"]["auc"] for r in Y["fig5"][f"{best}:{k}"]),
                 max(r["whole"]["auc"] for r in Y["fig5"][f"{best}:{k}"])] for k in ks}
    FIG5 = best
    res["fig5"]["dimension"] = FIG5

    # ---- Figs S1-S3 (Matlab, one dot per pair with distance <= 0.4)
    fs = H["figS"]
    x = np.array(fs["distance"])
    yeast_mix = Y["fig1a"]

    def mix_pdf(m, xs):
        w, mu, v = (np.array(m[k]) for k in ("weights", "means", "variances"))
        return (w * np.exp(-0.5 * (xs[:, None] - mu) ** 2 / v) / np.sqrt(2 * np.pi * v)).sum(axis=1)

    ype = mix_pdf(yeast_mix["edge"], x) * 0.001
    ypn = mix_pdf(yeast_mix["nonedge"], x) * 0.999
    ypost = ype / (ype + ypn)
    for name, file, ylim, key, colour, yeast_y in [
        ("figS1", "figure-S1.png", (0, 0.12), "s1_p_edge", (0, 0, 255), ype),
        ("figS2", "figure-S2.png", (0, 1.8), "s2_p_nonedge", (255, 0, 0), ypn),
        ("figS3", "figure-S3.png", (0, 1), "s3_score", (0, 255, 0), ypost / ypost.max()),
    ]:
        a = ft.load(pub / file)
        cal = ft.matlab_axes(a, (0, 0, a.shape[1], a.shape[0]), (0, 0.4), ylim)
        y = np.array(fs[key])
        top = (cal["top"], cal["bottom"])
        ours = [(x, y)]
        controls = [("densities fitted to Yhigh instead of HumanBG", "wrong_input", [(x, yeast_y)]),
                    ("y x 1.05", "near_miss", scale(ours, 1.05)),
                    ("y x 0.95", "near_miss", scale(ours, 0.95)),
                    ("x shifted by 0.004 (1% of the axis)", "near_miss", scale(ours, dx=0.004))]
        if key == "s3_score":
            controls.append(("posterior not divided by its maximum", "near_miss",
                             [(x, np.array(fs["s3_posterior"]))]))
        res[name] = run_panel(name, a, cal, [colour], [], ours, controls, out, smooth=False,
                              clip=top, dots=True, open_px=1)
    json.dump(res, open(out / "figures.json", "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:5])
