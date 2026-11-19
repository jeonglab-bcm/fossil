"""Figs 1 and 6 redrawn on the published pixels and scored (added after review on #61).

Fig. 1: the shifting and scaling examples. The paper prints no values; we read the 30 marker values off
the figure (axes from the frame: x 0 to 6, y 0 to 65 and 0 to 90), redraw both panels and score them
with wrong-input and near-miss controls. G1's fifth shifting value is under the legend; we take 49
(G2 + 30, the shift of the other four points), and the legend is left out of the score.

Fig. 6: the profile plots of panels (a) GDS825, (b) Yeast KY and (c) Yeast cell cycle. The paper does not
name the modules. For each dataset we run GeCON on the standardised genes over tau 15, 20, 25 and theta
0.6, 0.7, 0.8 and draw the largest module of each setting into the panel; the best setting is a search
result (reported with its neighbours). The gene labels legible in the network panels are checked against
our module. Panels (d) Sporulation and (e) Thaliana: their data could not be obtained. The network
drawings and heat maps are not compared: their layout and colour scale are not stated.

Usage: fig1_fig6.py DOWNLOADS PUBLISHED_DIR OUTDIR
"""
import gzip, json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figscore as fs
import gecon

FIG1 = {  # read off the figure; see the docstring
    "shifting": {"frame": (79.0, 555.0, 44.0, 485.5), "ylim": (0, 65), "legend": (400, 556, 40, 170), "markers": ["*", "*", "o"],
                 "series": {"G1": [40, 45, 60, 35, 49], "G2": [10, 15, 30, 5, 19], "G3": [5, 10, 25, 1, 9]}},
    "scaling": {"frame": (705.0, 1181.0, 43.0, 485.5), "ylim": (0, 90), "legend": (1025, 1182, 40, 170), "markers": ["*", "*", "s"],
                "series": {"G1": [28, 35, 85, 18, 50], "G2": [10, 15, 20, 5, 11], "G3": [3, 5, 7, 1, 6]}},
}
FIG6 = {  # frames of the profile panels (x0, x1, y0, y1), found from the frame lines; axis limits from the labels
    "a": {"frame": (569.5, 800.0, 213.5, 390.5), "xlim": (1, 4), "ylim": (-5, 5), "dataset": "GDS825"},
    "b": {"frame": (575.5, 792.5, 623.5, 790.5), "xlim": (1, 17), "ylim": (3, 10), "dataset": "Yeast KY"},
    "c": {"frame": (585.5, 794.0, 1024.0, 1193.5), "xlim": (1, 17), "ylim": (0, 4000), "dataset": "Yeast cell cycle"},
}
LEGIBLE = {  # gene labels legible in the network panels (read at 2.5x)
    "a": "FGL2 CPA1 ARSE APBB1IP HLA-DQB1 NKIRAS2 STMN1 MARCO ATP13A3 ARSB ABCB1 UCP3 ADH1B TOPBP1 CAMK1D DMPK CD53 FAM149B1".split(),
    "b": "YKR057W YPL081W YJL190C YJL177W YLR448W YML026C YJL189W YLR325C YKR094C YJL136C YLR167W YIR029W YOL127W YPR102C YOR312C YLR029C YLR333C YMR194W YLR406C YKL006W".split(),
}
TAUS, THETAS = (15.0, 20.0, 25.0), (0.6, 0.7, 0.8)


def lines_mask(shape, frame, xlim, ylim, rows, width=1, markers=None, msize=16):
    x0, x1, y0, y1 = frame
    c = None
    for k, row in enumerate(rows):
        xs = x0 + (np.arange(1, len(row) + 1) - xlim[0]) / (xlim[1] - xlim[0]) * (x1 - x0)
        ys = y1 - (np.clip(row, *ylim) - ylim[0]) / (ylim[1] - ylim[0]) * (y1 - y0)
        c = fs.draw_series(shape, list(zip(xs, ys)), width=width, canvas=c, marker=markers[k] if markers else None, msize=msize)
    return np.asarray(c) < 128


def region(shape, frame, inset=3, legend=None):
    x0, x1, y0, y1 = frame
    m = np.zeros(shape[:2], bool)
    m[int(y0) + inset:int(y1) - inset + 1, int(x0) + inset:int(x1) - inset + 1] = True
    if legend:
        lx0, lx1, ly0, ly1 = legend
        m[ly0:ly1, lx0:lx1] = False
    return m


