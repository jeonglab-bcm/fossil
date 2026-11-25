"""Build the inputs of CoLP from the downloaded sources.

prepare.py SOURCES OUTDIR

Writes to OUTDIR:
  proteins.tsv      accession, symbol, gold-standard locations, in network, sequence length
  edges.tsv         the pooled interaction network (accession pairs and their sources)
  annotations.json  InterPro motifs and GO function/process terms per protein (S_Motif, S_GO)
  sequences.tsv     accession and sequence for every protein used
  expr_<study>.npz  log2, quantile-normalised, gene-level expression of each study's selected samples
  prepare.json      the counts behind Table 1B, 1C and 1D
"""

from __future__ import annotations

import collections
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from settings import (CODES_GOLD, CONDITIONS, GO_RELEASE, LOCATIONS, LOC_TERMS, RAMANI_EXCLUDE,  # noqa: E402
                      REACTOME_TYPES, STUDIES, Y2H_MS_PUBMED)

from condloc.coherence import knn_impute, quantile_normalize  # noqa: E402


# ---------------------------------------------------------------- identifiers
class Resolver:
    """Map accessions, Entrez gene IDs and gene symbols onto current human Swiss-Prot accessions."""

    def __init__(self, path: Path):
        self.seq, self.symbol, self.interpro = {}, {}, {}
        self.by_acc, self.by_gene, self.by_sym, syn = {}, collections.defaultdict(list), {}, collections.defaultdict(set)
        self.by_name: dict[str, str] = {}
        with gzip.open(path, "rt") as h:
            next(h)
            for line in h:
                acc, name, gene, synonyms, ipr, geneid, seq = line.rstrip("\n").split("\t")
                self.by_name[name] = acc
                self.seq[acc] = seq
                self.symbol[acc] = gene
                self.interpro[acc] = [x for x in ipr.split(";") if x]
                self.by_acc[acc] = acc
                for g in geneid.split(";"):
                    if g:
                        self.by_gene[g].append(acc)
                if gene:
                    self.by_sym.setdefault(gene.upper(), acc)
                for s in synonyms.split():
                    syn[s.upper()].add(acc)
        for s, accs in syn.items():
            if s not in self.by_sym and len(accs) == 1:
                self.by_sym[s] = next(iter(accs))

    def acc(self, accession: str | None = None, gene: str | None = None, symbol: str | None = None,
            synonyms: list[str] | None = None) -> str | None:
        if accession:
            a = self.by_acc.get(accession.split("-")[0])
            if a:
                return a
        for s in synonyms or ():
            a = self.by_name.get(s) or self.by_acc.get(s)
            if a:
                return a
        if gene and gene in self.by_gene and len(self.by_gene[gene]) == 1:
            return self.by_gene[gene][0]
        if symbol:
            return self.by_sym.get(symbol.upper())
        return None


# ---------------------------------------------------------------- GO
def read_obo(path: Path) -> tuple[dict[str, set[str]], dict[str, str]]:
    parents: dict[str, set[str]] = collections.defaultdict(set)
    alt: dict[str, str] = {}
    cur, kind = None, None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if line.startswith("["):
            kind, cur = line, None
        elif line.startswith("id: ") and kind == "[Term]":
            cur = line[4:]
        elif cur and line.startswith("is_a: "):
            parents[cur].add(line[6:16])
        elif cur and line.startswith("relationship: part_of "):
            parents[cur].add(line[22:32])
        elif cur and line.startswith("alt_id: "):
            alt[line[8:]] = cur
    return parents, alt


def ancestors(term: str, parents, memo) -> set[str]:
    if term not in memo:
        out = {term}
        for p in parents.get(term, ()):
            out |= ancestors(p, parents, memo)
        memo[term] = out
    return memo[term]


def gold_standard(src: Path, res: Resolver):
    parents, alt = read_obo(src / "go" / f"gene_ontology.{GO_RELEASE}.obo")
    memo: dict[str, set[str]] = {}
    raw: dict[str, set[str]] = collections.defaultdict(set)
    fn: dict[str, set[str]] = collections.defaultdict(set)
    unresolved = set()
    with gzip.open(src / "go" / f"goa_human.{GO_RELEASE}.gaf.gz", "rt", errors="replace") as h:
        for line in h:
            if line.startswith("!"):
                continue
            p = line.rstrip("\n").split("\t")
            if not p[0].startswith("UniProt") or "NOT" in p[3] or "taxon:9606" not in p[12]:
                continue
            acc = res.acc(accession=p[1], symbol=p[2], synonyms=p[10].split("|"))
            if acc is None:
                unresolved.add(p[1])
                continue
            term = alt.get(p[4], p[4])
            if p[8] in ("F", "P"):
                fn[acc].add(term)  # GO function and process terms (S_GO); cellular component left out
            elif p[8] == "C" and p[6] in CODES_GOLD:
                anc = ancestors(term, parents, memo)
                for loc, go in LOC_TERMS.items():
                    if go in anc:
                        raw[acc].add(loc)
    gold = {a: sorted(v, key=LOCATIONS.index) for a, v in raw.items() if v}
    return gold, fn, len(unresolved)


