"""Hypothesis tests for the gaps between our run and the paper. Not part of the main run.

Usage: studies.py ALNDIR_SOURCE OUT.json [--alt-aln DIR] [--shriner FASTA --genbank GB
       --clinical TSV --muscle EXE]

1. The MUSCLE build: the same MUSCLE 3.6 release as a 2005 ia32 binary and as a build of its
   source give different alignments; how far does the estimate move?
2. The sequence set: LANL's special interest set 1 holds 212 more sequences (Shriner et al. 2004,
   accessions AY348xxx) for patients 2, 3, 7, 8 and 9, which the paper's accession list leaves out.
3. The average <M pA pB>: the paper reports 0.93. Which averaging convention comes closest?
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from hivrecomb.align import codon_align, read_fasta, write_fasta
from hivrecomb.recombination import (
    as_array,
    concat_events,
    estimate_rho,
    mean_MpApB,
    pair_events,
)

GEN = 365.25 / 12 / 2


def events_of(alndir):
    per = []
    for p in range(1, 12):
        path = Path(alndir) / f"p{p}.fasta"
        if not path.exists():
            continue
        a = read_fasta(path)
        names = list(a)
        X = as_array([a[n] for n in names])
        t = np.array([float(n.split("|")[1]) for n in names]) * GEN
        per.append(pair_events(X, t, patient=p))
    return per


def summary(per):
    ev = concat_events(per)
    f = estimate_rho(ev, weights="relative")
    return {"pairs": int(len(ev["d"])), "c0": f.c0, "c1": f.c1, "c2": f.c2,
            "MpApB": f.MpApB, "rho": f.rho}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("alndir")
    ap.add_argument("out")
    ap.add_argument("--alt-aln")
    ap.add_argument("--shriner")
    ap.add_argument("--genbank")
    ap.add_argument("--clinical")
    ap.add_argument("--muscle")
    a = ap.parse_args(argv)

    res = {"note": "Hypothesis tests, not part of the pipeline's results. See the README."}
    base_per = events_of(a.alndir)
    res["muscle_source_build"] = summary(base_per)

    if a.alt_aln and Path(a.alt_aln).exists():
        res["muscle_2005_binary"] = summary(events_of(a.alt_aln))

    if a.shriner and a.genbank and a.muscle:
        sys.path.insert(0, str(Path(__file__).parent))
        from prepare_data import parse_name, visit_months

        from Bio import SeqIO

        visits = visit_months(a.clinical)
        seqs: dict[int, dict[str, str]] = {}
        for r in SeqIO.parse(a.genbank, "genbank"):
            if not r.annotations.get("organism", "").startswith("Human immunodeficiency virus 1"):
                continue
            q = r.features[0].qualifiers
            name = (q.get("clone") or q.get("isolate"))[0]
            cds = [f for f in r.features if f.type == "CDS"]
            if not cds:
                continue
            patient, month, _ = parse_name(name, visits)
            start = int(cds[0].qualifiers.get("codon_start", ["1"])[0]) - 1
            nt = str(r.seq).upper()[start:]
            seqs.setdefault(patient, {})[f"{r.id}|{month}"] = nt[: len(nt) - len(nt) % 3]
        extra = read_fasta(a.shriner)
        added = 0
        for name, s in extra.items():
            parts = name.split(".")
            patient, month, _ = parse_name(parts[3] + "-1", visits)
            s = s.upper().replace("-", "")
            s = s[: len(s) - len(s) % 3]
            seqs[patient][f"{parts[4]}|{month}"] = s
            added += 1
        tmp = Path(a.out).parent / "aln_with_shriner"
        tmp.mkdir(parents=True, exist_ok=True)
        for p, d in seqs.items():
            write_fasta(codon_align(d, muscle=a.muscle), tmp / f"p{p}.fasta")
        res["with_shriner_sequences"] = dict(summary(events_of(tmp)), added=added)

    # bins of Figure 2A, seeds of the bootstrap, the hitch-hiking window, the codon background
    from hivrecomb.recombination import bin_events, bootstrap_rho, fit_saturation
    from hivrecomb.selection import concat_rates, frequency_changes, ks, linked_mask, share_above

    ev = concat_events(base_per)
    res["fig2a_bins"] = {}
    for nb in (6, 7, 8):
        b = bin_events(ev["d"], ev["found"], np.linspace(0.0, 536.0, nb + 1))
        o = bin_events(ev["d"], ev["other"], np.linspace(0.0, 536.0, nb + 1))
        ok = o.counts > 0
        slope = float(np.polyfit(o.centers[ok], o.p[ok], 1)[0])
        res["fig2a_bins"][str(nb)] = {"recombinant": [None if not np.isfinite(v) else round(v, 4)
                                                      for v in b.p],
                                      "other_rise_over_500bp": round(slope * 500, 4)}
    if "muscle_2005_binary" in res:
        ev2 = concat_events(events_of(a.alt_aln))
        o2 = bin_events(ev2["d"], ev2["other"], np.linspace(0.0, 536.0, 8))
        ok = o2.counts > 0
        res["muscle_2005_binary"]["other_rise_over_500bp"] = round(
            float(np.polyfit(o2.centers[ok], o2.p[ok], 1)[0]) * 500, 4)
        b2 = estimate_rho(ev2, weights="relative").binned
        res["muscle_2005_binary"]["fig2b_p"] = [None if not np.isfinite(v) else round(v, 4)
                                                for v in b2.p[:9]]
        bs2 = bootstrap_rho(events_of(a.alt_aln), n=500, seed=0, weights="relative")
        res["muscle_2005_binary"]["bootstrap"] = {"mean": float(np.mean(bs2)),
                                                  "median": float(np.median(bs2)),
                                                  "std": float(np.std(bs2))}
    res["bootstrap_seeds"] = {}
    for seed in range(6):
        bs = bootstrap_rho(base_per, n=500, seed=seed, weights="relative")
        res["bootstrap_seeds"][str(seed)] = {"mean": float(np.mean(bs)), "std": float(np.std(bs))}
    res["fit_start_values_min_count_4"] = []
    per4 = []
    for p in range(1, 12):
        path = Path(a.alndir) / f"p{p}.fasta"
        aln = read_fasta(path)
        names = list(aln)
        per4.append(pair_events(as_array([aln[n] for n in names]),
                                np.array([float(n.split("|")[1]) for n in names]) * GEN,
                                patient=p, min_count=4))
    ev4 = concat_events(per4)
    b4 = estimate_rho(ev4, weights="relative").binned
    for p0 in ((0.05, 0.1, 1e-5), (0.1, 0.25, 4e-5), (0.3, 0.3, 1e-4)):
        c = fit_saturation(b4, p0=p0, weights="relative")
        res["fit_start_values_min_count_4"].append({"start": list(p0), "c0": c[0], "c1": c[1],
                                                    "c2": c[2]})
    res["pairs_min_count_4"] = int(len(ev4["d"]))

    rates = concat_rates([frequency_changes(
        as_array([read_fasta(Path(a.alndir) / f"p{p}.fasta")[n]
                  for n in read_fasta(Path(a.alndir) / f"p{p}.fasta")]),
        np.array([float(n.split("|")[1]) for n in read_fasta(Path(a.alndir) / f"p{p}.fasta")]) * GEN,
        patient=p) for p in range(1, 12)])
    syn = rates["synonymous"].astype(bool)
    res["hitchhiking_window"] = {}
    for w in (50.0, 100.0, 150.0, 200.0):
        keep = syn & ~linked_mask(rates, window=w)
        r = rates["rate"][keep]
        D, pv = ks(rates["rate"][~syn], r)
        res["hitchhiking_window"][str(int(w))] = {"observations": int(keep.sum()),
                                                  "max_rate": float(r.max()), "D": D, "p": pv,
                                                  "share_above_0.002": share_above(r, 0.002)}
    # the codon background: the consensus of the later sample instead of the earlier one
    import hivrecomb.selection as hsel

    orig = hsel.consensus
    store = {}

    def later_consensus(block):
        return store.get("next", orig(block))

    rows = []
    for p in range(1, 12):
        aln = read_fasta(Path(a.alndir) / f"p{p}.fasta")
        names = list(aln)
        X = as_array([aln[n] for n in names])
        t = np.array([float(n.split("|")[1]) for n in names]) * GEN
        tps = np.unique(t)
        # rebuild with the consensus of t_{i+1}: patch consensus() per pair of samples
        for t0, t1 in zip(tps[:-1], tps[1:]):
            store["next"] = orig(X[t == t1])
            hsel.consensus = later_consensus
            sub = np.isin(t, [t0, t1])
            rows.append(frequency_changes(X[sub], t[sub], patient=p))
        hsel.consensus = orig
    alt = concat_rates(rows)
    syn_alt = alt["synonymous"].astype(bool)
    res["codon_background_later_sample"] = {
        "nonsynonymous": int((~syn_alt).sum()), "synonymous": int(syn_alt.sum()),
        "share_above_0.002_nonsynonymous": share_above(alt["rate"][~syn_alt], 0.002),
        "changed_class_fraction": None,
    }

    res["MpApB_conventions"] = {
        "paper": 0.93,
        "M(t_i+1) x minor alleles": mean_MpApB(ev, "M1", "minor"),
        "M(t_i) x minor alleles": mean_MpApB(ev, "M0", "minor"),
        "M(t_i+1) x the missing haplotype's alleles": mean_MpApB(ev, "M1", "missing"),
        "M(t_i) x the missing haplotype's alleles": mean_MpApB(ev, "M0", "missing"),
        "min(M) x minor alleles": float(np.mean(np.minimum(ev["M0"], ev["M1"])
                                                * ev["qA"] * ev["qB"])),
    }
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    print(json.dumps(res, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
