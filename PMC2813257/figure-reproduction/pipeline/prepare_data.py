"""Parse the GenBank records, assign patient and month, codon-align each patient with MUSCLE 3.6.

Usage: prepare_data.py GENBANK CLINICAL MUSCLE OUTDIR [--include-pseudogenes]

Writes OUTDIR/p<N>.fasta (aligned nucleotides, names '<accession>|<month>') and OUTDIR/samples.tsv
(one row per record with patient, month, clone name, kind and whether it was used).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path

from Bio import SeqIO

from hivrecomb.align import codon_align, translate, write_fasta


def visit_months(clinical: str) -> dict[tuple[int, int], int]:
    """(patient, visit) -> months after seroconversion, from LANL's set1_clinical_data.txt."""
    out = {}
    with open(clinical, encoding="latin-1") as f:
        rows = csv.reader(f, delimiter="\t")
        next(rows)
        for r in rows:
            if len(r) > 2 and r[0].startswith("p") and r[1].strip().isdigit():
                out[(int(r[0][1:]), int(r[1]))] = int(r[2])
    return out


def parse_name(name: str, visits) -> tuple[int, int, str]:
    """Clone name -> (patient, months after seroconversion, kind c|p|v)."""
    m = re.match(r"p(\d+)([cp])(-?\d+)-", name)
    if m:
        return int(m.group(1)), int(m.group(3)), m.group(2)
    m = re.match(r"(\d+)v(\d+)px", name)
    if m:
        p, v = int(m.group(1)), int(m.group(2))
        return p, visits[(p, v)], "v"
    raise ValueError(f"cannot parse clone name {name!r}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("genbank")
    ap.add_argument("clinical")
    ap.add_argument("muscle")
    ap.add_argument("outdir")
    ap.add_argument("--include-pseudogenes", action="store_true",
                    help="keep the 8 frameshifted p9 records, translated in frame 1 and trimmed")
    a = ap.parse_args(argv)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    visits = visit_months(a.clinical)
    rows, per_patient = [], {}
    for r in SeqIO.parse(a.genbank, "genbank"):
        if not r.annotations.get("organism", "").startswith("Human immunodeficiency virus 1"):
            continue
        q = r.features[0].qualifiers
        name = (q.get("clone") or q.get("isolate"))[0]
        patient, month, kind = parse_name(name, visits)
        cds = [f for f in r.features if f.type == "CDS"]
        start = int(cds[0].qualifiers.get("codon_start", ["1"])[0]) - 1 if cds else 0
        nt = str(r.seq).upper()[start:]
        nt = nt[: len(nt) - len(nt) % 3]
        pseudo = not cds
        used = (not pseudo) or a.include_pseudogenes
        if used and "*" in translate(nt) and not pseudo:
            raise ValueError(f"stop codon in {r.id}")
        rows.append(dict(accession=r.id, clone=name, patient=patient, month=month, kind=kind,
                         codon_start=start + 1, pseudogene=int(pseudo), used=int(used)))
        if used:
            per_patient.setdefault(patient, {})[f"{r.id}|{month}"] = nt
    # A digest of the parsed input: the HIV-1 records that the analysis uses, in a canonical
    # order. E-utilities does not return the records in a fixed order and GenBank adds
    # unrelated records to the accession ranges, so the file itself has no stable checksum.
    digest = hashlib.sha256()
    for key in sorted(f"{r['accession']}\t{r['patient']}\t{r['month']}" for r in rows):
        digest.update(key.encode() + b"\n")
    for patient in sorted(per_patient):
        for name in sorted(per_patient[patient]):
            digest.update(per_patient[patient][name].encode() + b"\n")
    (out / "input_digest.txt").write_text(digest.hexdigest() + "\n")

    with open(out / "samples.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    for p in sorted(per_patient):
        # MUSCLE's progressive alignment depends on the input order, and E-utilities does not
        # return the records in a fixed order: sort by accession so a rerun aligns the same way.
        ordered = {k: per_patient[p][k] for k in sorted(per_patient[p])}
        aln = codon_align(ordered, muscle=a.muscle)
        write_fasta(aln, out / f"p{p}.fasta")
        print(f"p{p}: {len(aln)} sequences, {len(next(iter(aln.values())))} columns", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
