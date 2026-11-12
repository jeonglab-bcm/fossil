"""Codon alignment: translate, align the proteins with MUSCLE, put the codons back.

Neher and Leitner (2010), Methods: "The sequences were translated into amino acid sequences and
aligned for each patient separately using MUSCLE v3.6 with default settings. Aligned nucleotide
sequences were then constructed by inserting a 3bp gap for each gap in the amino acid alignment."
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

CODON_TABLE = {
    a + b + c: aa
    for (a, b, c), aa in zip(
        ((x, y, z) for x in "TCAG" for y in "TCAG" for z in "TCAG"),
        "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG",
    )
}


def translate(nt: str) -> str:
    """Translate an in-frame nucleotide string (gaps not allowed). Unknown codons give X."""
    nt = nt.upper()
    return "".join(CODON_TABLE.get(nt[i : i + 3], "X") for i in range(0, len(nt) - len(nt) % 3, 3))


def back_translate(aligned_aa: str, nt: str) -> str:
    """Nucleotide alignment row from an aligned protein row and the in-frame nucleotides."""
    out, k = [], 0
    for ch in aligned_aa:
        if ch == "-":
            out.append("---")
        else:
            out.append(nt[k : k + 3].upper())
            k += 3
    if k != len(nt) - len(nt) % 3:
        raise ValueError("aligned protein does not match the nucleotide sequence")
    return "".join(out)


def read_fasta(path: str | os.PathLike) -> dict[str, str]:
    seqs: dict[str, list[str]] = {}
    name = None
    with open(path, encoding="ascii") as f:
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                name = line[1:].split()[0]
                seqs[name] = []
            elif name is not None:
                seqs[name].append(line)
    return {k: "".join(v) for k, v in seqs.items()}


def write_fasta(seqs: dict[str, str], path: str | os.PathLike) -> None:
    with open(path, "w", encoding="ascii") as f:
        for k, v in seqs.items():
            f.write(f">{k}\n")
            for i in range(0, len(v), 60):
                f.write(v[i : i + 60] + "\n")


def codon_align(seqs: dict[str, str], muscle: str = "muscle", workdir: str | None = None) -> dict[str, str]:
    """Align in-frame nucleotide sequences through their translations.

    ``seqs`` maps a name to an in-frame nucleotide sequence (length a multiple of 3, no stop codons
    expected). ``muscle`` is the MUSCLE executable (the paper used v3.6, default settings). Returns
    the nucleotide alignment in the input order.
    """
    if not seqs:
        raise ValueError("no sequences to align")
    aa = {k: translate(v) for k, v in seqs.items()}
    with tempfile.TemporaryDirectory(dir=workdir) as tmp:
        fin, fout = Path(tmp) / "in.fasta", Path(tmp) / "out.fasta"
        write_fasta(aa, fin)
        subprocess.run([muscle, "-in", str(fin), "-out", str(fout), "-quiet"], check=True)
        aligned = read_fasta(fout)
    return {k: back_translate(aligned[k], seqs[k]) for k in seqs}
