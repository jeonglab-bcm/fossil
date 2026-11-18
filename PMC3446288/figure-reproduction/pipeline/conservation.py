#!/usr/bin/env python3
"""phastCons profiles for Figs 5, S4, 7a and S5.

Fig. 5 (liver) and Fig. S4 (BMM): mean per-position phastCons (mm9, 30-way vertebrate) around single
exon skipping events, in transcript orientation: the last 25 nt of the upstream exon, 75 nt into its
intron, the 75 nt before the skipped exon, its first and last 25 nt, 75 nt after it, the 75 nt
before the downstream exon and its first 25 nt. Groups: exclusion (dPSI < -0.2) and inclusion
(dPSI > 0.2) events, each PTC+ (the up form carries the PTC) or PTC-, and unregulated events
(-0.2 < dPSI <= 0.2). The yellow line: every internal mm9 RefSeq exon, 25 nt into the exon and 75 nt
into the introns.
Fig. 7a / S5: phastCons in a 100-nt window centred on each stop (positions outside the stop's exon
left out), for up-regulated PTC+ junctions of each tissue and for the stops of all RefSeq models;
minus the mean of 4,000 random exonic windows (expressed exons for the tissues, RefSeq exons for
the normal stops).

Usage: conservation.py EVENTS.tsv.gz FIGURE_DATA.json JUNCTIONS_ANNOTATED.tsv.gz ANNOT_DIR PHASTCONS_DIR OUT.json [--seed N]
"""

import argparse
import gzip
import json
from collections import defaultdict

import numpy as np

from nmdsplice.annotation import read_genepred

E, I = 25, 75
SEG = [E, I, I, E, E, I, I, E]  # 400 positions


def load_chrom(path):
    """phastCons wigFix (gz) to a float32 array (NaN where there is no score)."""
    with gzip.open(path, "rt") as f:
        text = f.read()
    blocks = text.split("fixedStep")
    starts, arrays = [], []
    for b in blocks[1:]:
        head, _, body = b.partition("\n")
        kv = dict(x.split("=") for x in head.split())
        arr = np.array(body.split(), dtype=np.float32)
        starts.append(int(kv["start"]) - 1)
        arrays.append(arr)
    n = max(s + len(a) for s, a in zip(starts, arrays))
    out = np.full(n + 1, np.nan, np.float32)
    for s, a in zip(starts, arrays):
        out[s : s + len(a)] = a
    return out


def take(arr, a, b):
    """Scores at [a, b) (NaN outside the array)."""
    res = np.full(b - a, np.nan, np.float32)
    lo, hi = max(a, 0), min(b, len(arr))
    if hi > lo:
        res[lo - a : hi - a] = arr[lo:hi]
    return res


def ses_windows(up_exon_end, skip_start, skip_end, down_exon_start):
    """Genomic intervals of the eight segments in genomic (+ strand) order."""
    return [(up_exon_end - E, up_exon_end), (up_exon_end, up_exon_end + I),
            (skip_start - I, skip_start), (skip_start, skip_start + E),
            (skip_end - E, skip_end), (skip_end, skip_end + I),
            (down_exon_start - I, down_exon_start), (down_exon_start, down_exon_start + E)]


