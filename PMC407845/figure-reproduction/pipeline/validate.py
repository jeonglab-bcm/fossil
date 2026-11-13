"""The paper's validation analyses, from the classes of networker.py.

  validate.py DOWNLOADS RUN_DIR OUTDIR

Writes to OUTDIR:
  go.json        Fig. 2: over-represented GO categories in B+/C+ and B+/C- per TF
  deletion.json  Table 2 / text: response to TF deletion (Hughes 2000) of B+/C+ and B+/C- genes
  motifs.json    Table 3: cell cycle motifs in the 600 bp upstream of B+/C+ and B+/C- genes
  divergent.json text: probes shared by divergent genes; Fig. 3 coupling scores
  simon.json     text: overlap of B+/C+ groups from Simon et al. 2001 ChIP with Lee et al. 2002
"""

from __future__ import annotations

import gzip
import json
import re
import sys
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

import data
import manetworker as mn

GENOME = "S288C_reference_genome_R64-1-1_20110203"
MOTIFS = {"MCB": "ACGCGT", "SCB": "CGCGAAA", "Swi5p": "AACCAGC", "SFF": "GTAAACA"}
# Table 3: the motif-TF combinations the paper prints, and their -log10 P (B+/C+, B+/C-)
TABLE3 = [("MCB", "Mbp1", "38.4", "8.3"), ("MCB", "Swi4", "8.2", "0.0"), ("SCB", "Mbp1", "7.0", "1.3"),
          ("SCB", "Swi4", "19.1", "2.8"), ("Swi5p", "Ace2", "5.1", "0.6"), ("Swi5p", "Swi5", "2.6", "0.8"),
          ("SFF", "Fkh2", "12.9", "1.8"), ("SFF", "Mcm1", "3.1", "1.4"), ("SFF", "Ndd1", "8.3", "0.6"),
          ("SFF", "Swi4", "3.5", "0.1")]
CELL_CYCLE = ["Ace2", "Fkh2", "Mbp1", "Mcm1", "Ndd1", "Swi4", "Swi5"]
# Fig. 3: TF, gene name, printed score
FIG3 = [("Mbp1", "RAD51", "8.7"), ("Mbp1", "PUP3", "0.7"), ("Fhl1", "RPL40B", ">12.0"), ("Fhl1", "MLP1", "0.1"),
        ("Nrg1", "FSP2", ">12.0"), ("Nrg1", "HXT9", "11.1"), ("Hap6", "FSP2", "2.2"), ("Hap6", "HXT9", "0.5")]


def load_run(run_dir):
    z = np.load(Path(run_dir) / "run.npz")
    return {k: z[k] for k in z.files}


# ---------------------------------------------------------------------------------------------
# Genome: genes, synonyms, upstream regions


def read_genome(downloads):
    with tarfile.open(Path(downloads) / f"{GENOME}.tgz") as t:
        m = next(x for x in t.getmembers() if x.name.endswith(".gff"))
        text = t.extractfile(m).read().decode("latin-1")
    gff, fasta = text.split("##FASTA")
    genes, sgdid, names = {}, {}, {}
    feats = defaultdict(list)
    for line in gff.splitlines():
        if not line or line.startswith("#"):
            continue
        f = line.split("\t")
        if len(f) != 9:
            continue
        chrom, typ, s, e, strand, attr = f[0], f[2], int(f[3]), int(f[4]), f[6], f[8]
        a = dict(kv.split("=", 1) for kv in attr.split(";") if "=" in kv)
        if typ in ("gene", "tRNA", "ncRNA", "rRNA", "snoRNA", "snRNA", "transposable_element_gene", "pseudogene"):
            feats[chrom].append((s, e))
        if typ == "gene":
            orf = a["ID"].upper()
            genes[orf] = (chrom, s, e, strand)
            m2 = re.search(r"SGD:(S\d+)", a.get("dbxref", ""))
            if m2:
                sgdid[m2.group(1)] = orf
            for nm in [a.get("gene", "")] + a.get("Alias", "").split(","):
                nm = nm.strip().upper()
                if nm and nm not in names:
                    names[nm] = orf
            if "gene" in a:
                names[a["gene"].upper()] = orf
    seqs, cur = {}, None
    buf = []
    for line in fasta.splitlines():
        if line.startswith(">"):
            if cur:
                seqs[cur] = "".join(buf)
            cur, buf = line[1:].split()[0], []
        elif cur:
            buf.append(line.strip().upper())
    if cur:
        seqs[cur] = "".join(buf)
    for c in feats:
        feats[c].sort()
    return {"genes": genes, "sgdid": sgdid, "names": names, "feats": feats, "seqs": seqs}


