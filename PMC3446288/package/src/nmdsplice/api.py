"""High-level calls used by the command line and the tutorial."""

from __future__ import annotations

import csv
from pathlib import Path

from .annotation import read_genepred
from .fasta import Fasta
from .ptc import ExonCatalog, ModelIndex, detect

SOURCES = ("refGene", "knownGene", "ensGene", "genscan", "exoniphy")


def load_annotation(annot_dir) -> dict:
    """Read the UCSC tables (refGene, knownGene, ensGene, genscan, exoniphy) found in a folder."""
    out = {}
    for s in SOURCES:
        for name in (f"{s}.txt.gz", f"{s}.txt"):
            p = Path(annot_dir) / name
            if p.exists():
                out[s] = read_genepred(p, s)
                break
        else:
            out[s] = []
    if not out["refGene"]:
        raise FileNotFoundError(f"no refGene.txt(.gz) in {annot_dir}")
    return out


def read_junctions(path) -> list[dict]:
    """Junctions from a TSV with columns chrom, strand, donor, acceptor (others are kept)."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    for col in ("chrom", "strand", "donor", "acceptor"):
        if rows and col not in rows[0]:
            raise ValueError(f"junction file lacks column {col!r}")
    for r in rows:
        r["donor"], r["acceptor"] = int(r["donor"]), int(r["acceptor"])
        if r["strand"] not in "+-" or r["acceptor"] <= r["donor"]:
            raise ValueError(f"bad junction {r}")
    return rows


def ptc_table(junctions: list[dict], annotation: dict, genome) -> list[dict]:
    """PTC call of each junction: status, model, stop codon, its genomic position and PTC distance."""
    if isinstance(genome, (str, Path)):
        genome = Fasta(genome)
    cat = ExonCatalog(annotation)
    models = ModelIndex(annotation["refGene"], annotation["ensGene"])
    out = []
    for j in junctions:
        p = detect(genome, cat, models, j["chrom"], j["strand"], j["donor"], j["acceptor"])
        row = dict(j)
        row.update(status=p.status, ptc=p.ptc, model=p.model, stop_codon=p.stop_codon,
                   stop=p.stop_genomic, ptc_distance=p.distance)
        out.append(row)
    return out


def write_table(rows: list[dict], fh) -> None:
    if not rows:
        return
    w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (int(v) if isinstance(v, bool) else v) for k, v in r.items()})
