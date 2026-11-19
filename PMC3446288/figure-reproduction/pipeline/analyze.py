#!/usr/bin/env python3
"""Every junction-level result of the paper from the junction table and the gene counts.

Usage: analyze.py JUNCTIONS.tsv.gz GENE_COUNTS_DIR CATEGORIES_DIR ANNOT_DIR GENOME.fa OUTDIR [--seed N]

Writes OUTDIR/analysis.json (all numbers), OUTDIR/junctions_annotated.tsv.gz (per junction: gene,
canonical, PTC call, fold changes, regulation), OUTDIR/events.tsv.gz (splice events with PSI) and
OUTDIR/figure_data.json (the series behind Figs 3b, 6 and 7b).
"""

import argparse
import gzip
import json
import math
from collections import Counter, defaultdict

import numpy as np
import pysam
from scipy import stats

from nmdsplice.annotation import read_genepred, refseq_genes
from nmdsplice.classes import infer_events
from nmdsplice.junctions import annotate, false_positive_genes, fold_changes
from nmdsplice.ptc import ExonCatalog, ModelIndex
from nmdsplice.quant import EVIDENCE_READS, tmm_factors, upper_quartile_rpkm

SAMPLES = ["BMM_WT", "BMM_KO", "Liver_WT", "Liver_KO"]
TISSUES = {"BMM": (0, 1), "Liver": (2, 3)}
JUNCTION_KB = 0.142  # a junction "feature" is 2 x 71 nt of the database sequence


def gz_text(path):
    """A gzip text file without a timestamp, so reruns give the same bytes."""
    import io
    return io.TextIOWrapper(gzip.GzipFile(path, "wb", mtime=0), encoding="utf-8")


def load_table(path):
    keys, db, th = [], [], []
    with gzip.open(path, "rt") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            keys.append((p[0], int(p[1]), int(p[2])))
            db.append([int(x) for x in p[3:7]])
            th.append([float(x) for x in p[7:11]])
    return keys, np.array(db), np.array(th)


def load_genes(dirpath):
    rows = {}
    counts = []
    for k, s in enumerate(SAMPLES):
        with open(f"{dirpath}/{s}_gene_counts.tsv") as f:
            hdr = next(f).rstrip("\n").split("\t")
            col = []
            for line in f:
                p = line.rstrip("\n").split("\t")
                if k == 0:
                    rows[len(rows)] = p
                col.append(int(p[-1]))
        counts.append(col)
    return rows, np.array(counts).T