def upstream(genome, length=600):
    """Non-coding region up to `length` bp upstream of each ORF start, stopped at the nearest
    upstream feature on either strand; on the ORF's strand (5' to 3')."""
    comp = str.maketrans("ACGTN", "TGCAN")
    out = {}
    for orf, (chrom, s, e, strand) in genome["genes"].items():
        seq = genome["seqs"].get(chrom)
        if seq is None:
            continue
        fe = genome["feats"][chrom]
        if strand == "+":
            lo = max(1, s - length)
            prev_ends = [b for a, b in fe if b < s and b >= lo]
            if prev_ends:
                lo = max(prev_ends) + 1
            region = seq[lo - 1:s - 1]
        else:
            hi = e + length
            next_starts = [a for a, b in fe if a > e and a <= hi]
            if next_starts:
                hi = min(next_starts) - 1
            region = seq[e:hi].translate(comp)[::-1]
        out[orf] = region
    return out


def count_motif(seq, motif, both=True):
    """Non-overlapping occurrences of motif (and its reverse complement, counted separately)."""
    def n(s, m):
        return len(re.findall(f"(?={m})", s)) if False else _nonoverlap(s, m)
    rc = motif.translate(str.maketrans("ACGT", "TGCA"))[::-1]
    c = _nonoverlap(seq, motif)
    if both and rc != motif:
        c += _nonoverlap(seq, rc)
    return c


def _nonoverlap(s, m):
    k, i = 0, s.find(m)
    while i >= 0:
        k += 1
        i = s.find(m, i + len(m))
    return k


# ---------------------------------------------------------------------------------------------
# Gene Ontology


def read_obo(path):
    parents, ns, obsolete = defaultdict(set), {}, set()
    cur = None
    for line in open(path, encoding="latin-1"):
        line = line.strip()
        if line == "[Term]":
            cur = {}
        elif line.startswith("[") :
            cur = None
        elif cur is not None and ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if k == "id":
                cur["id"] = v
            elif k == "namespace":
                ns[cur["id"]] = v
            elif k == "is_a":
                parents[cur["id"]].add(v.split()[0])
            elif k == "relationship" and v.startswith("part_of"):
                parents[cur["id"]].add(v.split()[1])
            elif k == "is_obsolete" and v == "true":
                obsolete.add(cur["id"])
    return parents, ns, obsolete


def ancestors(term, parents, memo):
    if term in memo:
        return memo[term]
    out = {term}
    for p in parents.get(term, ()):
        out |= ancestors(p, parents, memo)
    memo[term] = out
    return out


def gene_terms(downloads, genome):
    parents, ns, obsolete = read_obo(Path(downloads) / "gene_ontology.obo")
    direct = defaultdict(set)
    orf_pat = re.compile(r"^(Y[A-P][LR]\d{3}[WC](-[A-Z])?|Q\d{4}|R\d{4}[WC]?)$", re.I)
    unmapped = set()
    with gzip.open(Path(downloads) / "sgd.gaf.gz", "rt", encoding="latin-1") as f:
        for line in f:
            if line.startswith("!"):
                continue
            c = line.rstrip("\n").split("\t")
            if len(c) < 11 or "NOT" in c[3]:
                continue
            orf = genome["sgdid"].get(c[1])
            if orf is None:
                for syn in [c[2]] + c[10].split("|"):
                    if orf_pat.match(syn.strip()):
                        orf = syn.strip().upper()
                        break
            if orf is None:
                orf = genome["names"].get(c[2].upper())
            if orf is None:
                unmapped.add(c[1])
                continue
            direct[orf].add(c[4])
    memo = {}
    full = {}
    roots = {"GO:0003674", "GO:0005575", "GO:0008150"}
    for orf, ts in direct.items():
        s = set()
        for t in ts:
            s |= ancestors(t, parents, memo)
        full[orf] = {t for t in s if t not in obsolete and t not in roots}
    return full, len(unmapped)


def enrichment(genes_set, universe, terms_of, q=0.05):
    """Over-represented terms in genes_set against universe (cumulative hypergeometric).
    Returns significant counts: Bonferroni over terms annotated in the universe (main), Bonferroni
    over terms with a hit in the set, and BH 5%."""
    U = [g for g in universe if terms_of.get(g)]
    S = [g for g in genes_set if terms_of.get(g)]
    if not S:
        return {"bonferroni": 0, "bonferroni_hit_terms": 0, "bh": 0, "n_set": 0, "n_universe": len(U)}
    tu = Counter(t for g in U for t in terms_of[g])
    ts = Counter(t for g in S for t in terms_of[g])
    N, n = len(U), len(S)
    terms = list(ts)
    p = np.array([stats.hypergeom.sf(ts[t] - 1, N, tu[t], n) for t in terms])
    return {
        "bonferroni": int((p * len(tu) < q).sum()),
        "bonferroni_hit_terms": int((p * len(terms) < q).sum()),
        "bh": int(mn.bh_reject(np.concatenate([p, np.ones(len(tu) - len(terms))]), q).sum()),
        "n_set": n, "n_universe": N,
    }