# ---------------------------------------------------------------- network
def read_pc1(src: Path, name: str, types=None, pubs=None) -> set[tuple[str, str]]:
    nodes = {}
    with open(src / "ppi" / f"{name}-node-attributes.txt") as h:
        next(h)
        for line in h:
            p = line.rstrip("\n").split("\t")
            nodes[p[0]] = p
    out = set()
    with open(src / "ppi" / f"{name}-edge-attributes.txt") as h:
        next(h)
        for line in h:
            p = line.rstrip("\n").split("\t")
            if types and p[1] not in types:
                continue
            if pubs and not any(x in pubs for x in p[6].split(";")):
                continue
            a, b = nodes.get(p[0]), nodes.get(p[2])
            if not a or not b or a[6] != "9606" or b[6] != "9606" or a[5] != "protein" or b[5] != "protein":
                continue
            out.add((a[1], a[2], a[3], b[1], b[2], b[3]))
    return out


def network(src: Path, res: Resolver):
    pooled: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    raw_counts = {}

    def add(source, a, b):
        if a and b and a != b:
            pooled[tuple(sorted((a, b)))].add(source)

    def pc1_acc(sym, accs, gene):
        first = accs.split(":")[0] if accs and accs != "NOT_SPECIFIED" else None
        return res.acc(accession=first, gene=gene if gene != "NOT_SPECIFIED" else None, symbol=sym)

    for source, name, kw in (("HPRD", "hprd", {}), ("REACTOME", "reactome", {"types": REACTOME_TYPES})):
        rows = read_pc1(src, name, **kw)
        raw_counts[source] = len({tuple(sorted((r[0], r[3]))) for r in rows})
        for r in rows:
            add(source, pc1_acc(r[0], r[1], r[2]), pc1_acc(r[3], r[4], r[5]))
    for source, pmid in Y2H_MS_PUBMED.items():
        rows = read_pc1(src, "biogrid", pubs={pmid})
        raw_counts[source] = len({tuple(sorted((r[0], r[3]))) for r in rows})
        for r in rows:
            add(source, pc1_acc(r[0], r[1], r[2]), pc1_acc(r[3], r[4], r[5]))
    n = 0
    for line in open(src / "ppi" / "ramani" / "gb-2005-6-5-r40-S4.txt"):
        s1, g1, s2, g2, ev = line.rstrip("\n").split("\t")[:5]
        if set(ev.split()) <= RAMANI_EXCLUDE:
            continue
        n += 1
        add("RAMANI", res.acc(gene=g1, symbol=s1), res.acc(gene=g2, symbol=s2))
    raw_counts["RAMANI"] = n
    return pooled, raw_counts


# ---------------------------------------------------------------- expression
def read_series(path: Path):
    titles, gsm, rows, genes = [], [], [], []
    with gzip.open(path, "rt", errors="replace") as h:
        for line in h:
            if line.startswith("!Sample_title"):
                titles = [x.strip('"') for x in line.rstrip("\n").split("\t")[1:]]
            elif line.startswith("!series_matrix_table_begin"):
                gsm = [x.strip('"') for x in next(h).rstrip("\n").split("\t")[1:]]
                for row in h:
                    if row.startswith("!series_matrix_table_end"):
                        break
                    p = row.rstrip("\n").split("\t")
                    genes.append(p[0].strip('"'))
                    rows.append([float(x) if x not in ("", "null", "NA", '"null"') else np.nan for x in p[1:]])
    return titles, gsm, genes, np.array(rows, dtype=float)


def read_soft_channel2(path: Path, platform: str):
    """Tumour channel (Cy5, ch2) of a two-colour GEO family: signal minus background, per sample."""
    samples = {}
    cur, title, plat, table, inside = None, None, None, [], False
    with gzip.open(path, "rt", errors="replace") as h:
        for line in h:
            if line.startswith("^SAMPLE"):
                cur, table = line.split("=")[1].strip(), []
            elif line.startswith("!Sample_title") and cur:
                title = line.split("=", 1)[1].strip()
            elif line.startswith("!Sample_platform_id") and cur:
                plat = line.split("=", 1)[1].strip()
            elif line.startswith("!sample_table_begin"):
                header = next(h).rstrip("\n").split("\t")
                si, bi = header.index("CH2_SIG_MEAN"), header.index("CH2_BKD_MEAN")
                inside = True
            elif line.startswith("!sample_table_end"):
                inside = False
                if plat == platform:
                    samples[cur] = (title, dict(table))
            elif inside:
                p = line.rstrip("\n").split("\t")
                try:
                    table.append((p[0], max(float(p[si]) - float(p[bi]), 1.0)))
                except ValueError:
                    table.append((p[0], np.nan))
    return samples


