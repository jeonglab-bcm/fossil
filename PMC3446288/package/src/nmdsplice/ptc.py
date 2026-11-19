"""PTC detection for splice junctions (Additional file 1, "PTC-detection").

For each junction: find the repository exons that end at its donor and start at its acceptor
(junctions with an unannotated exon are excluded); pick the longest compatible coding model from
RefSeq, then Ensembl; build the transcript from that model's exons upstream and downstream of the
junction exons; translate from the model's annotated start codon; call a PTC when the first stop is
more than 49 nt upstream of the 3'-most exon-exon junction. Junctions whose transcript loses the
annotated start are "ambiguous CDS" and excluded. Genes whose selected model is itself called PTC+
(an early normal stop) are false positives: their PTC calls are removed.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .annotation import IntervalIndex, Transcript

STOPS = {"TAA", "TAG", "TGA"}
PTC_DISTANCE = 49  # "more than 49 nucleotides upstream of the 3' terminal exon-exon junction"
_COMP = str.maketrans("ACGTNacgtn", "TGCANtgcan")


def revcomp(s: str) -> str:
    return s.translate(_COMP)[::-1]


@dataclass
class PTCResult:
    status: str  # ptc, no_ptc, unannotated, ambiguous_cds, no_model
    model: str = ""
    stop_genomic: int = -1  # genomic position of the stop codon's first base (0-based)
    stop_codon: str = ""
    distance: int = -1  # nt from the stop codon's first base (exclusive) to the last exon-exon junction
    left_ae: bool = False  # the left (genomic) exon is not in the model ("AE")
    right_ae: bool = False

    @property
    def ptc(self) -> bool:
        return self.status == "ptc"


class ExonCatalog:
    """Repository exons indexed by chromosome, strand and boundary."""

    def __init__(self, sets: dict[str, list[Transcript]]):
        self.by_end = defaultdict(set)
        self.by_start = defaultdict(set)
        self.first_ends = defaultdict(set)  # end coordinates (genomic) of 5'-first exons, by strand
        self.last_starts = defaultdict(set)
        for ts in sets.values():
            for t in ts:
                for s, e in t.exons:
                    self.by_end[(t.chrom, t.strand, e)].add((s, e))
                    self.by_start[(t.chrom, t.strand, s)].add((s, e))
                if t.source in ("refGene", "knownGene", "ensGene") and len(t.exons) > 1:
                    first, last = (t.exons[0], t.exons[-1]) if t.strand == "+" else (t.exons[-1], t.exons[0])
                    self.first_ends[(t.chrom, t.strand)].add(first)
                    self.last_starts[(t.chrom, t.strand)].add(last)

    def ending_at(self, chrom, strand, pos):
        return self.by_end.get((chrom, strand, pos), set())

    def starting_at(self, chrom, strand, pos):
        return self.by_start.get((chrom, strand, pos), set())


class ModelIndex:
    """Coding RefSeq and Ensembl models for PTC detection, by overlap."""

    def __init__(self, refgene: list[Transcript], ensgene: list[Transcript]):
        self.idx = {"refGene": IntervalIndex(), "ensGene": IntervalIndex()}
        for src, ts in (("refGene", refgene), ("ensGene", ensgene)):
            for t in ts:
                if t.coding:
                    self.idx[src].add(t.chrom, t.strand, t.tx_start, t.tx_end, t)

    def compatible(self, chrom, strand, donor, acceptor):
        """Longest coding model that has an exon ending at the donor or starting at the acceptor,
        RefSeq first, then Ensembl."""
        for src in ("refGene", "ensGene"):
            best = None
            for t in self.idx[src].overlapping(chrom, strand, donor - 1, acceptor + 1):
                ends = {e for _, e in t.exons}
                starts = {s for s, _ in t.exons}
                if donor in ends or acceptor in starts:
                    key = (donor in ends and acceptor in starts, t.length, t.name)
                    if best is None or key > best[0]:
                        best = (key, t)
            if best is not None:
                return best[1]
        return None


def build_transcript(model: Transcript, donor: int, acceptor: int, left_exons, right_exons):
    """Exons (genomic order) of the model with the junction's two exons in place."""
    m_ends = {e: (s, e) for s, e in model.exons}
    m_starts = {s: (s, e) for s, e in model.exons}
    if donor in m_ends:
        left = m_ends[donor]
        left_ae = False
    else:
        model_starts = {s for s, _ in model.exons}
        same = [x for x in left_exons if x[0] in model_starts]
        left = max(same) if same else max(left_exons)  # alternative 5'/3' site, else the shortest
        left_ae = True
    if acceptor in m_starts:
        right = m_starts[acceptor]
        right_ae = False
    else:
        model_ends = {e for _, e in model.exons}
        same = [x for x in right_exons if x[1] in model_ends]
        right = min(same, key=lambda x: (x[1], x[0])) if same else min(right_exons, key=lambda x: (x[1], x[0]))
        right_ae = True
    up = [x for x in model.exons if x[1] <= left[0]]
    down = [x for x in model.exons if x[0] >= right[1]]
    return up + [left, right] + down, left_ae, right_ae


