"""Figs 2, 3 and 7: expression profiles redrawn from the public data on the published pixel grid and scored.

Fig. 2: GDS3702 (rat pineal gland), probes 1367526_at (Mrps26) and 1367970_at (Pfn2), the 12 samples in
GEO's order. Fig. 3: Cheng and Church's yeast matrix (ref. 25), YBL002W, YBL003C and YBL006C (the figure
labels it YBL006W), 17 conditions. Fig. 7: the first three values of YBL003C, 343, 314 and 409.

Usage: profile_figures.py DOWNLOADS PUBLISHED_DIR OUTDIR
Writes OUTDIR/profiles.json and OUTDIR/figures/fig{2,3,7}_{ours,overlay}.png.
"""
import gzip, json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figscore as fs
import gecon

BORDER = 12  # px along the frame left out of the score: tick marks are there
# Line widths and marker sizes (px at the published 1200-px width) are presentation settings, chosen from
# 1-5 px and 16-24 px by the combined score; they are listed in results_notes.json as such.


def gds_rows(path):
    rows, order, inside = {}, [], False
    with gzip.open(path, "rt", encoding="latin-1") as f:
        for line in f:
            if line.startswith("!dataset_table_begin"):
                inside = True
                next(f)
                continue
            if line.startswith("!dataset_table_end"):
                break
            if inside:
                p = line.rstrip("\n").split("\t")
                rows[p[0]] = (p[1], p[2:])
                order.append(p[0])
    return rows, order


def yeast(downloads):
    genes = [l.strip() for l in open(os.path.join(downloads, "yeast.genes"))]
    X = np.loadtxt(os.path.join(downloads, "yeast.matrix"))
    return genes, X


def classify(img, kind):
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    mx, mn = img.max(2), img.min(2)
    if kind == "red":
        return (r - g > 60) & (r > 110) & (r - b > 50)
    if kind == "black":
        return (mx < 110) & (mx - mn < 40)
    if kind == "navy":
        return (b - r > 35) & (b > 60) & (r < 110)
    if kind == "brown":
        return (r - b > 35) & (r > 90) & (g < 120)
    if kind == "blue":
        return (b - r > 12) & (b - g > 12) & (img.mean(2) < 175) & (b - r < 70) & (r >= g)  # the dashed arcs are greener
    raise ValueError(kind)


SPECS = {
    "fig2": {
        "file": "fig2.jpg", "xlim": (1, 12), "ylim": (50, 500), "xticks": [2, 4, 6, 8, 10, 12], "yticks": list(range(50, 501, 50)),
        "legend": (805, 1150, 90, 235),
        "series": [
            {"name": "Mrps26", "key": "1367526_at", "class": "red", "colour": (200, 0, 0), "width": 5, "marker": "*", "msize": 20},
            {"name": "Pfn2", "key": "1367970_at", "class": "black", "colour": (0, 0, 0), "width": 5, "marker": "o", "msize": 20},
        ],
    },
    "fig3": {
        "file": "fig3.jpg", "xlim": (1, 17), "ylim": (200, 500), "xticks": list(range(2, 17, 2)), "yticks": list(range(200, 501, 50)),
        "legend": (880, 1165, 64, 210),
        "series": [
            {"name": "YBL002W", "key": "YBL002W", "class": "brown", "colour": (160, 40, 40), "width": 2, "marker": "o", "msize": 16},
            {"name": "YBL003C", "key": "YBL003C", "class": "navy", "colour": (0, 0, 140), "width": 2, "marker": "*", "msize": 16},
            {"name": "YBL006W (YBL006C in the data)", "key": "YBL006C", "class": "black", "colour": (0, 0, 0), "width": 2, "marker": "d", "msize": 16},
        ],
    },
    "fig7": {
        "file": "fig7.jpg", "xlim": (1, 3), "ylim": (300, 420), "xticks": [1.5, 2, 2.5], "yticks": list(range(320, 401, 20)),
        "legend": None,
        "series": [{"name": "G = {343, 314, 409}", "key": "YBL003C:3", "class": "blue", "colour": (40, 40, 200), "width": 3, "marker": None, "msize": 0}],
    },
}


def series_values(fig, key, gds, ygenes, Y):
    if fig == "fig2":
        return np.array([float(v) for v in gds[0][key][1]])
    if key.endswith(":3"):
        return Y[ygenes.index(key.split(":")[0])][:3]
    return Y[ygenes.index(key)]


def neighbours(fig, key, gds, ygenes):
    """The rows next to `key` in the source file: wrong-input controls."""
    if fig == "fig2":
        order = gds[1]
        i = order.index(key)
        return [order[i - 1], order[i + 1]]
    base = key.split(":")[0]
    i = ygenes.index(base)
    return [ygenes[i - 1] + (":3" if ":" in key else ""), ygenes[i + 1] + (":3" if ":" in key else "")]


def region_mask(shape, box, legend):
    x0, x1, y0, y1 = box
    m = np.zeros(shape[:2], bool)
    m[int(y0) + BORDER: int(y1) - BORDER, int(x0) + BORDER: int(x1) - BORDER] = True
    if legend:
        lx0, lx1, ly0, ly1 = legend
        m[ly0:ly1, lx0:lx1] = False
    return m