def read_annot(path: Path):
    out = {}
    with gzip.open(path, "rt", errors="replace") as h:
        header = None
        for line in h:
            if header is None:
                if line.startswith("ID\t"):
                    header = line.rstrip("\n").split("\t")
                    si, gi = header.index("Gene symbol"), header.index("Gene ID")
                continue
            if line.startswith("!"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) > gi and p[gi] and "///" not in p[gi]:
                out[p[0]] = (p[gi], p[si])
    return out


def gene_level(probes: list[str], x: np.ndarray, annot, res: Resolver):
    """log2, impute (genes < 30% missing), quantile normalise, then average the probes of each protein."""
    x = np.log2(np.clip(x, 1.0, None)) if np.nanmax(x) > 100 else x.copy()
    x, keep = knn_impute(x, k=10, max_missing=0.3)
    probes = [p for p, k in zip(probes, keep) if k]
    x = quantile_normalize(x)
    groups = collections.defaultdict(list)
    for i, p in enumerate(probes):
        if p in annot:
            acc = res.acc(gene=annot[p][0], symbol=annot[p][1])
            if acc:
                groups[acc].append(i)
    accs = sorted(groups)
    return accs, np.array([x[groups[a]].mean(axis=0) for a in accs], dtype=np.float32)


def expression(src: Path, out: Path, res: Resolver):
    counts = {}
    annots = {}
    for st in STUDIES:
        if st["platform"] not in annots:
            annots[st["platform"]] = read_annot(src / "geo" / f"{st['platform']}.annot.gz")
        annot = annots[st["platform"]]
        if st.get("two_colour"):
            samples = read_soft_channel2(src / "geo" / st["file"], st["platform"])
            chosen = [(t, tab) for _, (t, tab) in sorted(samples.items()) if re.fullmatch(st["select"], t)]
            probes = sorted(set().union(*[set(tab) for _, tab in chosen]))
            x = np.array([[tab.get(p, np.nan) for _, tab in chosen] for p in probes])
            titles = [t for t, _ in chosen]
        else:
            all_titles, _gsm, probes, mat = read_series(src / "geo" / st["file"])
            cols = [i for i, t in enumerate(all_titles) if re.fullmatch(st["select"], t)]
            x = mat[:, cols]
            titles = [all_titles[i] for i in cols]
        accs, g = gene_level(probes, x, annot, res)
        np.savez_compressed(out / f"expr_{st['id']}.npz", genes=np.array(accs), x=g, samples=np.array(titles))
        counts[st["id"]] = {"condition": st["condition"], "series": st["series"], "samples": len(titles),
                            "genes": len(accs), "subject_key": st.get("subject_key", st["series"])}
    per = {}
    for c in CONDITIONS:
        seen = {}
        for sid, v in counts.items():
            if v["condition"] == c:
                seen[v["subject_key"]] = max(seen.get(v["subject_key"], 0), v["samples"])
        per[c] = sum(seen.values())
    return counts, per


def main(src: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    res = Resolver(src / "uniprot" / "human_sprot.tsv.gz")
    gold, fn, unresolved = gold_standard(src, res)
    pooled, raw_counts = network(src, res)
    in_net = collections.Counter()
    for a, b in pooled:
        in_net[a] += 1
        in_net[b] += 1
    counts, per_condition = expression(src, out, res)

    used = sorted(res.seq)  # every human Swiss-Prot protein; those outside the network keep self-only network sets
    with open(out / "proteins.tsv", "w") as h:
        h.write("accession\tsymbol\tlocations\tdegree\tlength\n")
        for a in used:
            h.write(f"{a}\t{res.symbol[a]}\t{','.join(gold.get(a, []))}\t{in_net.get(a, 0)}\t{len(res.seq[a])}\n")
    with open(out / "sequences.tsv", "w") as h:
        for a in used:
            h.write(f"{a}\t{res.seq[a]}\n")
    with open(out / "edges.tsv", "w") as h:
        h.write("a\tb\tsources\n")
        for (a, b), s in sorted(pooled.items()):
            h.write(f"{a}\t{b}\t{','.join(sorted(s))}\n")
    json.dump({a: {"motif": res.interpro[a], "go": sorted(fn.get(a, ()))} for a in used},
              open(out / "annotations.json", "w"), sort_keys=True)

    loc_counts = collections.Counter(loc for v in gold.values() for loc in v)
    summary = {
        "go_release": GO_RELEASE,
        "table1b": {"proteins": len(gold), "locations": sum(loc_counts.values()),
                    "per_location": {loc: loc_counts.get(loc, 0) for loc in LOCATIONS},
                    "unresolved_go_accessions": unresolved},
        "table1c": {"interactions": len(pooled), "proteins": len(in_net), "per_source_raw": raw_counts,
                    "per_source_mapped": dict(collections.Counter(s for v in pooled.values() for s in v))},
        "table1d": {"per_condition": per_condition, "studies": counts},
        "gold_in_network": sum(1 for a in gold if a in in_net),
    }
    json.dump(summary, open(out / "prepare.json", "w"), indent=1, sort_keys=True)
    print(json.dumps({k: summary[k] for k in ("table1b", "table1c")}, indent=1))
    print(json.dumps(per_condition))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
