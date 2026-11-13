# PMC407845 figure reproduction

MA-Networker (Gao, Foat and Bussemaker 2004) rerun on the paper's ChIP data and a rebuilt expression
library, and every figure, table and claim compared with the paper. The method is the package
[`../package`](../package) (`manetworker`); the pipeline calls it and holds no second copy.

## Results

<!-- table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-TABLE-->
1 exact, 4 agrees, 7 partly, 1 inconclusive, 5 differs, 3 not attempted; 11 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Fig. 1a | not attempted | not attempted | A diagram of the method; there is nothing to recompute. |
| Text: 751 arrays and 113 TFs | partly | 1 of 2 fields as printed | The SGD archive holds 677 distinct arrays of the paper's 751. Casagrande 2000, Rutherford 2001 and Diehn 2000 (5 arrays) are not there; SGD keeps 15 of Roberts 2000's 56 arrays, 138 of Gasch 2000's 156 (replicates averaged), 55 of Spellman's 60 and 52 of Gasch 2001's 53; Yun 2000 and Protchenko 2001 share one file. All 113 TFs of Lee et al. are there. |
| Fig. 1b, activity profiles of Hap4, Ndd1 and Ste12 | agrees | 3 of 3 fields as printed | Assumed: TF activity profiles are the regression t-values, not the coefficients |
| Fig. 1c, Hap4 binding against coupling | partly | 52.54% within 2 px (pass 90.0%, best control 49.3%) | Our B+/C+ (red) and B+/C- (green) points fall in the published places better than any control, but our couplings are larger in magnitude (r from -0.81 to 0.92; B+/C+ genes up to 0.71, against about 0.65 in the paper), so many of our points sit above the published ones. The rebuilt library (2010 reprocessing, 677 arrays) is the likely reason; it cannot be checked without the authors' 2003 library or coupling_result. |
| Fig. 1c, Ndd1 binding against coupling | inconclusive | 58.95% within 2 px (pass 90.0%, best control 64.1%) | Our coupling scaled by 0.9 scores better than ours, so the score cannot confirm our coupling scale for Ndd1: our couplings are larger in magnitude than the published ones, as for Hap4, although the split itself is close (50 B+/C+ and 44 B+/C- against 50 and 42). |
| Fig. 1c, Ste12 binding against coupling | differs | 27.53% within 2 px (pass 90.0%, best control 34.3%) | Our Ste12 couplings are much stronger than the published ones (our B+/C+ genes reach r 0.67; the paper's stop near 0.45), and we call 25 B+/C+ and 25 B+/C- against 19 and 31. Our pheromone experiments are 15 Roberts 2000 arrays, where the paper had 56; Ste12's activity is carried by them. |
| Text: 37 of 113 TFs kept by backward selection | differs | 0 of 2 fields as printed | Backward selection at the paper's P = 0.005/751 keeps 63 TFs, among them 36 of the paper's 37 (Stb1 is dropped). The paper's TFs head our ranking (our 18 most significant TFs are all among them), so our P-values are stronger overall rather than ordered differently; the reprocessed, imputed library is the likely reason. |
| Table 1 | partly | 12 of 148 fields as printed | Bound (B+) totals agree within 8 genes for every TF (the same ChIP file), but our run calls more bound genes coupled (59% per TF against 58%, with larger per-TF differences), Stb1 is not in our model, and our B- column is 45 to 67 genes above the paper and the unclassified column 68 to 88 below, because the paper's gene list (6382) and its expression filter are not stated. |
| Text: on average 58% of bound genes couple | differs | 0 of 1 fields as printed | 59.0% in our run (59.1% pooled), against 58% (58.4% per TF from Table 1). The share follows the coupling calls of Table 1. |
| Claims recomputed from the paper's own tables | agrees | 6 of 6 claims come back from the paper's own tables and Fig. 2 values (58% is 58.4% per TF, 58.3% pooled; B+/C- insignificant for 5 of 7 in Table 2; 26 of 37 B+/C- bars are 0). Table 4 rows sum to [6027, 6067] genes (Dig1 6027), not to Table 1's 6382. |  |
| Fig. 2, GO categories per TF | partly | 29 of 73 fields as printed | 29 of 73 bars match exactly (24 of 37 B+/C- bars, mostly zeros). B+/C+ counts follow the coupling calls, the GO release (2004-03 against 2003-05) and the unstated correction; Stb1 is not in our model. |
| Text: no GO enrichment in most B+/C- groups | agrees | 2 of 2 fields as printed | Assumed: TF activity profiles are the regression t-values, not the coefficients; Coupling is a one-sided test for positive correlation |
| Table 2, deletion response | not attempted | not attempted | The text says Table 2 averages Hughes et al.'s mutant/wild-type log ratios, but its genome-wide means (0.52 to 0.83, SD 0.12 to 0.34) are not log ratios: the genome-wide mean of the log10 ratios is 0.00 (SD 0.05 to 0.17) and of their absolute values 0.03 to 0.11. The values fit Hughes et al.'s per-gene P-values, which are not public (the Rosetta download sits behind a registration form; the SGD file has ratios only). The claim the table supports is checked from the ratios as text.deletion. |
| Text: B+/C+ genes respond to TF deletion, B+/C- mostly not | partly | 1 of 2 fields as printed | B+/C+ genes respond for 6 of 7 TFs in our run (Yap1: P = 0.13); B+/C- do not respond for any of the 7, so the claim's second half holds. The paper tested Hughes et al.'s P-values (see table2), which are not public. |
| Table 3, cell cycle motifs | partly | 1 of 20 fields as printed | 1 of 20 values matches at printed precision, but the pattern holds: the same motifs are strongly enriched in the same B+/C+ groups (MCB in Mbp1 43.1 against 38.4; SFF in Fkh2 16.7 against 12.9), and far less in B+/C-. The genome release, the cutting of upstream regions, strand handling and the binomial's unit are not stated. |
| Text: motif enrichment in B+/C- always far below B+/C+ | differs | 0 of 1 fields as printed | 9 of 10 combinations hold in our run; SFF in Mcm1 gives 2.4 for B+/C+ and 2.6 for B+/C- (the paper: 3.1 and 1.4). With forward-strand counts, or with genes carrying the motif instead of counts, all 10 hold: the claim turns on how motifs are counted, which the paper does not state. |
| Text: 85% overlap with B+/C+ groups from Simon et al. | differs | 0 of 1 fields as printed | 83% in our run against 85%. The overlap measure is not stated; as a share of the Lee groups it comes closest. |
| Text: 1592 of 4532 probes shared by divergent genes | exact | 2 of 2 fields as printed |  |
| Fig. 3, coupling scores at divergent promoters | partly | 2 of 6 fields as printed, 2 paper errors | Both scores above 12 come back, and every regulatory call of the figure is the same (RAD51, RPL40B, FSP2 and HXT9 coupled; PUP3 and MLP1 not), but the other printed scores differ (Mbp1 to RAD51 11.1 against 8.7), as our couplings are stronger throughout (see fig1c). Hap6 cannot be computed: it is not in the ChIP data. |
| Table 4, deletion in place of coupling | not attempted | not attempted | D+ needs Hughes et al.'s per-gene P-values (P < 1e-2), which are not public. The table is also inconsistent with itself: its Dig1 row sums to 6027 genes and the other six to 6067, while every Table 1 row sums to 6382. |
| Python package manetworker and its tutorial | agrees | manetworker 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |
<!--/RESULTS-TABLE-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| 751 arrays from 19 sources, log2 ratios, preprocessing not stated | 677 arrays from the 15 sources in the SGD expression archive (2010 reprocessing: filtered, KNN-imputed, replicates averaged); Hughes 2000 converted from log10 to log2; Yun 2000 and Protchenko 2001 share one SGD file, used once (`data.py`) |
| Lee et al. 2002 ChIP, 113 TFs; bound at P < 1e-3 | the same file; log2 of the ratios, missing ratios set to 0 in the regression, those genes unclassified (`data.py`, `manetworker.log_ratio`) |
| Regression per experiment; F-test P per coefficient; backward selection to P = 0.005/751 | the same, with the genes measured in each experiment (`manetworker.regress_activities`, `backward_select`) |
| Coupling = Pearson r of expression and activity profile; t-test; 5% FDR | the same, with t-value activity profiles and a one-sided test for positive r, as Figs 1b and 1c show; Benjamini-Hochberg per TF (`manetworker.coupling`, `coupled`) |
| Unclassified: no expression or no binding P | no ChIP ratio, or measured in fewer than half of the arrays (not stated in the paper) |
| GO, May 2003, hypergeometric, Bonferroni | GO 2004-03-01 (the oldest archived), propagated over is_a and part_of; Bonferroni over the terms annotated among the TF's classified genes (`validate.py`) |
| Deletion response, Hughes 2000, sample t-test; deletion arrays left out of the library | Hughes log10 ratios of the single-deletion array; one-sample t-test against the genome mean; the TF's deletion arrays left out before refitting (`networker.py`, `validate.py`) |
| Motifs in up to 600 bp upstream, no overlaps, binomial | S288C R64-1-1; region cut at the nearest upstream feature; motif and reverse complement; binomial over positions (`validate.py`) |
| B+/C+ from Simon et al. 2001 overlap 85% with Lee | Simon et al.'s file; B+ at P < 1e-3 with our coupling; overlap as a share of the Lee group (`validate.py`) |

The choices the paper does not state are assumptions in `results.json`, each with what changes when it
moves; Table 1 is computed for every variant (`output/table1.json`).

## Layout

```text
figure-reproduction/
├── main.nf, nextflow.config, requirements.txt
├── results_notes.json        labels, assumptions, causes and page text (written by hand)
├── results.json              the repository's results-check file (tools/check_results.py)
├── pipeline/
│   ├── fetch_inputs.sh       downloads with SHA-256 checks
│   ├── data.py               the compendium and the ChIP files
│   ├── networker.py          MA-Networker on the paper's data, Table 1 and its variants
│   ├── validate.py           GO, deletion response, motifs, divergent promoters, Simon overlap
│   ├── figures.py            Figs 1 to 3 on the published pixel grids; Fig. 1c pixel scores
│   ├── compare.py            every field, score and claim against the paper
│   ├── build_results.py      results_notes.json + comparison.json -> ../results.json
│   ├── build_page.py, page_template.html   the results page
│   ├── check_reproduction.py the check step
│   └── check_results.py, compare_runs.py, check_package.py   copied from Paper2Repro v0.5.0
├── published/                the paper's figures, with the licence note
└── output/                   the committed outputs of a run
```

## Run

From the repository root, with Python 3.12, the packages in `requirements.txt`, uv, Java 21 and
Nextflow 26.04.3:

```bash
nextflow run PMC407845/figure-reproduction/main.nf --outdir results
```

About 2 minutes on 4 cores (the package check takes most of it). CI runs the same command
(`.github/workflows/reproduce-pmc407845.yml`) on every change to the paper's folder.

## Pipeline steps

1. `FETCH`: the 22 inputs, SHA-256 checked (SGD and GO files fall back to their second host).
2. `NETWORKER`: the compendium; backward selection; activity profiles; coupling; Table 1 for the main run and six variants; the leave-one-out refits for the deletion analysis.
3. `VALIDATE`: Fig. 2's GO counts (and the published bar heights from the vector EPS), Table 2's claim, Table 3, the divergent probes and Fig. 3, the Simon overlap.
4. `FIGURES`: our Figs 1b, 1c, 2 and 3 drawn on the published images, overlays, and the Fig. 1c scores with their controls.
5. `COMPARE`: every field, pixel score and claim.
6. `PACKAGE`: `check_package.py` on `../package` (fresh install, tests, tutorial rerun).
7. `RESULTS`: `../results.json`, verdicts computed by `check_results.py`.
8. `PAGE`: the results page and `report.md`.
9. `CHECK`: `check_results.py` passes, no verdict changed against the committed `../results.json`, and `compare_runs.py` finds the fresh outputs equal to `output/`.

## Limits

- The expression library is not the paper's. Every count that rests on coupling (Table 1, Figs 1c, 2 and 3, the text's 58%) inherits that difference, and it cannot be separated from the unstated settings without the authors' library or their released result files, which this session could not download.
- Backward selection keeps 63 TFs, not 37; Stb1 is not among them, so its Table 1 row and Fig. 2 bars have no value of ours.
- Tables 2 and 4 need Hughes et al.'s per-gene P-values, which are not public.
- Fig. 1b is compared by its caption's claim, not by bars: the panel shows a subset of the arrays in an order the paper does not give.
