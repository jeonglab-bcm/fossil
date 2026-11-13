"""Fig. 5: our re-measured times drawn on the published axes.

The published points are read off the figure (marker centres; read_published below). Our times come from
timing.py on another machine and other implementations, so each method's times are multiplied by one
constant, fitted by least squares on log10 times against the published readings (timing-and-estimation.md).
The constants and the per-size ratios are reported; the render shows the scaled curves.

Usage: fig5_plot.py PUBLISHED_DIR TIMING.json OUTDIR
"""
import json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figscore as fs

# Marker centres read off the published figure (x: genes, y: seconds) with the tick-fitted axes; GeCON at
# 250 and 1000 genes sits on the zero line and cannot be read to better than about 0.5 s.
PUBLISHED = {
    "sizes": [250, 1000, 1500, 2000, 2585, 3000],
    "aracne": [4.5, 17.0, 34.0, 61.0, 103.0, 256.0],
    "gecon": [None, None, 1.9, 3.0, 5.0, 11.2],
}


def main():
    pubdir, timing, outdir = sys.argv[1:4]
    img = fs.load_rgb(os.path.join(pubdir, "fig5.jpg"))
    box = fs.frame_box(img)
    xt = fs.match_ticks(img, box, "x", [500, 1000, 1500, 2000, 2500, 3000], (178.0, 3043.0), search=15)
    yt = fs.match_ticks(img, box, "y", [50, 100, 150, 200, 250], (-1.0, 260.0), search=15)
    ax, bx, rx = fs.fit_axis([p for _, p in xt], [v for v, _ in xt])
    ay, by, ry = fs.fit_axis([p for _, p in yt], [v for v, _ in yt])
    tim = json.load(open(timing))
    rows = {r["genes"]: r for r in tim["rows"]}
    sizes = PUBLISHED["sizes"]
    res = {"axes": {"x_ticks": len(xt), "y_ticks": len(yt), "x_residual_px": round(rx, 2), "y_residual_px": round(ry, 2)},
           "published": PUBLISHED, "ours": {}, "scale": {}, "ratios": {}}
    for m, key in (("aracne", "aracne_total_s"), ("gecon", "gecon_s")):
        ours = np.array([rows[s][key] for s in sizes])
        pub = PUBLISHED[m]
        ok = [i for i, v in enumerate(pub) if v is not None]
        c = 10 ** float(np.mean([np.log10(pub[i]) - np.log10(ours[i]) for i in ok]))
        res["scale"][m] = round(c, 3)
        res["ours"][m] = [round(float(v), 4) for v in ours]
        res["ratios"][m] = [round(pub[i] / ours[i], 2) if pub[i] else None for i in range(len(sizes))]
    out = img.copy()
    from PIL import ImageDraw
    canvas = Image.fromarray(out.astype(np.uint8))
    d = ImageDraw.Draw(canvas)
    for m, col in (("aracne", (0, 150, 0)), ("gecon", (230, 120, 0))):
        ys = np.array(res["ours"][m]) * res["scale"][m]
        pts = [(ax * s + bx, ay * y + by) for s, y in zip(sizes, ys)]
        d.line(pts, fill=col, width=4)
        for x, y in pts:
            d.rectangle([x - 8, y - 8, x + 8, y + 8], outline=col, width=3)
    os.makedirs(os.path.join(outdir, "figures"), exist_ok=True)
    canvas.save(os.path.join(outdir, "figures", "fig5_overlay.png"))
    # ours alone: the published curves removed (blue and red ink inside the axes), ours in their colours
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    trace = ((b > 150) & (r < 150) & (g < 150)) | ((r > 150) & (g < 130) & (b < 130))
    trace[:, : int(box[0]) + 3] = False
    trace[: int(box[2]) + 3] = False
    trace[80:230, 140:480] = False  # the legend stays
    clean = img.copy()
    clean[trace] = 255
    c2 = Image.fromarray(clean.astype(np.uint8))
    d2 = ImageDraw.Draw(c2)
    for m, col in (("aracne", (0, 0, 255)), ("gecon", (255, 0, 0))):
        ys = np.array(res["ours"][m]) * res["scale"][m]
        pts = [(ax * s + bx, ay * y + by) for s, y in zip(sizes, ys)]
        d2.line(pts, fill=col, width=3)
        for x, y in pts:
            d2.ellipse([x - 10, y - 10, x + 10, y + 10], outline=col, width=3)
    c2.save(os.path.join(outdir, "figures", "fig5_ours.png"))
    res["faster"] = {str(s): bool(rows[s]["gecon_s"] < rows[s]["aracne_total_s"]) for s in sizes}
    json.dump(res, open(os.path.join(outdir, "fig5.json"), "w"), indent=1)
    print(res["scale"], res["ratios"], res["faster"])


if __name__ == "__main__":
    main()
