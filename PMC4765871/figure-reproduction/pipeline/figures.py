"""Draw our results on the published pixel grid, overlay, and score them.

usage: figures.py RUN_DIR PUBLISHED_DIR PUBLISHED_DATA_JSON OUTDIR

Each scored panel is drawn with matplotlib on a canvas the size of the published 600 dpi render,
with the axes placed on the published frame (params/panels.json) and the published data limits, in
the published colours. The score of an element class (the red fit lines, say) is two-way: the share
of published pixels of that class within 2 px of ours, and of ours within 2 px of the published
ones; the smaller is the score. Controls are scored the same way: a wrong input (another panel's
series) and near misses (a shift of 1% of the x range; amplitude x 1.05).

Writes figN_ours.png (the published figure with the plot areas of the scored panels redrawn from
our results), figN_overlay.png (red channel = published, green and blue = ours: cyan is ink only in
the paper, red only ours, black both) and scores.json.
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from scipy import ndimage  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import grn  # noqa: E402

DPI = 600
TOL = 2
BOXES = json.loads((HERE / "params" / "figure_boxes.json").read_text())["figures"]
PANELS = json.loads((HERE / "params" / "panels.json").read_text())["panels"]
COL = {"red": (0.93, 0.2, 0.17), "green": (0.08, 0.66, 0.29), "dark": (0.14, 0.12, 0.13)}
PASS = 0.9  # pass mark: 90% of the trace within 2 px both ways (raised above any control)


def frame_px(fig, panel):
    clip = BOXES[fig]["clip"]
    x0, y0, x1, y1 = PANELS[panel]["frame"]
    s = DPI / 72
    return ((x0 - clip[0] + 2) * s, (y0 - clip[1] + 2) * s, (x1 - clip[0] + 2) * s, (y1 - clip[1] + 2) * s)


def draw(fig, size, layers):
    """layers: {panel: [element, ...]}; element = ('line', x, y, colour, lw_pt) or
    ('circles', x, y, colour, size_pt) or ('dots', x, y, colours, size_pt). Returns an RGB array."""
    W, H = size
    f = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    for panel, els in layers.items():
        px0, py0, px1, py1 = frame_px(fig, panel)
        ax = f.add_axes([px0 / W, 1 - py1 / H, (px1 - px0) / W, (py1 - py0) / H])
        ax.set_xlim(*PANELS[panel]["xlim"])
        ax.set_ylim(*PANELS[panel]["ylim"])
        ax.axis("off")
        for e in els:
            kind, x, y, c, w = e
            if kind == "line":
                ax.plot(x, y, color=c, lw=w, solid_capstyle="butt", clip_on=True)
            elif kind == "circles":
                ax.scatter(x, y, s=w**2, facecolors="none", edgecolors=[c], linewidths=0.35, clip_on=True)
            elif kind == "dots":
                ax.scatter(x, y, s=w**2, c=c, linewidths=0, clip_on=True)
    f.canvas.draw()
    img = np.asarray(f.canvas.buffer_rgba())[:, :, :3]
    plt.close(f)
    out = np.full((H, W, 3), 255, np.uint8)  # the canvas can come out a pixel short
    h, w = min(H, img.shape[0]), min(W, img.shape[1])
    out[:h, :w] = img[:h, :w]
    return out


def colour_mask(img, colour, tol=60):
    c = np.array(colour) * 255
    return (np.abs(img.astype(float) - c).max(2) < tol)


def ink_mask(img):
    return img.astype(float).min(2) < 200


def score(pub_mask, our_mask, region):
    a = pub_mask & region
    b = our_mask & region
    if not a.any() or not b.any():
        return {"published_near_ours": 0.0, "ours_near_published": 0.0, "score": 0.0}
    da = ndimage.distance_transform_edt(~b)
    db = ndimage.distance_transform_edt(~a)
    p = float((da[a] <= TOL).mean())
    o = float((db[b] <= TOL).mean())
    return {"published_near_ours": round(p, 4), "ours_near_published": round(o, 4), "score": round(min(p, o), 4)}


def region_of(fig, panel, shape, inset=6):
    px0, py0, px1, py1 = frame_px(fig, panel)
    m = np.zeros(shape[:2], bool)
    m[max(0, int(py0) + inset):int(py1) - inset, max(0, int(px0) + inset):int(px1) - inset] = True
    return m


def blank_frames(pub, fig, panels):
    out = pub.copy()
    for p in panels:
        px0, py0, px1, py1 = frame_px(fig, p)
        out[int(py0) + 4:int(py1) - 3, int(px0) + 4:int(px1) - 3] = 255
    return out


def compose(base, layer):
    """Our drawing on top of base: non-white pixels of layer replace base."""
    out = base.copy()
    m = layer.min(2) < 250
    out[m] = layer[m]
    return out


def overlay(pub, ours):
    g = lambda a: a.astype(float).mean(2)
    o = np.zeros_like(pub)
    o[:, :, 0] = g(pub).astype(np.uint8)
    o[:, :, 1] = g(ours).astype(np.uint8)
    o[:, :, 2] = g(ours).astype(np.uint8)
    return o


def shifted(el, dx=0.0, amp=1.0):
    kind, x, y, c, w = el
    y = np.asarray(y, float)
    mid = (np.nanmax(y) + np.nanmin(y)) / 2
    return (kind, np.asarray(x, float) + dx, mid + (y - mid) * amp, c, w)


def score_figure(fig, pub, panels, elements, classes, controls, outdir):
    """elements: {panel: [els]}; classes: {panel: colour name scored}; controls: {name: (kind,
    {panel: [els]})}. Writes the render and the overlay and returns the scores."""
    size = (pub.shape[1], pub.shape[0])
    layer = draw(fig, size, elements)
    ours = compose(blank_frames(pub, fig, panels), layer)
    Image.fromarray(ours).save(outdir / f"{fig}_ours.png", optimize=True)
    Image.fromarray(overlay(pub, ours)).save(outdir / f"{fig}_overlay.png", optimize=True)
    res = {}
    clayers = {n: (k, draw(fig, size, els)) for n, (k, els) in controls.items()}
    for p in panels:
        region = region_of(fig, p, pub.shape)
        cl = classes[p]
        pm = colour_mask(pub, COL[cl]) if cl != "ink" else ink_mask(pub)
        om = colour_mask(layer, COL[cl]) if cl != "ink" else ink_mask(layer)
        r = score(pm, om, region)
        r["controls"] = []
        for n, (kind, lay) in clayers.items():
            cm = colour_mask(lay, COL[cl]) if cl != "ink" else ink_mask(lay)
            if not (cm & region).any():
                continue
            r["controls"].append({"name": n, "kind": kind, "score": score(pm, cm, region)["score"]})
        best = max([c["score"] for c in r["controls"]] or [0])
        r["threshold"] = round(max(PASS, best + 0.02), 4)
        r["class"] = cl
        res[p] = r
    return res


# ---------------------------------------------------------------- per figure


def load_runs(run):
    run = Path(run)
    out = {}
    for name in ("ffl", "haem", "toggle"):
        f = run / f"{name}.json"
        if f.exists():
            out[name] = json.loads(f.read_text())
    out["ffl_fits"] = json.loads((run / "ffl_fits.json").read_text())
    out["haem_fits"] = json.loads((run / "haem_fits.json").read_text())
    out["haem_series"] = json.loads((run / "haem_series.json").read_text())
    out["ffl_data"] = np.load(run / "ffl_data.npz")
    out["toggle_fits"] = json.loads((run / "toggle_fits.json").read_text())
    out["toggle_data"] = np.load(run / "toggle_data.npz")
    return out


FIG9 = {"fig9.GATA2_SCL": ("GATA2", "SCL"), "fig9.GATA2_GFI1": ("GATA2", "GFI1"),
        "fig9.GATA2_and": ("GATA2", "and(GFI1,NFE2)"), "fig9.GFI1_GFI1B": ("GFI1", "GFI1B"),
        "fig9.GFI1B_GATA2": ("GFI1B", "GATA2"), "fig9.GFI1B_GFI1": ("GFI1B", "GFI1")}


def haem_curves(R):
    import haem
    out = {}
    for panel, (target, spec) in FIG9.items():
        pw = haem.TARGETS[target][0]
        f = next(f for f in R["haem_fits"] if f["target"] == target and f["model"] == spec)
        m = grn.Model(haem.signed(spec, target))
        ser = haem.make_series(target, m.inputs, R["haem_series"]["pdata"][pw], [0])
        g, y = grn.Problem(m, ser).trajectories(f["map"])[0]
        out[panel] = {"t": ser[0].t, "y": ser[0].y, "fit_t": g, "fit_y": y}
    return out


def fig9(R, pub, outdir):
    C = haem_curves(R)
    lw = 1.3
    els = {p: [("circles", c["t"], c["y"], COL["dark"], 3.2), ("line", c["fit_t"], c["fit_y"], COL["red"], lw)]
           for p, c in C.items()}
    lines = {p: [("line", c["fit_t"], c["fit_y"], COL["red"], lw)] for p, c in C.items()}
    keys = list(C)
    wrong = {p: [("line", C[keys[(i + 3) % 6]]["fit_t"], C[keys[(i + 3) % 6]]["fit_y"], COL["red"], lw)]
             for i, p in enumerate(keys)}
    controls = {"other panel's fit (GATA2 <-> GFI1/GFI1B)": ("wrong_input", wrong),
                "shift +1.2 pseudo time": ("near_miss", {p: [shifted(e[0], dx=1.2)] for p, e in lines.items()}),
                "amplitude x 1.05": ("near_miss", {p: [shifted(e[0], amp=1.05)] for p, e in lines.items()})}
    return score_figure("fig9", pub, list(C), els, {p: "red" for p in C}, controls, outdir), C


def fig4(R, pub, outdir):
    per = R["ffl"]["perturbations"]
    names = {"fig4.deletion": "deletion", "fig4.knockdown": "knockdown", "fig4.simultaneous": "simultaneous"}
    els, lines = {}, {}
    for p, k in names.items():
        d = per[k]
        els[p] = [("dots", d["t"], d["gZ_data"], [COL["dark"]], 2.2), ("line", d["grid"], d["gZ_pred"], COL["red"], 1.1)]
        lines[p] = [("line", d["grid"], d["gZ_pred"], COL["red"], 1.1)]
    keys = list(names)
    wrong = {p: [("line", per[names[keys[(i + 1) % 3]]]["grid"], per[names[keys[(i + 1) % 3]]]["gZ_pred"], COL["red"], 1.1)]
             for i, p in enumerate(keys)}
    controls = {"another perturbation's prediction": ("wrong_input", wrong),
                "shift +0.7 time": ("near_miss", {p: [shifted(e[0], dx=0.68)] for p, e in lines.items()}),
                "amplitude x 1.05": ("near_miss", {p: [shifted(e[0], amp=1.05)] for p, e in lines.items()})}
    return score_figure("fig4", pub, keys, els, {p: "red" for p in keys}, controls, outdir)


def ffl_fit_curve(R, spec):
    import ffl
    f = R["ffl_fits"]["fits"][spec]
    d = R["ffl_data"]
    X, reps = d["X"], d["reps"]
    T = float(R["ffl"]["T_f"])
    m = grn.Model(spec)
    ser = ffl.build_series(X, reps[:1], T, "gZ", m.inputs, T)
    g, y = grn.Problem(m, ser).trajectories(f["map"])[0]
    return ser[0].t / T * 100, ser[0].y, g / T * 100, y


def fig2(R, pub, outdir):
    t, y, go, yo = ffl_fit_curve(R, "or(gX+,gY-)")
    _, _, ga, ya = ffl_fit_curve(R, "and(gX+,gY-)")
    p = "fig2.d"
    els = {p: [("circles", t, y, COL["dark"], 2.6), ("line", ga, ya, COL["green"], 0.9), ("line", go, yo, COL["red"], 0.9)]}
    controls = {"AND fit drawn as the OR fit": ("wrong_input", {p: [("line", ga, ya, COL["red"], 0.9)]}),
                "shift +1 pseudo time": ("near_miss", {p: [shifted(("line", go, yo, COL["red"], 0.9), dx=1.0)]}),
                "amplitude x 1.05": ("near_miss", {p: [shifted(("line", go, yo, COL["red"], 0.9), amp=1.05)]})}
    s = score_figure("fig2", pub, [p], els, {p: "red"}, controls, outdir)
    # the AND (green) line scored on its own
    size = (pub.shape[1], pub.shape[0])
    lay = draw("fig2", size, {p: [("line", ga, ya, COL["green"], 0.9)]})
    reg = region_of("fig2", p, pub.shape)
    g = score(colour_mask(pub, COL["green"]), colour_mask(lay, COL["green"]), reg)
    gc = []
    for name, kind, el in [("OR fit drawn as the AND fit", "wrong_input", ("line", go, yo, COL["green"], 0.9)),
                           ("shift +1 pseudo time", "near_miss", shifted(("line", ga, ya, COL["green"], 0.9), dx=1.0)),
                           ("amplitude x 1.05", "near_miss", shifted(("line", ga, ya, COL["green"], 0.9), amp=1.05))]:
        l2 = draw("fig2", size, {p: [el]})
        gc.append({"name": name, "kind": kind, "score": score(colour_mask(pub, COL["green"]), colour_mask(l2, COL["green"]), reg)["score"]})
    g.update({"controls": gc, "class": "green", "threshold": round(max(PASS, max(c["score"] for c in gc) + 0.02), 4)})
    s["fig2.d.and"] = g
    return s


def fig6(R, pub, outdir):
    import toggle as tg
    tf = R["toggle_fits"]
    d = R["toggle_data"]
    f = next(x for x in tf["fig6"] if x["model"] == "and(A+,D-)")
    geom = json.loads((Path(R["_run"]) / "toggle_geometry.json").read_text())
    Xo = d["Xo"]
    T = float(R["toggle"]["T_f"])
    m = grn.Model("and(A+,D-)")
    ds = {"Xo": Xo, "geom": geom, "T": T, "pts": {b: d[f"pt_{b}"] for b in ("C", "D")}}
    curves = {}
    for p, b in (("fig6.top", "C"), ("fig6.bottom", "D")):
        ser = tg.series_for(ds, "C", m.inputs, [b])[:1]
        g, y = grn.Problem(m, ser).trajectories(f["map"])[0]
        n = len(geom["branches"][b]["cells"]) - 1
        curves[p] = (ser[0].t / T * n, ser[0].y, g / T * n, y)
    els = {p: [("circles", c[0], c[1], COL["dark"], 3.0), ("line", c[2], c[3], COL["red"], 1.6)] for p, c in curves.items()}
    lines = {p: [("line", c[2], c[3], COL["red"], 1.6)] for p, c in curves.items()}
    keys = list(curves)
    wrong = {keys[0]: [("line", curves[keys[1]][2], curves[keys[1]][3], COL["red"], 1.6)],
             keys[1]: [("line", curves[keys[0]][2], curves[keys[0]][3], COL["red"], 1.6)]}
    controls = {"the other branch's fit": ("wrong_input", wrong),
                "shift +1.4 pseudo time": ("near_miss", {p: [shifted(e[0], dx=1.4)] for p, e in lines.items()}),
                "amplitude x 1.05": ("near_miss", {p: [shifted(e[0], amp=1.05)] for p, e in lines.items()})}
    return score_figure("fig6", pub, keys, els, {p: "red" for p in keys}, controls, outdir)


def fig5(R, pub, outdir):
    d = R["toggle_data"]
    geom = json.loads((Path(R["_run"]) / "toggle_geometry.json").read_text())
    b = "C"
    cells = np.array(geom["branches"][b]["cells"])
    traj = d[f"pt_{b}"][0]
    order = np.argsort(traj)
    X = d["Xo"][cells][order]
    x = np.arange(len(order))
    cmap = plt.get_cmap("jet")
    cols = cmap(np.linspace(0, 1, len(order)))[:, :3]
    els, wrong = {}, {}
    for gi, g in enumerate(["A", "B", "C", "D"]):
        p = f"fig5.g{g}"
        els[p] = [("dots", x, X[:, gi], cols, 2.0)]
        other = (gi + 2) % 4
        wrong[p] = [("dots", x, X[:, other], cols, 2.0)]
    controls = {"another gene's series": ("wrong_input", wrong),
                "shift +1.5 pseudo time": ("near_miss", {p: [("dots", x + 1.5, e[0][2], cols, 2.0)] for p, e in els.items()})}
    return score_figure("fig5", pub, list(els), els, {p: "ink" for p in els}, controls, outdir)


TYPE_COLOURS = {"PreMegE": (0.58, 0.1, 0.11), "LMPP": (0.95, 0.44, 0.19), "HSC": (0.39, 0.74, 0.35),
                "GMP": (0.04, 0.52, 0.78), "CLP": (0.2, 0.19, 0.52)}


def colour_ink(img):
    a = img.astype(float)
    return (a.max(2) - a.min(2)) > 60


def project(Y, types, pub_centroids):
    """Linear map (2 x 3 plus offset) of the 3D embedding onto the page that sends each cell
    type's centroid closest to the published one (least squares over the five types)."""
    ts = list(pub_centroids)
    A = np.array([np.r_[Y[types == t].mean(0), 1.0] for t in ts])
    B = np.array([pub_centroids[t] for t in ts])
    M, *_ = np.linalg.lstsq(A, B, rcond=None)
    return np.c_[Y, np.ones(len(Y))] @ M, M


