# PMC2563693 figure reproduction

Lee E, Chuang HY, Kim JW, Ideker T, Lee D. Inferring pathway activity toward precise disease
classification. *PLoS Computational Biology* 4(11):e1000217 (2008).
[doi:10.1371/journal.pcbi.1000217](https://doi.org/10.1371/journal.pcbi.1000217). CC BY 4.0.

Every figure, table and claim of the paper against our run, from the method rebuilt as
[`pacorg`](../package/) and the seven datasets rebuilt from public archives. The verdicts are
computed by `pipeline/check_results.py` from [`../results.json`](../results.json); nothing below
is typed by hand except the prose.

## Results

<!-- generated: python3 figure-reproduction/pipeline/check_results.py results.json --markdown -->

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Fig. 1, schematic of CORG identification | not attempted | not attempted | A diagram of the method; there is nothing to recompute. |
| Table S1, class sizes of the seven datasets | partly | 12 of 14 fields as printed | GEO's clinical table for GSE2034 has 107 patients with a distant relapse and 179 without; the paper (and GEO's series summary) say 106 and 180. All other class sizes come back. |
| Methods: MSigDB v1.0 C2 gene sets, genes and the top 10% | exact | 3 of 3 fields as printed |  |
| Fig. 2A | partly | 11 of 20 fields as printed | The breast datasets' preprocessing and probe-to-gene mapping are not stated, and our breast data are not the paper's: only 3 of Table S2's 15 CORG lists come back. The source curves (A, C) keep the published shape and order; the verification curves (B, D) differ by up to 0.5. |
| Fig. 2B | partly | 7 of 18 fields as printed | The breast datasets' preprocessing and probe-to-gene mapping are not stated, and our breast data are not the paper's: only 3 of Table S2's 15 CORG lists come back. The source curves (A, C) keep the published shape and order; the verification curves (B, D) differ by up to 0.5. |
| Fig. 2C | partly | 7 of 17 fields as printed | The breast datasets' preprocessing and probe-to-gene mapping are not stated, and our breast data are not the paper's: only 3 of Table S2's 15 CORG lists come back. The source curves (A, C) keep the published shape and order; the verification curves (B, D) differ by up to 0.5. |
| Fig. 2D | partly | 9 of 19 fields as printed | The breast datasets' preprocessing and probe-to-gene mapping are not stated, and our breast data are not the paper's: only 3 of Table S2's 15 CORG lists come back. The source curves (A, C) keep the published shape and order; the verification curves (B, D) differ by up to 0.5. |
| Fig. 2E | partly | 19 of 20 fields as printed | One point is off: PAC_all at 2% reads 2.43 on the figure and 2.55 in our run; the other 19 are within 0.1. |
| Fig. 2F | partly | 17 of 18 fields as printed | One point is off: PAC at 2% reads 1.73 on the figure and 1.37 in our run (the paper's curve rises at 2% and falls again); every other readable point is within 0.1. |
| Fig. 2G | partly | 14 of 20 fields as printed | Boston's top pathways are not those of Tian's statistic on the GSEA Boston file: Table 1's Boston-to-Michigan pathways rank as low as 375th in it. The Boston CORGs themselves are exact (Table 1), so the difference is in which pathways are ranked; our PAC is 0.2 to 0.4 above the figure in G and up to 0.5 below it in H. |
| Fig. 2H | partly | 5 of 20 fields as printed | Boston's top pathways are not those of Tian's statistic on the GSEA Boston file: Table 1's Boston-to-Michigan pathways rank as low as 375th in it. The Boston CORGs themselves are exact (Table 1), so the difference is in which pathways are ranked; our PAC is 0.2 to 0.4 above the figure in G and up to 0.5 below it in H. |
| Fig. 3A, AUC within datasets (bar heights) | partly | 23 of 42 fields as printed | 23 of 42 bars within 0.02. PAC_random differs because the paper's random sets skip the CORG search (supported); NF-kB is near 1 for every method in our data (open); the rest differ by up to 0.05 with unstated classifier settings. |
| Fig. 3B, AUC across datasets (bar heights) | partly | 5 of 8 fields as printed | 5 of 8 bars within 0.02. Boston to Michigan: our PAC is 0.56 against 0.66, because the paper's Boston markers were not Tian's top 52 (with all pathways as input, PAC is 0.71); the Gene bars of both lung directions are 0.02 to 0.03 high. |
| Fig. 3, -log(p) of PAC against Gene (printed labels) | differs | 0 of 9 fields as printed | -log10 p of a Wilcoxon test on 500 paired AUCs moves with every unstated setting and with the random partitions; no printed value comes back to its decimal. Where both are significant the sizes are close (Breast Netherlands 19.2 against 16.9); the significance pattern is compared in text.pac_beats_gene_within and _across. |
| Table 1 (lung), CORGs of each frequently used pathway | exact | 18 of 18 fields as printed |  |
| Table 1 (lung), number of CORGs / members | exact | 18 of 18 fields as printed |  |
| Table 1 (lung), how often each pathway is used in 500 classifiers | partly | 1 of 18 fields as printed | Michigan to Boston: our eight most frequent pathways are the paper's eight, in its order but for one swap, used more often (477 to 294 times against 433 to 102): our classifiers keep more markers. Boston to Michigan: six of the ten pathways are not in Boston's Tian top 52 and are never used. |
| Table S2 (breast), CORGs of each frequently used pathway | partly | 3 of 15 fields as printed | 3 of 15 breast CORG lists come back exactly (Netherlands: cyclin regulated genes, actinY; USA: cell cycle checkpoint II); most others share their first genes. The breast preprocessing is not stated and our matrices are not the paper's. |
| Table S2 (breast), number of CORGs / members | partly | 4 of 15 fields as printed | 3 of 15 breast CORG lists come back exactly (Netherlands: cyclin regulated genes, actinY; USA: cell cycle checkpoint II); most others share their first genes. The breast preprocessing is not stated and our matrices are not the paper's. |
| Table S2 (breast), how often each pathway is used in 500 classifiers | partly | 2 of 15 fields as printed | Follows from the breast data (table_s2.corgs) and the marker count (table1.frequency): 2 of 15 frequencies within 50. |
| Fig. 4, glycolysis and estrogen-signalling activity higher in poor prognosis | exact | 6 of 6 fields as printed |  |
| Fig. S1, marker overlap over 100 two-fold splits, NF-kB | partly | 10 of 18 fields as printed | The pathway and gene curves follow the figure within about 0.1 at most points. The paper does not say how the CORG overlap was computed: ours is close to the figure for NF-kB and below it in the other six datasets (0 to 0.06 against 0.13 to 0.25 in the breast and lung sets). |
| Fig. S1, marker overlap over 100 two-fold splits, Leukemia | partly | 6 of 18 fields as printed | The pathway and gene curves follow the figure within about 0.1 at most points. The paper does not say how the CORG overlap was computed: ours is close to the figure for NF-kB and below it in the other six datasets (0 to 0.06 against 0.13 to 0.25 in the breast and lung sets). |
| Fig. S1, marker overlap over 100 two-fold splits, Prostate | partly | 9 of 18 fields as printed | The pathway and gene curves follow the figure within about 0.1 at most points. The paper does not say how the CORG overlap was computed: ours is close to the figure for NF-kB and below it in the other six datasets (0 to 0.06 against 0.13 to 0.25 in the breast and lung sets). |
| Fig. S1, marker overlap over 100 two-fold splits, Breast Netherlands | partly | 9 of 18 fields as printed | The pathway and gene curves follow the figure within about 0.1 at most points. The paper does not say how the CORG overlap was computed: ours is close to the figure for NF-kB and below it in the other six datasets (0 to 0.06 against 0.13 to 0.25 in the breast and lung sets). |
| Fig. S1, marker overlap over 100 two-fold splits, Breast USA | partly | 11 of 18 fields as printed | The pathway and gene curves follow the figure within about 0.1 at most points. The paper does not say how the CORG overlap was computed: ours is close to the figure for NF-kB and below it in the other six datasets (0 to 0.06 against 0.13 to 0.25 in the breast and lung sets). |
| Fig. S1, marker overlap over 100 two-fold splits, Lung Michigan | partly | 10 of 18 fields as printed | The pathway and gene curves follow the figure within about 0.1 at most points. The paper does not say how the CORG overlap was computed: ours is close to the figure for NF-kB and below it in the other six datasets (0 to 0.06 against 0.13 to 0.25 in the breast and lung sets). |
| Fig. S1, marker overlap over 100 two-fold splits, Lung Boston | partly | 10 of 18 fields as printed | The pathway and gene curves follow the figure within about 0.1 at most points. The paper does not say how the CORG overlap was computed: ours is close to the figure for NF-kB and below it in the other six datasets (0 to 0.06 against 0.13 to 0.25 in the breast and lung sets). |
| Fig. S2A, kNN, k = 3 (bar heights) | partly | 30 of 43 fields as printed | The classifiers' settings (distance and ties for kNN, the naive Bayes model, LDA's covariance) are not stated; NF-kB and Leukemia are near 1 in our data; our bars differ by up to 0.1. |
| Fig. S2A, kNN, k = 3, -log(p) labels | differs | 0 of 6 fields as printed | -log10 p of a Wilcoxon test on 500 paired AUCs moves with every unstated setting and with the random partitions; no printed value comes back to its decimal. Where both are significant the sizes are close (Breast Netherlands 19.2 against 16.9); the significance pattern is compared in text.pac_beats_gene_within and _across. |
| Fig. S2B, kNN, k = 5 (bar heights) | partly | 33 of 43 fields as printed | The classifiers' settings (distance and ties for kNN, the naive Bayes model, LDA's covariance) are not stated; NF-kB and Leukemia are near 1 in our data; our bars differ by up to 0.1. |
| Fig. S2B, kNN, k = 5, -log(p) labels | differs | 0 of 7 fields as printed | -log10 p of a Wilcoxon test on 500 paired AUCs moves with every unstated setting and with the random partitions; no printed value comes back to its decimal. Where both are significant the sizes are close (Breast Netherlands 19.2 against 16.9); the significance pattern is compared in text.pac_beats_gene_within and _across. |
| Fig. S2C, naive Bayes (bar heights) | partly | 12 of 43 fields as printed | The classifiers' settings (distance and ties for kNN, the naive Bayes model, LDA's covariance) are not stated; NF-kB and Leukemia are near 1 in our data; our bars differ by up to 0.1. |
| Fig. S2C, naive Bayes, -log(p) labels | differs | 0 of 6 fields as printed | -log10 p of a Wilcoxon test on 500 paired AUCs moves with every unstated setting and with the random partitions; no printed value comes back to its decimal. Where both are significant the sizes are close (Breast Netherlands 19.2 against 16.9); the significance pattern is compared in text.pac_beats_gene_within and _across. |
| Fig. S2D, LDA (bar heights) | partly | 13 of 43 fields as printed | The classifiers' settings (distance and ties for kNN, the naive Bayes model, LDA's covariance) are not stated; NF-kB and Leukemia are near 1 in our data; our bars differ by up to 0.1. |
| Fig. S2D, LDA, -log(p) labels | differs | 0 of 8 fields as printed | -log10 p of a Wilcoxon test on 500 paired AUCs moves with every unstated setting and with the random partitions; no printed value comes back to its decimal. Where both are significant the sizes are close (Breast Netherlands 19.2 against 16.9); the significance pattern is compared in text.pac_beats_gene_within and _across. |
| Fig. S3, sequential against forward selection | partly | 18 of 28 fields as printed | 18 of 28 bars within 0.02. The forward selection's stopping rule is not stated; NF-kB is near 1 for every method in our data. |
| Fig. S4, breast pathway activity heatmaps | not attempted | not attempted | A heatmap without values or a claim in the text beyond Table S2; the clustering and colour scale are not stated. Our heatmap of the Table S2 pathways is drawn for reference (figure-reproduction/output/figures/fig_s4_ours.png). |
| Fig. S5, CORGs per pathway in the top 10% | partly | 25 of 42 fields as printed | The box plots summarize the CORG counts of each dataset's top 52 pathways; the medians come back in 5 of 7 datasets. Which 52 pathways the paper counted is not certain (Boston's differ, fig2.g), and the breast data differ. |
| PAC markers discriminate better than gene markers (Fig. 2) | partly | 5 of 8 fields as printed | PAC is above the top genes in all four source panels and in Michigan to Boston; not at every fraction in the two breast verification panels (our breast data differ) and in Boston to Michigan (Boston's top pathways differ). |
| PAC above its own CORGs and above PAC_all in the source datasets (Fig. 2) | agrees | 8 of 8 fields as printed | Assumed: Tian et al.'s pathway score as |sum of member t| / sqrt(members) (Tian 2005's standardized statistic), not the plain mean the Methods name |
| Top genes more powerful than CORGs in the source datasets (Fig. 2) | agrees | 4 of 4 fields as printed | Assumed: Tian et al.'s pathway score as |sum of member t| / sqrt(members) (Tian 2005's standardized statistic), not the plain mean the Methods name |
| PAC significantly better than Gene within datasets (Fig. 3A) | partly | 4 of 7 fields as printed | PAC is significantly better than Gene in Breast Netherlands, Lung Michigan and Lung Boston, and Leukemia shows no PAC advantage, as in the paper; not in NF-kB (both near 1 in our data), Prostate (Gene 0.961 against PAC 0.955) or Breast USA (p = 0.10). |
| PAC significantly better than Gene across datasets (Fig. 3B) | partly | 2 of 4 fields as printed | Michigan to Boston is significant and Netherlands to USA is not, as in the paper; USA to Netherlands is not (our breast data differ) and Boston to Michigan favours Gene (Boston's markers differ: with all pathways as input PAC wins, 0.711 against 0.610). |
| PAC above PAC_random (Fig. 3A) | partly | 5 of 7 fields as printed | With the CORG search inside the random sets, PAC_random reaches PAC in Prostate and Breast USA; without it (the reading the paper's PAC_random values support) PAC is above PAC_random in every dataset. |
| Mean, Median and PCA above PAC_random (Fig. 3A) | partly | 3 of 7 fields as printed | As text.pac_above_random: our PAC_random runs the CORG search; without it Mean, Median and PCA average above PAC_random in every dataset (Leukemia 0.974 against 0.900, Prostate 0.948 against 0.888, Breast Netherlands 0.648 against 0.619, Breast USA 0.593 against 0.568). |
| The same trend with kNN, naive Bayes, LDA and forward selection (Figs S2, S3) | agrees | 5 of 5 fields as printed | Assumed: Tian et al.'s pathway score as |sum of member t| / sqrt(members) (Tian 2005's standardized statistic), not the plain mean the Methods name |
| CORG sets of two to four genes, some of more than eight (Fig. S5) | agrees | 2 of 2 fields as printed | Assumed: Tian et al.'s pathway score as |sum of member t| / sqrt(members) (Tian 2005's standardized statistic), not the plain mean the Methods name |
| The paper's own numbers checked against each other | agrees | 6 of 6 checks on the paper's own numbers hold: every printed -log(p) is at least -log10(0.05) = 1.30 (base 10; base e would need 3.00); the PAC bar is above the Gene bar wherever a -log(p) is printed (36 of 36); every Table 1 and Table S2 frequency is above 100 of 500; 10% of 522 pathways is 52; Fig. S5 medians lie between 2 and 4 (the text's 'two to four') and the largest set has more than eight; published Fig. 2: PAC above Genes in the source panels |  |
| Cross-validation repeats rerun from scratch against the committed full run | agrees | 22 cross-validation repeats rerun from scratch equal the committed full run |  |
| Port against the authors' code | not attempted | not attempted | The authors' software is lost: no link, no availability statement and no code in the supplement; searches of GitHub, CRAN, Bioconductor, PyPI and the authors' lab pages found nothing (issue #47). pacorg is written from the Methods and checked against the paper. |
| pacorg, the method as a Python package | agrees | pacorg 0.1.0: wheel installed in a fresh environment and imported from it; tests 5 passed; tutorial 6 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |

4 exact, 7 agrees, 33 partly, 5 differs, 3 not attempted; 35 open causes.

The main claim, that classifiers on CORG-based pathway activity beat classifiers on genes, holds where our data are the paper's or close to it: Breast Netherlands, Lung Michigan, Lung Boston and Michigan to Boston, with Leukemia and Netherlands to USA showing no difference as in the paper. It does not hold in our NF-kB, Prostate, Breast USA, USA to Netherlands and Boston to Michigan runs; the causes are our breast and NF-kB data, which are not the authors' (open), and Boston's pathway pre-selection (Boston to Michigan comes back with all pathways as input).


## What the code does, against the paper

| Step | The paper | Here |
| --- | --- | --- |
| Pathways | MSigDB v1.0 C2: 472 pathways and 50 clusters, 5602 genes | `c2.symbols.gmt` from the GSEA site (522 sets, 5602 genes). For the non-lung datasets its old symbols are mapped to Entrez Gene IDs (official symbol, then a unique synonym, then a discontinued symbol in NCBI's gene history; `annotation/`). |
| Lung Michigan, Boston | Subramanian et al. 2005's labels | GSEA's `Lung_*_collapsed_symbols.gct` and `.cls` as they are, no log. All 18 CORG lists of Table 1 come back from them. |
| Breast Netherlands | 295 patients, 78 metastatic within five years | `seventyGeneData`'s van de Vijver ExpressionSet (log10 ratios), probes averaged per Entrez ID; metastatic = distant metastasis within 5 years (78 / 217, exact). |
| Breast USA | 286 patients, 106 metastatic | GSE2034 series matrix (MAS5), single-gene probes, per-sample maximum per gene; labels from GEO's clinical table: 107 / 179. |
| Leukemia | 79 TEL-AML1, 64 hyperdiploid | `stjudem` 1.40.0 (vsn, median polish), same probe rule. |
| NF-kB | 12 wildtype, 12 mutant | GSE2624, the 1, 3 and 6 h TNF arrays; no doxycycline = mutant IkBa on. Which 24 of the 32 arrays the paper used is not stated. |
| Prostate | 62 tumours, 41 normals | GSE3933 on its three platforms (log2 ratios), IMAGE clones mapped through GPL2695's annotation, genes measured in 80% of arrays, the rest imputed (10 nearest genes). |
| Activity, CORGs | z-score per gene, sum over sqrt(k), greedy search on t | As stated (`pacorg.activity`, `pacorg.find_corgs`), pooled-variance t. |
| Pre-selection | "the top 10% by Tian et al.'s average t" | Tian et al.'s standardized statistic, sum of t over sqrt(members). With the plain average, Fig. 2E and Table 1 do not come back; with the standardized sum they do (see `output/hypotheses.json`, `tian_rank`). |
| Classifier | logistic regression, markers added by p-value, count by validation AUC, 100 x 5-fold CV | As stated; folds stratified; ridge 1e-8; seeds per dataset and repeat. |
| PAC_random | "1000 sets of same-size random gene sets" | Two random draws per partition with the CORG search inside each set. The paper's values fit random sets without the search (a tested hypothesis, not our main run). |
| Gene | as many top genes as pooled CORGs | As stated. |
| Mean, Median, PCA | Guo et al. 2005, Bild et al. 2006 | Over all measured members of the same 52 pathways; PCA fitted on the marker-selection samples. |
| -log(p) | Wilcoxon signed-rank, 500 paired AUCs | As stated, base 10 (the paper's own labels require it). |

## Reading the published figures

Figs 2 and 3 are raster images; their values are read off the PLOS PNGs (`pipeline/digitize.py`):
each panel's y axis is calibrated on its grid lines (residual below 0.05 of a unit), line points
are read at the five category positions, and points where two series overlap are left out. Figs
S1, S2, S3 and S5 are vector PDFs; `pipeline/read_published.py` reads the exact bar tops, marker
centres and box edges from their drawing commands. Values read off a raster figure carry the
assumption `read_from_figure`, which caps a figure's verdict at "agrees".

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config`, `run_skyriver.sbatch` | The pipeline; the cluster launcher. |
| `requirements.txt` | Pinned Python packages. |
| `results_notes.json` | Labels, sources, tolerances, assumptions and causes, written by hand; merged with the run's numbers into `../results.json`. |
| `annotation/` | Identifier tables built once from NCBI Gene and GEO annotations (`pipeline/build_annotation.py`). |
| `variants/` | Summaries of the cross-validation runs that test hypotheses (PAC_VARIANT, below). |
| `published/` | The paper's figures (CC BY 4.0): Figs 1 to 4 and Table 1 as PLOS serves them, Figs S1, S2, S3, S5 rasterized from the supplementary PDFs. |
| `pipeline/fetch_inputs.sh` | Downloads every input and checks its SHA-256. |
| `pipeline/export_bioc.py`, `prepare_data.py` | The two Bioconductor packages read without R; the seven gene-level datasets and their gene sets. |
| `pipeline/markers.py`, `fig2.py`, `robustness.py`, `cv.py` | CORGs of every pathway, Fig. 2, Figs S1 and S5, the cross-validation. |
| `pipeline/pack_cv.py`, `reduce_cv.py` | Pack and check repeats; means, standard errors, Wilcoxon tests and frequencies. |
| `pipeline/read_published.py`, `digitize.py` | The published values. |
| `pipeline/compare.py`, `render.py`, `hypotheses.py` | Paper against ours; the renders and overlays; the hypothesis tests. |
| `pipeline/build_results.py`, `check_results.py`, `check_reproduction.py`, `compare_runs.py`, `check_package.py`, `build_page.py`, `make_results_check.py` | results.json, the checks, the results page and the repository's results-check file. |
| `output/` | The committed run: `cv/` (all 1,100 cross-validation repeats), `comparison.json`, `cv_summary.json`, `hypotheses.json`, the renders in `figures/`. |
| `results.json` | The repository's results-check file (`tools/check_results.py`). |

## Run

```bash
pip install -r PMC2563693/figure-reproduction/requirements.txt
nextflow run PMC2563693/figure-reproduction/main.nf --outdir results          # about 15 minutes on 4 cores
sbatch PMC2563693/figure-reproduction/run_skyriver.sbatch --full               # every CV repeat again, on Slurm
```

The default run downloads and checks the inputs, rebuilds the seven datasets, recomputes Fig. 2,
Figs S1 and S5, every CORG list and the hypothesis tests from scratch, reruns the first two
repeats of each of the 11 cross-validation experiments and checks them against `output/cv`
number for number, summarizes and compares everything from `output/cv`, checks the package, and
compares the whole run with the committed `output/`. The full cross-validation (100 repeats of
5-fold CV for 7 datasets and 4 dataset pairs, with five classifiers and forward selection) took
3.3 CPU hours on the cluster; `--full` reruns it, and its `results/cv` replaces `output/cv`.

The hypothesis runs in `variants/` are the same script with `PAC_VARIANT` set, logistic
regression only, for example

```bash
PAC_VARIANT=random_nocorg,lr_only python cv.py DATA OUT within breast_usa 0 20
PAC_VARIANT=cross_all,lr_only     python cv.py DATA OUT cross lung_boston lung_michigan 0 25
```

then `reduce_cv.py` on OUT; they ran on the cluster (`random_nocorg`, `seq_stop`: 20 repeats per
dataset; `seq_stop`, `nfkb_alt`: 100 repeats; `cross_all`: the repeats finished in the time
given).

## Pipeline steps

1. `FETCH`: GSEA files, GEO series matrices, GSE2034's clinical table, `seventyGeneData` and
   `stjudem`, the supplementary PDFs; SHA-256 checked.
2. `PREPARE`: the Bioconductor objects read with `rdata`; the seven datasets (`datasets.json`
   records every choice and the class sizes of Table S1).
3. `MARKERS`: CORGs and Tian scores of every pathway in every whole dataset (Tables 1 and S2,
   Fig. 4); Fig. 2.
4. `ROBUSTNESS`: Fig. S1 over 100 seeded two-fold splits; Fig. S5.
5. `HYPOTHESES`: the pathway-score and USA-preprocessing tests, plus `variants/`.
6. `CV_CHUNK`, `CV_CHECK`: two repeats per experiment from scratch, against `output/cv` (`--full`:
   all repeats, packed by `CV_PACK`).
7. `COMPARE`: summaries, the published values, `comparison.json`, renders and overlays.
8. `PACKAGE`: `check_package.py` on `../package`.
9. `RESULTS`: `results.json`, `check_reproduction.py` (fails on any broken rule, a rerun repeat
   that differs, a failed package check, or any difference from the committed `output/`), and
   the results page.

## Limits

- The breast datasets are not the authors' matrices: 3 of the 15 CORG lists of Table S2 come
  back, and 12 ways of preparing the USA arrays and 107 single relabellings did not bring more.
  Every breast result inherits this.
- Boston's pathway pre-selection is not Tian's statistic on the GSEA file; the Boston CORGs are
  exact, so the difference is the pathway list. Boston to Michigan comes back only with all
  pathways as input.
- NF-kB: on our 24 arrays every method classifies almost perfectly; the paper's gene classifier
  reaches 0.82. The paper does not say which 24 of GSE2624's 32 arrays it used.
- The classifier settings, the random splits and the CORG overlap of Fig. S1 are not stated; AUC
  bars agree within 0.02 for about half the bars, the -log(p) labels do not come back to their
  decimal, and the frequencies of Tables 1 and S2 are higher in our run.
- Fig. S4 has no values and no claim beyond Table S2; ours is drawn but not scored.
