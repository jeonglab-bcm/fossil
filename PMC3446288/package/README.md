# nmdsplice

RAINMAN rebuilt: the junction-level method of Weischenfeldt et al. (2012) as a Python package.

- Combinatorial exon-exon junction database from UCSC Known Genes, Ensembl, RefSeq, GENSCAN and Exoniphy exons.
- PTC detection by the 50-nucleotide rule, with the paper's PTC distance.
- TMM normalisation factors as edgeR computes them; upper-quartile gene RPKM; junction fold changes.
- Seven splice classes (SES, MES, A5SS, A3SS, AFE, ALE, MXE) with PSI and dPSI.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3446288/package"
```

## Quick start

```python
import nmdsplice as nm

rows = nm.ptc_table(nm.read_junctions(nm.example_path("example_junctions.tsv")),
                    nm.load_annotation(nm.example_path("example_annotation")),
                    nm.example_path("example_genome.fa"))
```

```bash
nmdsplice ptc junctions.tsv --annotation ucsc_mm9/ --genome mm9.fa -o ptc.tsv
nmdsplice tmm counts.tsv
```

Tutorial: [tutorial/TUTORIAL.md](tutorial/TUTORIAL.md).

## Why Python

The authors' RAINMAN was a set of Python and R scripts, and it is lost. The method is junction
bookkeeping, sequence translation and counting; its only R dependency was edgeR's TMM, which this
package implements and the reproduction checks against edgeR 4.4.0 on the paper's junction counts.
By the default rule (R only when the method relies on R or Bioconductor packages), the package is Python.

## What it is checked against

The package was written from the paper's text and Additional file 1; it contains no authors' code.
The reproduction (`PMC3446288/figure-reproduction/`) checks it against the paper: it gives the PTC
distance printed in Additional files 8 and 9 for 42 of 45 PTC-upon-exclusion events, and its TMM
factors equal edgeR's.

## Citation

Weischenfeldt J, Waage J, Tian G, Zhao J, Damgaard I, Jakobsen JS, Kristiansen K, Krogh A, Wang J,
Porse BT. Mammalian tissues defective in nonsense-mediated mRNA decay display highly aberrant splicing
patterns. *Genome Biology* 13(5):R35 (2012). doi:10.1186/gb-2012-13-5-r35

## Licence

MIT (the fossil repository's licence). The example data are from the paper (CC BY 2.0) and UCSC.