def fig1(pubdir, outdir):
    img = fs.load_rgb(os.path.join(pubdir, "fig1.jpg"))
    g = img.mean(2)
    res, pub_all, our_all, ours_col = {}, np.zeros(img.shape[:2], bool), np.zeros(img.shape[:2], bool), []
    colours = {"shifting": {"G1": (220, 30, 30), "G2": (0, 0, 0), "G3": (30, 30, 220)},
               "scaling": {"G1": (30, 30, 220), "G2": (0, 0, 0), "G3": (220, 30, 30)}}
    for name, p in FIG1.items():
        reg = region(img.shape, p["frame"], inset=12, legend=p["legend"])  # 12 px: the tick marks
        pub = (g < 200) & reg & ~((img.max(2) - img.min(2) < 40) & (g > 120))  # ink: dark or coloured
        pub_all |= pub

        def draw(series):
            return lines_mask(img.shape, p["frame"], (0, 6), p["ylim"], list(series.values()), width=1, markers=p["markers"], msize=12) & reg

        ours = draw(p["series"])
        our_all |= ours
        for j, (k, v) in enumerate(p["series"].items()):
            ours_col.append((lines_mask(img.shape, p["frame"], (0, 6), p["ylim"], [v], width=1, markers=[p["markers"][j]], msize=12) & reg, colours[name][k]))
        sc = fs.score(pub, ours)
        other = FIG1["scaling" if name == "shifting" else "shifting"]["series"]
        controls = [{"name": f"the {'scaling' if name == 'shifting' else 'shifting'} panel's values", "kind": "wrong_input", "score": fs.score(pub, draw(other))["score"]},
                    {"name": "conditions in reverse order", "kind": "wrong_input", "score": fs.score(pub, draw({k: v[::-1] for k, v in p["series"].items()}))["score"]}]
        yr = p["ylim"][1] - p["ylim"][0]
        for nm, f in (("amplitude x1.05", lambda v: list(np.mean(v) + 1.05 * (np.array(v) - np.mean(v)))),
                      ("amplitude x0.95", lambda v: list(np.mean(v) + 0.95 * (np.array(v) - np.mean(v)))),
                      ("shifted +2% of the y range", lambda v: [x + 0.02 * yr for x in v]),
                      ("each value +1 unit", lambda v: [x + 1 for x in v])):
            controls.append({"name": nm, "kind": "near_miss", "score": fs.score(pub, draw({k: f(v) for k, v in p["series"].items()}))["score"]})
        # GeCON on the example: the three genes of each panel should be positively connected
        X = np.array(list(p["series"].values()), float)
        s = gecon.supports(X)
        res[name] = {**sc, "controls": controls, "values": p["series"],
                     "supports_pos": [[round(float(s.pos[i, j]), 4) for j in range(3)] for i in range(3)],
                     "supports_neg": [[round(float(s.neg[i, j]), 4) for j in range(3)] for i in range(3)],
                     "all_pairs_positive": bool(all(gecon.network(s)[i, j] == 1 for i in range(3) for j in range(3) if i != j))}
    res["combined"] = fs.score(pub_all, our_all)
    fs.save_ours(img, pub_all, ours_col, os.path.join(outdir, "figures", "fig1_ours.png"))
    fs.save_overlay(img, pub_all, our_all, os.path.join(outdir, "figures", "fig1_overlay.png"))
    return res


def kayee(path):
    rows = [l.rstrip("\n").split("\t") for l in open(path)]
    body = [r for r in rows[1:] if len(r) > 18]
    return [r[0].upper() for r in body], [int(r[1]) for r in body], np.array([[float(v) for v in r[2:19]] for r in body])


def gds825(path):
    sym, vals, inside = [], [], False
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
                try:
                    v = [float(x) for x in p[2:]]
                except ValueError:
                    continue
                sym.append(p[1].upper())
                vals.append(v)
    return sym, np.array(vals)