def draw(shape, mp, spec, values_list):
    masks = []
    for s, vals in zip(spec["series"], values_list):
        x = np.arange(1, len(vals) + 1)
        px, py = mp(x, vals)
        c = fs.draw_series(shape, list(zip(px, py)), width=s["width"], marker=s["marker"], msize=s["msize"])
        masks.append(np.asarray(c) < 128)
    return masks


def run(fig, downloads, pubdir, outdir, gds, ygenes, Y):
    spec = SPECS[fig]
    img = fs.load_rgb(os.path.join(pubdir, spec["file"]))
    mp = fs.Mapping(img, spec["xlim"], spec["ylim"], spec["xticks"], spec["yticks"])
    region = region_mask(img.shape, mp.box, spec["legend"])
    pub = [classify(img, s["class"]) & region for s in spec["series"]]
    vals = [series_values(fig, s["key"], gds, ygenes, Y) for s in spec["series"]]
    ours = [m & region for m in draw(img.shape, mp, spec, vals)]
    pub_all, our_all = np.logical_or.reduce(pub), np.logical_or.reduce(ours)
    res = {"mapping": mp.info(), "tolerance_px": fs.TOL, "series": {}, "values": {}}
    for s, p, o, v in zip(spec["series"], pub, ours, vals):
        res["series"][s["name"]] = fs.score(p, o)
        res["values"][s["name"]] = [float(x) for x in v]
    res["combined"] = fs.score(pub_all, our_all)
    # controls: replace one series at a time by a wrong input or a near miss, and score the whole figure again
    controls = []
    yr = spec["ylim"][1] - spec["ylim"][0]
    def ctrl(name, kind, vl):
        om = np.logical_or.reduce([m & region for m in draw(img.shape, mp, spec, vl)])
        controls.append({"name": name, "kind": kind, "score": fs.score(pub_all, om)["score"]})
    # wrong input: one series replaced by the row before or after it in the source file
    for k, s in enumerate(spec["series"]):
        for nb in neighbours(fig, s["key"], gds, ygenes):
            vl = list(vals)
            vl[k] = series_values(fig, nb, gds, ygenes, Y)
            ctrl(f"{s['name']} -> {nb.split(':')[0]}", "wrong_input", vl)
    # near misses: every series at once
    ctrl("amplitude x1.05", "near_miss", [v.mean() + 1.05 * (v - v.mean()) for v in vals])
    ctrl("amplitude x0.95", "near_miss", [v.mean() + 0.95 * (v - v.mean()) for v in vals])
    ctrl("shifted +1% of the y range", "near_miss", [v + 0.01 * yr for v in vals])
    ctrl("shifted -1% of the y range", "near_miss", [v - 0.01 * yr for v in vals])
    res["controls"] = controls
    os.makedirs(os.path.join(outdir, "figures"), exist_ok=True)
    fs.save_ours(img, pub_all, [(o, s["colour"]) for o, s in zip(ours, spec["series"])], os.path.join(outdir, "figures", f"{fig}_ours.png"))
    fs.save_overlay(img, pub_all, our_all, os.path.join(outdir, "figures", f"{fig}_overlay.png"))
    return res


def main():
    downloads, pubdir, outdir = sys.argv[1:4]
    gds = gds_rows(os.path.join(downloads, "GDS3702.soft.gz"))
    ygenes, Y = yeast(downloads)
    out = {}
    for fig in ("fig2", "fig3", "fig7"):
        out[fig] = run(fig, downloads, pubdir, outdir, gds, ygenes, Y)
        print(fig, out[fig]["combined"], {k: v["score"] for k, v in out[fig]["series"].items()},
              "best control", max(c["score"] for c in out[fig]["controls"]), flush=True)
    # Fig. 7 as values: Eq. (4) and (5) on G = {343, 314, 409}
    r, a = gecon.edge_patterns(out["fig7"]["values"]["G = {343, 314, 409}"])
    out["fig7_values"] = {"angles": [round(float(x), 4) for x in a], "angles_printed_precision": [f"{x:.0f}" for x in a],
                          "regulation": [int(x) for x in r]}
    # the sign GeCON gives the pairs of Figs 2 and 3 (theta 0.5, tau 20)
    pairs = {}
    v2 = out["fig2"]["values"]
    s = gecon.supports(np.array([v2["Mrps26"], v2["Pfn2"]]))
    pairs["fig2 Mrps26-Pfn2"] = {"pos": round(float(s.pos[0, 1]), 4), "neg": round(float(s.neg[0, 1]), 4)}
    v3 = out["fig3"]["values"]
    names = list(v3)
    s = gecon.supports(np.array([v3[n] for n in names]))
    for i in range(3):
        for j in range(i + 1, 3):
            pairs[f"fig3 {names[i].split()[0]}-{names[j].split()[0]}"] = {"pos": round(float(s.pos[i, j]), 4), "neg": round(float(s.neg[i, j]), 4)}
    out["supports"] = pairs
    json.dump(out, open(os.path.join(outdir, "profiles.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
