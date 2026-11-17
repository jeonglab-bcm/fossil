# PMC4168973 figure reproduction

Huang, Yee, Ching, Yu and Garmire (2014), every table, figure and number with computed results:
Table 1, Figs 1 and 3 to 6, Tables 2 and 3, Figs S1 to S4 and the claims of the text, from the
R package `pdscox` ([`../package`](../package)), which rebuilds the paper's lost pipeline from its
text. The paper is CC BY 4.0; `published/` holds its figures for comparison (see
[`../README.md`](../README.md)).

## Results

<!-- full table from ../results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-TABLE-->
<!--/RESULTS-TABLE-->

<!--CLAIMS-LINE-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| Four GEO series of HG-U133A arrays: GSE3494 (Miller, training, 236 patients), GSE1456 (Pawitan, 159), GSE4922 (Ivshina, 249), GSE7390 (Desmedt, 198) | The series matrices as deposited (MAS5, log2); Miller's clinical data from Bioconductor breastCancerUPP 1.40.0 (GEO has none), p53 from the GSE4922 clinical file; the 236 are the tumours with a relapse status there |
| Probes to Gene IDs with biomaRt through RefSeq; geometric mean of a gene's log2 probes | GEO's GPL96 annotation (gene symbols, probes of several genes left out); geometric mean of the log2 probes |
| limma normalization of each data set; CONOR "with the Bayesian method" across data sets | limma quantile normalization of each data set; no CONOR, because pathifier standardizes every gene within each data set, which cancels any per-gene batch shift |
| 403 KEGG and BioCarta gene sets from GSEA | MSigDB v6.0 c2.cp.kegg (186) and c2.cp.biocarta (217), symbols |
| pathifier PDS | pathifier 1.40.0, defaults, no normal samples (none of the sets has any), each data set on its own; each score turned to rise with its genes' expression |
| Cox model with an L1 penalty (penalized), lambda chosen by likelihood cross-validation over 250 simulations | 250 runs of `penalized::optL1` with 10 random folds; the median of the 250 optimal lambdas; `penalized` at that lambda |
| PI = log hazard ratio; higher risk above the training 3rd quartile, applied to every test set | the same |
| "Wilcoxon log-rank test" | `survival::survdiff`, rho = 0 (rho = 1 does not give Fig. 1's p-values; rho = 0 does) |
| ROC curves and AUC of the PI against relapse | AUC of the PI against the relapse status |
| Gene-based models: the same without PDS, trained on each set, cutoff at the set's relapse ratio (Fig. 5) | all 12,502 genes, the same LASSO, cutoff at the set's relapse share |
| Clinical and combined models, features and PDS standardized | ER, PgR, p53, grade, LN, size (mm) and age, missing values filled with the median, standardized within each set; combined: standardized PDS of all pathways plus these |
| 1/2 to 1/16 of the pathways, 18 draws each (Fig. S1) | the same draws of pathways (seed 20140929) on the training PDS; 25 cross-validation runs per model, not 250 |
| LOOCV: leave one out, reset the cutoff to the remaining relapse ratio (Figs S2, S4) | the same, without refitting |
| NKI70: correlation with the good-prognosis profile, as van de Vijver et al. | genefu's `sig.gene70` profile, Spearman correlation of the standardized genes, poor when -correlation >= -0.3 |

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. |
| `requirements.txt`, `pipeline/install_r.sh` | Pinned Python packages; R 4.3.3 and the R packages at fixed Ubuntu 24.04 versions, pathifier 1.40.0 and penalized 0.9-53 from their source tarballs. |
| `results_notes.json` | Labels, sources, assumptions and causes, written by hand; merged with the computed numbers into `../results.json`. |
| `pipeline/fetch_inputs.sh` | Downloads with SHA-256 checks: the four GEO series matrices, the GSE4922 clinical file, the GPL96 annotation, MSigDB v6.0 KEGG and BioCarta sets, breastCancerUPP 1.40.0 and genefu 2.34.0 (Bioconductor 3.18). |
| `pipeline/prepare_data.R` | The four data sets (genes by samples, clinical table), the gene sets, the PAM50 genes; `datasets.json`. |
| `pipeline/pds.R` | Pathway deregulation scores of one data set; `output/pds/<set>.csv`. |
| `pipeline/clinical.R` | Table 1, the Fig. 1 tests and curves, Table 2's univariate clinical p-values; `output/clinical.json`. |
| `pipeline/models.R` | The genomic, clinical and combined models, the per-set models of Fig. 5, LOOCV, the subsampling of Fig. S1 and NKI70; `output/models.json`, `output/models/lambdas.json`, `output/curves/`. |
| `pipeline/table3.R` | Table 3's genomic columns and the coverage numbers of the Discussion; `output/table3.json`. |
| `pipeline/score_figures.py`, `pipeline/panels.json` | Every Kaplan-Meier and ROC panel: our curves drawn on the published pixel grid (placed from the published tick marks), scored two ways within 2 px against the published curves, with controls; `output/fig*_ours.png`, `output/fig*_overlay.png`, `output/pixel_scores.json`. |
| `pipeline/compare.py`, `pipeline/paper_values.json` | Our values against the paper's (typed from the paper); the text's claims, also on the paper's own numbers. |
| `pipeline/build_results.py`, `pipeline/check_results.py` | `../results.json` and its verdicts. |
| `pipeline/check_r_package.sh` | `R CMD build`, `R CMD check`, tutorial render compared with the committed `TUTORIAL.md`. |
| `pipeline/build_page.py`, `pipeline/page_template.html` | The results page (`site/PMC4168973/index.html`). |
| `pipeline/check_rerun.py`, `pipeline/check_reproduction.py`, `pipeline/compare_runs.py` | The checks against the committed outputs. |
| `pipeline/make_results_check.py`, `results.json` | The repository's results-check file (`tools/check_results.py`). |
| `pipeline/update_readmes.py` | The generated parts of the READMEs and the front-page verdict. |
| `output/` | Everything the pipeline writes, committed. |

## Run

From the repository root, on Ubuntu 24.04 with Java 21 and Nextflow 26.04.3:

```bash
bash PMC4168973/figure-reproduction/pipeline/install_r.sh
```

```bash
pip install -r PMC4168973/figure-reproduction/requirements.txt
```

```bash
nextflow run PMC4168973/figure-reproduction/main.nf --outdir results
```

The default run (the CI run of `.github/workflows/reproduce-pmc4168973.yml`) rescores 4 of the 403
pathways in each data set and reruns the first 2 cross-validation runs of every model (the first
model of each Fig. S1 fraction), checks that they equal the committed ones, and fits every model
from the committed scores and penalties. `--full` scores every pathway and runs every
cross-validation run (<!--FULL-TIME--> on 4 cores) and builds everything from the fresh run; the
workflow does that when started by hand with `full`.

## Pipeline steps

1. `FETCH`: download the inputs and check their SHA-256.
2. `INSTALL`: install `pdscox` from `../package` into the run's own library.
3. `PREPARE`: the four data sets, the gene sets, `datasets.json`.
4. `PDS`: the rescored pathways (or every pathway with `--full`).
5. `CLINICAL`, `MODELS`, `TABLE3`: Table 1 and Fig. 1; every model; Table 3 and the coverage.
6. `RERUN_CHECK`: the rescored pathways and the rerun cross-validation runs must equal the committed ones.
7. `COMPARE`: renders, overlays, pixel scores and the comparison with the paper.
8. `PACKAGE`: the R package checks.
9. `RESULTS`, `PAGE`: `results.json` with computed verdicts; the results page and `report.md`.
10. `CHECK`: `check_results.py`, the verdicts against the committed `../results.json`, and
    `compare_runs.py` against the committed `output/`.

## Limits

<!--LIMITS-->
