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

# Table 2's multi-hit column under six readings of the method (132 nulls on Slurm; needs the
# UTR maps and miRanda pair files of a --full run, see the script):
bash run_multihit_readings.sh WORK
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
| Table 2, multi-hit | Not reproduced at count level | 28 of 29 zero/non-zero calls (Liu: 0 against 1); counts differ by up to 3.3× (Munch 72 against 22), in both directions. Six readings of the method and a second seed do not close the gap (below). |
| S5 | Same setup | 1,552 significant terms (S5 1,580), 1,551 in both. |

### What the multi-hit test is for

Both algorithms compare a published miRNA list with 999,999 random lists of the same size, so
both correct the targeting bias that is the paper's subject. They differ in what they count:

- **Basic.** A list's targets are the union of its miRNAs' predicted target genes. A term's
  overlap is the fraction of those genes that carry the term. A gene counts once, whether one
  miRNA of the list targets it with one site or ten miRNAs target it with thirty.
- **Multi-hit** (Section 3.4). Each gene gets a score: its predicted binding sites summed over
  the list's miRNAs, repeated sites of one miRNA included. A term's overlap is the summed score
  of its genes divided by the summed score of all target genes.

The basic test throws away convergence: several miRNAs of a list hitting the same genes, which
the paper (citing Gusev 2008 and Lee et al. 2012) calls key information. The multi-hit test is
not a second bias correction; it keeps the empirical correction and puts that information back,
to show that the corrected test can still find biology. The paper reports two things from it:
every list with enriched terms under the basic test also has them under multi-hit, with fewer
terms; and six lists with none under the basic test have some under multi-hit. Our run gives
both for the paper's lists: its five basic-positive lists are multi-hit positive with fewer
terms, and five of its six lists gain terms (Liu does not: 0 against 1). Collino, positive only in
our basic run (one term), has no multi-hit term.

**How much rests on it.** Little. The main claim, that the hypergeometric test flags terms
random miRNAs hit just as often and that after correction 5 of 22 human and 0 of 7 mouse lists
have an enriched term, stands on the basic test, Figure 1, Table 1 and S1, all of which
reproduce. The multi-hit counts enter no conclusion; only the qualitative pattern above does.

### Why the multi-hit counts differ

The paper's multi-hit counts are not reproduced, and no reading of the Methods we tried
reproduces them. Everything feeding the basic column is shared with the multi-hit column and
agrees: the target genes of every list with a gap are 99.8–99.9% of S3's, and the basic counts of
the large lists are within 0.4%. What only the multi-hit column uses:

1. **Site counts per miRNA and gene** (`gene_sites.py`, `pipeline/inputs/sites_*.txt.xz`). The
   paper says "the total number of predicted binding sites" but not over which of a gene's
   transcripts, nor whether sites on pairs failing the score and energy thresholds count. No
   supplementary table records site counts, so this cannot be checked against the paper.
2. **The weighting** (`empirical.py`: `sc = ST @ XT`, `w = go @ sc`): gene score = summed sites,
   term score = summed member scores. The text defines this directly.
3. **The denominator** (`multi_total`): "divided by total score for input miRNAs". We divide by
   the score of all target genes, as S5 shows for the basic overlap; the GO-gene-only version was
   tried too.
4. **The significance cut** (`table2.py`): BH at 0.05 over all terms, the rule that reproduces S5.

`run_multihit_readings.sh` reruns every null under six readings, each changing one thing against
Table 2's reference (most sites on any one of the gene's UTRs). Significant terms, all lists with
a non-zero count anywhere (`output/multihit_readings.csv`):

