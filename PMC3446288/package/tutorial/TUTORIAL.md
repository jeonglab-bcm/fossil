<!-- Generated from tutorial.ipynb by check_package.py --write. Do not edit by hand. -->

# nmdsplice tutorial

`nmdsplice` rebuilds RAINMAN, the lost pipeline of Weischenfeldt et al. (2012), which measured how the loss of nonsense-mediated mRNA decay (NMD) changes splicing in mouse liver and macrophages. For each exon-exon junction it builds the transcript the junction implies, translates it from the annotated start codon and calls a premature termination codon (PTC) when the first stop lies more than 49 nt upstream of the last exon-exon junction (the 50-nucleotide rule). It also builds the combinatorial junction database, computes TMM factors as edgeR does, and infers seven splice classes with PSI.

Citation: Weischenfeldt J, Waage J, Tian G, et al. Mammalian tissues defective in nonsense-mediated mRNA decay display highly aberrant splicing patterns. *Genome Biology* 13(5):R35 (2012). doi:10.1186/gb-2012-13-5-r35

## 1. Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3446288/package"
```

It needs Python 3.10 or later and NumPy.

```python
import nmdsplice as nm

print("nmdsplice", nm.__version__)
```

```text
nmdsplice 0.1.0
```

## 2. The example input

Twelve junctions of PTC events from the paper's Additional files 8 and 9, the UCSC mm9 annotation rows of their genes and the mm9 sequence of those regions. `data/README.md` says where each file comes from.

```python
junctions = nm.read_junctions(nm.example_path("example_junctions.tsv"))
annotation = nm.load_annotation(nm.example_path("example_annotation"))
print(len(junctions), "junctions;", {k: len(v) for k, v in annotation.items()}, "annotation rows")
for j in junctions[:4]:
    print(j)
```

```text
12 junctions; {'refGene': 44, 'knownGene': 39, 'ensGene': 105, 'genscan': 5, 'exoniphy': 108} annotation rows
{'gene': '2410004B18Rik', 'chrom': 'chr3', 'strand': '+', 'donor': 145601292, 'acceptor': 145601506}
{'gene': 'Dnajc5', 'chrom': 'chr2', 'strand': '+', 'donor': 181283546, 'acceptor': 181283630}
{'gene': 'Hnrnpl', 'chrom': 'chr7', 'strand': '+', 'donor': 29600371, 'acceptor': 29602353}
{'gene': 'Acot8', 'chrom': 'chr2', 'strand': '-', 'donor': 164625445, 'acceptor': 164630189}
```

## 3. Run the method

`ptc_table` picks the longest compatible coding model (RefSeq first, then Ensembl), puts the junction's two exons in it, translates from the annotated start and reports the first stop.

```python
rows = nm.ptc_table(junctions, annotation, nm.example_path("example_genome.fa"))
print(f"{'gene':<15}{'status':<8}{'model':<15}{'stop':>6}{'PTC distance':>14}")
for r in rows:
    print(f"{r['gene']:<15}{r['status']:<8}{r['model']:<15}{r['stop_codon']:>6}{r['ptc_distance']:>14}")
```

```text
gene           status  model            stop  PTC distance
2410004B18Rik  ptc     NM_001356284      TGA           301
Dnajc5         ptc     NM_001271585      TGA            66
Hnrnpl         ptc     NM_177301         TGA           844
Acot8          ptc     NM_133240         TGA           367
Clk1           ptc     NM_001042634      TAG           811
Dpp7           ptc     NM_031843         TGA           266
Fus            ptc     NM_139149         TGA           713
Hnrnph1        ptc     NM_001362523      TGA           658
Mgea5          ptc     NM_023799         TGA           529
Psmg2          ptc     NM_001368147      TGA           393
Snrpa1         ptc     NM_021336         TAA           166
Vps29          ptc     NM_001347453      TGA           255
```

## 4. Compare with the expected output

The expected output is the PTC distance the paper prints for each event, computed by the authors' pipeline, not by this package.

```python
import csv

with open(nm.example_path("example_expected.tsv")) as f:
    expected = {(r["chrom"], int(r["donor"]), int(r["acceptor"])): int(r["ptc_distance"])
                for r in csv.DictReader(f, delimiter="\t")}
matches = sum(r["ptc"] and r["ptc_distance"] == expected[(r["chrom"], r["donor"], r["acceptor"])] for r in rows)
print(f"{matches} of {len(rows)} junctions give the paper's PTC distance")
assert matches == len(rows)
```

```text
12 of 12 junctions give the paper's PTC distance
```

## 5. From the command line

The same run as `nmdsplice ptc`. Without `-o` it writes the table to standard output.

```python
folder = nm.example_path("example_annotation").parent
!nmdsplice ptc "{folder}/example_junctions.tsv" --annotation "{folder}/example_annotation" --genome "{folder}/example_genome.fa" | cut -f1,6,12
```

```text
gene	status
2410004B18Rik	ptc
Dnajc5	ptc
Hnrnpl	ptc
Acot8	ptc
Clk1	ptc
Dpp7	ptc
Fus	ptc
Hnrnph1	ptc
Mgea5	ptc
Psmg2	ptc
Snrpa1	ptc
Vps29	ptc
```

## 6. Your own data

- **Junctions:** a TSV with columns `chrom`, `strand`, `donor` and `acceptor` in UCSC coordinates (donor = end of the upstream exon in genome order, acceptor = start of the downstream exon, both 0-based). Other columns are carried through.
- **Annotation:** a folder with UCSC tables named `refGene.txt.gz`, `ensGene.txt.gz`, `knownGene.txt.gz`, `genscan.txt.gz` and `exoniphy.txt.gz` for your assembly (refGene is required). A junction whose exons are in none of them is `unannotated`.
- **Genome:** a FASTA file; with a `.fai` index next to it only the needed bases are read.
- **Output columns:** `status` (`ptc`, `no_ptc`, `unannotated`, `ambiguous_cds` when the transcript loses the annotated start, `no_model` when no coding RefSeq or Ensembl model shares an exon with the junction), `model`, `stop_codon`, `stop` (genomic position of its first base) and `ptc_distance` (nt from the stop to the last exon-exon junction, as the paper prints it).
- **Other parts of the method:** `nm.combinatorial_junctions` and `nm.write_fasta` build the junction database, `nm.tmm_factors` gives edgeR's TMM factors, and `nm.infer_events` finds SES, MES, A5SS, A3SS, AFE, ALE and MXE events with PSI and dPSI.

## 7. The reproduction

The whole paper rerun with this package, from the SRA reads: results page <https://jeonglab-bcm.github.io/fossil/PMC3446288/>, pipeline `PMC3446288/figure-reproduction/` in <https://github.com/jeonglab-bcm/fossil>.
