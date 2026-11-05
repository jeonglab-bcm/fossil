# PMC4426843 figure reproduction

Figure 1, Tables 1 and 2, and the checks against Supplementary Tables S1, S3 and S5 of Bleazard,
Lamb and Griffiths-Jones (2015), rerun from public data. The authors' script
(sgjlab.org/empirical-go) is gone; the empirical test is rebuilt from the Methods and checked
against the supplement.

## Run

```bash
# From the committed miRanda site tables (minutes, plus about 10 CPU-minutes per empirical null):
nextflow run main.nf --outdir results

# Everything, miRanda included (about 45 CPU hours), on the Skyriver cluster:
sbatch run_skyriver.sbatch --full                  # from this folder; SOURCES=dir reuses downloads

# Resample only some nulls and read the rest from output/empirical (what CI does):
nextflow run main.nf --outdir results --rerun Human:39,Human:1,Mouse:10
```

A `--full` run on Skyriver (Slurm job 1535972: 2 UTR tasks, 91 miRanda tasks, about 40 minutes
each) regenerated `pipeline/inputs/sites_hsa.txt.xz` and `sites_mmu.txt.xz` byte for byte. The
committed outputs come from the run that follows them (job 1536169, all 22 nulls resampled).

Needs Python 3.12 with numpy, scipy, pillow and xlrd; R 4.4 with the Liberation Sans font; and,
for `--full`, miRanda 3.3a (`conda install -c bioconda miranda=3.3a`; the original MSKCC source
archive is gone). `.github/workflows/reproduce-pmc4426843.yml` runs the pipeline on
`ubuntu-24.04` (x86_64) and checks it against `results.json`.

## Steps

| Process | Script | What it does |
| --- | --- | --- |
| FETCH | `fetch_inputs.sh` | miRBase 20 `mature.fa`; Ensembl 75 BioMart GO and gene tables; the supplement (PMC open-access copy). `--full` adds the Ensembl 75 GTFs, toplevel genomes and core assembly tables. All checked against `params/SHA256SUMS`. |
| SUPPLEMENT | `parse_supplement.py` | Supplementary Tables S1–S5 to TSV (the committed copies are in `pipeline/inputs/`). |
| GO | `build_go.py`, `go_universe.py` | Gene → biological-process terms from the BioMart dumps; checks the universe against S1. |
| UTRS (`--full`) | `extract_utrs.py`, `dedup_utrs.py` | The 3′ UTR of every coding transcript; identical sequences collapsed. |
| MIRANDA (`--full`) | `run_miranda.sh` | miRanda 3.3a, default settings, 2,578 human and 1,908 mouse mature miRNAs, 50 per task. |
| SITES | `gene_sites.py`, `sites_codec.py` | Per-UTR totals → gene-level targets and site counts, packed into `pipeline/inputs/sites_*.txt.xz`. |
| TARGETS | `compare_targets.py` | Each list's target genes against S3. |
| AXON_SELECT | `axonogenesis.py` | The S5 positive-control list. |
| EMPIRICAL | `empirical.py` | One null per (species, list size): 999,999 random miRNA sets; per term, the number at or above each list's overlap, for the basic and multi-hit algorithms. |
| TABLE1, TABLE2 | `table1.py`, `table2.py` | Table 1 and S1; empirical P, Benjamini–Hochberg, Table 2; S5. |
| FIGURE1 | `figure1.R`, `compare_figure1.py` | Figure 1 in base R on the published pixel grid, from our null and from the paper's bar heights; pixel comparison. |
| CHECK, PAGE | `check_reproduction.py`, `build_page.py` | `report.md`, `results_table.csv`, and the page copied to `site/PMC4426843/`. |

## What the supplement pinned down

The Methods leave several choices open. The supplementary tables settle each one; the rest of the
pipeline uses what they show.

1. **GO universe.** By gene name ("Associated Gene Name"), direct annotations, all evidence codes:
   15,733 human genes and all 9,462 S1 term sizes equal. Ensembl gene IDs give 17,454 genes and
   7,413 equal sizes.
