"""Conditional location maps (CLMs) for normal brain, low- and high-grade glioma, and everything read from them.

conditional.py RUN OUTDIR

Writes OUTDIR/clm.json (counts, named proteins, Fig. 3I/J, mislocations, Fig. 5A, the blinded and
validated candidates, the KIF13A links) and RUN/clm.npz (every possibility degree).
"""

from __future__ import annotations

import collections
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import dump, load_proteome, load_studies  # noqa: E402
from settings import ALPHA, CONDITIONS, K, LOCATIONS, RHO, THRESHOLD  # noqa: E402

from condloc.dcknn import null_threshold  # noqa: E402
from condloc.model import (Model, condition_link_weights, knn_counts, network_sets,  # noqa: E402
                           possibility_map, weighted_adjacency)

# Published conditional location maps: the location marked H in each condition (normal, low, high).
PUBLISHED_TOP = {
    "NKX2-2": ("ER", "ER", "ER"),      # Fig. 3A
    "CPB1": ("CY", "ER", "ER"),        # Fig. 3E
    "KIF13A": ("GL", "NU", "NU"),      # Fig. 4A
    "RNF138": ("ER", "NU", "NU"),      # Fig. 5B
    "TLX3": ("NU", "ER", "ER"),        # Fig. 5C
    "GFRA4": ("PM", "ER", "ER"),       # Fig. 6A
    "PSPN": ("PM", "ER", "ER"),        # Fig. 6B
    "RET": ("PM", "PM", "PM"),         # Fig. 6C
    "SMAD4": ("NU", "NU", "NU"),       # text, Suppl. Fig. S6A
}

# Fig. 3I, read from the figure: condition of each column and the observed (+) locations among CY, ER, GL, NU, PM.
FIG3I_LOCS = ["CY", "ER", "GL", "NU", "PM"]
FIG3I = {
    "normal": {"AGAP1": "CY", "CPB1": "CY", "FOXO1": "NU", "MAPK1": "NU", "P2RX7": "CY PM", "PSPN": "PM",
               "SNAI2": "CY NU", "STAT3": "PM"},
    "low": {"ARFGEF2": "CY ER GL", "BACE1": "ER GL PM", "FOLH1": "PM", "GSK3B": "NU", "NFRKB": "NU",
            "SMAD4": "NU", "SOX10": "CY NU"},
    "high": {"CYTH4": "ER GL", "NKX2-2": "ER", "PSEN1": "ER", "REV3L": "ER", "SOX2": "NU"},
}

# Text: blinded test (predicted mislocating, then predicted stable) and the 15 validated mislocations.
BLINDED_MISLOCATING = {"ATIC": "CY>NU", "DIP2A": "NU>ER", "DLX2": "ER>NU", "HPS5": "PM>ER", "TBX19": "ER>NU"}
BLINDED_STABLE = {"CDH2": "PM", "HSF1": "NU", "MAGED1": "CY", "PAX6": "NU", "STAT3": "NU"}
VALIDATED = {"KIF13A": "GL>NU", "RNF138": "ER>NU", "TLX3": "NU>ER", "PSPN": "PM>ER", "GFRA4": "PM>ER",
             "ATIC": "CY>NU", "DIP2A": "NU>ER", "DLX2": "ER>NU", "TBX19": "ER>NU", "AGAP1": "CY>GL",
             "CPB1": "CY>ER", "NFRKB": "ER>NU", "ARHGEF15": "ER>PM", "CLK2": "ER>NU", "SYT9": "GL>NU"}
FIG5A = {"ER>NU": "21.66", "NU>ER": "15.92", "PM>ER": "12.10", "ER>PM": "6.37", "CY>ER": "5.73",
         "PM>NU": "3.82", "CY>NU": "3.18"}
KIF13A_LINKS = ["AP1G1", "COG2", "ATF7IP"]


def mislocation(pv: np.ndarray, hv: np.ndarray) -> str | None:
    """'F>T' when the top location in normal brain (F) differs from the top location in both gliomas (T),
    and T is a high-confidence location (P < 0.005) in both gliomas but not in normal brain.
    Stricter and looser variants are counted in mislocation_variants()."""
    top = pv.argmax(axis=0)
    f, t_low, t_high = top
    if t_low != t_high or t_low == f:
        return None
    t = t_low
    if hv[t, 1] and hv[t, 2] and not hv[t, 0]:
        return f"{LOCATIONS[f]}>{LOCATIONS[t]}"
    return None