def read_fig2_eps(path):
    """Bar heights of Fig. 2 from the vector EPS: red B+/C+, green B+/C- bars, left to right."""
    text = open(path, encoding="latin-1").read()
    ticks = sorted({int(m.group(1)) for m in re.finditer(r"^1032 (\d+) m  1164 \1 l  ps", text, re.M)}, reverse=True)
    base = ticks[0]
    vals = np.arange(len(ticks)) * 10.0
    slope, icpt = np.polyfit(np.array(ticks, float), vals, 1)
    resid = float(np.abs(np.polyval([slope, icpt], ticks) - vals).max())
    bars = {"red": [], "green": []}
    # each filled shape: "R G B c x y m  x y l ... \np ef"
    for m in re.finditer(r"([\d.]+) ([\d.]+) ([\d.]+) c ([\d\sml]+?)\s*p ef", text):
        r, g = float(m.group(1)), float(m.group(2))
        nums = [int(v) for v in re.findall(r"\d+", m.group(4))]
        xs, ys = nums[0::2], nums[1::2]
        col = "red" if r > 0.9 and g < 0.1 else "green" if g > 0.4 and r < 0.1 else None
        if col and max(ys) == base:
            bars[col].append((min(xs), (base - min(ys)) * -slope))
    xt = sorted({int(m.group(1)) for m in re.finditer(r"^(\d+) 6773 m  \1 6694 l  ps", text, re.M)})
    out = {}
    for col, b in bars.items():
        slots = [None] * (len(xt) - 1)
        for x, h in b:
            k = int(np.searchsorted(xt, x, side="right")) - 1
            slots[k] = h
        out[col] = [None if h is None else (int(round(h)) if h > 0.5 else 0) for h in slots]
        out[col + "_raw"] = [None if h is None else round(h, 3) for h in slots]
    out["axis_fit_residual"] = round(resid, 3)
    out["units_per_count"] = round(-1 / slope, 3)
    return out


# ---------------------------------------------------------------------------------------------