| List (miRNAs) | Paper | Reference | Other seed | Longest UTR | Sum, UTRs | Sum, transcripts | GO-gene denominator | All pairs | Reference at FDR 0.025 / 0.1 | FDR giving the paper's count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Chen (176) | 1,193 | 1,300 | 1,304 | 1,290 | 1,347 | 1,420 | 1,170 | 1,824 | 1,013 / 1,676 | 0.039 |
| Romero-Cordoba (130) | 206 | 266 | 267 | 289 | 230 | 255 | 217 | 372 | 141 / 502 | 0.039 |
| Tanic (46) | 317 | 526 | 524 | 528 | 489 | 523 | 448 | 636 | 320 / 746 | 0.024 |
| Sokolov (39) | 337 | 842 | 840 | 818 | 650 | 541 | 930 | 1,640 | 639 / 1,121 | 0.0028 |
| Sanchez-Diaz (26) | 28 | 31 | 32 | 32 | 24 | 27 | 13 | 28 | 5 / 126 | 0.049 |
| Wu (25) | 138 | 192 | 193 | 182 | 156 | 170 | 152 | 208 | 102 / 379 | 0.037 |
| Chen 2013b (15) | 6 | 5 | 5 | 5 | 5 | 1 | 5 | 4 | 5 / 11 | 0.057 |
| Raponi (15) | 239 | 120 | 116 | 120 | 148 | 160 | 118 | 244 | 71 / 206 | 0.12 |
| Collino (11) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 0 / 1 | |
| Munch (10) | 22 | 72 | 72 | 74 | 47 | 45 | 63 | 65 | 48 / 141 | 0.0076 |
| Presneau (5) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 26 | 0 / 12 | |
| Chartoumpekis (mouse, 10) | 17 | 17 | 3 | 17 | 2 | 2 | 17 | 0 | 2 / 68 | 0.050 |
| Liu (mouse, 27) | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 | 0.23 |

The other 16 lists have no significant multi-hit term under any reading, as in the paper.
`output/multihit_terms.tsv.gz` lists, per list, every term significant under any reading.

What the table shows:

- **No consistent direction.** Seven lists are too high under the reference, three too low
  (Raponi, Chen 2013b, Liu), and Chartoumpekis matches. Every reading moves some lists toward the
  paper and others away. Counting sites on all miRanda pairs gives Raponi 244 (paper 239) and
  Sanchez-Diaz 28 (28) but doubles Sokolov and Chen and makes Collino and Presneau positive.
  A cause that changed every list the same way (a wrong denominator, a stricter cut) would move
  the ratios together; they do not, so either several things differ or the difference is in the
  site counts themselves, which vary by list.
- **The P-values differ, not only the cut.** If the paper had our P-values and only a different
  threshold, one FDR would give its counts. The FDR at which our ranking gives the paper's count
  runs from 0.0028 (Sokolov) to 0.12 (Raponi).
- **The counts are fragile.** Many multi-hit P-values sit near the BH line: between FDR 0.025
  and 0.1 the counts change 1.7- to 25-fold (Chen 1,013 to 1,676; Sanchez-Diaz 5 to 126). Small changes in site
  counts move many terms across it, so count-level agreement needs the paper's exact site
  counts. Monte Carlo noise is small for most lists (another seed changes counts by at most four
  terms, 3.3%) but not for Chartoumpekis, which falls from 17 to 3: its match is chance.
- **The term sets move less than the counts.** Under another seed the reference's terms are kept
  (Jaccard 0.91–1.00 except Chartoumpekis, 0.18); between site-counting readings 0.12–1.00.

**Verdict: not reproducible from the paper's Methods.** The site counts per gene are not
defined by the text, are not in the supplement, and the authors' script is gone. Six readings
and a second seed do not reproduce the counts, and the errors point both ways. Still untried:
per-site score and energy filters for the site counts (needs miRanda's full alignment output,
which our runs did not keep: a rerun of about 45 CPU hours) and other miRanda options. Neither
is suggested by the paper, and with the counts this fragile, a match on a few lists would not
identify the method.

### Comparing counts

`table2.csv` gives `multi_diff` (ours − paper) and `multi_rel_diff` ((ours − paper) / paper,
empty when the paper's count is 0); the same for the basic column. These are the "Δ multi" of
issue #33. They are right for what they say, how far apart two counts are, but not alone: a
zero difference can be chance (Chartoumpekis), and the counts move several-fold with the FDR.
Comparing the significant term sets with the paper's, the better measure, is not possible: the
paper publishes term lists only for S5, which reproduces (1,551 of 1,580 terms). For the
multi-hit column, `multihit_readings.csv` adds the range over readings, the counts at FDR 0.025
and 0.1, and the FDR that would give the paper's count.

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
Table 2 do not. Another seed changes the multi-hit counts by at most four terms (Raponi 120 to
116), except Chartoumpekis (17 to 3), whose agreement with the paper is therefore chance.
