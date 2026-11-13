"""Fig. 4: does the published bar chart draw Table 2? Bar heights read off the published panels.

Each panel's axes come from its frame and the zero line; the y scale from the frame (0 to the top tick) and
the tick marks. Each bar is a non-white run of columns just above the zero line; its height is the topmost
non-white pixel of its centre column. 13 groups of 4 bars (GeCON, ARACNE, CLR, MRNET). The legend hides
the top of D11's GeCON bar in each panel; that bar is left out.

Also draws our run's values (dream.json) and the paper's on the published grid: fig4_ours.png (the paper's
Table 2 values drawn as bars at the published positions, published bars removed), fig4_overlay.png, and
fig4_run.png (our run's values in the same layout).

Usage: fig4_bars.py PUBLISHED_DIR TABLE2.json DREAM.json OUTDIR
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figscore as fs

METHODS = ["gecon", "aracne", "clr", "mrnet"]
COLOURS = {"gecon": (0, 0, 143), "aracne": (80, 210, 230), "clr": (250, 210, 30), "mrnet": (128, 0, 0)}
PUB_COLOURS = {"gecon": (40, 40, 110), "aracne": (100, 195, 200), "clr": (235, 220, 25), "mrnet": (120, 16, 18)}  # sampled
PANELS = {  # rows of the frame lines (top, bottom) and the y limit, read from the axis labels
    "aupr": {"rows": (48, 654.5), "ymax": 0.9, "yticks": [0.1 * i for i in range(1, 9)]},
    "auroc": {"rows": (977.5, 1584.5), "ymax": 0.8, "yticks": [0.1 * i for i in range(1, 8)]},
    "f": {"rows": (1922.5, 2528.5), "ymax": 0.9, "yticks": [0.1 * i for i in range(1, 9)]},
}


def panel_cols(img, top, bottom):
    """x range of the panel: the ends of the dark bottom frame line."""
    g = img[int(round(bottom)) - 1:int(round(bottom)) + 2].mean(2).min(0) < 100
    idx = np.where(g)[0]
    groups = np.split(idx, np.where(np.diff(idx) > 3)[0] + 1)
    longest = max(groups, key=len)
    return float(longest[0]) + 1, float(longest[-1]) - 1


def read_panel(img, key):
    p = PANELS[key]
    top, bottom = p["rows"]
    x0, x1 = panel_cols(img, top, bottom)
    sub = img.copy()
    box = (x0, x1, top, bottom)
    ticks = fs.match_ticks(sub, box, "y", p["yticks"], (0, p["ymax"]))
    ys = [bottom, top] + [t for _, t in ticks]
    vs = [0, p["ymax"]] + [v for v, _ in ticks]
    a, b, res = fs.fit_axis(ys, vs)  # value -> pixel
    white = img.min(2) > 200
    yrow = int(bottom) - 6
    row = img[yrow, int(x0) + 3:int(x1) - 2].astype(float)
    pal = np.array([PUB_COLOURS[m] for m in METHODS] + [(0, 0, 0), (255, 255, 255)], float)
    cls = np.argmin(((row[:, None, :] - pal[None]) ** 2).sum(2), 1)
    runs = []
    start = 0
    for i in range(1, len(cls) + 1):
        if i == len(cls) or cls[i] != cls[start]:
            if cls[start] < 4 and i - start >= 2:
                if runs and runs[-1][0] == cls[start] and start - runs[-1][2] <= 3:
                    runs[-1][2] = i  # the same colour again after a JPEG speck: one bar
                else:
                    runs.append([cls[start], start, i])
            start = i
    runs = [np.arange(a, b) + int(x0) + 3 for _, a, b in runs if b - a >= 4]
    # bar layout: 13 groups at x = 1..13 on an axis from 0 to 14 (the frame), 4 bars per group at a fixed
    # pitch, measured as the median gap between neighbouring bar centres found in the row above zero
    centres = np.array([r.mean() for r in runs])
    gaps = np.diff(centres)
    pitch = float(np.median(gaps[gaps < 20]))
    unit = (x1 - x0) / 14.0
    layout = [x0 + unit * (k + 1) + (j - 1.5) * pitch for k in range(13) for j in range(4)]
    half = pitch / 2 - 1
    runs = [np.arange(int(round(c - half)), int(round(c + half)) + 1) for c in layout]
    bars = []
    for r in runs:
        c = int(round(r.mean()))
        col = ~white[int(top) + 2:int(bottom) - 1, c - 1:c + 2].all(1)
        # topmost non-white pixel of the contiguous run that reaches the zero line
        k = len(col) - 1
        while k > 0 and col[k - 1]:
            k -= 1
        ytop = int(top) + 2 + k
        bars.append({"x0": int(r[0]), "x1": int(r[-1]), "centre": c, "top_px": ytop, "value": (ytop - b) / a})
    # the legend box (top right): its left edge is the column in the right half with the longest dark run
    # that starts at the top frame; its bottom is where that run ends
    g = img.mean(2) < 100
    best = None
    for c in range(int((x0 + x1) / 2), int(x1) - 5):
        col = g[int(top):int(bottom), c]
        n = int(np.argmin(col)) if not col.all() else len(col)
        if n > 100 and (best is None or n > best[1] + 3):
            best = (c, n)
            break
    legend = [best[0], int(x1), int(top), int(top) + best[1]]
    return {"box": [round(v, 1) for v in box], "legend": legend, "y_fit_residual_px": round(res, 2), "ticks_matched": len(ticks),
            "bar_pitch_px": round(pitch, 2), "group_pitch_px": round(unit, 2),
            "px_per_unit": round(-a, 1), "bars": bars}


def draw_bars(img, panel, values, top, bottom, a, b, out, colours=True):
    d = ImageDraw.Draw(out)
    for bar, v in zip(panel["bars"], values):
        if v is None:
            continue
        y = a * v + b
        d.rectangle([bar["x0"], y, bar["x1"], bottom - 1], fill=bar["colour"] if colours else 0, outline=(0, 0, 0) if colours else 0)


def main():
    pubdir, table2, dream, outdir = sys.argv[1:5]
    img = fs.load_rgb(os.path.join(pubdir, "fig4.jpg"))
    t2 = json.load(open(table2))["table2"]
    run = json.load(open(dream)) if os.path.exists(dream) else None
    res = {}
    canvas = img.copy()
    ours_img = Image.fromarray(img.astype(np.uint8))
    run_img = Image.fromarray(img.astype(np.uint8))
    pub_mask_all = np.zeros(img.shape[:2], bool)
    our_mask_all = np.zeros(img.shape[:2], bool)
    for key in PANELS:
        p = read_panel(img, key)
        top, bottom = PANELS[key]["rows"]
        a, b, _ = fs.fit_axis([bottom, top] + [], [0, PANELS[key]["ymax"]])
        fields = []
        if len(p["bars"]) != 52:
            raise SystemExit(f"{key}: found {len(p['bars'])} bars, expected 52")
        for k, bar in enumerate(p["bars"]):
            ds, m = f"D{k // 4 + 1}", METHODS[k % 4]
            bar["dataset"], bar["method"], bar["colour"] = ds, m, COLOURS[m]
            hidden = p["legend"][0] - 2 <= bar["centre"] <= p["legend"][1] + 2 and bar["top_px"] <= p["legend"][3] + 2
            expected = t2[key][ds][m]
            fields.append({"name": f"{ds} {m}", "expected": expected,
                           "observed": None if hidden else round(bar["value"], 3), "hidden_by_legend": bool(hidden)})
        res[key] = {"panel": {k: (list(map(int, v)) if k == "legend" else v) for k, v in p.items() if k != "bars"}, "fields": fields}
        # renders: published bars removed, the table's values drawn; and our run's values
        x0, x1, _, _ = p["box"]
        region = np.zeros(img.shape[:2], bool)
        region[int(top) + 2:int(bottom) - 1, int(x0) + 2:int(x1) - 1] = True
        legend = np.zeros_like(region)
        lx0, lx1, ly0, ly1 = p["legend"]
        legend[ly0:ly1 + 3, lx0 - 2:lx1 + 3] = True
        pub_mask = region & ~legend & (img.min(2) < 200)
        arr = np.asarray(ours_img).copy()
        arr[pub_mask] = 255
        ours_img = Image.fromarray(arr)
        draw_bars(img, p, [float(t2[key][f"D{k // 4 + 1}"][METHODS[k % 4]]) for k in range(52)], top, bottom, a, b, ours_img)
        tmp = Image.new("L", (img.shape[1], img.shape[0]), 255)
        draw_bars(img, p, [float(t2[key][f"D{k // 4 + 1}"][METHODS[k % 4]]) for k in range(52)], top, bottom, a, b, tmp, colours=False)
        our_mask_all |= (np.asarray(tmp) < 128) & region & ~legend
        pub_mask_all |= pub_mask
        if run:
            arr = np.asarray(run_img).copy()
            arr[pub_mask] = 255
            run_img = Image.fromarray(arr)
            draw_bars(img, p, [run["datasets"][f"D{k // 4 + 1}"][METHODS[k % 4]]["f_max" if key == "f" else key] for k in range(52)],
                      top, bottom, a, b, run_img)
    os.makedirs(os.path.join(outdir, "figures"), exist_ok=True)
    ours_img.save(os.path.join(outdir, "figures", "fig4_ours.png"))
    fs.save_overlay(img, pub_mask_all, our_mask_all, os.path.join(outdir, "figures", "fig4_overlay.png"))
    if run:
        run_img.save(os.path.join(outdir, "figures", "fig4_run.png"))
    res["pixels_table_drawn"] = fs.score(pub_mask_all, our_mask_all)
    json.dump(res, open(os.path.join(outdir, "fig4.json"), "w"), indent=1)
    for key in PANELS:
        f = [x for x in res[key]["fields"] if x["observed"] is not None]
        err = [abs(float(x["expected"]) - x["observed"]) for x in f]
        print(key, res[key]["panel"], "read", len(f), "max |diff|", round(max(err), 3), "within 0.01:", sum(e <= 0.01 for e in err))


if __name__ == "__main__":
    main()