def mislocation_variants(P: np.ndarray, H: np.ndarray, rows: np.ndarray) -> dict:
    """How many proteins each version of the (unstated) mislocation test calls."""
    P, H = P[rows], H[rows]
    top = P.argmax(axis=1)
    i = np.arange(len(P))
    f, t = top[:, 0], top[:, 1]
    chg = (top[:, 1] == top[:, 2]) & (t != f)
    gain = chg & H[i, t, 1] & H[i, t, 2]
    ours = gain & ~H[i, t, 0]
    strict = ours & H[i, f, 0] & ~H[i, f, 1] & ~H[i, f, 2]
    return {"top_location_changes": int(chg.sum()), "target_high_in_both_gliomas": int(gain.sum()),
            "ours_target_not_high_in_normal": int(ours.sum()), "strict_source_lost": int(strict.sum())}


def call(pv: np.ndarray | None, hv: np.ndarray | None = None) -> str:
    if pv is None:
        return "not in proteome"
    m = mislocation(pv, hv)
    if m:
        return m
    top = [LOCATIONS[i] for i in pv.argmax(axis=0)]
    return top[0] if len(set(top)) == 1 else "/".join(top)


def main(run: Path, out: Path) -> None:
    t0 = time.time()
    p, symbol = load_proteome(run)
    model_js = json.load(open(out / "model.json"))
    model = Model({LOCATIONS.index(k): v for k, v in model_js["selected"].items()},
                  {LOCATIONS.index(k): v for k, v in model_js["weights"].items()}, K)
    used = sorted({m for v in model.selected.values() for m in v})
    s_used = [m for m in used if m in p.s]
    net_used = [m for m in used if m not in p.s]
    gold = np.flatnonzero(p.known)
    s_counts = knn_counts({m: p.s[m] for m in s_used}, p)
    studies = load_studies(run)
    n = len(p.accessions)
    P = np.zeros((n, len(LOCATIONS), len(CONDITIONS)))
    H = np.zeros((n, len(LOCATIONS), len(CONDITIONS)), dtype=bool)
    thresholds = {}
    link_w = {}
    for ci, cond in enumerate(CONDITIONS):
        w = condition_link_weights(p, [(g, x) for g, x, _ in studies[cond]])
        link_w[cond] = w
        sets = network_sets(p, link_weight=weighted_adjacency(p, w), rho=RHO)
        counts = {**s_counts, **knn_counts({m: sets[m] for m in net_used}, p)}
        conf = model.confidence(counts)
        P[:, :, ci] = possibility_map(conf, conf[gold], p.labels[gold])
        thr = [null_threshold(conf[gold][~p.labels[gold][:, loc], loc], ALPHA) for loc in range(len(LOCATIONS))]
        H[:, :, ci] = conf > np.array(thr)[None, :]
        thresholds[cond] = {"confidence": thr, "possibility": [float(P[:, loc, ci][conf[:, loc] > thr[loc]].min())
                            if (conf[:, loc] > thr[loc]).any() else None for loc, _ in enumerate(LOCATIONS)]}
        print(f"{cond}: CLM done ({time.time() - t0:.0f} s)", flush=True)
    np.savez_compressed(run / "clm.npz", P=P.astype(np.float32), H=H, accessions=np.array(p.accessions))

    by_symbol = {}
    for i, a in enumerate(p.accessions):
        by_symbol.setdefault(symbol[a].upper(), i)
    degree = np.zeros(n, dtype=int)
    for i, j in p.edges:
        degree[i] += 1
        degree[j] += 1
    in_net = degree > 0

    def pv(sym):
        i = by_symbol.get(sym.upper())
        return None if i is None else P[i]

    def hv(sym):
        i = by_symbol.get(sym.upper())
        return None if i is None else H[i]

    hi = H
    lit = P >= THRESHOLD
    res = {"threshold": THRESHOLD, "alpha": ALPHA, "thresholds": thresholds, "network_proteins": int(in_net.sum())}
    res["literal_040"] = {"locations": int(lit[in_net].sum()), "proteins": int(lit[in_net].any(axis=(1, 2)).sum()),
                          "median_possibility": float(np.median(P[in_net]))}
    res["high_confidence"] = {
        "locations": int(hi[in_net].sum()), "proteins": int(hi[in_net].any(axis=(1, 2)).sum()),
        "locations_unknown": int(hi[in_net & ~p.known].sum()),
        "proteins_unknown": int(hi[in_net & ~p.known].any(axis=(1, 2)).sum()),
        "per_condition": {c: int(hi[in_net, :, ci].sum()) for ci, c in enumerate(CONDITIONS)}}

    named = {}
    for sym, pub in PUBLISHED_TOP.items():
        v = pv(sym)
        named[sym] = {"published": list(pub), "ours": None if v is None else [LOCATIONS[i] for i in v.argmax(axis=0)],
                      "P": None if v is None else v.T, "known": None if v is None else
                      [LOCATIONS[j] for j in np.flatnonzero(p.labels[by_symbol[sym.upper()]])]}
    res["named"] = named

    conf_m = collections.Counter()
    cells = []
    for ci, cond in enumerate(CONDITIONS):
        for sym, obs in FIG3I.get(cond, {}).items():
            v = pv(sym)
            for loc in FIG3I_LOCS:
                actual = loc in obs.split()
                pred = None if v is None else bool(hv(sym)[LOCATIONS.index(loc), ci])
                key = "missing" if pred is None else ("TP" if pred and actual else "FN" if actual else
                                                      "FP" if pred else "TN")
                conf_m[key] += 1
                cells.append({"protein": sym, "condition": cond, "location": loc, "actual": actual,
                              "predicted": pred, "P": None if v is None else v[LOCATIONS.index(loc), ci]})
    res["fig3i"] = {"cells": cells, "counts": dict(conf_m), "correct": conf_m["TP"] + conf_m["TN"]}

    mis = {}
    for i in np.flatnonzero(in_net):
        m = mislocation(P[i], H[i])
        if m:
            mis[p.accessions[i]] = m
    kinds = collections.Counter(mis.values())
    res["mislocation_variants"] = mislocation_variants(P, H, np.flatnonzero(in_net))
    res["mislocations"] = {"count": len(mis), "by_kind": dict(kinds.most_common()),
                           "share": {k: 100.0 * v / max(len(mis), 1) for k, v in kinds.items()},
                           "proteins": {symbol[a]: m for a, m in sorted(mis.items(), key=lambda t: symbol[t[0]])}}
    res["fig5a"] = {"published": FIG5A, "ours": {k: 100.0 * kinds.get(k, 0) / max(len(mis), 1) for k in FIG5A},
                    "top7_ours": [k for k, _ in kinds.most_common(7)]}
    res["blinded"] = {"mislocating": {s: {"published": v, "ours": call(pv(s), hv(s))} for s, v in BLINDED_MISLOCATING.items()},
                      "stable": {s: {"published": v, "ours": call(pv(s), hv(s))} for s, v in BLINDED_STABLE.items()}}
    res["validated"] = {s: {"published": v, "ours": call(pv(s), hv(s))} for s, v in VALIDATED.items()}

    links = {}
    k = by_symbol.get("KIF13A")
    for sym in KIF13A_LINKS:
        j = by_symbol.get(sym)
        hit = None
        if k is not None and j is not None:
            a, b = sorted((k, j))
            idx = np.flatnonzero((p.edges[:, 0] == a) & (p.edges[:, 1] == b))
            if len(idx):
                hit = {c: float(link_w[c][idx[0]]) for c in CONDITIONS}
        links[sym] = hit
    res["kif13a_links"] = links
    res["kif13a_degree"] = int(degree[k]) if k is not None else 0
    dump(res, out / "clm.json")
    print(json.dumps({"high_confidence": res["high_confidence"], "fig3i": res["fig3i"]["counts"],
                      "mislocations": len(mis), "top": res["fig5a"]["top7_ours"]}, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