2. **Table 1's statistic.** S1's caption says "rounded empirical mean". All 9,462 S1 P-values come
   back to 1e-13 with `floor(mean)`: P = Pr(X ≥ floor(m)), X ~ Hypergeometric(15,733, K,
   10,057). Rounding gives 3,716.
3. **miRanda thresholds.** "Score > 155, energy < −20 kcal/mol" filters miRanda's per-UTR totals
   (the `>>` lines: total score and total energy over all sites of a miRNA–UTR pair, sites ≥ 140
   by default), inclusively (≥ 155, ≤ −20). On the six single-miRNA lists:

   | Rule | Arndt (S3: 1,400) | Davidson (744) | Hunter (447) | Yan (961) |
   | --- | --- | --- | --- | --- |
   | Per site, > 155 and < −20 | 397 | 57 | 206 | 37 |
   | Per UTR total, > 155 and < −20 | 1,357 | 734 | 400 | 955 |
   | Per UTR total, ≥ 155 and ≤ −20 | 1,397 | 741 | 445 | 957 |

   Summing totals over a gene's transcripts adds 600–1,400 genes that S3 does not have.
4. **3′ UTRs.** Cut from the Ensembl 75 GTF and genome, they equal BioMart's 3′ UTRs
   (transcript length − `cdna_coding_end`) for all 104,763 coding transcripts. In the toplevel
   FASTA, haplotype and patch sequences hold N where they equal their parent chromosome; the
   bases are copied from the parent through Ensembl's `assembly_exception` table (176 human and 13
   mouse sequences). Before this, HERC2's 14,318-nt UTR on HSCHR15_1_CTG4 was all N.
5. **Empirical P.** S5's P-values are integer multiples of 1/999,999 and include 0: 999,999
   draws, P = count/999,999, no pseudo-count. Its BH flags (`**` q < 0.01, `*` q < 0.05) are
   reproduced exactly by BH over all 9,462 terms.
6. **Overlap denominator.** S5's observed overlaps are k/1,064, but its eight miRNAs target 851
   genes with a biological-process term and 1,049 genes in all (ours). The overlap divides by
   all target genes; our mean random overlaps are 1.016× S5's this way and 1.25× with the
   universe denominator.
7. **S5's eight miRNAs.** The text says they are the eight with the most predicted targets in
   'regulation of axonogenesis'. By count those (hsa-miR-6797-5p, -4739, -608, …, 16–21 term
   genes each) target about 9,200 genes, not 1,064. S5 itself identifies its list: a term with no
   target in S5 rules out every miRNA that targets one of its genes, and exactly eight human
   miRNAs survive (hsa-let-7e-3p, miR-1307-5p, -3181, -4800-3p, -521, -551a, -551b-3p,
   -6726-3p; 1–3 term genes each). Their union matches S5's term counts in 9,394 of 9,462 terms
   and is within one gene in all.
8. **A spreadsheet in the way.** S3 lists MARCH1, MARCH5, MARCH7, SEPT7 and SEP15 (and mouse
   March/Sept genes) as Excel date serials (36951.0 = 1 March 2001). `compare_targets.py` maps
   them back.

## Results

From `output/report.md` (the committed run):

| Item | Status | Evidence |
| --- | --- | --- |
| S3 target genes | Same setup, 99.87% | 155,595 of 155,795 study–gene pairs; none outside S3. Identical lists: Cheng, Keck-Wherley, Schonrock. The 200 missing pairs come from 51 human and 8 mouse genes (ANKRD33 in 15 lists, SIRPG 13, MRPL28 11, …) whose 3′ UTRs here are short; no Ensembl 75 table we found gives longer ones. |
| Table 1 | Identical from S1; same setup from our null | See above. Our null: the paper's 10 terms at ranks 1–10 (8 and 9 swapped); 7 of 10 P-values identical. |
| Fig. 1 | Same setup | Empirical mean 250.57 (paper 250.60); hypergeometric P of the mean 5.97e-07 (paper 5.97e-07). Every empirical bar within 0.001 of the published height (pixel resolution 0.0004). |
| Table 2, basic | Same setup | 28 of 29 zero/non-zero calls; large lists within 0.4%. Collino: 1 significant term against 0. |
| Table 2, multi-hit | Not reproduced at count level | 28 of 29 zero/non-zero calls (Liu: 0 against 1); counts differ by up to 2.5×. |
| S5 | Same setup | 1,552 significant terms (S5 1,580), 1,551 in both. |

