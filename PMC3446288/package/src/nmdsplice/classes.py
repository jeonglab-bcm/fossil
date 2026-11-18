"""Splice isoform classes, PSI and dPSI (Additional file 1, "Splice isoform inference").

Seven classes from junction evidence alone: single and multiple exon skipping (SES, MES), alternative
5' and 3' splice sites (A5SS, A3SS), alternative first and last exons (AFE, ALE) and mutually
exclusive exons (MXE). PSI is the share of reads supporting one form; dPSI = PSI_KO - PSI_WT; an event
is regulated when |dPSI| > 0.2. Class names follow the transcript strand.

The paper's PSI formulas are equation objects that do not survive conversion; we read them as
proportions: SES inclusion = mean reads of the two inclusion junctions, PSI = inclusion /
(inclusion + skipping); MES inclusion = mean over the n skipped junctions; for two alternative
junctions PSI = r_tested / (r_tested + r_alternative).
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from dataclasses import dataclass, field

DPSI = 0.2


@dataclass
class Event:
    cls: str  # SES, MES, A5SS, A3SS, AFE, ALE, MXE
    chrom: str
    strand: str
    gene: str
    # SES/MES: skipping junction first, then the inclusion junctions; pairs: the two junctions
    junctions: tuple
    psi_wt: float
    psi_ko: float
    reads_wt: tuple = ()
    reads_ko: tuple = ()
    ptc_up: bool = False  # the form that goes up in KO carries a PTC
    direction: str = ""  # inclusion / exclusion for ES; up form for pairs
    ptc_mode: str = ""  # "exclusion", "inclusion" or "" (ES only)
    extra: dict = field(default_factory=dict)

    @property
    def dpsi(self) -> float:
        return self.psi_ko - self.psi_wt

    @property
    def regulated(self) -> bool:
        return abs(self.dpsi) > DPSI


def _psi(a, b):
    return a / (a + b) if a + b > 0 else None


def infer_events(junctions: dict, exons, first_exons, last_exons, ptc: dict, gene_of: dict, strand_of: dict,
                 max_skip: int = 8) -> list[Event]:
    """Find events among evident junctions.

    junctions: {(chrom, donor, acceptor): (wt_reads, ko_reads)} for the evident junctions of a tissue.
    exons: set of (chrom, strand, start, end) repository exons.
    first_exons / last_exons: sets of (chrom, strand, start, end) annotated first / last exons.
    ptc: {(chrom, donor, acceptor): bool}.
    gene_of / strand_of: junction -> gene key / strand.
    """
    by_chrom = defaultdict(list)
    for j in junctions:
        by_chrom[(j[0], strand_of[j])].append(j)
    ex_by_start = defaultdict(list)
    ex_by_end = defaultdict(list)
    for c, s, a, b in exons:
        ex_by_start[(c, s, a)].append(b)
        ex_by_end[(c, s, b)].append(a)
    exons_by_cs = defaultdict(set)
    for c, st, s0, e0 in exons:
        exons_by_cs[(c, st)].add((s0, e0))
    events: list[Event] = []
    seen = set()
    for (chrom, strand), js in by_chrom.items():
        jset = set(js)
        out_of = defaultdict(list)  # donor -> acceptors
        into = defaultdict(list)  # acceptor -> donors
        for _, d, a in js:
            out_of[d].append(a)
            into[a].append(d)
        starts_sorted = sorted(exons_by_cs[(chrom, strand)])

        def r(j):
            return junctions[j]

        # --- exon skipping
        for j in js:
            _, d, a = j
            paths = []

            def walk(pos, path, depth):
                if depth > max_skip:
                    return
                for x in out_of.get(pos, ()):
                    if x >= a:
                        continue
                    for y in ex_by_start.get((chrom, strand, x), ()):
                        if y >= a:
                            continue
                        if y in out_of:
                            if (chrom, y, a) in jset:
                                paths.append(path + [(x, y)])
                            walk(y, path + [(x, y)], depth + 1)

            walk(d, [], 1)
            if not paths:
                continue
            uniq = sorted({tuple(p) for p in paths})
            if len(uniq) == 1 and len(uniq[0]) == 1:
                cls = "SES"
                path = list(uniq[0])
            else:
                cls = "MES"
                multi = [p for p in uniq if len(p) >= 2] or uniq
                path = list(max(multi, key=lambda p: min(sum(r(k)) for k in _path_juncs(chrom, d, a, p))))
                if len(path) < 2:
                    continue
            inc = _path_juncs(chrom, d, a, path)
            wi = sum(r(k)[0] for k in inc) / len(inc)
            ki = sum(r(k)[1] for k in inc) / len(inc)
            pw, pk = _psi(wi, r(j)[0]), _psi(ki, r(j)[1])
            if pw is None or pk is None:
                continue
            key = (cls, j, tuple(inc))
            if key in seen:
                continue
            seen.add(key)
            ev = Event(cls, chrom, strand, gene_of.get(j, ""), (j, *inc), pw, pk,
                       (r(j)[0], *[r(k)[0] for k in inc]), (r(j)[1], *[r(k)[1] for k in inc]))
            if ev.dpsi < 0:
                ev.direction = "exclusion"
                ev.ptc_up = bool(ptc.get(j))
                ev.ptc_mode = "exclusion" if ev.ptc_up else ""
            else:
                ev.direction = "inclusion"
                ev.ptc_up = any(ptc.get(k) for k in inc) and not ptc.get(j)
                ev.ptc_mode = "inclusion" if ev.ptc_up else ""
            ev.extra["exons"] = path
            events.append(ev)

        # --- pairs sharing one edge: A5SS/A3SS, AFE/ALE, MXE
        for a, donors in into.items():
            ds = sorted(set(donors))
            for i in range(len(ds)):
                for k in range(i + 1, len(ds)):
                    d1, d2 = ds[i], ds[k]
                    st1 = set(ex_by_end.get((chrom, strand, d1), ()))
                    st2 = set(ex_by_end.get((chrom, strand, d2), ()))
                    ex1 = {(x, d1) for x in st1}
                    ex2 = {(x, d2) for x in st2}
                    j1, j2 = (chrom, d1, a), (chrom, d2, a)
                    if st1 & st2:  # same exon start, alternative end: alternative splice site
                        cls = "A5SS" if strand == "+" else "A3SS"
                    elif strand == "+" and _first_or_last(chrom, strand, d1, d2, ex1, ex2, first_exons, into, True):
                        cls = "AFE"
                    elif strand == "-" and _first_or_last(chrom, strand, d1, d2, ex1, ex2, last_exons, into, True):
                        cls = "ALE"
                    else:
                        continue
                    events.append(_pair(cls, chrom, strand, j1, j2, junctions, ptc, gene_of))
        for d, accs in out_of.items():
            as_ = sorted(set(accs))
            for i in range(len(as_)):
                for k in range(i + 1, len(as_)):
                    a1, a2 = as_[i], as_[k]
                    en1 = set(ex_by_start.get((chrom, strand, a1), ()))
                    en2 = set(ex_by_start.get((chrom, strand, a2), ()))
                    ex1 = {(a1, y) for y in en1}
                    ex2 = {(a2, y) for y in en2}
                    j1, j2 = (chrom, d, a1), (chrom, d, a2)
                    if en1 & en2:
                        cls = "A3SS" if strand == "+" else "A5SS"
                    elif strand == "+" and _first_or_last(chrom, strand, a1, a2, ex1, ex2, last_exons, out_of, False):
                        cls = "ALE"
                    elif strand == "-" and _first_or_last(chrom, strand, a1, a2, ex1, ex2, first_exons, out_of, False):
                        cls = "AFE"
                    else:
                        mx = _mxe(chrom, strand, d, a1, a2, ex_by_start, out_of, jset, starts_sorted)
                        if mx is None:
                            continue
                        e1, e2, b = mx
                        ev = _pair("MXE", chrom, strand, j1, j2, junctions, ptc, gene_of)
                        up = (j1, (chrom, e1, b)) if ev.dpsi > 0 else (j2, (chrom, e2, b))
                        ev.ptc_up = any(ptc.get(x) for x in up)
                        ev.extra["exons"] = [(a1, e1), (a2, e2)]
                        events.append(ev)
                        continue
                    events.append(_pair(cls, chrom, strand, j1, j2, junctions, ptc, gene_of))
    return [e for e in events if e is not None]


def _path_juncs(chrom, d, a, path):
    pts = [d] + [p for x, y in path for p in (x, y)] + [a]
    return [(chrom, pts[i], pts[i + 1]) for i in range(0, len(pts), 2)]


def _first_or_last(chrom, strand, p1, p2, ex1, ex2, terminal, links, donors_side):
    """Alternative terminal exons: one junction's exon is annotated terminal, the other exon differs
    in its outer coordinate, and no junction reaches the outer side of either exon."""
    term1 = {x for x in ex1 if (chrom, strand, *x) in terminal}
    term2 = {x for x in ex2 if (chrom, strand, *x) in terminal}
    if not (term1 or term2):
        return False
    outer = 0 if donors_side else 1  # start of an upstream exon, end of a downstream one
    o1 = {x[outer] for x in (term1 or ex1)}
    o2 = {x[outer] for x in (term2 or ex2)}
    if o1 & o2:
        return False
    # no junction reaches the outer edge of either exon
    return not any(o in links for o in o1 | o2)


def _mxe(chrom, strand, d, a1, a2, ex_by_start, out_of, jset, starts_sorted):
    e1s = ex_by_start.get((chrom, strand, a1), ())
    e2s = ex_by_start.get((chrom, strand, a2), ())
    for e1 in sorted(e1s):
        if e1 >= a2:
            continue
        if (chrom, e1, a2) in jset:  # both exons included together
            continue
        for e2 in sorted(e2s):
            common = set(out_of.get(e1, ())) & set(out_of.get(e2, ()))
            common = {b for b in common if b > e2}
            if not common:
                continue
            k0 = bisect.bisect_right(starts_sorted, (e1, 1 << 40))
            if any(x[1] < a2 for x in starts_sorted[k0 : bisect.bisect_left(starts_sorted, (a2, 0))]):
                continue
            return e1, e2, min(common)
    return None


def _pair(cls, chrom, strand, j1, j2, junctions, ptc, gene_of):
    w1, k1 = junctions[j1]
    w2, k2 = junctions[j2]
    pw, pk = _psi(w1, w2), _psi(k1, k2)
    if pw is None or pk is None:
        return None
    ev = Event(cls, chrom, strand, gene_of.get(j1, ""), (j1, j2), pw, pk, (w1, w2), (k1, k2))
    up = j1 if ev.dpsi > 0 else j2
    ev.direction = "first" if ev.dpsi > 0 else "second"
    ev.ptc_up = bool(ptc.get(up)) and cls != "ALE"
    return ev