def main(downloads, run_dir, outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    R = load_run(run_dir)
    genes = [str(g) for g in R["genes"]]
    gi = {g: i for i, g in enumerate(genes)}
    tfs = [str(t) for t in R["tfs"]]
    cls = R["classes"]
    genome = read_genome(downloads)

    # --- Fig. 2: GO
    from networker import PAPER_TFS
    terms_of, n_unmapped = gene_terms(downloads, genome)
    pub = read_fig2_eps(Path(downloads) / "moesm2.eps")
    go = {"published": pub, "tfs": PAPER_TFS, "ours": {}, "unmapped_annotation_ids": n_unmapped}
    for t in PAPER_TFS:
        if t not in tfs:
            go["ours"][t] = None
            continue
        j = tfs.index(t)
        classified = [g for g, c in zip(genes, cls[:, j]) if c != 3]
        res = {}
        for k, name in ((1, "B+/C+"), (2, "B+/C-")):
            res[name] = enrichment([g for g, c in zip(genes, cls[:, j]) if c == k], classified, terms_of)
        go["ours"][t] = res
    (out / "go.json").write_text(json.dumps(go, indent=1) + "\n")

    # --- Table 2 and the deletion claim
    from networker import DELETION_TFS
    dele = {"tfs": DELETION_TFS, "ours": {}}
    H = R["hughes_deletion"]
    for k, t in enumerate(DELETION_TFS):
        x = H[:, k].astype(float)
        ok = ~np.isnan(x)
        lc = R["loo_classes"][:, k]
        row = {"genome": {"n": int(ok.sum())}}
        for qname, v in (("log_ratio", x), ("abs_log_ratio", np.abs(x))):
            gm, gs = float(np.nanmean(v[ok])), float(np.nanstd(v[ok], ddof=1))
            row["genome"][qname] = {"mean": gm, "sd": gs}
            for c, name in ((1, "B+/C+"), (2, "B+/C-")):
                sub = v[(lc == c) & ok]
                d = row.setdefault(name, {"n": int(sub.size)})
                if sub.size >= 2:
                    tt = stats.ttest_1samp(sub, gm)
                    d[qname] = {"mean": float(sub.mean()), "sd": float(sub.std(ddof=1)),
                                "neglog10_p": float(-np.log10(max(tt.pvalue, 1e-300)))}
                else:
                    d[qname] = None
        dele["ours"][t] = row
    (out / "deletion.json").write_text(json.dumps(dele, indent=1) + "\n")

    # --- Table 3
    ups = upstream(genome)
    mot = {"rows": [], "variants": {}}
    for variant, both, unit in (("main", True, "count"), ("forward_strand", False, "count"), ("genes_with_motif", True, "gene")):
        rows = []
        for motif, tf, pc, pm in TABLE3:
            m = MOTIFS[motif]
            allg = [g for g in ups if ups[g]]
            if unit == "count":
                cnt = {g: count_motif(ups[g], m, both) for g in allg}
                L = {g: max(len(ups[g]) - len(m) + 1, 0) for g in allg}
                rate = sum(cnt.values()) / sum(L.values())
            else:
                cnt = {g: int(count_motif(ups[g], m, both) > 0) for g in allg}
                rate = sum(cnt.values()) / len(allg)
            j = tfs.index(tf)
            vals = []
            for c in (1, 2):
                S = [g for g, cc in zip(genes, cls[:, j]) if cc == c and g in cnt]
                k = sum(cnt[g] for g in S)
                n = sum(L[g] for g in S) if unit == "count" else len(S)
                p = stats.binom.sf(k - 1, n, rate) if n else 1.0
                vals.append({"k": int(k), "n": int(n), "neglog10_p": float(-np.log10(max(p, 1e-300)))})
            rows.append({"motif": motif, "tf": tf, "paper": [pc, pm], "B+/C+": vals[0], "B+/C-": vals[1]})
        mot["variants"][variant] = rows
    mot["rows"] = mot["variants"]["main"]
    mot["n_upstream"] = len(ups)
    (out / "motifs.json").write_text(json.dumps(mot, indent=1) + "\n")

    # --- divergent promoters and Fig. 3
    L_ = data.lee(downloads)
    spots = Counter(L_["spot"])
    div = {"probes": len(spots), "probes_shared": sum(1 for v in spots.values() if v >= 2), "fig3": []}
    for tf, name, printed in FIG3:
        orf = genome["names"].get(name)
        row = {"tf": tf, "gene": name, "orf": orf, "paper": printed}
        if tf in tfs and orf in gi:
            p = float(R["p"][gi[orf], tfs.index(tf)])
            two = min(1.0, 2 * p) if R["r"][gi[orf], tfs.index(tf)] > 0 else 1.0
            row["neglog10_p_one_sided"] = float(-np.log10(max(p, 1e-300)))
            row["neglog10_p_two_sided"] = float(-np.log10(max(min(1.0, 2 * min(p, 1 - p)), 1e-300)))
            row["r"] = float(R["r"][gi[orf], tfs.index(tf)])
            row["same_probe"] = L_["spot"][L_["genes"].index(orf)] if orf in L_["genes"] else None
        else:
            row["neglog10_p_one_sided"] = None
            row["why"] = f"{tf} is not among the TFs of our run" if tf not in tfs else f"{name} not in our gene list"
        div["fig3"].append(row)
    div["hap6_in_lee"] = "Hap6" in L_["tfs"]
    (out / "divergent.json").write_text(json.dumps(div, indent=1) + "\n")

    # --- Simon et al. 2001 overlap
    S_ = data.simon(downloads)
    sg = {g: i for i, g in enumerate(S_["genes"])}
    sim = {"tfs": CELL_CYCLE, "per_tf": {}}
    for t in CELL_CYCLE:
        j = tfs.index(t)
        k = S_["tfs"].index(t)
        lee_cc = {g for g, c in zip(genes, cls[:, j]) if c == 1}
        coupled_ = {g for g, c in zip(genes, cls[:, j]) if c in (1,)}
        # C+ calls of our run do not depend on the ChIP data: a gene is C+ when its coupling
        # passes the FDR. Recover them as the genes with p below the TF's BH cut.
        p = R["p"][:, j].astype(float)
        cp = mn.coupled(p[:, None], 0.05, "per_tf")[:, 0]
        sim_bound = {g for g in genes if g in sg and S_["p"][sg[g], k] < 1e-3}
        sim_cc = {g for g in sim_bound if cp[gi[g]] and cls[gi[g], j] != 3}
        inter = lee_cc & sim_cc
        sim["per_tf"][t] = {"lee_b+c+": len(lee_cc), "simon_b+c+": len(sim_cc), "both": len(inter),
                            "share_of_lee": len(inter) / len(lee_cc) if lee_cc else None,
                            "share_of_simon": len(inter) / len(sim_cc) if sim_cc else None,
                            "jaccard": len(inter) / len(lee_cc | sim_cc) if lee_cc | sim_cc else None}
    for key in ("share_of_lee", "share_of_simon", "jaccard"):
        v = [d[key] for d in sim["per_tf"].values() if d[key] is not None]
        sim[f"mean_{key}"] = float(np.mean(v)) if v else None
    (out / "simon.json").write_text(json.dumps(sim, indent=1) + "\n")
    print("validation done")


if __name__ == "__main__":
    main(*sys.argv[1:4])