def fig6(downloads, pubdir, outdir):
    img = fs.load_rgb(os.path.join(pubdir, "fig6.jpg"))
    g = img.mean(2)
    rng = np.random.default_rng(6)
    data = {}
    gk, ck, K = kayee(os.path.join(downloads, "logcho_237_4class.txt"))
    _, _, KN = kayee(os.path.join(downloads, "normcho_237_4class.txt"))
    data["b"] = (gk, K, KN, ck)
    gc, cc, C = kayee(os.path.join(downloads, "raw_cellcycle_384_17.txt"))
    data["c"] = (gc, C, C, cc)
    sym, G = gds825(os.path.join(downloads, "GDS825.soft.gz"))
    sd = G.std(1)
    keep = np.argsort(-sd, kind="mergesort")[:277]  # the paper's 277 genes: the most variable, our filter
    data["a"] = ([sym[i] for i in keep], G[keep], G[keep], None)
    leg_idx = [i for i, s_ in enumerate(sym) if s_ in set(LEGIBLE["a"])]
    res, pub_all, our_all = {}, np.zeros(img.shape[:2], bool), np.zeros(img.shape[:2], bool)
    for key, p in FIG6.items():
        genes, raw, base, classes = data[key]
        reg = region(img.shape, p["frame"], inset=3)
        pub = (g < 170) & reg
        Z = (base - base.mean(1, keepdims=True)) / np.where(base.std(1, keepdims=True) == 0, 1, base.std(1, keepdims=True))
        grid = []
        for tau in TAUS:
            s = gecon.supports(Z, tau=tau)
            for th in THETAS:
                mods = gecon.modules(gecon.network(s, th), 5)
                if not mods:
                    grid.append({"tau": tau, "theta": th, "genes": 0, "score": 0.0})
                    continue
                m = mods[0]
                sc = fs.score(pub, lines_mask(img.shape, p["frame"], p["xlim"], p["ylim"], raw[m]) & reg)
                grid.append({"tau": tau, "theta": th, "genes": len(m), "score": sc["score"], "members": m})
        best = max(grid, key=lambda r: (r["score"], -r["tau"], -r["theta"]))
        m = best["members"]
        ours = lines_mask(img.shape, p["frame"], p["xlim"], p["ylim"], raw[m]) & reg
        sc = fs.score(pub, ours)
        controls = []
        for k in range(3):
            pick = rng.choice(len(raw), len(m), replace=False)
            controls.append({"name": f"{len(m)} random genes of the dataset (draw {k + 1})", "kind": "wrong_input",
                             "score": fs.score(pub, lines_mask(img.shape, p["frame"], p["xlim"], p["ylim"], raw[pick]) & reg)["score"]})
        for r in grid:
            if r is best or r["genes"] == 0:
                continue
            if abs(r["tau"] - best["tau"]) + 50 * abs(r["theta"] - best["theta"]) <= 5.01:
                controls.append({"name": f"the module at tau {r['tau']:g}, theta {r['theta']:g} ({r['genes']} genes)", "kind": "near_miss", "score": r["score"]})
        legible = LEGIBLE.get(key)
        member_names = {genes[i] for i in m}
        res[key] = {**sc, "dataset": p["dataset"], "setting": {"tau": best["tau"], "theta": best["theta"]}, "genes": len(m),
                    "grid": [{k: v for k, v in r.items() if k != "members"} for r in grid], "controls": controls,
                    "legible_labels": legible,
                    "legible_in_module": sorted(x for x in (legible or []) if x in member_names),
                    "legible_in_data": sorted(x for x in (legible or []) if x in set(genes))}
        if key == "a":  # the legible network genes, all their probes, from the whole data set
            lg = G[leg_idx]
            res[key]["legible_probes"] = {
                "genes": sorted({sym[i] for i in leg_idx}), "probes": len(leg_idx),
                "range": [round(float(lg.min()), 3), round(float(lg.max()), 3)],
                "score": fs.score(pub, lines_mask(img.shape, p["frame"], p["xlim"], p["ylim"], lg) & reg)["score"],
                "random_probe_sets": [fs.score(pub, lines_mask(img.shape, p["frame"], p["xlim"], p["ylim"], G[rng.choice(len(G), len(leg_idx), replace=False)]) & reg)["score"] for _ in range(3)]}
            res[key]["legible_in_data"] = res[key]["legible_probes"]["genes"]
        pub_all |= pub
        our_all |= ours
    out = img.copy()
    out[pub_all] = 255
    out[our_all] = 0
    Image.fromarray(out.astype(np.uint8)).save(os.path.join(outdir, "figures", "fig6_ours.png"))
    fs.save_overlay(img, pub_all, our_all, os.path.join(outdir, "figures", "fig6_overlay.png"))
    return res


def main():
    downloads, pubdir, outdir = sys.argv[1:4]
    os.makedirs(os.path.join(outdir, "figures"), exist_ok=True)
    out = {"fig1": fig1(pubdir, outdir), "fig6": fig6(downloads, pubdir, outdir)}
    json.dump(out, open(os.path.join(outdir, "fig1_fig6.json"), "w"), indent=1)
    for k in ("shifting", "scaling"):
        r = out["fig1"][k]
        print("fig1", k, r["score"], "best control", max(c["score"] for c in r["controls"]), "positive", r["all_pairs_positive"])
    for k, r in out["fig6"].items():
        print("fig6", k, r["genes"], r["setting"], r["score"], "controls", sorted(c["score"] for c in r["controls"])[-3:],
              "legible", len(r["legible_in_module"]), "of", len(r["legible_in_data"]))


if __name__ == "__main__":
    main()
