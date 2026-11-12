"""Build the seven gene-level datasets and their MSigDB v1.0 C2 gene sets.

Usage: prepare_data.py SOURCES ANNOTATION OUTDIR

SOURCES is the folder fetch_inputs.sh fills (gsea/, geo/, bioc_export/); ANNOTATION the
committed identifier tables (build_annotation.py). For each dataset, writes OUTDIR/<name>.npz with
  genes    row keys (gene symbols for the two lung sets, Entrez Gene IDs otherwise)
  symbols  a display symbol per row
  samples  sample names
  X        genes x samples expression, no missing values
  y        True for the case class (Mutant, Cancer, TEL-AML1, Metastatic, Poor)
  classes  the two class names, control first
and OUTDIR/<name>_sets.json: {pathway: {"size": members in the GMT file, "rows": [row index]}}.
OUTDIR/datasets.json records every choice and count.

Choices (the paper states none of them):
  Lung Michigan, Lung Boston  GSEA's collapsed-symbol files as they are (no log): the CORGs of
                              Table 1 come back exactly from them.
  Other Affymetrix sets       probes mapped to Entrez Gene IDs by the GEO platform annotation,
                              probes with more than one gene dropped, collapsed by the per-sample
                              maximum (GSEA's Max_probe rule, which the lung files follow).
  Breast Netherlands          the 295 arrays of van de Vijver et al. 2002 (Bioconductor
                              seventyGeneData), log10 ratios, probes collapsed by their mean.
  Prostate                    the three GEO platforms of GSE3933 (log2 ratios), IMAGE clones
                              mapped to Entrez Gene IDs through GPL2695's annotation, genes
                              measured in at least 80% of the arrays, the rest imputed (k = 10
                              nearest genes).
  C2 symbols                  mapped to Entrez Gene IDs by NCBI gene_info: official symbol, then
                              a unique synonym, then a discontinued symbol in gene_history.
"""

from __future__ import annotations

import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

csv.field_size_limit(1 << 30)


def read_gmt(path):
    sets = {}
    for line in open(path, encoding="utf-8"):
        parts = line.rstrip("\n").split("\t")
        seen, members = set(), []
        for g in parts[2:]:
            if g and g not in seen:
                seen.add(g)
                members.append(g)
        sets[parts[0]] = members
    return sets


