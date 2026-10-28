import json, os, subprocess, sys, tempfile, shutil
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.environ.get("FOSSIL_PUBLISHED", os.path.join(HERE, "..", "published"))
DATA = os.environ.get("FOSSIL_DATA", os.getcwd())
GREY = lambda v: "#%02X%02X%02X" % (v, v, v)

SPEC = {  # paper panel value, panel bbox (x0,x1,y0,y1), strip, legend key
    "2": dict(pv=233, box=(143, 509, 15, 444), strip=212, key=244),
    "4": dict(pv=238, box=(105, 433, 10, 419), strip=212, key=249),
    "5": dict(pv=238, box=(77, 458, 15, 424), strip=212, key=249),
    "6": dict(pv=233, box=(83, 571, 61, 312), strip=212, key=244),
}


def paper(fig):
    return np.asarray(Image.open(f"{PAPER}/figure-{fig}.jpg").convert("L")).astype(float)


def panel_box(a, pv, tol):
    m = np.abs(a - pv) <= tol
    cs = np.where(m.sum(0) > a.shape[0] * 0.25)[0]
    rs = np.where(m.sum(1) > a.shape[1] * 0.12)[0]
    return cs.min(), cs.max(), rs.min(), rs.max()


def render(fig, font, W, H, dpi, extra=None, keep=None, dpiy=None):
    s = SPEC[fig]
    cfg = dict(fig=fig, font=font, W=W, H=H, datadir=DATA,
               panel=GREY(s["pv"]), minor=GREY((s["pv"] + 255) // 2), strip=GREY(s["strip"]), key=GREY(s["key"]),
               xtitle_gap=2.75, ytitle_gap=2.75, legend_pad=5.5, strip_pad=4.4, title_gap=5.5)
    cfg.update(extra or {})
    d = tempfile.mkdtemp(dir=DATA)
    try:
        cfg["tex"] = os.path.join(d, "f.tex")
        json.dump(cfg, open(os.path.join(d, "cfg.json"), "w"))
        subprocess.run(["Rscript", os.path.join(HERE, "plot_fig.R"), os.path.join(d, "cfg.json")], check=True, capture_output=True)
        subprocess.run(["pdflatex", "-interaction=batchmode", "f.tex"], cwd=d, check=True, capture_output=True)
        subprocess.run(["pdftoppm", "-rx", str(dpi), "-ry", str(dpiy or dpi), "-gray", "-png", "-singlefile", "f.pdf", "f"], cwd=d, check=True, capture_output=True)
        if keep:
            shutil.copy(os.path.join(d, "f.pdf"), keep + ".pdf")
            shutil.copy(os.path.join(d, "f.tex"), keep + ".tex")
        return np.asarray(Image.open(os.path.join(d, "f.png")).convert("L")).astype(float)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def align(ours, fig):
    s = SPEC[fig]; P = paper(fig)
    ox0, _, oy0, _ = panel_box(ours, s["pv"], 2)
    px0, _, py0, _ = s["box"]
    out = np.full(P.shape, 255.0)
    dy, dx = py0 - oy0, px0 - ox0
    h, w = ours.shape
    ys, xs = max(0, dy), max(0, dx)
    ye, xe = min(P.shape[0], h + dy), min(P.shape[1], w + dx)
    out[ys:ye, xs:xe] = ours[ys - dy:ye - dy, xs - dx:xe - dx]
    return out, (dx, dy)


def fit(fig, font, dpi, extra=None, keep=None, dpiy=None):
    dpiy = dpiy or dpi
    s = SPEC[fig]; P = paper(fig)
    tx0, tx1, ty0, ty1 = s["box"]
    W, H = P.shape[1] / dpi, P.shape[0] / dpiy
    for _ in range(3):
        a = render(fig, font, W, H, dpi, extra, dpiy=dpiy)
        x0, x1, y0, y1 = panel_box(a, s["pv"], 2)
        W += ((tx1 - tx0) - (x1 - x0)) / dpi
        H += ((ty1 - ty0) - (y1 - y0)) / dpiy
    a = render(fig, font, W, H, dpi, extra, keep, dpiy=dpiy)
    al, shift = align(a, fig)
    x0, x1, y0, y1 = s["box"]
    m = np.ones(P.shape, bool); m[y0:y1 + 1, x0:x1 + 1] = False
    return dict(W=W, H=H, dpi=dpi, dpiy=dpiy, shift=tuple(int(v) for v in shift), score=float(np.abs(al - P).mean()),
                text=float(np.abs(al - P)[m].mean()),
                box=panel_box(a, s["pv"], 2)), al


if __name__ == "__main__":
    fig = sys.argv[1]
    best = None
    for font in ("cm", "times"):
        for dpi in (100, 115, 130, 145, 160, 175, 190):
            r, _ = fit(fig, font, dpi)
            print(fig, font, dpi, "W=%.2f H=%.2f shift=%s score=%.3f text=%.3f" % (r["W"], r["H"], r["shift"], r["score"], r["text"]), flush=True)
            if best is None or r["text"] < best[0]["text"]:
                best = (r, font)
    print("BEST", fig, best[1], json.dumps(best[0], default=int))