def fig7(R, pub, pubdata, outdir):
    hs = R["haem_series"]
    types = np.array(hs["types"])
    dots = pubdata["fig7.b"]["dots"]
    cols = {tuple(round(c, 2) for c in v): k for k, v in TYPE_COLOURS.items()}
    pubc = {}
    for t in TYPE_COLOURS:
        xy = np.array([d[:2] for d in dots if cols.get(tuple(d[2])) == t or (t == "CLP" and tuple(d[2]) == (0.2, 0.17, 0.46))])
        pubc[t] = xy.mean(0)
    p = "fig7.b"
    rng = np.random.default_rng(7)

    def layer(Y, ty):
        xy, M = project(Y, ty, pubc)
        return [("dots", xy[:, 0], xy[:, 1], [TYPE_COLOURS[t] for t in ty], 1.62)], M

    Y = np.array(hs["Y"])
    els, M = layer(Y, types)
    shuffled = rng.permutation(types)
    controls = {"cell types shuffled": ("wrong_input", {p: layer(Y, shuffled)[0]}),
                "sigma 100.9 (supp. Table 10 as printed)": ("near_miss", {p: layer(np.array(hs["Y_controls"]["table10_literal"]), types)[0]}),
                "sigma halved": ("near_miss", {p: layer(np.array(hs["Y_controls"]["half"]), types)[0]}),
                "sigma doubled": ("near_miss", {p: layer(np.array(hs["Y_controls"]["double"]), types)[0]})}
    size = (pub.shape[1], pub.shape[0])
    lay = draw("fig7", size, {p: els})
    region = region_of("fig7", p, pub.shape, inset=0)
    base = pub.copy()
    m = colour_ink(pub) & region
    base[m] = 255
    ours = compose(base, lay)
    Image.fromarray(ours).save(outdir / "fig7_ours.png", optimize=True)
    Image.fromarray(overlay(pub, ours)).save(outdir / "fig7_overlay.png", optimize=True)
    pm = colour_ink(pub)
    r = score(pm, colour_ink(lay), region)
    r["controls"] = [{"name": n, "kind": k, "score": score(pm, colour_ink(draw("fig7", size, e)), region)["score"]}
                     for n, (k, e) in controls.items()]
    r["threshold"] = round(max(PASS, max(c["score"] for c in r["controls"]) + 0.02), 4)
    r["class"] = "coloured dots"
    r["projection"] = M.tolist()
    return {p: r}