def read_gct(path):
    lines = [l.rstrip("\r") for l in open(path, encoding="utf-8").read().split("\n")]
    samples = lines[2].rstrip("\t").split("\t")[2:]
    genes, rows = [], []
    for line in lines[3:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        genes.append(parts[0])
        rows.append([float(v) for v in parts[2 : 2 + len(samples)]])
    return genes, samples, np.array(rows)


def read_cls(path):
    lines = [l for l in open(path, encoding="utf-8").read().split("\n") if l.strip()]
    return lines[2].split()


def series_matrix(path):
    """GEO series matrix: (sample header dict, probe ids, values with NaN for null)."""
    meta, ids, rows = defaultdict(list), [], []
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        in_table = False
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("!series_matrix_table_begin"):
                in_table = True
                header = None
                continue
            if line.startswith("!series_matrix_table_end"):
                break
            if not in_table:
                if line.startswith("!Sample_"):
                    parts = [p.strip('"') for p in line.split("\t")]
                    meta[parts[0]].append(parts[1:])
                continue
            parts = [p.strip('"') for p in line.split("\t")]
            if header is None:
                header = parts
                continue
            ids.append(parts[0])
            rows.append([float(v) if v not in ("", "null", "NA") else np.nan for v in parts[1:]])
    meta["ID_REF"] = [header[1:]]
    return meta, ids, np.array(rows)


def geo_annot(path):
    """probe -> Entrez Gene ID (single-gene probes only) from a GEO .annot.gz file."""
    out = {}
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        header = None
        for line in f:
            if line.startswith(("!", "#", "^")):
                continue
            parts = line.rstrip("\n").split("\t")
            if header is None:
                header = parts
                i_id, i_gene = header.index("ID"), header.index("Gene ID")
                i_clone = header.index("Platform_CLONEID") if "Platform_CLONEID" in header else None
                continue
            gid = parts[i_gene] if len(parts) > i_gene else ""
            if gid and "///" not in gid:
                out[parts[i_id]] = gid
                if i_clone is not None and parts[i_clone]:
                    out["clone:" + parts[i_clone]] = gid
    return out


def entrez_tables(src):
    return entrez_tables_from(src / "annot/Homo_sapiens.gene_info.gz", src / "annot/gene_history_human.tsv.gz")


def entrez_tables_from(gene_info, gene_history):
    symbol, synonyms, display = {}, defaultdict(set), {}
    with gzip.open(gene_info, "rt", encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            gid, sym = p[1], p[2]
            display[gid] = sym
            symbol.setdefault(sym, gid)
            if p[4] != "-":
                for s in p[4].split("|"):
                    synonyms[s].add(gid)
    history = defaultdict(set)
    with gzip.open(gene_history, "rt", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if p[1] != "-":
                history[p[3]].add(p[1])
    return symbol, synonyms, history, display


def symbol_to_entrez(sym, tables):
    symbol, synonyms, history, _ = tables
    if sym in symbol:
        return symbol[sym], "symbol"
    if len(synonyms.get(sym, ())) == 1:
        return next(iter(synonyms[sym])), "synonym"
    if len(history.get(sym, ())) == 1:
        return next(iter(history[sym])), "history"
    return None, "unmapped"


def table(path):
    """A two-column gzip TSV with a header as a dict."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        next(f)
        return dict(line.rstrip("\n").split("\t")[:2] for line in f)


class Annotation:
    """The committed identifier tables (build_annotation.py)."""

    def __init__(self, folder: Path):
        self.symbol_entrez = {k: v for k, v in table(folder / "symbol_entrez.tsv.gz").items() if v}
        self.display = table(folder / "entrez_symbol.tsv.gz")
        self.probe = {g: table(folder / f"probe_entrez_{g}.tsv.gz") for g in ("GPL96", "GPL8300", "GPL2695")}
        self.clone = table(folder / "clone_entrez.tsv.gz")
        self.spot = {g: table(folder / f"spot_clone_{g}.tsv.gz") for g in ("GPL3044", "GPL3289")}

    def entrez(self, symbol):
        return self.symbol_entrez.get(symbol)


def collapse(keys, X, how):
    """Rows of X grouped by key (None dropped): per-sample max or nan-mean."""
    groups = defaultdict(list)
    for i, k in enumerate(keys):
        if k:
            groups[k].append(i)
    genes = sorted(groups, key=lambda k: groups[k][0])
    if how == "max":
        Y = np.array([np.nanmax(X[groups[g]], axis=0) for g in genes])
    else:
        with np.errstate(all="ignore"):
            Y = np.array([np.nanmean(X[groups[g]], axis=0) for g in genes])
    return genes, Y


def impute_knn(X, k=10):
    """Fill missing values from the k nearest genes (Euclidean distance over shared columns)."""
    from sklearn.impute import KNNImputer

    # KNNImputer works on samples x features; genes are the "samples" here.
    return KNNImputer(n_neighbors=k).fit_transform(X)


def save(out, name, genes, symbols, samples, X, y, classes, sets_src, ann, record):
    X = np.asarray(X, dtype=float)
    keep = np.all(np.isfinite(X), axis=1) & (X.std(axis=1) > 0)
    genes = [g for g, k in zip(genes, keep) if k]
    symbols = [s for s, k in zip(symbols, keep) if k]
    X = X[keep]
    index = {g: i for i, g in enumerate(genes)}
    sets, stats = {}, Counter()
    for pname, members in sets_src.items():
        rows = []
        for m in members:
            key = m if ann is None else ann.entrez(m)
            if key in index and index[key] not in rows:
                rows.append(index[key])
        sets[pname] = {"size": len(members), "rows": rows}
        stats["members"] += len(members)
        stats["measured"] += len(rows)
    np.savez_compressed(out / f"{name}.npz", genes=np.array(genes), symbols=np.array(symbols),
                        samples=np.array(samples), X=X, y=np.asarray(y, dtype=bool), classes=np.array(classes))
    (out / f"{name}_sets.json").write_text(json.dumps(sets))
    c2_genes = {m for ms in sets_src.values() for m in ms}
    if ann is None:
        covered = sum(g in index for g in c2_genes)
    else:
        covered = sum(ann.entrez(g) in index for g in c2_genes)
    record[name] = dict(record.get(name, {}), genes=len(genes), samples=len(samples),
                        cases=int(np.sum(y)), controls=int(len(y) - np.sum(y)), classes=list(classes),
                        c2_genes_measured=covered, c2_genes=len(c2_genes),
                        member_slots_measured=stats["measured"], member_slots=stats["members"])
    print(name, record[name], flush=True)


def main(src: Path, annotation: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    c2 = read_gmt(src / "gsea/c2.symbols.gmt")
    tables = Annotation(annotation)
    display = tables.display
    record = {"c2": {"sets": len(c2), "genes": len({g for m in c2.values() for g in m})}}
    record["c2"]["genes_with_entrez_id"] = sum(tables.entrez(g) is not None for g in {g for m in c2.values() for g in m})

    # Lung: GSEA files as they are.
    for name, gct, cls in [("lung_michigan", "Lung_Michigan_collapsed_symbols.gct", "Lung_Michigan.cls"),
                           ("lung_boston", "Lung_Boston_collapsed_symbols.gct", "Lung_Boston.cls")]:
        genes, samples, X = read_gct(src / "gsea" / gct)
        y = np.array(read_cls(src / "gsea" / cls)) == "D"
        record[name] = {"source": gct, "transform": "none"}
        save(out, name, genes, genes, samples, X, y, ["Good", "Poor"], c2, None, record)

    # Breast USA: GSE2034 MAS5 values; labels from the series' clinical table.
    meta, ids, X = series_matrix(src / "geo/GSE2034_series_matrix.txt.gz")
    gsm = meta["ID_REF"][0]
    clin = {}
    for line in open(src / "geo/gse2034_miniml/GSE2034-tbl-2.txt", encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        clin[p[1]] = int(p[4])
    y = np.array([clin[g] == 1 for g in gsm])
    annot = tables.probe["GPL96"]
    genes, Xg = collapse([annot.get(i) for i in ids], X, "max")
    record["breast_usa"] = {"source": "GSE2034 series matrix (MAS5)", "transform": "none",
                            "collapse": "per-sample max over single-gene probes",
                            "labels": "relapse (distant metastasis) column of the GEO clinical table"}
    save(out, "breast_usa", genes, [display.get(g, g) for g in genes], gsm, Xg, y,
         ["Non-metastatic", "Metastatic"], c2, tables, record)

    # Breast Netherlands: van de Vijver 295, metastasis within five years.
    vdv = src / "bioc_export"  # export_bioc.py
    samples, rows, probes = None, [], []
    with gzip.open(vdv / "vdv_exprs.tsv.gz", "rt") as f:
        r = csv.reader(f, delimiter="\t")
        samples = next(r)[1:]
        for p in r:
            probes.append(p[0])
            rows.append([float(v) if v not in ("NA", "") else np.nan for v in p[1:]])
    X = np.array(rows)
    fdata = {p["" if "" in p else list(p)[0]]: p for p in csv.DictReader(open(vdv / "vdv_fdata.tsv"), delimiter="\t")}
    keys = []
    for pr in probes:
        gid = ((fdata.get(pr) or {}).get("EntrezGene.ID") or "NA").strip()
        keys.append(gid if gid not in ("NA", "", None) else None)
    pdata = {p[""]: p for p in csv.DictReader(open(vdv / "vdv_pdata.tsv"), delimiter="\t")}
    y = np.array([pdata[s]["TTMevent"] == "1" and float(pdata[s]["TTM"]) <= 5 for s in samples])
    genes, Xg = collapse(keys, X, "mean")
    frac_missing = np.mean(np.isnan(Xg))
    Xg = np.where(np.isnan(Xg), np.nanmean(Xg, axis=1, keepdims=True), Xg)
    record["breast_netherlands"] = {"source": "seventyGeneData vanDeVijver (log10 ratios)", "transform": "none",
                                    "collapse": "mean over probes with one Entrez ID",
                                    "missing_filled_with_gene_mean": float(frac_missing),
                                    "labels": "TTMevent = 1 and TTM <= 5 years"}
    save(out, "breast_netherlands", genes, [display.get(g, g) for g in genes], samples, Xg, y,
         ["Non-metastatic", "Metastatic"], c2, tables, record)

    # Leukemia: stjudem (vsn), TEL-AML1 against hyperdiploid > 50.
    with gzip.open(src / "bioc_export/stjude_exprs.tsv.gz", "rt") as f:
        r = csv.reader(f, delimiter="\t")
        samples = next(r)[1:]
        probes, rows = [], []
        for p in r:
            probes.append(p[0])
            rows.append([float(v) for v in p[1:]])
    X = np.array(rows)
    labels = [p["label"] for p in csv.DictReader(open(src / "bioc_export/stjude_pdata.tsv"), delimiter="\t")]
    keep = [i for i, l in enumerate(labels) if l in ("TEL", "Hyperdip")]
    annot95 = tables.probe["GPL8300"]
    genes, Xg = collapse([annot95.get(p) for p in probes], X[:, keep], "max")
    y = np.array([labels[i] == "TEL" for i in keep])
    record["leukemia"] = {"source": "stjudem 1.40.0 (vsn, median polish)", "transform": "none",
                          "collapse": "per-sample max over single-gene probes"}
    save(out, "leukemia", genes, [display.get(g, g) for g in genes], [samples[i] for i in keep], Xg, y,
         ["HH", "TEL-AML1"], c2, tables, record)

    # NF-kB: GSE2624, the 24 TNF-stimulated arrays (1, 3 and 6 h); C = no doxycycline (mutant IkBa on).
    meta, ids, X = series_matrix(src / "geo/GSE2624_series_matrix.txt.gz")
    titles = meta["!Sample_title"][0]
    keep = [i for i, t in enumerate(titles) if not t.endswith("0")]
    genes, Xg = collapse([annot95.get(i) for i in ids], X[:, keep], "max")
    y = np.array([titles[i][3] == "C" for i in keep])
    record["nfkb"] = {"source": "GSE2624 series matrix (MAS5)", "transform": "none",
                      "collapse": "per-sample max over single-gene probes",
                      "samples_kept": "TNF 1, 3, 6 h; 0 h dropped", "mutant": "C (no doxycycline)"}
    save(out, "nfkb", genes, [display.get(g, g) for g in genes], [titles[i] for i in keep], Xg, y,
         ["Wildtype", "Mutant"], c2, tables, record)

    # Variant (a hypothesis, not the main run): the three complete replicate series 180, 220 and
    # 266 at all four time points (0, 1, 3, 6 h), 12 C and 12 D arrays.
    keep = [i for i, t in enumerate(titles) if t[:3] in ("180", "220", "266")]
    genes, Xg = collapse([annot95.get(i) for i in ids], X[:, keep], "max")
    y = np.array([titles[i][3] == "C" for i in keep])
    record["nfkb_alt"] = dict(record["nfkb"], samples_kept="series 180, 220, 266 at 0, 1, 3, 6 h")
    save(out, "nfkb_alt", genes, [display.get(g, g) for g in genes], [titles[i] for i in keep], Xg, y,
         ["Wildtype", "Mutant"], c2, tables, record)

    # Prostate: GSE3933 on three platforms, PT (cancer) and PN (normal) arrays.
    a2695 = tables.probe["GPL2695"]
    per_platform = []
    for plat in ("GPL2695", "GPL3044", "GPL3289"):
        meta, ids, X = series_matrix(src / f"geo/GSE3933-{plat}_series_matrix.txt.gz")
        titles = meta["!Sample_title"][0]
        if plat == "GPL2695":
            keys = [a2695.get(i) for i in ids]
        else:
            spot = tables.spot[plat]
            keys = [tables.clone.get(spot.get(i, "")) for i in ids]
        keep = [i for i, t in enumerate(titles) if t.startswith(("PT", "PN"))]
        genes, Xg = collapse(keys, X[:, keep], "mean")
        per_platform.append((dict(zip(genes, Xg)), [titles[i] for i in keep]))
    all_genes = sorted({g for d, _ in per_platform for g in d}, key=int)
    samples = [s for _, t in per_platform for s in t]
    X = np.full((len(all_genes), len(samples)), np.nan)
    col = 0
    for d, t in per_platform:
        for gi, g in enumerate(all_genes):
            if g in d:
                X[gi, col : col + len(t)] = d[g]
        col += len(t)
    present = np.mean(np.isfinite(X), axis=1) >= 0.8
    all_genes = [g for g, k in zip(all_genes, present) if k]
    X = impute_knn(X[present])
    y = np.array([s.startswith("PT") for s in samples])
    record["prostate"] = {"source": "GSE3933 series matrices, three platforms (log2 ratios)", "transform": "none",
                          "collapse": "mean over spots of a gene within a platform",
                          "filter": "measured in >= 80% of the 103 arrays", "impute": "KNN, k = 10"}
    save(out, "prostate", all_genes, [display.get(g, g) for g in all_genes], samples, X, y,
         ["Normal", "Cancer"], c2, tables, record)

    (out / "datasets.json").write_text(json.dumps(record, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
