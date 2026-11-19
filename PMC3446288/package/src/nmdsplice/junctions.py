"""Junction annotation: gene, strand, canonical or alternative, PTC status, regulation."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from .annotation import Gene, Transcript
from .ptc import ExonCatalog, ModelIndex, PTCResult, detect, model_is_ptc
from .quant import EVIDENCE_READS, regulation


@dataclass
class AnnotatedJunction:
    chrom: str
    donor: int
    acceptor: int
    gene: str = ""  # gene key, "" when the junction lies in no RefSeq gene
    symbol: str = ""
    strand: str = ""
    canonical: bool = False
    ptc: PTCResult | None = None

    @property
    def key(self):
        return (self.chrom, self.donor, self.acceptor)


def assign_genes(junctions, genes: list[Gene]) -> dict:
    """Gene of each junction: a RefSeq gene whose span contains it; when several do, the one with an
    exon boundary at the donor or acceptor, then the shorter span."""
    by_chrom = defaultdict(list)
    for g in genes:
        by_chrom[g.chrom].append(g)
    starts = {}
    for c, gs in by_chrom.items():
        gs.sort(key=lambda g: g.start)
        starts[c] = np.array([g.start for g in gs])
    bounds = {}
    for g in genes:
        b = set()
        for t in g.refseq:
            for s, e in t.exons:
                b.add(s)
                b.add(e)
        bounds[g.key] = b
    maxlen = max((g.end - g.start for g in genes), default=0)
    out = {}
    for j in junctions:
        c, d, a = j
        if c not in by_chrom:
            continue
        hi = np.searchsorted(starts[c], d, side="left")
        lo = np.searchsorted(starts[c], d - maxlen, side="left")
        best = None
        for g in by_chrom[c][lo:hi]:
            if g.start < d and a < g.end:
                key = (d in bounds[g.key] or a in bounds[g.key], -(g.end - g.start))
                if best is None or key > best[0]:
                    best = (key, g)
        if best is not None:
            out[j] = best[1]
    return out


def canonical_set(genes: list[Gene]) -> set:
    """Junctions between consecutive exons of the longest RefSeq model of each gene."""
    out = set()
    for g in genes:
        t = g.longest()
        for d, a in t.junctions():
            out.add((g.chrom, d, a))
    return out


def annotate(junctions, genes, catalog: ExonCatalog, models: ModelIndex, fasta) -> dict:
    """Gene, strand, canonical flag and PTC call of each junction."""
    gene_of = assign_genes(junctions, genes)
    canon = canonical_set(genes)
    out = {}
    for j in junctions:
        g = gene_of.get(j)
        aj = AnnotatedJunction(*j)
        if g is not None:
            aj.gene, aj.symbol, aj.strand = g.key, g.symbol, g.strand
            aj.canonical = j in canon
            aj.ptc = detect(fasta, catalog, models, j[0], g.strand, j[1], j[2])
        else:
            # no RefSeq gene: try both strands for exon evidence only
            aj.ptc = PTCResult("unannotated")
        out[j] = aj
    return out


def false_positive_genes(annotated: dict, fasta, model_lookup: dict) -> set:
    """Genes whose selected model is itself called PTC+ (early normal stop)."""
    cache = {}
    bad = set()
    for aj in annotated.values():
        p = aj.ptc
        if p is None or not p.ptc or not p.model:
            continue
        if p.model not in cache:
            m = model_lookup.get(p.model)
            cache[p.model] = m is not None and model_is_ptc(fasta, m)
        if cache[p.model]:
            bad.add(aj.gene)
    return bad


def evident(wt: float, ko: float, reads: int = EVIDENCE_READS) -> bool:
    return wt >= reads or ko >= reads


def fold_changes(wt, ko, wt_lib, ko_lib, gene_fc=None):
    """Vectorised KO/WT fold change of TMM-scaled junction reads, divided by the gene fold change."""
    wt = np.asarray(wt, float) / wt_lib
    ko = np.asarray(ko, float) / ko_lib
    with np.errstate(divide="ignore", invalid="ignore"):
        fc = np.where(wt > 0, ko / np.where(wt > 0, wt, 1), np.where(ko > 0, np.inf, 1.0))
        if gene_fc is not None:
            g = np.asarray(gene_fc, float)
            ok = np.isfinite(g) & (g > 0)
            fc = np.where(ok, fc / np.where(ok, g, 1), fc)
    return fc


def regulations(fc) -> list[str]:
    return [regulation(x) for x in fc]