def profile(arr, wins, strand):
    v = np.concatenate([take(arr, a, b) for a, b in wins])
    return v if strand == "+" else v[::-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("events")
    ap.add_argument("figdata")
    ap.add_argument("junctions")
    ap.add_argument("annot")
    ap.add_argument("phastcons")
    ap.add_argument("out")
    ap.add_argument("--seed", type=int, default=20120524)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)

    # SES events
    groups = defaultdict(list)  # (tissue, group) -> [(chrom, strand, wins)]
    with gzip.open(a.events, "rt") as f:
        hdr = next(f).rstrip("\n").split("\t")
        for line in f:
            r = dict(zip(hdr, line.rstrip("\n").split("\t")))
            if r["class"] != "SES":
                continue
            js = [tuple(map(int, x.split("-"))) for x in r["junctions"].split(";")]
            (d, ac), (d1, a1), (d2, a2) = js
            wins = ses_windows(d, a1, d2, ac)
            dp = float(r["dpsi"])
            if dp < -0.2:
                g = "exclusion_" + ("ptc" if r["ptc_mode"] == "exclusion" else "noptc")
            elif dp > 0.2:
                g = "inclusion_" + ("ptc" if r["ptc_mode"] == "inclusion" else "noptc")
            else:
                g = "unregulated"
            groups[(r["tissue"], g)].append((r["chrom"], r["strand"], wins))

    # RefSeq internal exons (unique)
    ref = read_genepred(f"{a.annot}/refGene.txt.gz", "refGene")
    internal = set()
    stops = set()
    for t in ref:
        for k in range(1, len(t.exons) - 1):
            internal.add((t.chrom, t.strand, t.exons[k - 1][1], t.exons[k][0], t.exons[k][1], t.exons[k + 1][0]))
        if t.coding:
            s = t.cds_end - 3 if t.strand == "+" else t.cds_start
            ex = next(((x, y) for x, y in t.exons if x <= s < y), None)
            if ex:
                stops.add((t.chrom, t.strand, s, ex))
    refseq_exons = [(c, st, ses_windows(u, s, e, d)[2:6]) for c, st, u, s, e, d in internal]
    unique_internal_exons = len({(c, s, e) for c, st, u, s, e, d in internal})

    # Fig. 7a: PTC positions (with their exon) and random expressed exons
    fd = json.load(open(a.figdata))
    stop_exon = {}
    expressed = {"BMM": set(), "Liver": set()}
    with gzip.open(a.junctions, "rt") as f:
        hdr = next(f).rstrip("\n").split("\t")
        for line in f:
            r = dict(zip(hdr, line.rstrip("\n").split("\t")))
            if r["strand"] == "":
                continue
            for t, cols in (("BMM", ("BMM_WT", "BMM_KO")), ("Liver", ("Liver_WT", "Liver_KO"))):
                if int(r[cols[0]]) + int(r[cols[1]]) >= 3:
                    expressed[t].add((r["chrom"], r["strand"], int(r["donor"]), int(r["acceptor"])))
    ex_by = defaultdict(list)
    for t in ref:
        for x, y in t.exons:
            ex_by[t.chrom].append((x, y))
    # exon containing a position: any repository-free approximation: windows clipped at the nearest
    # junction coordinates of expressed junctions are not needed; we clip to RefSeq exons when one
    # contains the stop, else keep the full window.
    for c in ex_by:
        ex_by[c] = sorted(set(ex_by[c]))
    starts = {c: np.array([x for x, _ in v]) for c, v in ex_by.items()}

    def containing_exon(c, p):
        if c not in starts:
            return None
        k = np.searchsorted(starts[c], p, side="right")
        best = None
        for x, y in ex_by[c][max(0, k - 30) : k]:
            if x <= p < y and (best is None or y - x < best[1] - best[0]):
                best = (x, y)
        return best

    ptc_sites = {}
    for t in ("BMM", "Liver"):
        sites = []
        for c, st, p in fd["fig7a_positions"][t]:
            if p < 0:
                continue
            sites.append((c, st, p, containing_exon(c, p)))
        ptc_sites[t] = sites
    # random exons: exons flanked by expressed junctions (acceptor..next donor) of each tissue
    rand_ex = {}
    for t in ("BMM", "Liver"):
        acc = defaultdict(set)
        don = defaultdict(set)
        for c, st, d, ac in expressed[t]:
            acc[(c, st)].add(ac)
            don[(c, st)].add(d)
        cand = []
        for (c, st), aset in acc.items():
            ds = np.array(sorted(don[(c, st)]))
            for ac in aset:
                k = np.searchsorted(ds, ac, side="right")
                if k < len(ds) and ds[k] - ac <= 5000:
                    cand.append((c, st, ac, int(ds[k])))
        idx = rng.choice(len(cand), size=min(4000, len(cand)), replace=False)
        rand_ex[t] = [cand[i] for i in idx]
    refseq_all = sorted({(t.chrom, t.strand, x, y) for t in ref for x, y in t.exons})
    idx = rng.choice(len(refseq_all), size=4000, replace=False)
    rand_ex["RefSeq"] = [refseq_all[i] for i in idx]
    rand_centres = {k: [(c, st, int(rng.integers(x, y)), (x, y)) for c, st, x, y in v] for k, v in rand_ex.items()}

    # accumulate per chromosome
    acc5 = defaultdict(lambda: [np.zeros(400), np.zeros(400), np.zeros(400), 0])  # sum, sumsq, count, events
    acc7 = defaultdict(lambda: [np.zeros(101), np.zeros(101), 0])
    per_event = defaultdict(list)  # (tissue, group) -> [(mean flanking-intron score, mean skipped-exon score)]
    chroms = sorted({c for v in groups.values() for c, _, _ in v} | {c for c, *_ in refseq_exons}
                    | {c for v in ptc_sites.values() for c, *_ in v} | {c for c, *_ in stops})
    for c in chroms:
        path = f"{a.phastcons}/{c}.data.gz"
        try:
            arr = load_chrom(path)
        except FileNotFoundError:
            continue
        for key, lst in list(groups.items()) + [(("all", "refseq"), refseq_exons)]:
            for cc, st, wins in lst:
                if cc != c:
                    continue
                if key[1] == "refseq":
                    v = profile(arr, wins, st)
                    full = np.full(400, np.nan, np.float32)
                    full[100:300] = v
                    v = full
                else:
                    v = profile(arr, wins, st)
                if key[1] != "refseq":
                    per_event[key].append((float(np.nanmean(np.r_[v[100:175], v[225:300]])), float(np.nanmean(v[175:225]))))
                ok = ~np.isnan(v)
                s = acc5[key]
                s[0][ok] += v[ok]
                s[1][ok] += v[ok] ** 2
                s[2][ok] += 1
                s[3] += 1

        def window(st, p, ex):
            w = take(arr, p - 50, p + 51)
            if ex is not None:
                pos = np.arange(p - 50, p + 51)
                w[(pos < ex[0]) | (pos >= ex[1])] = np.nan
            return w if st == "+" else w[::-1]

        for t, sites in ptc_sites.items():
            for cc, st, p, ex in sites:
                if cc == c:
                    w = window(st, p, ex)
                    ok = ~np.isnan(w)
                    acc7[t][0][ok] += w[ok]
                    acc7[t][1][ok] += 1
                    acc7[t][2] += 1
        for cc, st, p, ex in stops:
            if cc == c:
                w = window(st, p, ex)
                ok = ~np.isnan(w)
                acc7["RefSeq_STOP"][0][ok] += w[ok]
                acc7["RefSeq_STOP"][1][ok] += 1
                acc7["RefSeq_STOP"][2] += 1
        for k, lst in rand_centres.items():
            for cc, st, p, ex in lst:
                if cc == c:
                    w = window(st, p, ex)
                    ok = ~np.isnan(w)
                    acc7["random_" + k][0][ok] += w[ok]
                    acc7["random_" + k][1][ok] += 1
                    acc7["random_" + k][2] += 1
        del arr
    res = {"fig5": {}, "fig7a": {}, "refseq_internal_exons": unique_internal_exons,
           "refseq_exon_windows": len(refseq_exons)}
    for (t, g), (s, ss, n, ne) in acc5.items():
        with np.errstate(invalid="ignore", divide="ignore"):
            mean = s / n
            sem = np.sqrt(np.maximum(ss / n - mean ** 2, 0) / np.maximum(n - 1, 1))
        res["fig5"][f"{t}:{g}"] = {"events": int(ne), "mean": np.where(n > 0, mean, np.nan).tolist(),
                                   "sem": np.where(n > 1, sem, np.nan).tolist()}
    from scipy.stats import ks_2samp
    ks = {}
    for t in ("BMM", "Liver"):
        def col(g, i):
            return np.array([x[i] for x in per_event.get((t, g), []) if np.isfinite(x[i])])
        for mode in ("exclusion", "inclusion"):
            reg = np.r_[col(f"{mode}_ptc", 0), col(f"{mode}_noptc", 0)]
            un = col("unregulated", 0)
            if len(reg) and len(un):
                ks[f"{t}:{mode}_vs_unregulated_intron"] = {"p": float(ks_2samp(reg, un).pvalue),
                                                           "regulated_mean": float(reg.mean()), "unregulated_mean": float(un.mean())}
            a_, b_ = col(f"{mode}_noptc", 0), col(f"{mode}_ptc", 0)
            if len(a_) and len(b_):
                ks[f"{t}:{mode}_noptc_vs_ptc_intron"] = {"p": float(ks_2samp(a_, b_).pvalue), "noptc_mean": float(a_.mean()), "ptc_mean": float(b_.mean())}
            a_, b_ = col(f"{mode}_ptc", 1), col(f"{mode}_noptc", 1)
            if len(a_) and len(b_):
                ks[f"{t}:{mode}_ptc_vs_noptc_exon"] = {"p": float(ks_2samp(a_, b_).pvalue), "ptc_mean": float(a_.mean()), "noptc_mean": float(b_.mean())}
    res["ks"] = ks
    for k, (s, n, ne) in acc7.items():
        with np.errstate(invalid="ignore", divide="ignore"):
            res["fig7a"][k] = {"positions": int(ne), "mean": (s / n).tolist()}
    def clean(x):
        if isinstance(x, dict):
            return {k: clean(v) for k, v in x.items()}
        if isinstance(x, list):
            return [clean(v) for v in x]
        if isinstance(x, float) and not np.isfinite(x):
            return None
        return x

    with open(a.out, "w") as fo:
        json.dump(clean(res), fo, allow_nan=False)


if __name__ == "__main__":
    main()