def spliced(fasta, chrom, exons, strand):
    seq = "".join(fasta.fetch(chrom, s, e) for s, e in exons).upper()
    return seq if strand == "+" else revcomp(seq)


def first_stop(exons, strand, cds_start_genomic, seq):
    """Transcript position of the start codon and the first in-frame stop, and the junction positions."""
    lengths = [e - s for s, e in exons]
    # transcript coordinates in 5'->3' order
    order = exons if strand == "+" else exons[::-1]
    tpos = None
    acc = 0
    for s, e in order:
        if s <= cds_start_genomic < e:
            tpos = acc + (cds_start_genomic - s if strand == "+" else e - 1 - cds_start_genomic)
            break
        acc += e - s
    if tpos is None:
        return None
    juncs = []
    acc = 0
    for s, e in order[:-1]:
        acc += e - s
        juncs.append(acc)
    stop = None
    for p in range(tpos, len(seq) - 2, 3):
        if seq[p : p + 3] in STOPS:
            stop = p
            break
    return tpos, stop, juncs, sum(lengths)


def genomic_of(exons, strand, tpos):
    order = exons if strand == "+" else exons[::-1]
    acc = 0
    for s, e in order:
        if tpos < acc + (e - s):
            off = tpos - acc
            return s + off if strand == "+" else e - 1 - off
        acc += e - s
    return -1


def detect(fasta, catalog: ExonCatalog, models: ModelIndex, chrom, strand, donor, acceptor) -> PTCResult:
    left_exons = catalog.ending_at(chrom, strand, donor)
    right_exons = catalog.starting_at(chrom, strand, acceptor)
    if not left_exons or not right_exons:
        return PTCResult("unannotated")
    model = models.compatible(chrom, strand, donor, acceptor)
    if model is None:
        return PTCResult("no_model")
    exons, lae, rae = build_transcript(model, donor, acceptor, left_exons, right_exons)
    if any(exons[i][1] > exons[i + 1][0] for i in range(len(exons) - 1)):
        return PTCResult("ambiguous_cds", model.name, left_ae=lae, right_ae=rae)
    return _call(fasta, chrom, strand, exons, model, lae, rae)


def _call(fasta, chrom, strand, exons, model, lae=False, rae=False) -> PTCResult:
    start = model.cds_start if strand == "+" else model.cds_end - 1
    seq = spliced(fasta, chrom, exons, strand)
    r = first_stop(exons, strand, start, seq)
    if r is None:
        return PTCResult("ambiguous_cds", model.name, left_ae=lae, right_ae=rae)
    tpos, stop, juncs, _ = r
    if stop is None:
        return PTCResult("no_ptc", model.name, left_ae=lae, right_ae=rae)
    g = genomic_of(exons, strand, stop)
    codon = seq[stop : stop + 3]
    if not juncs:
        return PTCResult("no_ptc", model.name, g, codon, -1, lae, rae)
    # The paper's "PTC distance" (Additional files 8 and 9) counts from the base after the stop
    # codon's first base: 42 of 45 PTC-upon-exclusion events give the printed distance this way.
    dist = juncs[-1] - (stop + 1)
    status = "ptc" if dist > PTC_DISTANCE else "no_ptc"
    return PTCResult(status, model.name, g, codon, dist, lae, rae)


def model_is_ptc(fasta, model: Transcript) -> bool:
    """Whether a model's own first stop already lies 50 nt or more upstream of its last junction."""
    return _call(fasta, model.chrom, model.strand, model.exons, model).ptc