def main(run, pubdir, pubdata, outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    R = load_runs(run)
    R["_run"] = run
    pub = {f: np.asarray(Image.open(Path(pubdir) / f"figure-{f[3:]}.png").convert("RGB")) for f in BOXES}
    S = {}
    S.update(fig2(R, pub["fig2"], out))
    S.update(fig4(R, pub["fig4"], out))
    S.update(fig5(R, pub["fig5"], out))
    S.update(fig6(R, pub["fig6"], out))
    s9, C9 = fig9(R, pub["fig9"], out)
    S.update(s9)
    P = json.loads(Path(pubdata).read_text())
    S.update(fig7(R, pub["fig7"], P, out))
    # curve distances in data units against the curves read from the vector figure
    dist = {}
    for p, c in C9.items():
        pc = np.array(next(iter(P[p]["curves"].values())))
        yo = np.interp(pc[:, 0], c["fit_t"], c["fit_y"])
        dist[p] = {"rmse_fit_vs_published_fit": float(np.sqrt(np.mean((yo - pc[:, 1]) ** 2))),
                   "n_points_published": len(P[p].get("points", [])), "n_points_ours": int(len(c["t"]))}
    (out / "scores.json").write_text(json.dumps({"pixels": S, "curves": dist}, indent=1))
    for k, v in S.items():
        print(k, v["score"], v["threshold"], [(c["name"], c["score"]) for c in v["controls"]])


if __name__ == "__main__":
    main(*sys.argv[1:5])
