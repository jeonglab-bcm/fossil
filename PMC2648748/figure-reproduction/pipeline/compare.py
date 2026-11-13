"""Compare our Figs 2 and 3 with the published ones: values, pixels and the claims of the text.

usage: compare.py PUBLISHED_VALUES SUMMARY RENDER_DIR PUBLISHED_DIR OUT_JSON

* Values. Fig. 2: each bar (power, %) against the bar read off the published figure, within Monte
  Carlo error: |ours - paper| <= 1.96 sqrt(2 p (1 - p) / 100) with p = (paper + ours + 1) / 202
  (two independent sets of 100 data sets; the +1 keeps the band open at 0 and 100). Fig. 3: each
  box's median against the published median, within 1.96 sqrt(2) times the standard error of a
  median of 100 values (1.2533 sigma / 10, sigma from our interquartile range / 1.349), plus 0.5
  for reading the published median.
* Pixels. Each figure is compared inside its six frames (4 px in from the frame lines; the legend
  of Fig. 2 and the BEAM bars, which we did not run, masked) after aligning each of our frames on
  the published one. Ink is grey < 60 (outlines, medians, whiskers, outliers; the grey bar fills
  are not ink). Score: the smaller of the shares of published ink within 2 px of ours and of our
  ink within 2 px of the published. The same score for the negative controls drawn by render.R
  (wrong model or r^2; values shifted by 5 power points or 2 SNPs). Pass mark: halfway between
  the best control and 100%.
* Claims. Each statement of the text about Figs 2 and 3, computed on the published values
  (the arithmetic check) and on ours.

Also writes the overlays fig2_overlay.png and fig3_overlay.png into RENDER_DIR: the published
figure in dark ink, ours in green.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from read_published import frames, load  # noqa: E402

MAFS = (0.05, 0.1, 0.2, 0.5)
MAF_TXT = ("0.05", "0.10", "0.20", "0.50")
METHODS = ("epiforest", "beam", "lr", "chisq")
PANELS = [(m, r2) for r2 in (0.7, 1.0) for m in (1, 2, 3)]
INK = 60
TOL_PX = 2


def setting_name(model, r2, maf_i):
    return f"Model {model}, r2 = {r2:.1f}, MAF {MAF_TXT[maf_i]}"


def mc_tol(paper, ours):
    p = (paper + ours + 1) / 202
    return round(100 * 1.96 * math.sqrt(2 * p * (1 - p) / 100), 3)


def fmt_median(v):
    r = round(v * 2) / 2
    return f"{r:g}"


# ---------------------------------------------------------------- values

def fig2_values(pub, summ):
    out = {}
    for mi, meth in enumerate(METHODS):
        if meth == "beam":
            continue
        fields = []
        for p, (model, r2) in enumerate(PANELS):
            ours_panel = summ["panels"][p]["power"]
            for g in range(4):
                bar = next(b for b in pub["fig2"][p]["bars"] if b["maf_index"] == g and b["method_index"] == mi)
                obs = ours_panel[mi][g] if ours_panel else None
                f = {"name": setting_name(model, r2, g), "expected": str(bar["count"]),
                     "observed": obs, "read": bar["value"]}
                if obs is not None:
                    f["tolerance"] = {"abs": mc_tol(bar["count"], obs)}
                fields.append(f)
        out[meth] = fields
    return out


def fig3_values(pub, summ):
    fields = []
    for p, (model, r2) in enumerate(PANELS):
        for g in range(4):
            box = pub["fig3"][p]["boxes"][g]
            ks = summ["panels"][p]["selected"][g]
            f = {"name": setting_name(model, r2, g), "expected": fmt_median(box["median"]), "read": box["median"]}
            if ks:
                a = np.array(ks, float)
                q1, q3 = np.percentile(a, [25, 75])
                sigma = max((q3 - q1) / 1.349, 1.0)
                se = 1.2533 * sigma / math.sqrt(len(a))
                f["observed"] = float(np.median(a))
                f["tolerance"] = {"abs": round(1.96 * math.sqrt(2) * se + 0.5, 3)}
            else:
                f["observed"] = None
            fields.append(f)
    return fields


# ---------------------------------------------------------------- pixels

def masks(pub_img, kind, pub_values):
    """Scoring mask (inside frames, minus legend and BEAM bars) in published coordinates."""
    m = np.zeros(pub_img.shape, bool)
    for p, (x0, y0, x1, y1) in enumerate(frames(pub_img)):
        m[int(y0) + 4:int(y1) - 3, int(x0) + 4:int(x1) - 3] = True
        if kind == "fig2":
            unit = (x1 - x0) / (19 * 1.08)
            for b in pub_values["fig2"][p]["bars"]:
                if b["method_index"] == 1:            # BEAM
                    xc = b["x_px"]
                    m[:, int(xc - 0.5 * unit - 3):int(xc + 0.5 * unit + 4)] &= False
            if p == 0:                                 # the legend box (with a margin)
                lg = pub_img[int(y0) + 3:int(y1) - 3, int(x0) + 100:int(x1) - 3] < INK
                rows = np.where(lg.any(axis=1))[0]
                cols = np.where(lg.any(axis=0))[0]
                top = int(y0) + 3 + rows.min() - 6
                bottom = int(y0) + 3 + rows[rows < 200].max() + 6
                m[top:bottom, int(x0) + 100 + cols.min() - 6:int(x0) + 100 + cols[cols < 470].max() + 6] = False
    return m


def aligned(ours_img, pub_img):
    """Shift each of our frames onto the published one (integer pixels)."""
    out = np.full(pub_img.shape, 255.0)
    fp, fo = frames(pub_img), frames(ours_img)
    shifts = []
    for (px0, py0, px1, py1), (ox0, oy0, ox1, oy1) in zip(fp, fo):
        dx, dy = int(round(px0 - ox0)), int(round(py0 - oy0))
        shifts.append((dx, dy))
        # copy the panel region (frame plus 80 px around) from ours, shifted
        ys, ye = int(py0) - 80, int(py1) + 80
        xs, xe = int(px0) - 170, int(px1) + 50
        src = ours_img[max(0, ys - dy):ye - dy, max(0, xs - dx):xe - dx]
        out[max(0, ys):max(0, ys) + src.shape[0], max(0, xs):max(0, xs) + src.shape[1]] = src
    return out, shifts


def score(pub_img, ours_img, mask):
    A = (pub_img < INK) & mask
    B = (ours_img < INK) & mask
    if not A.any() or not B.any():
        return 0.0, 0.0
    dB = ndimage.distance_transform_edt(~B)
    dA = ndimage.distance_transform_edt(~A)
    return float((dB[A] <= TOL_PX).mean()), float((dA[B] <= TOL_PX).mean())


def overlay(pub_img, ours_img, path):
    pub_ink = pub_img < 128
    our_ink = ours_img < 128
    rgb = np.full(pub_img.shape + (3,), 255, np.uint8)
    rgb[pub_ink] = (40, 50, 48)
    rgb[our_ink & ~pub_ink] = (60, 170, 110)
    rgb[our_ink & pub_ink] = (20, 100, 70)
    Image.fromarray(rgb).save(path, optimize=True)


def pixel_item(kind, pub_path, render_dir, pub_values, controls):
    pub_img = load(pub_path)
    mask = masks(pub_img, kind, pub_values)
    ours_raw = load(Path(render_dir) / f"{kind}_ours.png")
    ours, shifts = aligned(ours_raw, pub_img)
    s1, s2 = score(pub_img, ours, mask)
    overlay(pub_img, ours, Path(render_dir) / f"{kind}_overlay.png")
    ctrl = []
    for name, ck, fname in controls:
        c, _ = aligned(load(Path(render_dir) / "controls" / fname), pub_img)
        a, b = score(pub_img, c, mask)
        ctrl.append({"name": name, "kind": ck, "score": round(min(a, b), 6)})
    best = max(c["score"] for c in ctrl)
    return {"tolerance_px": TOL_PX, "dpi": 200, "published_near_ours": round(s1, 6),
            "ours_near_published": round(s2, 6), "threshold": round(best + (1 - best) / 2, 6),
            "controls": ctrl, "frame_shifts_px": shifts, "masked_px": int((~mask).sum())}


# ---------------------------------------------------------------- claims

def claims(power, ks):
    """The text's statements about Figs 2 and 3, as fields computed from a power table.

    power[(model, r2, maf_i)][method] in percent; ks[(model, r2, maf_i)] list of selected counts
    (None for the published figure, which gives medians and maxima instead)."""
    def tol(a, b):
        return mc_tol(a, b)

    def similar(a, b):
        return abs(a - b) <= tol(a, b)

    out = {}
    m1 = [power[(1, r2, g)] for r2 in (0.7, 1.0) for g in range(4)]
    out["model1_similar"] = all(similar(x["epiforest"], x["lr"]) and similar(x["epiforest"], x["chisq"])
                                and similar(x["lr"], x["chisq"]) for x in m1)
    for model in (2, 3):
        sm = [power[(model, 1.0, g)] for g in (0, 1)]
        out[f"model{model}_epiforest_above_small_maf"] = all(
            x["epiforest"] > x["lr"] and x["epiforest"] > x["chisq"] for x in sm)
        out[f"model{model}_chisq_lowest_small_maf"] = all(
            x["chisq"] <= min(x["epiforest"], x["lr"]) for x in sm)
    allp = list(power.values())
    out["epiforest_comparable_to_lr"] = all(x["epiforest"] >= x["lr"] - tol(x["epiforest"], x["lr"]) for x in allp)
    out["epiforest_sometimes_higher_than_lr"] = any(x["epiforest"] > x["lr"] + tol(x["epiforest"], x["lr"]) for x in allp)
    out["epiforest_not_below_chisq"] = all(x["epiforest"] >= x["chisq"] - tol(x["epiforest"], x["chisq"]) for x in allp)
    out["epiforest_sometimes_higher_than_chisq"] = any(x["epiforest"] > x["chisq"] + tol(x["epiforest"], x["chisq"]) for x in allp)
    n_ge = sum(1 for x in allp if x["epiforest"] >= x["lr"])
    out["epiforest_at_least_lr_settings"] = n_ge
    return out


def yes(b):
    return "yes" if b else "no"


def main():
    pub_values, summary, render_dir, pub_dir, outp = sys.argv[1:6]
    pub = json.loads(Path(pub_values).read_text())
    summ = json.loads(Path(summary).read_text())
    res = {"fig2": {}, "fig3": {}}
    res["fig2"]["values"] = fig2_values(pub, summ)
    res["fig3"]["medians"] = fig3_values(pub, summ)
    res["fig2"]["pixels"] = pixel_item("fig2", Path(pub_dir) / "figure-2.png", render_dir, pub, [
        ("each panel with the next model's powers", "wrong_input", "fig2_wrong_model.png"),
        ("each panel with the other r2's powers", "wrong_input", "fig2_wrong_r2.png"),
        ("powers 5 points higher", "near_miss", "fig2_plus5.png"),
        ("powers 5 points lower", "near_miss", "fig2_minus5.png")])
    res["fig3"]["pixels"] = pixel_item("fig3", Path(pub_dir) / "figure-3.png", render_dir, pub, [
        ("each panel with the next model's counts", "wrong_input", "fig3_wrong_model.png"),
        ("counts 2 higher", "near_miss", "fig3_plus2.png"),
        ("counts 2 lower", "near_miss", "fig3_minus2.png")])

    # claims on the published values (arithmetic check) and on ours
    pubp, ourp = {}, {}
    for p, (model, r2) in enumerate(PANELS):
        for g in range(4):
            bars = {b["method_index"]: b["count"] for b in pub["fig2"][p]["bars"] if b["maf_index"] == g}
            pubp[(model, r2, g)] = {"epiforest": bars[0], "beam": bars[1], "lr": bars[2], "chisq": bars[3]}
            op = summ["panels"][p]["power"]
            if op and op[0][g] is not None:
                ourp[(model, r2, g)] = {"epiforest": op[0][g], "lr": op[2][g], "chisq": op[3][g]}
    pub_medians = [b["median"] for p in pub["fig3"] for b in p["boxes"]]
    pub_max = [b["max"] for p in pub["fig3"] for b in p["boxes"]]
    cl = {"paper": claims(pubp, None), "ours": claims(ourp, None) if len(ourp) == 24 else None}
    cl["paper"]["beam_epiforest_above_lr_chisq"] = all(
        v["beam"] >= v["lr"] - mc_tol(v["beam"], v["lr"]) for v in pubp.values())
    cl["paper"]["fig3_median_of_medians"] = float(np.median(pub_medians))
    cl["paper"]["fig3_medians_range"] = [min(pub_medians), max(pub_medians)]
    cl["paper"]["fig3_max_below_80_settings"] = sum(1 for v in pub_max if v < 80)
    if cl["ours"] is not None:
        all_k = [k for s in summ["settings"] for k in s["selected"]]
        meds = [s["selected_median"] for s in summ["settings"]]
        cl["ours"]["fig3_median_of_medians"] = float(np.median(meds))
        cl["ours"]["fig3_medians_range"] = [min(meds), max(meds)]
        cl["ours"]["fig3_pooled_median"] = float(np.median(all_k))
        cl["ours"]["fig3_max_below_80_settings"] = sum(1 for s in summ["settings"] if s["selected_max"] < 80)
        cl["ours"]["selected_median_below_100"] = float(np.median(all_k)) < 100
    res["claims"] = cl
    Path(outp).write_text(json.dumps(res, indent=1, default=lambda o: o if not isinstance(o, np.generic) else o.item()))
    print(f"wrote {outp}")


if __name__ == "__main__":
    main()
