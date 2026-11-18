"""A minimal FASTA reader with the ``fetch(chrom, start, end)`` call PTC detection needs.

Reads a ``.fai`` index (samtools faidx) when one sits next to the file and then reads only the
requested bases; otherwise loads the whole file (fine for small examples). A record named
``chrom:start-end`` (0-based start) holds that stretch of ``chrom``, so a small file can carry the
regions of a few genes at their genome coordinates. pysam.FastaFile works in its place.
"""

from __future__ import annotations

import gzip
from pathlib import Path


class Fasta:
    def __init__(self, path):
        self.path = Path(path)
        fai = Path(str(path) + ".fai")
        self._seqs = None
        self._index = None
        if fai.exists() and self.path.suffix != ".gz":
            self._index = {}
            for line in open(fai):
                name, length, offset, linebases, linewidth = line.split("\t")[:5]
                self._index[name] = (int(length), int(offset), int(linebases), int(linewidth))
            self._fh = open(self.path, "rb")
        else:
            self._seqs = {}
            opener = gzip.open if self.path.suffix == ".gz" else open
            name, parts = None, []
            with opener(self.path, "rt") as f:
                for line in f:
                    if line.startswith(">"):
                        if name is not None:
                            self._seqs[name] = "".join(parts)
                        name, parts = line[1:].split()[0], []
                    else:
                        parts.append(line.strip())
            if name is not None:
                self._seqs[name] = "".join(parts)

        self._regions = {}
        if self._seqs is not None:
            for name in list(self._seqs):
                if ":" in name and "-" in name.rsplit(":", 1)[1]:
                    chrom, rng = name.rsplit(":", 1)
                    a, _b = rng.split("-")
                    self._regions.setdefault(chrom, []).append((int(a), self._seqs.pop(name)))

    @property
    def references(self):
        if self._seqs is not None:
            return list(self._seqs) + list(self._regions)
        return list(self._index)

    def fetch(self, chrom: str, start: int, end: int) -> str:
        if self._seqs is not None:
            if chrom in self._seqs:
                return self._seqs[chrom][max(start, 0) : end]
            for a, seq in self._regions.get(chrom, ()):
                if a <= start and end <= a + len(seq):
                    return seq[start - a : end - a]
            raise KeyError(f"{chrom}:{start}-{end} is not in the FASTA file")
        length, offset, lb, lw = self._index[chrom]
        start, end = max(start, 0), min(end, length)
        if end <= start:
            return ""
        a = offset + (start // lb) * lw + start % lb
        b = offset + (end // lb) * lw + end % lb
        self._fh.seek(a)
        return self._fh.read(b - a).decode().replace("\n", "").replace("\r", "")
