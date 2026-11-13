"""Two executable checks that back the reconstruction.

pseudolik : the divergence-time traversal behind the genetic pseudo-likelihood
            (Eq. 5) reproduces div(i,j) for every pair in the worked four-premise
            example of Fig. S1 (Text S1 Eq. 3).
arithmetic: numbers that can be recomputed from the paper's own data agree with
            the text (IP5 is 18.2 km from IP1b; the distance spans).

    checks.py pseudolik  --out pseudolik_check.json
    checks.py arithmetic --sources DIR --out arithmetic_check.json
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from transtree.core import divergence_premise
import datasets as D


def pseudolik_check():
    j, i, k, l = 0, 1, 2, 3
    J = np.array([-1, j, j, i])
    Tinf = np.array([0.0, 1.0, 2.0, 3.0])
    expected = {(i, j): i, (k, j): k, (k, i): i, (l, j): i, (l, i): l, (l, k): i}
    ok = True
    for (a, b), want in expected.items():
        if not (divergence_premise(a, b, J, Tinf) == want == divergence_premise(b, a, J, Tinf)):
            ok = False
    return {"passed": ok,
            "detail": f"divergence traversal matches all {len(expected)} pairs of the Fig. S1 example"}


def arithmetic_check(sources):
    d07 = D.load_real(sources, "y2007")
    d01 = D.load_real(sources, "y2001")
    i1 = d07.names.index("IP1b"); i5 = d07.names.index("IP5")
    ip5 = float(np.hypot(*(d07.X[i5] - d07.X[i1])))
    def span(X):
        dd = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
        return float(dd.max())
    checks = {
        "IP5-IP1b km (paper 18.2)": (ip5, 18.2, 0.2),
        "2007 distance span km (~24)": (span(d07.X), 24.0, 3.0),
        "2001 distance span km (~16)": (span(d01.X), 16.0, 3.0),
    }
    results = {k: {"observed": round(v, 2), "expected": e, "ok": abs(v - e) <= tol}
               for k, (v, e, tol) in checks.items()}
    passed = all(r["ok"] for r in results.values())
    return {"passed": passed,
            "detail": f"{sum(r['ok'] for r in results.values())} of {len(results)} data arithmetic checks agree with the text",
            "results": results}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["pseudolik", "arithmetic"])
    ap.add_argument("--sources", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.which == "pseudolik":
        rep = pseudolik_check()
    else:
        rep = arithmetic_check(args.sources)
    json.dump(rep, open(args.out, "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
