"""Which of our summary statistics each published bar and curve shows (shared by render.py and
compare.py).

Figs 1 and 2: five groups (0-4 SNPs in LD), eight bars per group in the published order
  RF0:IM0 n, RF0:IM0 r, RF1:IM0 n, RF1:IM0 r, RF0:IM1 n, RF0:IM1 r, RF1:IM1 n, RF1:IM1 r
where "n" is LD model n<k> (k LD.nSNPs per SNP 97-100) and "r" is r<k> (k LD.rSNPs per rSNP); with
k = 0 both are n0.
Figs 4 and 5: eleven groups (r^2 = 0, 0.1, ..., 1), bars rSNP, rHAP, PRED.rHAP.
"""

PRIMARY_RULE = "empirical_ratio"
BAR_ORDER = [("RF0:IM0", "n"), ("RF0:IM0", "r"), ("RF1:IM0", "n"), ("RF1:IM0", "r"),
             ("RF0:IM1", "n"), ("RF0:IM1", "r"), ("RF1:IM1", "n"), ("RF1:IM1", "r")]
R2 = [f"{0.1 * i:.1f}" for i in range(11)]
HAP_ORDER = ["SNP", "HAP", "PRED"]

# Legends of the curve panels, in data units (x0, y0, x1, y1), read from the figures: kept from
# the published image when ours is drawn.
LEGENDS = {
    "fig3.a.left": (44, 0.15, 103, 0.72), "fig3.a.right": (44, 0.15, 103, 0.72),
    "fig3.b.left": (44, 0.1, 103, 0.53), "fig3.b.right": (44, 0.1, 103, 0.53),
    "fig3.c.left": (44, -0.02, 103, 0.32), "fig3.c.right": (44, -0.02, 103, 0.32),
    "fig6.a.left": (82, -0.02, 103, 0.47), "fig6.a.right": (82, -0.02, 103, 0.47),
    "fig6.b.left": (82, -0.02, 103, 0.47), "fig6.b.right": (82, -0.02, 103, 0.47),
    "fig6.c.left": (73, 0.02, 103, 0.27), "fig6.c.right": (73, 0.02, 103, 0.27),
}


def ld_model(kind, k):
    return "n0" if k == 0 else f"{kind}{k}"


def bar_series(fig, summ):
    """Our values (and error half-lengths for Figs 1 and 4) in the published bar order."""
    vals, errs = [], []
    if fig in ("fig1", "fig2"):
        for k in range(5):
            gv, ge = [], []
            for combo, kind in BAR_ORDER:
                s = summ["snp"][ld_model(kind, k)][combo]
                gv.append(s["mean_im"] if fig == "fig1" else s["above_noise"])
                ge.append(ERROR_BAR_Z * s["se_im"] if fig == "fig1" else None)
            vals.append(gv)
            errs.append(ge)
    else:
        hap = summ["hap"][PRIMARY_RULE]
        for r2 in R2:
            gv, ge = [], []
            for coding in HAP_ORDER:
                s = hap[r2][coding]
                gv.append(s["mean_im"] if fig == "fig4" else s["above_noise"])
                ge.append(ERROR_BAR_Z * s["se_im"] if fig == "fig4" else None)
            vals.append(gv)
            errs.append(ge)
    return vals, (errs if fig in ("fig1", "fig4") else None)


# The paper does not say what its error bars show. Ours are 95% intervals of the mean (1.96 SE);
# compare.py measures the ratio of the published half-lengths to our SE.
ERROR_BAR_Z = 1.96


def curve(summ, fig, panel_id, name):
    """(x values, proportions) of one published curve, from our summary."""
    if fig == "fig3":
        snp = summ["snp"]
        k = 1 if panel_id.endswith("left") else 4
        if panel_id.startswith("fig3.a"):
            combo = "RF0:IM0" if panel_id.endswith("left") else "RF0:IM1"
            ld = name
            ys = snp[ld][combo]["top_any"]
        elif panel_id.startswith("fig3.b"):
            if name.startswith("n0"):
                ys = snp["n0"]["RF0:IM1"]["top_r"]
            elif "LD.rSNPs" in name and "/" in name:
                ys = snp[f"r{k}"]["RF0:IM1"]["top_any"]
            else:
                ys = snp[f"r{k}"]["RF0:IM1"]["top_r"]
        else:
            if name.startswith("n0"):
                ys = snp["n0"]["RF0:IM0"]["top_r"]
            else:
                ys = snp[f"r{k}"][name]["top_any"]
        x0 = 4
    else:
        hap = summ["hap"][PRIMARY_RULE]
        if panel_id.startswith("fig6.c"):
            r2 = "0.0" if panel_id.endswith("left") else "0.9"
            key = {"SNP": "SNP", "BEST.SNP": "BEST.SNP", "HAP": "HAP", "PRED.HAP": "PRED"}[name]
        else:
            r2 = name.split("=")[1]
            key = {"fig6.a.left": "SNP", "fig6.a.right": "BEST.SNP", "fig6.b.left": "HAP",
                   "fig6.b.right": "PRED"}[panel_id]
        ys = hap[r2][key]["top"]
        x0 = 8 if key == "SNP" else 4
    xs = list(range(1, len(ys) + 1))
    keep = [i for i, x in enumerate(xs) if x0 <= x <= 100]
    return [xs[i] for i in keep], [ys[i] for i in keep]


def curve_series(fig, summ, pub):
    """For render.py: per panel, a list of (name, colour, xs, ys); also sets each panel's legend
    box in pixels."""
    out = []
    for panel in pub["panels"]:
        px = panel["px"]
        x0, y0, x1, y1 = LEGENDS[panel["id"]]
        top, bottom, left, right = panel["box"]
        bx0 = int(max(left + 2, px["ax"] * x0 + px["bx"]))
        bx1 = int(min(right - 2, px["ax"] * x1 + px["bx"]))
        by0 = int(max(top + 2, px["ay"] * y1 + px["by"]))
        by1 = int(min(bottom - 2, px["ay"] * y0 + px["by"]))
        panel["legend_box_px"] = [bx0, by0, bx1, by1]
        series = []
        for name, colour in zip(panel["series"], panel["colours"]):
            xs, ys = curve(summ, fig, panel["id"], name)
            series.append((name, colour, xs, ys))
        out.append(series)
    return out
