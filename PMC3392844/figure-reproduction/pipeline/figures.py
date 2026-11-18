"""Draw our ROC curves of Figs 2-4 on the published frames and score them against the published curves.

Usage: figures.py PUBLISHED_DIR CURVES.json ROCS.json OUT_DIR

PUBLISHED_DIR holds fig2.png ... fig4.png, the paper's figures cropped from its PDF at 600 dpi.
CURVES.json is published_curves.json (the published curves read from the PDF's vector paths); ROCS.json
is our curves (evaluate.py). For each figure it writes:
  figN_ours.png     the published figure with its curves removed and ours drawn in their colours and dashes
  figN_overlay.png  red channel the published figure, green and blue ours: cyan is ink only in the paper,
                    red ink only in ours, black both
and figures.json: the share of published curve pixels within 2 px of ours and of ours within 2 px of the
published (each curve against its own counterpart), the same for the negative controls, and the TPR of
each curve at a few FPRs, published and ours.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_published import DPI, FIGURES  # noqa: E402

TOL = 2  # px at 600 dpi (0.085 mm)
FPR_POINTS = [0.01, 0.05, 0.1, 0.2, 0.5]
SOURCE = {"fig2": ("svm", "all"), "fig3": ("svm", "50+"), "fig4": ("alg", "all")}
ALG = {"svm": "svm:chem+bio+pheno", "rf": "rf:chem+bio+pheno", "knn": "knn:chem+bio+pheno",
       "nb": "nb:chem+bio+pheno", "lr": "lr:chem+bio+pheno"}


def model_of(fig, curve):
    return ALG[curve] if SOURCE[fig][0] == "alg" else f"svm:{curve}"


def to_px(fig, frame, fpr, tpr):
    bx0, by0 = FIGURES[fig]["box"][:2]
    x0, y0, x1, y1 = frame
    s = DPI / 72.0
    X = (x0 + np.asarray(fpr) * (x1 - x0) - bx0) * s
    Y = (y1 - np.asarray(tpr) * (y1 - y0) - by0) * s
    return np.c_[X, Y]


def mask(size, pts, width_px):
    im = Image.new("1", size, 0)
    ImageDraw.Draw(im).line([tuple(p) for p in pts], fill=1, width=max(1, int(round(width_px))))
    return np.array(im, dtype=bool)


def shares(pub, ours):
    """Share of pub pixels within TOL of ours, and of ours within TOL of pub."""
    d_ours = distance_transform_edt(~ours)
    d_pub = distance_transform_edt(~pub)
    a = (d_ours[pub] <= TOL).mean() if pub.any() else 0.0
    b = (d_pub[ours] <= TOL).mean() if ours.any() else 0.0
    return float(a), float(b)


def pooled(pairs):
    """Pool per-curve pixel counts: (sum of pub pixels near ours) / (all pub pixels), and the reverse."""
    na = sum(p.sum() * a for p, o, a, b in pairs)
    nb = sum(o.sum() * b for p, o, a, b in pairs)
    return float(na / sum(p.sum() for p, o, a, b in pairs)), float(nb / sum(o.sum() for p, o, a, b in pairs))


def score(fig, frame, pub_curves, our_curves, size, width_px):
    pairs = []
    per = {}
    for name in pub_curves:
        P = mask(size, to_px(fig, frame, *pub_curves[name]), width_px)
        O = mask(size, to_px(fig, frame, *our_curves[name]), width_px)
        a, b = shares(P, O)
        pairs.append((P, O, a, b))
        per[name] = {"published_near_ours": round(a, 6), "ours_near_published": round(b, 6)}
    pn, op = pooled(pairs)
    return round(pn, 6), round(op, 6), per


def dash_style(d):
    if not d:
        return "-"
    return (0, [float(x) for x in d.split()])


def render(fig, frame, pub_png, pub_curves_raw, ours, width_pt, out_ours, out_overlay):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    matplotlib.rcParams["lines.scale_dashes"] = False
    base = np.array(Image.open(pub_png).convert("RGB"))
    H, W = base.shape[:2]
    s = DPI / 72.0
    # Remove the published curves: their pixels (dilated), outside the axes' frame lines.
    erase = np.zeros((H, W), bool)
    for name, c in pub_curves_raw.items():
        erase |= mask((W, H), to_px(fig, frame, c["fpr"], c["tpr"]), width_pt * s)
    erase = binary_dilation(erase, iterations=4)
    fx0, fy0 = to_px(fig, frame, [0], [1])[0]
    fx1, fy1 = to_px(fig, frame, [1], [0])[0]
    yy, xx = np.mgrid[0:H, 0:W]
    near_frame = (np.abs(xx - fx0) <= 4) | (np.abs(xx - fx1) <= 4) | (np.abs(yy - fy0) <= 4) | (np.abs(yy - fy1) <= 4)
    clean = base.copy()
    clean[erase & ~near_frame] = 255
    f = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    ax = f.add_axes([0, 0, 1, 1])
    ax.imshow(clean, interpolation="none", extent=(0, W, H, 0))
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    for name, c in pub_curves_raw.items():
        P = to_px(fig, frame, *ours[name])
        col = [float(v.strip(" %")) / 100 for v in c["stroke"][4:-1].split(",")]
        ax.plot(P[:, 0], P[:, 1], color=col, linewidth=width_pt, linestyle=dash_style(c["dash"]), solid_capstyle="butt")
    f.savefig(out_ours, dpi=DPI)
    plt.close(f)
    ours_img = np.array(Image.open(out_ours).convert("L"))
    pub_l = np.array(Image.open(pub_png).convert("L"))
    Image.fromarray(np.dstack([pub_l, ours_img, ours_img]).astype(np.uint8)).save(out_overlay)


def main():
    pub_dir, curves_f, rocs_f, out = map(Path, sys.argv[1:5])
    out.mkdir(parents=True, exist_ok=True)
    pubc = json.load(open(curves_f))
    rocs = json.load(open(rocs_f))
    grid = np.array(rocs["grid"])
    res = {"tolerance_px": TOL, "dpi": DPI, "figures": {}}
    for fig in ("fig2", "fig3", "fig4"):
        spec = FIGURES[fig]
        frame = pubc[fig]["frame_pt"]
        part = SOURCE[fig][1]
        width_pt = float(spec["width"])
        width_px = width_pt * DPI / 72.0
        size = Image.open(pub_dir / f"{fig}.png").size
        pub = {k: (np.array(v["fpr"]), np.array(v["tpr"])) for k, v in pubc[fig]["curves"].items()}
        ours = {k: (grid, np.array(rocs["curves"][model_of(fig, k)][part])) for k in pub}
        pn, op, per = score(fig, frame, pub, ours, size, width_px)
        controls = []
        # Wrong input: every curve replaced by the next series' curve (a derangement of the legend).
        names = list(pub)
        shifted = {k: ours[names[(i + 1) % len(names)]] for i, k in enumerate(names)}
        a, b, _ = score(fig, frame, pub, shifted, size, width_px)
        controls.append({"name": "each curve drawn from the next series of the legend", "kind": "wrong_input", "score": min(a, b)})
        # Wrong input: the other ADR set (all ADRs for Fig. 3, ADR_50+ for Figs 2 and 4).
        other = "50+" if part == "all" else "all"
        swapped = {k: (grid, np.array(rocs["curves"][model_of(fig, k)][other])) for k in pub}
        a, b, _ = score(fig, frame, pub, swapped, size, width_px)
        controls.append({"name": f"the same models over {'ADR_50+' if other == '50+' else 'all ADRs'}", "kind": "wrong_input", "score": min(a, b)})
        # Near misses: our curves moved by 1% of the axis.
        for nm, dx, dy in (("TPR - 0.01", 0, -0.01), ("TPR + 0.01", 0, 0.01), ("FPR + 0.01", 0.01, 0), ("FPR - 0.01", -0.01, 0)):
            moved = {k: (np.clip(v[0] + dx, 0, 1), np.clip(v[1] + dy, 0, 1)) for k, v in ours.items()}
            a, b, _ = score(fig, frame, pub, moved, size, width_px)
            controls.append({"name": f"ours with {nm}", "kind": "near_miss", "score": min(a, b)})
        render(fig, frame, pub_dir / f"{fig}.png", pubc[fig]["curves"], ours, width_pt, out / f"{fig}_ours.png", out / f"{fig}_overlay.png")
        at = {}
        for k in pub:
            at[k] = {f"{x}": {"published": round(float(np.interp(x, *pub[k])), 6), "ours": round(float(np.interp(x, *ours[k])), 6)} for x in FPR_POINTS}
        tpr_fields = [{"name": f"{k} at FPR {x}", "expected": f"{at[k][f'{x}']['published']:.2f}", "observed": at[k][f"{x}"]["ours"]}
                      for k in pub for x in FPR_POINTS]
        res["figures"][fig] = {"tpr_fields": tpr_fields, "published_near_ours": pn, "ours_near_published": op, "per_curve": per,
                               "controls": controls, "tpr_at_fpr": at,
                               "curve_auc_published": {k: round(float(np.trapezoid(v[1], v[0])), 6) for k, v in pub.items()}}
        print(fig, pn, op, [c["score"] for c in controls], file=sys.stderr)
    (out / "figures.json").write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
