import sys, json
import numpy as np
sys.path.insert(0, ".")
from fit_render import fit, paper, SPEC
def runs(proj, gap=3):
    idx = np.where(proj > 0)[0]
    if not len(idx): return []
    out, s, p = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - p > gap: out.append((s, p)); s = i
        p = i
    out.append((s, p)); return out
def regions(P, box):
    x0, x1, y0, y1 = box; D = P < 170; R = {}
    left = D[:, :x0 - 1]; rl = runs(left.sum(0))
    if rl: R["ytitle"] = (rl[0][0], rl[0][1], 0, P.shape[0]); R["yticks"] = (rl[-1][0], x0 - 2, y0 - 8, y1 + 8)
    below = D[y1 + 2:, :]; rb = runs(below.sum(1))
    if rb: R["xticks"] = (x0 - 20, P.shape[1], y1 + 2 + rb[0][0], y1 + 2 + rb[0][1]); R["xtitle"] = (x0, P.shape[1], y1 + 2 + rb[-1][0], y1 + 2 + rb[-1][1])
    if x1 + 3 < P.shape[1] and D[:, x1 + 3:].sum() > 50: R["legend"] = (x1 + 3, P.shape[1], 0, P.shape[0])
    if y0 > 30: ra = runs(D[:y0 - 1, x0:x1].sum(1)); R["title"] = (x0, x1, ra[0][0], ra[0][1]) if ra else None; R["strip"] = (x0, x1, ra[-1][0], y0 - 1) if len(ra) > 1 else None
    return {k: v for k, v in R.items() if v}
def best_shift(al, P, r, s=10):
    xa, xb, ya, yb = r; best = None
    for dy in range(-s, s + 1):
        for dx in range(-s, s + 1):
            ya2, yb2, xa2, xb2 = max(ya, s), min(yb, P.shape[0] - s - 1), max(xa, s), min(xb, P.shape[1] - s - 1)
            a = al[ya2 - dy:yb2 - dy + 1, xa2 - dx:xb2 - dx + 1]; b = P[ya2:yb2 + 1, xa2:xb2 + 1]
            v = np.abs(a - b).mean()
            if best is None or v < best[0]: best = (v, dx, dy)
    return best
if __name__ == "__main__":
    fig, font, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3])
    extra = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
    r, al = fit(fig, font, dpi, extra)
    P = paper(fig); R = regions(P, SPEC[fig]["box"])
    print(fig, "fit", json.dumps({k: r[k] for k in ("W", "H", "shift", "score")}))
    for k, reg in R.items():
        v, dx, dy = best_shift(al, P, reg)
        print("  %-7s region %-22s ours needs dx=%+d dy=%+d px  (%.1f pt, %.1f pt)" % (k, reg, dx, dy, dx * 72 / dpi, dy * 72 / dpi))
