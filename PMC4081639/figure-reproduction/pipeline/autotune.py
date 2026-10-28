import sys, json
import numpy as np
sys.path.insert(0, ".")
from fit_render import fit, paper, SPEC
from offsets import runs, best_shift
def regions(P, box):
    x0, x1, y0, y1 = box; D = P < 170; R = {}
    rl = runs(D[:, :x0 - 1].sum(0))
    R["ytitle"] = (rl[0][0], rl[0][1], 0, P.shape[0])
    lab = rl[1] if len(rl) >= 3 else rl[-1]
    R["yticks"] = (lab[0], lab[1], y0 - 8, y1 + 8)
    rb = runs(D[y1 + 2:, :].sum(1))
    if len(rb) >= 3:
        R["xticks"] = (x0 - 20, P.shape[1], y1 + 2 + rb[1][0], y1 + 2 + rb[1][1])
        R["xtitle"] = (x0, P.shape[1], y1 + 2 + rb[-1][0], y1 + 2 + rb[-1][1])
    else:
        R["xrot"] = (x0, P.shape[1], y1 + 2 + rb[-1][0], y1 + 2 + rb[-1][1])
    if x1 + 3 < P.shape[1] and D[:, x1 + 3:].sum() > 50: R["legend"] = (x1 + 3, P.shape[1], 0, P.shape[0])
    if y0 > 30:
        ra = runs(D[:y0 - 1, x0:x1].sum(1)); R["title"] = (x0, x1, ra[0][0], ra[0][1])
    return R
fig, font, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3])
p = dict(xtitle_gap=2.75, ytitle_gap=2.75, ytitle_hjust=0.5, legend_space=5.67, legend_vjust=0.5, title_gap=5.5, xtext_gap=2.85, xtext_vjust=0.5)
p.update(json.loads(sys.argv[4]) if len(sys.argv) > 4 else {})
skip = set(sys.argv[5].split(",")) if len(sys.argv) > 5 else set()
P = paper(fig); R = regions(P, SPEC[fig]["box"]); k = 72 / dpi
x0, x1, y0, y1 = SPEC[fig]["box"]
for it in range(3):
    r, al = fit(fig, font, dpi, p)
    off = {n: best_shift(al, P, reg)[1:] for n, reg in R.items()}
    print(f"iter {it} score {r['score']:.3f}", {n: v for n, v in off.items()}, flush=True)
    if it == 2: break
    if "ytitle" not in skip: dx, dy = off["ytitle"]; p["ytitle_gap"] -= dx * k; p["ytitle_hjust"] -= dy / (y1 - y0)
    if "xtitle" in off: p["xtitle_gap"] += off["xtitle"][1] * k
    if "xrot" in off and "xrot" not in skip: dx, dy = off["xrot"]; p["xtext_gap"] += dy * k; p["xtext_vjust"] += dx / 16.0
    if "legend" in off: dx, dy = off["legend"]; p["legend_space"] += dx * k; p["legend_vjust"] -= dy / P.shape[0]
    if "title" in off: p["title_gap"] -= off["title"][1] * k
print("PARAMS", json.dumps({"fig": fig, "font": font, "dpi": dpi, "W": r["W"], "H": r["H"], "shift": r["shift"], "score": r["score"], "p": p}))