### The multi-hit algorithm

"Each gene is assigned a score … based on the total number of predicted binding sites, including
multiple sites for the same miRNA." With several transcripts per gene, the number of sites is not
defined. Four readings were run for the lists of 10, 15, 39 (human) and 10, 27 (mouse) miRNAs
(significant terms, paper / ours):

| Sites per gene | Munch (10) | Chen 2013b (15) | Raponi (15) | Sokolov (39) | Chartoumpekis (mouse, 10) | Liu (mouse, 27) |
| --- | --- | --- | --- | --- | --- | --- |
| Most on one UTR (used) | 22 / 72 | 6 / 5 | 239 / 120 | 337 / 842 | 17 / 17 | 1 / 0 |
| Longest UTR | 22 / 74 | 6 / 5 | 239 / 120 | 337 / 818 | 17 / 17 | 1 / 0 |
| Sum over distinct UTRs | 22 / 47 | 6 / 5 | 239 / 148 | 337 / 650 | 17 / 2 | 1 / 0 |
| Sum over transcripts | 22 / 45 | 6 / 1 | 239 / 160 | 337 / 541 | 17 / 2 | 1 / 0 |
| Most on one UTR, universe denominator | 22 / 63 | 6 / 5 | 239 / 118 | 337 / 930 | 17 / 17 | 1 / 0 |

None fits; the counts move in both directions, so no single choice explains them. The basic
algorithm, which needs only the target sets, reproduces.

## Fitted, not measured

Figure 1 (`pipeline/params/figure1_params.R`), fitted on a render of the bar heights read off the
published figure (`params/published_empirical_bins.tsv`):

- Raster resolution 118 dpi at R's default 12 pt; Liberation Sans in place of Helvetica.
- The y-title centre (row 278, line 2.95) and the legend position (device px 572, −11). The
  published image is cropped on the top and right; the render is drawn on a padded canvas and
  cropped to the published frame.
- Fill colours: the hypergeometric fill as sampled (186, 182, 210); the empirical fill
  (246, 117, 117) at alpha 0.53, which gives the sampled (250, 182, 182) on white and the sampled
  overlap grey. The overlap hue differs: the published colours went through a colour conversion
  that alpha blending does not model.

Measured, not fitted: the axis calibration (tick centres) and the bins (right-closed,
`seq(165, 295, 5)`, from the bar edges and the zero baseline).

The hypergeometric bars are the exact distribution. They agree with the published heights to
0.0009 (2 px); 10⁶ `rhyper` draws would agree as well, so the figure cannot tell the two apart.

## Not reproduced

- **Table 3** (rice): psRNATarget's 2011 server, its default parameters and the agriGO GO tables
  for TIGR OSA1R5 loci are not available; psRNATarget V2 (2017) scores differently.
- **Section 3.3 and S2's other columns**: PITA catalog v6 (404), DIANA-microT-v4 downloads,
  starBase v2's 36 human and 5 mouse CLIP sets, and DAVID 6.7's BP_FAT are gone. KEGG.db 3.2.4
  survives, but the KEGG counts appear only in S2.
- The 3′ UTR length correlation (r = −0.36) and the convergence test of Section 4: text only.

## Randomness

Each null uses NumPy's PCG64 with seed = list size (human) or 1,000 + list size (mouse); the
draws are shared by all lists of one size. Union and site sums are float32 sums of small
integers (exact), and the ≥ comparison is done by cross-multiplication in float64 (exact), so a
rerun on any x86_64 machine gives the same counts. CI checks this on the nulls it resamples.
With 999,999 draws, P-values near the BH threshold move between seeds; the large counts of
Table 2 do not.
