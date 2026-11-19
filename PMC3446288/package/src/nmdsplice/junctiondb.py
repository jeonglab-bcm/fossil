"""The combinatorial exon-exon junction database.

Additional file 1: exons from UCSC Known Genes, Ensembl, RefSeq, GENSCAN and Exoniphy are
"combined in all possible combinations within each RefSeq gene-model, with a read/exon overlap
requirement of 4 bp on each side of the junction". Here every exon end (donor) is joined to every
exon start (acceptor) downstream of it inside the same RefSeq gene and on its strand. Each junction
sequence is the last ``flank`` bases of the upstream exon and the first ``flank`` bases of the
downstream one (shorter when the exon is shorter), with ``flank = read length - overhang``.
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from dataclasses import dataclass

from .annotation import Gene, Transcript, exons_within

OVERHANG = 4


@dataclass(frozen=True)
class Junction:
    chrom: str
    donor: int  # end of the upstream exon (0-based, exclusive) = last exonic base, 1-based
    acceptor: int  # start of the downstream exon (0-based)

    @property
    def id(self) -> str:
        return f"{self.chrom}:{self.donor}-{self.acceptor}"

    @classmethod
    def parse(cls, text: str) -> "Junction":
        chrom, rest = text.rsplit(":", 1)
        d, a = rest.split("-")
        return cls(chrom, int(d), int(a))


def combinatorial_junctions(
    genes: list[Gene], sets: dict[str, list[Transcript]], min_intron: int = 1
) -> dict[Junction, dict]:
    """All donor-acceptor pairs inside each RefSeq gene.

    Returns, for each junction, the gene keys it belongs to, the longest upstream exon length that
    ends at the donor and the longest downstream exon length that starts at the acceptor.
    """
    ex = exons_within(genes, sets)
    out: dict[Junction, dict] = {}
    for g in genes:
        es = ex[g.key]
        up = defaultdict(int)  # donor -> longest exon ending there
        down = defaultdict(int)  # acceptor -> longest exon starting there
        for s, e in es:
            up[e] = max(up[e], e - s)
            down[s] = max(down[s], e - s)
        acc = sorted(down)
        for d in sorted(up):
            for a in acc[bisect.bisect_left(acc, d + min_intron):]:
                j = Junction(g.chrom, d, a)
                rec = out.get(j)
                if rec is None:
                    out[j] = {"genes": [g.key], "up": up[d], "down": down[a]}
                else:
                    rec["genes"].append(g.key)
                    rec["up"] = max(rec["up"], up[d])
                    rec["down"] = max(rec["down"], down[a])
    return out


def junction_sequence(fasta, j: Junction, up: int, down: int, flank: int) -> tuple[str, int]:
    """Sequence of a junction (forward strand) and the length of its left part."""
    left = min(flank, up)
    right = min(flank, down)
    seq = fasta.fetch(j.chrom, j.donor - left, j.donor) + fasta.fetch(j.chrom, j.acceptor, j.acceptor + right)
    return seq.upper(), left


def write_fasta(junctions: dict[Junction, dict], fasta, out, flank: int = 71) -> int:
    """Write the database as FASTA. Names are ``chrom:donor-acceptor:left``. Returns the count."""
    n = 0
    for j in sorted(junctions, key=lambda j: (j.chrom, j.donor, j.acceptor)):
        rec = junctions[j]
        seq, left = junction_sequence(fasta, j, rec["up"], rec["down"], flank)
        if left < OVERHANG or len(seq) - left < OVERHANG:
            continue
        out.write(f">{j.id}:{left}\n{seq}\n")
        n += 1
    return n


def spans_junction(left: int, offset: int, length: int, overhang: int = OVERHANG) -> bool:
    """Whether a read aligned at ``offset`` (0-based) of a junction sequence covers
    at least ``overhang`` bases on each side of the junction point ``left``."""
    return offset <= left - overhang and offset + length >= left + overhang