def pct(a, b):
    return 100.0 * a / b if b else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("junctions")
    ap.add_argument("genes")
    ap.add_argument("categories")
    ap.add_argument("annot")
    ap.add_argument("genome")
    ap.add_argument("outdir")
    ap.add_argument("--seed", type=int, default=20120524)
    a = ap.parse_args()
    out = {}
    fig = {}

    fa = pysam.FastaFile(a.genome)
    chroms = set(fa.references)
    sets = {s: read_genepred(f"{a.annot}/{s}.txt.gz", s) for s in
            ("refGene", "knownGene", "ensGene", "genscan", "exoniphy")}
    for s in sets:
        sets[s] = [t for t in sets[s] if t.chrom in chroms]
    genes = refseq_genes(sets["refGene"], chroms)
    catalog = ExonCatalog(sets)
    models = ModelIndex(sets["refGene"], sets["ensGene"])
    model_lookup = {t.name: t for t in sets["refGene"] + sets["ensGene"] if t.coding}

    keys, db, th = load_table(a.junctions)
    reads = np.where(db > 0, db, np.rint(th)).astype(np.int64)
    in_db = db > 0
    in_th = th > 0
    cats = {s: json.load(open(f"{a.categories}/{s}_categories.json")) for s in SAMPLES}

    # ---------------- Fig. 1a and mapping numbers
    out["fig1a"] = {s: cats[s] for s in SAMPLES}
    tot_reads = sum(cats[s]["reads"] for s in SAMPLES)
    tot_mapped = sum(cats[s]["total_mapped"] for s in SAMPLES)
    tot_junc = sum(cats[s]["junction"] for s in SAMPLES)
    out["mapping"] = {
        "mapped_fraction": tot_mapped / tot_reads,
        "junction_fraction_of_mapped": tot_junc / tot_mapped,
        "truncation_recovered": {s: cats[s]["truncation_recovered"] for s in SAMPLES},
        "truncation_fraction": {s: cats[s]["truncation_recovered"] / cats[s]["reads"] for s in SAMPLES},
    }

    # ---------------- Table S1 (per sample, no read cut-off)
    s1 = {}
    for k, s in enumerate(SAMPLES):
        det = (reads[:, k] > 0)
        dbo = int((in_db[:, k] & ~in_th[:, k]).sum())
        tho = int((in_th[:, k] & ~in_db[:, k]).sum())
        both = int((in_db[:, k] & in_th[:, k]).sum())
        s1[s] = {"comb_db_only": dbo, "tophat_only": tho, "both": both, "total": int(det.sum())}
    out["tableS1"] = s1
    any_reads = reads.sum(axis=1) > 0
    out["unique_junctions_all_samples"] = int(any_reads.sum())
    ev_any = np.zeros(len(keys), bool)
    for t, (w, k) in TISSUES.items():
        ev_any |= (reads[:, w] >= EVIDENCE_READS) | (reads[:, k] >= EVIDENCE_READS)
    out["unique_junctions_min3"] = int(ev_any.sum())

    # ---------------- TMM
    # TMM within each tissue (WT against KO): the paper's factors multiply to 1.000 in each tissue
    # (0.998 x 1.002, 1.188 x 0.841), which a four-sample normalisation would not give.
    tmm = np.ones(4)
    for t, (w, k) in TISSUES.items():
        sub = reads[:, [w, k]]
        sub = sub[sub.sum(axis=1) > 0]
        tmm[[w, k]] = tmm_factors(sub)
    out["tmm_factors"] = dict(zip(SAMPLES, map(float, tmm)))
    out["tmm_factors_four_samples"] = dict(zip(SAMPLES, map(float, tmm_factors(reads[any_reads]))))
    np.savetxt(f"{a.outdir}/junction_matrix_for_edger.tsv.gz", reads[any_reads], fmt="%d", delimiter="\t")
    lib = reads.sum(axis=0) * tmm  # effective library sizes

    # ---------------- genes: upper-quartile RPKM, fold changes
    grows, gcounts = load_genes(a.genes)
    glen = np.array([int(grows[i][6]) for i in range(len(grows))], float)
    rpkm = upper_quartile_rpkm(gcounts, glen)
    gene_fc = {}
    for t, (w, k) in TISSUES.items():
        with np.errstate(divide="ignore", invalid="ignore"):
            fc = np.where(rpkm[:, w] > 0, rpkm[:, k] / np.where(rpkm[:, w] > 0, rpkm[:, w], 1), np.nan)
        gene_fc[t] = fc
    gkey = {}
    for i, r in grows.items():
        gkey[(r[0], r[2], r[3])] = i  # symbol, chrom, strand (first locus wins)
    sym_fc = {t: {grows[i][0]: float(gene_fc[t][i]) for i in range(len(grows)) if np.isfinite(gene_fc[t][i])}
              for t in TISSUES}

    # ---------------- annotate junctions (gene, canonical, PTC)
    idx = np.flatnonzero(any_reads)
    jkeys = [keys[i] for i in idx]
    ann = annotate(jkeys, genes, catalog, models, fa)
    fp = false_positive_genes(ann, fa, model_lookup)
    ptc = {}
    for j, aj in ann.items():
        p = aj.ptc
        ptc[j] = bool(p and p.ptc and aj.gene not in fp)

    # gene index for fold change normalisation
    gidx_of = {}
    for j, aj in ann.items():
        if aj.gene:
            sym = aj.symbol
            g = gkey.get((sym, j[0], aj.strand))
            if g is not None:
                gidx_of[j] = g

    excl = {}
    for k, s in enumerate(SAMPLES):
        excl[s] = int(sum(1 for n, i in enumerate(idx) if reads[i, k] > 0 and ann[keys[i]].ptc.status == "unannotated"))
    out["ptc_filters"] = {"unannotated_exon_junctions": excl}

    # ---------------- per tissue
    R = reads[idx]
    tissue = {}
    reg_of = {}
    evident_sets = {}
    for t, (w, k) in TISSUES.items():
        ev = (R[:, w] >= EVIDENCE_READS) | (R[:, k] >= EVIDENCE_READS)
        gfc = np.array([gene_fc[t][gidx_of[j]] if j in gidx_of else np.nan for j in jkeys])
        fc = fold_changes(R[:, w], R[:, k], lib[w], lib[k], gfc)
        fc_raw = fold_changes(R[:, w], R[:, k], lib[w], lib[k], None)
        reg = np.where(fc >= 2, "up", np.where(fc <= 0.5, "down", "unregulated"))
        reg_raw = np.where(fc_raw >= 2, "up", np.where(fc_raw <= 0.5, "down", "unregulated"))
        isptc = np.array([ptc[j] for j in jkeys])
        status = np.array([ann[j].ptc.status for j in jkeys])
        has_gene = np.array([bool(ann[j].gene) for j in jkeys])
        canon = np.array([ann[j].canonical for j in jkeys])
        gene_sym = np.array([ann[j].gene for j in jkeys])
        evident_sets[t] = ev
        reg_of[t] = (reg, fc, reg_raw)

        def table(mask, regv):
            row = {}
            for r in ("up", "unregulated", "down"):
                m = mask & (regv == r)
                row[r] = {"junctions": int(m.sum()), "genes": int(len(set(gene_sym[m & has_gene])))}
            tj = sum(row[r]["junctions"] for r in row)
            tg = sum(row[r]["genes"] for r in row)
            for r in row:
                row[r]["junctions_pct"] = pct(row[r]["junctions"], tj)
                row[r]["genes_pct"] = pct(row[r]["genes"], tg)
            return row

        ambiguous = int((ev & (status == "ambiguous_cds")).sum())
        res = {
            "evident_junctions": int(ev.sum()),
            "fig2a_all": table(ev, reg),
            "fig2a_ptc": table(ev & isptc, reg),
            "fig2a_all_raw_fc": table(ev, reg_raw),
            "fig2a_ptc_raw_fc": table(ev & isptc, reg_raw),
            "ambiguous_cds_junctions": ambiguous,
            "status_counts": dict(Counter(status[ev].tolist())),
            "false_positive_genes": int(len({ann[j].gene for j, e in zip(jkeys, ev) if e} & fp)),
        }
        # Table S2
        th_only = (in_th[idx][:, [w, k]].any(axis=1)) & ~(in_db[idx][:, [w, k]].any(axis=1))
        res["tableS2"] = {"all": int(ev.sum()), "ptc": int((ev & isptc).sum()),
                          "tophat_all": int((ev & th_only).sum()), "tophat_ptc": int((ev & th_only & isptc).sum())}
        # PTC+ up per gene and expressed genes
        up_ptc = ev & isptc & (reg == "up")
        up_all = ev & (reg == "up")
        expressed = set(gene_sym[ev & has_gene])
        res["up_junctions_per_gene"] = float(up_all.sum() / max(1, len(set(gene_sym[up_all & has_gene]))))
        res["genes_with_up_ptc_share_of_expressed"] = len(set(gene_sym[up_ptc & has_gene])) / max(1, len(expressed))
        res["ptc_up_share"] = float(up_ptc.sum() / max(1, (ev & isptc).sum()))
        # Chi-square: regulation distribution of all vs PTC+ junctions
        tab = np.array([[res["fig2a_all"][r]["junctions"] for r in ("up", "unregulated", "down")],
                        [res["fig2a_ptc"][r]["junctions"] for r in ("up", "unregulated", "down")]])
        chi = stats.chi2_contingency(tab)
        res["chisq_all_vs_ptc"] = {"statistic": float(chi.statistic), "p": float(chi.pvalue)}
        # Fig. 3a canonical vs alternative
        f3 = {}
        for name, m in (("canonical", ev & canon), ("alternative", ev & has_gene & ~canon)):
            n = int(m.sum())
            f3[name] = {r: pct(int((m & (reg == r)).sum()), n) for r in ("up", "unregulated", "down")}
            upm = m & (reg == "up")
            f3[name]["ptc_of_up"] = pct(int((upm & isptc).sum()), int(upm.sum()))
            f3[name]["n"] = n
        res["fig3a"] = f3
        tissue[t] = res

    # ---------------- common rows (junctions evident in both tissues)
    evb = evident_sets["BMM"] & evident_sets["Liver"]
    rb, rl = reg_of["BMM"][0], reg_of["Liver"][0]
    creg = np.where((rb == "up") & (rl == "up"), "up", np.where((rb == "down") & (rl == "down"), "down", "unregulated"))
    isptc = np.array([ptc[j] for j in jkeys])
    gene_sym = np.array([ann[j].gene for j in jkeys])
    symbols = np.array([ann[j].symbol for j in jkeys])
    has_gene = gene_sym != ""
    canon = np.array([ann[j].canonical for j in jkeys])

    def table_c(mask):
        row = {}
        for r in ("up", "unregulated", "down"):
            m = mask & (creg == r)
            row[r] = {"junctions": int(m.sum()), "genes": int(len(set(gene_sym[m & has_gene])))}
        tj = sum(row[r]["junctions"] for r in row)
        tg = sum(row[r]["genes"] for r in row)
        for r in row:
            row[r]["junctions_pct"] = pct(row[r]["junctions"], tj)
            row[r]["genes_pct"] = pct(row[r]["genes"], tg)
        return row

    common = {"fig2a_all": table_c(evb), "fig2a_ptc": table_c(evb & isptc)}
    core = evb & isptc & (creg == "up")
    common["core_junctions"] = int(core.sum())
    common["core_genes"] = sorted(set(symbols[core & has_gene]))
    f3c = {}
    for name, m in (("canonical", evb & canon), ("alternative", evb & has_gene & ~canon)):
        n = int(m.sum())
        f3c[name] = {r: pct(int((m & (creg == r)).sum()), n) for r in ("up", "unregulated", "down")}
        upm = m & (creg == "up")
        f3c[name]["ptc_of_up"] = pct(int((upm & isptc).sum()), int(upm.sum()))
    common["fig3a"] = f3c
    out["tissues"] = tissue
    out["common"] = common

    # ---------------- Fig. 3b: AS junctions per sample (no cut-off), per million junction reads,
    # and slopes after downsampling junction reads to BMM WT
    rng = np.random.default_rng(a.seed)
    alt = has_gene & ~canon
    f3b = {}
    base = int(R[:, 0].sum())
    series = {}
    for k, s in enumerate(SAMPLES):
        det = R[:, k] > 0
        n_as = int((det & alt).sum())
        jr_m = cats[s]["junction"] / 1e6
        x = R[:, k]
        if k > 0 and x.sum() > base:
            x = rng.binomial(x, base / x.sum())
        d2 = (x > 0) & has_gene
        per_gene = defaultdict(lambda: [0, 0, 0])
        for g, al, p in zip(gene_sym[d2], alt[d2], isptc[d2]):
            v = per_gene[g]
            v[0] += 1
            v[1] += int(al)
            v[2] += int(p)
        arr = np.array(list(per_gene.values()), float)
        slope_as = float((arr[:, 0] * arr[:, 1]).sum() / (arr[:, 0] ** 2).sum())
        slope_ptc = float((arr[:, 0] * arr[:, 2]).sum() / (arr[:, 0] ** 2).sum())
        f3b[s] = {"as_junctions": n_as, "per_million_junction_reads": n_as / jr_m,
                  "slope_as": slope_as, "slope_ptc": slope_ptc}
        series[s] = arr.astype(int).tolist()
    for t, (w, k) in TISSUES.items():
        f3b[t + "_union"] = int((((R[:, w] > 0) | (R[:, k] > 0)) & alt).sum())
    out["fig3b"] = f3b
    fig["fig3b_per_gene"] = series

    # ---------------- Fig. 6: PTC+/PTC- ratio by junction RPKM (1-RPKM bins), all junctions
    f6 = {}
    for k, s in enumerate(SAMPLES):
        mapped_m = cats[s]["total_mapped"] / 1e6
        rp = R[:, k] / JUNCTION_KB / mapped_m / tmm[k]
        m = (R[:, k] > 0) & has_gene
        bins = np.floor(rp[m]).astype(int)
        pp = isptc[m]
        xs, ys = [], []
        for b in range(1, 41):
            sel = bins == b
            n_p = int((sel & pp).sum())
            n_n = int((sel & ~pp).sum())
            if n_n > 0:
                xs.append(b)
                ys.append(n_p / n_n)
        f6[s] = {"rpkm_bin": xs, "ptc_ratio": ys}
    fig["fig6"] = f6

    def at(s, b):
        d = dict(zip(f6[s]["rpkm_bin"], f6[s]["ptc_ratio"]))
        return d.get(b)

    common_bins = sorted(set.intersection(*[set(f6[s]["rpkm_bin"]) for s in SAMPLES])) if all(f6[s]["rpkm_bin"] for s in SAMPLES) else []
    claims = {}
    if common_bins:
        claims["liver_above_bmm_all_bins"] = "yes" if all(min(at("Liver_WT", b), at("Liver_KO", b)) > max(at("BMM_WT", b), at("BMM_KO", b))
                                                         for b in common_bins) else "no"
        claims["low_expression_enriched"] = "yes" if all(
            at(s, 1) is not None and at(s, 1) > max([y for x, y in zip(f6[s]["rpkm_bin"], f6[s]["ptc_ratio"]) if x > 10], default=0)
            for s in SAMPLES) else "no"
        claims["ko_above_wt_liver_bin1"] = "yes" if at("Liver_KO", 1) > at("Liver_WT", 1) else "no"
        claims["ko_above_wt_bmm_bin1"] = "yes" if at("BMM_KO", 1) > at("BMM_WT", 1) else "no"
    out["fig6_claims"] = claims

    # ---------------- splice classes, Table 1
    exons = set()
    for src, ts in sets.items():
        for tr in ts:
            for s_, e_ in tr.exons:
                exons.add((tr.chrom, tr.strand, s_, e_))
    first_ex = set()
    last_ex = set()
    for src in ("refGene", "knownGene", "ensGene"):
        for tr in sets[src]:
            if len(tr.exons) < 2:
                continue
            f_, l_ = (tr.exons[0], tr.exons[-1]) if tr.strand == "+" else (tr.exons[-1], tr.exons[0])
            first_ex.add((tr.chrom, tr.strand, *f_))
            last_ex.add((tr.chrom, tr.strand, *l_))
    gene_of = {j: ann[j].symbol for j in jkeys}
    strand_of = {j: ann[j].strand for j in jkeys}
    all_events = {}
    t1 = {}
    for t, (w, k) in TISSUES.items():
        ev = evident_sets[t]
        jd = {jkeys[i]: (int(R[i, w]), int(R[i, k])) for i in np.flatnonzero(ev & has_gene)}
        events = infer_events(jd, exons, first_ex, last_ex, ptc, gene_of, strand_of)
        all_events[t] = events
        reg = [e for e in events if e.regulated]
        row = {}
        ses = [e for e in reg if e.cls == "SES"]
        mes = [e for e in reg if e.cls == "MES"]
        es = ses + mes

        def es_row(lst, inclusion_ptc=True):
            exc = [e for e in lst if e.direction == "exclusion"]
            inc = [e for e in lst if e.direction == "inclusion"]
            r = {"total": len(lst), "exclusion": len(exc), "ptc_upon_exclusion": sum(e.ptc_mode == "exclusion" for e in exc),
                 "inclusion": len(inc)}
            if inclusion_ptc:
                r["ptc_upon_inclusion"] = sum(e.ptc_mode == "inclusion" for e in inc)
            return r

        row["Total ES"] = es_row(es, False)
        row["Total ES"]["ptc_upon_inclusion"] = sum(e.ptc_mode == "inclusion" for e in ses if e.direction == "inclusion")
        row["Total ES"]["ptc"] = row["Total ES"]["ptc_upon_exclusion"] + row["Total ES"]["ptc_upon_inclusion"]
        row["Single ES"] = es_row(ses)
        row["Multiple ES"] = es_row(mes, False)
        for c in ("A5SS", "A3SS", "MXE", "AFE", "ALE"):
            lst = [e for e in reg if e.cls == c]
            row[c] = {"total": len(lst), "ptc": sum(e.ptc_up for e in lst)}
        row["all_events_unfiltered"] = dict(Counter(e.cls for e in events))
        t1[t] = row
    out["table1"] = t1

    # ---------------- Tables S7 and S8: SES regulated in both tissues
    def ses_key(e):
        return e.junctions

    both = {}
    for t in TISSUES:
        both[t] = {ses_key(e): e for e in all_events[t] if e.cls == "SES"}
    common_keys = set(both["BMM"]) & set(both["Liver"])
    s7, s8 = [], []
    for kk in common_keys:
        eb, el = both["BMM"][kk], both["Liver"][kk]
        if eb.dpsi > 0.2 and el.dpsi > 0.2 and eb.ptc_mode == "inclusion" and el.ptc_mode == "inclusion":
            s7.append(eb.gene)
        if eb.dpsi < -0.2 and el.dpsi < -0.2 and eb.ptc_mode == "exclusion" and el.ptc_mode == "exclusion":
            s8.append(eb.gene)
    out["tableS7"] = {"events": len(s7), "genes": sorted(set(s7))}
    out["tableS8"] = {"events": len(s8), "genes": sorted(set(s8))}

    # ---------------- example events and gene fold changes named in the text
    def best_event(t, sym, cls, junction=None):
        cands = [e for e in all_events[t] if e.gene == sym and e.cls == cls]
        if junction is not None:
            cands = [e for e in cands if junction in e.junctions] or cands
        if not cands:
            return None
        e = max(cands, key=lambda e: abs(e.dpsi))
        return {"dpsi": e.dpsi, "psi_wt": e.psi_wt, "psi_ko": e.psi_ko, "junctions": [list(x) for x in e.junctions],
                "reads_wt": list(e.reads_wt), "reads_ko": list(e.reads_ko), "ptc_up": e.ptc_up}

    ex = {}
    for t in TISSUES:
        ex[t] = {
            "Mgea5": best_event(t, "Mgea5", "SES"),
            "Tmem183a": best_event(t, "Tmem183a", "SES"),
            "Rps12": best_event(t, "Rps12", "A5SS"),
            "Smg5": best_event(t, "Smg5", "A3SS"),
            "Srsf9": best_event(t, "Srsf9", "SES"),
        }
    out["examples"] = ex
    out["gene_fc"] = {t: {g: sym_fc[t].get(g) for g in ("Soat2", "Nktr", "Upf2")} for t in TISSUES}
    sf = ["Srsf1", "Srsf2", "Srsf3", "Srsf4", "Srsf5", "Srsf6", "Srsf7", "Srsf8", "Srsf9", "Tra2b", "Tra2a",
          "Srsf11", "Clasrp", "Hnrnpa2b1", "Hnrnpd", "Hnrnpf", "Hnrnph1", "Hnrnph3", "Hnrnpk", "Hnrnpl",
          "Hnrnpdl", "Hnrnpr", "Ptbp1", "Ptbp2", "Hnrnpll"]
    s5 = {}
    for t in TISSUES:
        s5[t] = {}
        for g in sf:
            gfc = sym_fc[t].get(g)
            # the major up-regulated PTC+ event of the gene: PSI of its PTC+ form in WT and KO
            cands = [e for e in all_events[t] if e.gene == g and e.ptc_up and e.regulated]
            wt_r = ko_r = None
            if cands:
                e = max(cands, key=lambda e: abs(e.dpsi))
                if e.cls in ("SES", "MES"):
                    up_incl = e.direction == "inclusion"
                    wt_r = e.psi_wt if up_incl else 1 - e.psi_wt
                    ko_r = e.psi_ko if up_incl else 1 - e.psi_ko
                else:
                    first = e.dpsi > 0
                    wt_r = e.psi_wt if first else 1 - e.psi_wt
                    ko_r = e.psi_ko if first else 1 - e.psi_ko
            canonical = None
            if gfc is not None and wt_r is not None and wt_r < 1:
                canonical = gfc * (1 - ko_r) / (1 - wt_r)
            s5[t][g] = {"gene_fc": gfc, "wt_ratio": wt_r, "ko_ratio": ko_r, "canonical_fc": canonical}
    out["tableS5"] = s5

    # ---------------- Fig. 7b: stop codons of strongly up-regulated PTC+ junctions
    f7b = {}
    for t, (w, k), minr in (("BMM", (0, 1), 5), ("Liver", (2, 3), 10)):
        fc = reg_of[t][1]
        sel = isptc & (np.log2(np.where(fc > 0, fc, 1e-9)) > 2) & ((R[:, w] + R[:, k]) >= minr)
        codons = Counter()
        positions = set()
        for i in np.flatnonzero(sel):
            p = ann[jkeys[i]].ptc
            if (jkeys[i][0], p.stop_genomic) in positions:
                continue
            positions.add((jkeys[i][0], p.stop_genomic))
            codons[p.stop_codon] += 1
        f7b[t] = {"n": sum(codons.values()), "codons": dict(codons)}
    fig["fig7b"] = f7b

    # ---------------- Fig. 7a: stop positions of up-regulated PTC+ junctions (fold change >= 2)
    f7a = {}
    for t, (w, k) in TISSUES.items():
        sel = isptc & (reg_of[t][0] == "up") & evident_sets[t]
        pos = sorted({(jkeys[i][0], ann[jkeys[i]].strand, ann[jkeys[i]].ptc.stop_genomic) for i in np.flatnonzero(sel)})
        f7a[t] = pos
    fig["fig7a_positions"] = f7a

    # ---------------- per-junction and per-event tables
    with gz_text(f"{a.outdir}/junctions_annotated.tsv.gz") as fo:
        fo.write("chrom\tdonor\tacceptor\tgene\tstrand\tcanonical\tptc_status\tptc\tstop\tstop_codon\tptc_distance\t"
                 + "\t".join(SAMPLES) + "\tfc_BMM\tfc_Liver\treg_BMM\treg_Liver\n")
        for n, j in enumerate(jkeys):
            aj = ann[j]
            p = aj.ptc
            fo.write(f"{j[0]}\t{j[1]}\t{j[2]}\t{aj.symbol}\t{aj.strand}\t{int(aj.canonical)}\t{p.status}\t{int(ptc[j])}\t"
                     f"{p.stop_genomic}\t{p.stop_codon}\t{p.distance}\t" + "\t".join(str(int(x)) for x in R[n]) + "\t"
                     f"{reg_of['BMM'][1][n]:.6g}\t{reg_of['Liver'][1][n]:.6g}\t{reg_of['BMM'][0][n]}\t{reg_of['Liver'][0][n]}\n")
    with gz_text(f"{a.outdir}/events.tsv.gz") as fo:
        fo.write("tissue\tclass\tgene\tchrom\tstrand\tjunctions\treads_wt\treads_ko\tpsi_wt\tpsi_ko\tdpsi\tdirection\tptc_up\tptc_mode\texons\n")
        for t in TISSUES:
            for e in all_events[t]:
                fo.write(f"{t}\t{e.cls}\t{e.gene}\t{e.chrom}\t{e.strand}\t"
                         + ";".join(f"{x[1]}-{x[2]}" for x in e.junctions) + "\t"
                         + ",".join(f"{x:g}" for x in e.reads_wt) + "\t" + ",".join(f"{x:g}" for x in e.reads_ko)
                         + f"\t{e.psi_wt:.6f}\t{e.psi_ko:.6f}\t{e.dpsi:.6f}\t{e.direction}\t{int(e.ptc_up)}\t{e.ptc_mode}\t"
                         + ";".join(f"{x}-{y}" for x, y in e.extra.get("exons", [])) + "\n")
    with open(f"{a.outdir}/analysis.json", "w") as fo:
        json.dump(out, fo, indent=1, default=float)
    with open(f"{a.outdir}/figure_data.json", "w") as fo:
        json.dump(fig, fo, default=float)


if __name__ == "__main__":
    main()
