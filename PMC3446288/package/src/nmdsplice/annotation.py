"""Exon and transcript models from UCSC genePred-style tables.

Coordinates follow UCSC: 0-based starts, half-open ends. A junction is the pair
(donor, acceptor) = (end of the upstream exon in genome order, start of the downstream exon),
which is also how the paper's Additional files 8 and 9 print "Left jxn" and "Right jxn".
"""

from __future__ import annotations

import gzip
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Transcript:
    name: str
    chrom: str
    strand: str
    tx_start: int
    tx_end: int
    cds_start: int
    cds_end: int
    exons: list[tuple[int, int]]
    gene: str = ""
    source: str = ""

    @property
    def coding(self) -> bool:
        return self.cds_end > self.cds_start

    @property
    def length(self) -> int:
        return sum(e - s for s, e in self.exons)

    def junctions(self) -> list[tuple[int, int]]:
        return [(self.exons[i][1], self.exons[i + 1][0]) for i in range(len(self.exons) - 1)]


def _open(path):
    path = Path(path)
    return gzip.open(path, "rt") if path.suffix == ".gz" else open(path)


# Column layout of each UCSC table: (offset of the name column, has a gene-name column at +11).
_LAYOUT = {
    "refGene": (1, True),  # bin, name, chrom, strand, txStart, txEnd, cdsStart, cdsEnd, exonCount, starts, ends, score, name2
    "ensGene": (1, True),
    "knownGene": (0, False),  # name, chrom, strand, ...
    "genscan": (1, False),
    "exoniphy": (1, False),
}


def read_genepred(path, source: str, gene_names: dict[str, str] | None = None) -> list[Transcript]:
    """Read a UCSC genePred table (refGene, ensGene, knownGene, genscan or exoniphy)."""
    off, has_name2 = _LAYOUT[source]
    out = []
    with _open(path) as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            name, chrom, strand = p[off], p[off + 1], p[off + 2]
            tx_start, tx_end, cds_start, cds_end = (int(x) for x in p[off + 3 : off + 7])
            starts = [int(x) for x in p[off + 8].rstrip(",").split(",") if x]
            ends = [int(x) for x in p[off + 9].rstrip(",").split(",") if x]
            gene = p[off + 11] if has_name2 and len(p) > off + 11 else ""
            if gene_names is not None:
                gene = gene_names.get(name, gene)
            out.append(
                Transcript(name, chrom, strand, tx_start, tx_end, cds_start, cds_end,
                           list(zip(starts, ends)), gene, source)
            )
    return out


@dataclass
class Gene:
    """A RefSeq gene: the transcripts of one symbol on one chromosome and strand, merged if they overlap."""

    symbol: str
    chrom: str
    strand: str
    start: int
    end: int
    refseq: list[Transcript] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.symbol}|{self.chrom}:{self.start}-{self.end}"

    def longest(self) -> Transcript:
        """Longest RefSeq model (by exonic length; ties: coding first, then name)."""
        return max(self.refseq, key=lambda t: (t.length, t.coding, t.name))


def refseq_genes(refgene: list[Transcript], chroms: set[str] | None = None) -> list[Gene]:
    """Group RefSeq transcripts into genes by symbol, chromosome and strand, splitting distant loci."""
    by = defaultdict(list)
    for t in refgene:
        if chroms is not None and t.chrom not in chroms:
            continue
        by[(t.gene, t.chrom, t.strand)].append(t)
    genes = []
    for (sym, chrom, strand), ts in by.items():
        ts.sort(key=lambda t: t.tx_start)
        cur = None
        for t in ts:
            if cur is not None and t.tx_start < cur.end:
                cur.end = max(cur.end, t.tx_end)
                cur.refseq.append(t)
            else:
                cur = Gene(sym, chrom, strand, t.tx_start, t.tx_end, [t])
                genes.append(cur)
    genes.sort(key=lambda g: (g.chrom, g.start, g.end, g.symbol))
    return genes


class IntervalIndex:
    """Bins items with (start, end) per chromosome and strand for overlap queries."""

    BIN = 100_000

    def __init__(self):
        self._bins = defaultdict(list)

    def add(self, chrom, strand, start, end, item):
        for b in range(start // self.BIN, (max(end - 1, start)) // self.BIN + 1):
            self._bins[(chrom, strand, b)].append((start, end, item))

    def overlapping(self, chrom, strand, start, end):
        seen = set()
        for b in range(start // self.BIN, (max(end - 1, start)) // self.BIN + 1):
            for s, e, it in self._bins.get((chrom, strand, b), ()):
                if s < end and e > start and id(it) not in seen:
                    seen.add(id(it))
                    yield it


def exons_within(genes: list[Gene], sets: dict[str, list[Transcript]]) -> dict[str, set[tuple[int, int]]]:
    """Exons of every set that lie inside each RefSeq gene's span on its strand."""
    idx = IntervalIndex()
    for g in genes:
        idx.add(g.chrom, g.strand, g.start, g.end, g)
    out: dict[str, set[tuple[int, int]]] = {g.key: set() for g in genes}
    for ts in sets.values():
        for t in ts:
            for s, e in t.exons:
                for g in idx.overlapping(t.chrom, t.strand, s, e):
                    if s >= g.start and e <= g.end:
                        out[g.key].add((s, e))
    return out
