# PMC4168973 figure reproduction

Huang, Yee, Ching, Yu and Garmire (2014), every table, figure and number with computed results:
Table 1, Figs 1 and 3 to 6, Tables 2 and 3, Figs S1 to S4 and the claims of the text, from the
R package `pdscox` ([`../package`](../package)), which rebuilds the paper's lost pipeline from its
text. The paper is CC BY 4.0; `published/` holds its figures for comparison (see
[`../README.md`](../README.md)).

## Results

<!-- full table from ../results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-TABLE-->
14 agrees, 21 partly, 7 inconclusive, 11 differs, 4 not attempted; 35 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1, training set (Miller) | agrees | 39 of 39 fields as printed, 6 paper errors | Assumed: Miller's relapse-free survival, ER, PgR, size, grade, node and age from Bioconductor breastCancerUPP 1.40.0; p53 status from the GSE4922 clinical file (same Uppsala tumours); Two Miller patients have a relapse status (one relapse, one censored) but no relapse time in breastCancerUPP; their time is 0 |
| Table 1, test set 1 (Pawitan) | agrees | 14 of 14 fields as printed | Assumed: Pawitan's relapse-free time is the earlier of SURV_RELAPSE and SURV_DEATH (GSE1456); the event is RELAPSE |
| Table 1, test set 2 (Ivshina) | partly | 37 of 40 fields as printed | The size classes' boundaries are not given. Counting 50 mm tumours as over 50 gives the paper's 10 (strictly over 50: 6); under 10 mm gives 15 against the printed 14 with any boundary we tried. |
| Table 1, test set 3 (Desmedt) | partly | 29 of 30 fields as printed | The largest Desmedt tumour is 50 mm; the paper's one tumour over 50 mm is it, counted as over 50 (as for Ivshina; Miller's three 50 mm tumours are in no class). |
| Fig. 1A, PAM50 heatmap | not attempted | not attempted | The heatmap's gene scaling, palette and ordering are not given; its one testable number, the chi-square p of its two patient clusters against relapse, is item fig1.A.pam50_groups. |
| Fig. 1A, chi-square p of ER, PG, p53, grade and LN against relapse (Miller) | agrees | 5 of 5 fields as printed | Assumed: Miller's relapse-free survival, ER, PgR, size, grade, node and age from Bioconductor breastCancerUPP 1.40.0; p53 status from the GSE4922 clinical file (same Uppsala tumours) |
| Fig. 1A and text, chi-square p of the two PAM50 clusters against relapse | differs | 0 of 1 fields as printed | Two PAM50 clusters of the Miller tumours are not associated with relapse under any clustering we tried (best p 0.011 against the printed 7.46e-5); the paper does not say how it clustered or which PAM50 genes it used (41 of 50 are on our gene list). |
| Fig. 1B to E and text, log-rank p of LN, grade, p53, size, ER and PG (Miller) | agrees | 6 of 6 fields as printed | Assumed: Miller's relapse-free survival, ER, PgR, size, grade, node and age from Bioconductor breastCancerUPP 1.40.0; p53 status from the GSE4922 clinical file (same Uppsala tumours); Two Miller patients have a relapse status (one relapse, one censored) but no relapse time in breastCancerUPP; their time is 0; The 'Wilcoxon log-rank test' is survival::survdiff with rho = 0 (the log-rank test) |
| Fig. 1B, Kaplan-Meier by lymph node status | agrees | 97.90% within 2 px (pass 90.0%, best control 78.7%) | Assumed: Miller's relapse-free survival, ER, PgR, size, grade, node and age from Bioconductor breastCancerUPP 1.40.0; p53 status from the GSE4922 clinical file (same Uppsala tumours); Two Miller patients have a relapse status (one relapse, one censored) but no relapse time in breastCancerUPP; their time is 0 |
| Fig. 1C, Kaplan-Meier by grade | agrees | 96.16% within 2 px (pass 90.0%, best control 77.6%) | Assumed: Miller's relapse-free survival, ER, PgR, size, grade, node and age from Bioconductor breastCancerUPP 1.40.0; p53 status from the GSE4922 clinical file (same Uppsala tumours); Two Miller patients have a relapse status (one relapse, one censored) but no relapse time in breastCancerUPP; their time is 0 |
| Fig. 1D, Kaplan-Meier by p53 status | agrees | 98.37% within 2 px (pass 90.0%, best control 79.7%) | Assumed: Miller's relapse-free survival, ER, PgR, size, grade, node and age from Bioconductor breastCancerUPP 1.40.0; p53 status from the GSE4922 clinical file (same Uppsala tumours); Two Miller patients have a relapse status (one relapse, one censored) but no relapse time in breastCancerUPP; their time is 0 |
| Fig. 1E, Kaplan-Meier by tumour size | agrees | 96.72% within 2 px (pass 90.0%, best control 77.1%) | Assumed: Miller's relapse-free survival, ER, PgR, size, grade, node and age from Bioconductor breastCancerUPP 1.40.0; p53 status from the GSE4922 clinical file (same Uppsala tumours); Two Miller patients have a relapse status (one relapse, one censored) but no relapse time in breastCancerUPP; their time is 0 |
| Fig. 2, workflow of the model | not attempted | not attempted | A diagram of the four steps of the method; it is the structure of the package pdscox. |
| Fig. 3, heatmap of the 15 selected pathways | not attempted | not attempted | The heatmap's scaling, palette and ordering are not given; its testable numbers are in item fig3.values. |
| Fig. 3, chi-square p of ER, PG, p53, grade and LN against relapse (more digits) | agrees | 5 of 5 fields as printed | Assumed: Miller's relapse-free survival, ER, PgR, size, grade, node and age from Bioconductor breastCancerUPP 1.40.0; p53 status from the GSE4922 clinical file (same Uppsala tumours) |
| Fig. 3 and text, PDS clusters against relapse and median-PDS correlation | differs | 0 of 3 fields as printed | On our scores of the paper's 15 pathways the two clusters are not associated with relapse (p 0.23, printed 1.99e-6) and the median score hardly correlates with it (0.047, printed 0.17); on the pathways our own model selects, the same clustering gives p 2.8e-5 and correlation 0.11. Our scores of the paper's pathways are not the paper's (see table2.genomic_univariate). |
| Table 2, pathway-based genomic model: pathways and coefficients | partly | 3 of 30 fields as printed | Our LASSO keeps 5 pathways, 3 of them the paper's (SRCRPTP, RARRXR, IL5); the paper keeps 15. The selection follows from the scores, and our scores of the paper's pathways are not the paper's (table2.genomic_univariate). The paper's coefficients applied to our scores give Miller p 2.3e-4 and AUC 0.66 (printed 6.25e-12 and 0.80). |
| Table 2, univariate Cox p of the 15 pathways on our scores | partly | 4 of 15 fields as printed | Our pathway scores are not the paper's: of the 15 pathways of Table 2, 4 have a univariate Cox p within one order of magnitude of the printed one on our scores, and VIP, LYSOSOME, AKAP13 and LINOLEIC ACID, printed p 2e-6 to 4e-3, have p 0.5 to 0.8. pathifier is deterministic here (seeds 1 to 3 give the same scores), and no preprocessing variant we tried brings these pathways back. The paper's pathifier run, gene mapping and MSigDB release are not available. |
| Table 2, clinical model: features and coefficients | partly | 5 of 9 fields as printed | The same four features are selected; the coefficients differ by 0.0003 to 0.049. The penalty is the median of 250 random cross-validations (ours 7.32); its exact value depends on the folds, which the paper does not give. |
| Table 2, univariate Cox p of LN, size, grade and p53 | agrees | 4 of 4 fields as printed | Assumed: Miller's relapse-free survival, ER, PgR, size, grade, node and age from Bioconductor breastCancerUPP 1.40.0; p53 status from the GSE4922 clinical file (same Uppsala tumours); Two Miller patients have a relapse status (one relapse, one censored) but no relapse time in breastCancerUPP; their time is 0 |
| Table 2 and text, combined model: pathways kept and clinical features | partly | 4 of 5 fields as printed | Lymph node and size are kept and grade and p53 are not, as in the paper; 4 of our 5 genomic pathways are kept (paper: 10 of 15). The pathway count follows from our genomic model (table2.genomic). |
| Fig. 4 and text, log-rank p and AUC of the genomic model on the four sets | partly | 1 of 8 fields as printed | The models are fitted on our pathway scores, which are not the paper's (table2.genomic_univariate): our genomic model keeps 5 pathways, not 15. It reaches Miller p 1.1e-7 and AUC 0.73 (printed 6.25e-12, 0.80), Pawitan 5.4e-4 (3.91e-5), Ivshina 1.9e-6 (1.52e-4) and Desmedt 0.69 (3.73e-4); Ivshina's AUC is the paper's. Ivshina is not an independent test set: 232 of its 249 arrays are Miller's (GSE4922 re-deposits GSE3494's arrays), which is why it scores best. |
| Fig. 4A, training set (Miller) | partly | 36.83% within 2 px (pass 90.0%, best control 33.6%) | The curves follow our model, not the paper's; see fig4.values. |
| Fig. 4B, test set 1 (Pawitan) | partly | 47.02% within 2 px (pass 90.0%, best control 43.1%) | The curves follow our model, not the paper's; see fig4.values. |
| Fig. 4C, test set 2 (Ivshina) | partly | 39.68% within 2 px (pass 90.0%, best control 35.1%) | The curves follow our model, not the paper's; see fig4.values. |
| Fig. 4D, test set 3 (Desmedt) | inconclusive | 13.62% within 2 px (pass 90.0%, best control 24.8%) | The curves follow our model, not the paper's; see fig4.values. |
| Fig. 4E, ROC curves of the genomic model | partly | 9.96% within 2 px (pass 90.0%, best control 8.8%) | The curves follow our model, not the paper's; see fig4.values. |
| Fig. S1 and text, AUC falls as fewer pathways are kept | differs | median AUC 1/2 0.715, 1/4 0.722, 1/8 0.712, 1/16 0.707; 1/2 against 1/4 t-test p 0.222; AUC range 0.661 to 0.794 (paper: decreasing, p < 0.05, 0.69 to 0.81) | With 1/2 to 1/16 of the pathways the median AUC stays at 0.71 to 0.72 (1/2 against 1/4: t-test p 0.22) instead of falling. Our full model already keeps only 5 pathways, so a random half rarely loses much; we ran 25 cross-validations per model, not 250. |
| Fig. 5 and text, log-rank p and AUC of the gene- and pathway-based models | partly | 2 of 16 fields as printed | The models are fitted on our pathway scores, which are not the paper's (table2.genomic_univariate). Desmedt has almost no relapse signal in our hands: no pathway has univariate p below 0.008 and no gene below 3.4e-5 (of 7,455 expressed), so cross-validation picks a penalty (pathways 4.7 to 6.2, genes 47 to 79) that keeps nothing and both Desmedt models are empty. The paper's Desmedt pathway result (p 5.12e-36, AUC 0.92 on 198 patients) is what a penalty near 1 gives in-sample: 77 pathways, p 2.8e-37, AUC 0.94. |
| Fig. 5A, Miller gene-based model | inconclusive | 72.29% within 2 px (pass 90.0%, best control 74.7%) | The curves follow our model, not the paper's; see fig5.values. |
| Fig. 5B, Miller pathway-based model | inconclusive | 56.75% within 2 px (pass 90.0%, best control 57.3%) | The curves follow our model, not the paper's; see fig5.values. |
| Fig. 5C, Pawitan gene-based model | partly | 56.01% within 2 px (pass 90.0%, best control 49.7%) | The curves follow our model, not the paper's; see fig5.values. |
| Fig. 5D, Pawitan pathway-based model | partly | 55.83% within 2 px (pass 90.0%, best control 50.9%) | The curves follow our model, not the paper's; see fig5.values. |
| Fig. 5E, Ivshina gene-based model | inconclusive | 15.04% within 2 px (pass 90.0%, best control 45.1%) | The curves follow our model, not the paper's; see fig5.values. |
| Fig. 5F, Ivshina pathway-based model | partly | 53.57% within 2 px (pass 90.0%, best control 52.6%) | The curves follow our model, not the paper's; see fig5.values. |
| Fig. 5G, Desmedt gene-based model | differs | 0.69% within 2 px (pass 90.0%, best control 6.6%) | The curves follow our model, not the paper's; see fig5.values. |
| Fig. 5H, Desmedt pathway-based model | differs | 0.85% within 2 px (pass 90.0%, best control 26.1%) | The curves follow our model, not the paper's; see fig5.values. |
| Text: pathway-based models beat gene-based models on all four sets | differs | pathway-based better than gene-based (lower p and higher AUC) in 1 of 4 sets: pawitan | On our scores the pathway model beats the gene model on Pawitan only; on Miller it has the higher AUC but the higher p, on Ivshina the gene model wins, and on Desmedt neither model keeps a feature. See fig5.values. |
| Fig. S2: LOOCV, pathway-based above gene-based on all four sets (t-test p < 0.001) | differs | LOOCV: pathway-based above gene-based with t-test p < 0.001 for both p and AUC in 2 of 4 sets | Leave-one-out without refitting puts the pathway model's AUC above the gene model's on Miller and Pawitan (t-test p < 1e-100; on Miller its p-values are the weaker) and below it on Ivshina; Desmedt has no model. See fig5.values. |
| Fig. S3 and text, NKI70 on the training set: log-rank p and AUC | agrees | 2 of 2 fields as printed | Assumed: Two Miller patients have a relapse status (one relapse, one censored) but no relapse time in breastCancerUPP; their time is 0 |
| Fig. S3, ROC of NKI70 and the pathway-based model | inconclusive | 14.38% within 2 px (pass 90.0%, best control 14.5%) | The NKI70 curve is ours and agrees in number (figS3.nki70); the pathway-model curve follows our model, not the paper's; see fig4.values. |
| Fig. 6 and text, log-rank p and AUC of the genomic, combined and clinical models | partly | 6 of 12 fields as printed | The models are fitted on our pathway scores, which are not the paper's (table2.genomic_univariate). The clinical model is the paper's (Miller p 4e-11 against 2.2e-10, AUC 0.75 against 0.74); the genomic and combined models are weaker on Miller and stronger on Ivshina, whose arrays are mostly Miller's. |
| Fig. 6A, Miller genomic model | partly | 37.55% within 2 px (pass 90.0%, best control 33.6%) | The curves follow our model, not the paper's; see fig6.values. |
| Fig. 6B, Ivshina genomic model | partly | 35.47% within 2 px (pass 90.0%, best control 32.3%) | The curves follow our model, not the paper's; see fig6.values. |
| Fig. 6C, Miller combined model | partly | 43.70% within 2 px (pass 90.0%, best control 38.0%) | The curves follow our model, not the paper's; see fig6.values. |
| Fig. 6D, Ivshina combined model | inconclusive | 52.59% within 2 px (pass 90.0%, best control 52.6%) | The curves follow our model, not the paper's; see fig6.values. |
| Fig. 6E, Miller clinical model | partly | 69.09% within 2 px (pass 90.0%, best control 56.3%) | The curves follow our model, not the paper's; see fig6.values. |
| Fig. 6F, Ivshina clinical model | inconclusive | 25.36% within 2 px (pass 90.0%, best control 29.1%) | The curves follow our model, not the paper's; see fig6.values. |
| Fig. 6G, ROC curves of the three models | partly | 25.16% within 2 px (pass 90.0%, best control 21.4%) | The curves follow our model, not the paper's; see fig6.values. |
| Text: combined beats genomic beats clinical, on Miller and Ivshina | differs | combined > genomic > clinical by AUC, combined below genomic by p: miller no, ivshina yes | Combined beats genomic beats clinical on Ivshina; on Miller our genomic model (AUC 0.73) is below the clinical model (0.75), because it keeps 5 pathways, not 15. See fig6.values. |
| Fig. S4: LOOCV, combined above pathway above clinical (t-test p < 0.001) | differs | LOOCV: combined > pathway > clinical by AUC with t-test p < 0.001: miller no, ivshina yes | As text.fig6_claim: the order holds on Ivshina; on Miller the pathway model's leave-one-out AUC (0.73) is below the clinical model's (0.75). |
| Table 3, genomic-model counts and weighted counts of the top 30 genes | agrees | 60 of 60 fields as printed | Assumed: A gene's weighted count is the sum of exp(coefficient) of the Table 2 pathways that contain it, compared within 1e-5 |
| Table 3, combined-model counts and weighted counts, and the 265 shared genes | not attempted | not attempted | The combined model's hazard ratios are not printed, and its gene counts are higher than its 10 starred pathways can give, so the columns cannot be rebuilt; our combined model differs as well (table2.combined). |
| Discussion: genes covered by the 403 pathways and expressed | differs | 403 pathways: 403; over 4500 genes in them: 5555; over 3200 expressed (mean log2 > 7): 1502; U133A over 14,000 genes: 12502; over 10,000 expressed: 3936 | 5,555 genes are in the 403 sets (paper: over 4,500) and all 403 are scored. The paper's 'over 3,200 expressed' and 'over 14,000 genes, over 10,000 expressed' on U133A depend on its mapping and expression cutoff, which are not given: we have 12,502 genes (13,909 with probes of several genes), 1,502 genes in the sets and 3,936 of all genes with mean log2 above 7. |
| Claims recomputed from the paper's own tables and figure titles | agrees | 9 of 9 claims come back from the paper's own tables and figure titles |  |
| Text: the main claims on our run (test p < 0.0005, average test AUC 0.68, combined 3 orders better) | differs | 0 of 3 fields as printed | Follows from fig4.values and fig6.values: Desmedt's p is 0.69, the average test AUC is 0.63, and on Ivshina the combined model's p (2.0e-9) is 2.98 orders below the genomic model's (1.9e-6), just short of 3 (on Miller it is more than 6 orders below both). |
| R package pdscox and its tutorial | agrees | R package pdscox: R CMD check OK; tests 17 passed, 0 failed, 0 skipped; tutorial rendering equals the committed TUTORIAL.md (figures by name) |  |
<!--/RESULTS-TABLE-->

The paper's main claim does not hold on our run: the pathway model is weaker than printed and does not carry to Desmedt. Adding clinical features does help it on both sets (AUC 0.81 against 0.73 on Miller, 0.69 against 0.67 on Ivshina). Ivshina is not an independent test set: 232 of its 249 arrays are Miller's.

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
cross-validation run and builds everything from the fresh run: about 9 hours on 4 cores (pathway
scores about 7 hours, the gene models' cross-validations 1.3 hours), longer than a GitHub-hosted job
may run, so it is run locally:

```bash
nextflow run PMC4168973/figure-reproduction/main.nf --outdir results --full
```

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

- **Our pathway scores are not the paper's.** On our scores 11 of the paper's 15 selected pathways
  have univariate p-values more than ten times larger than printed. On five of them, pathifier gives the
  same scores with seeds 1, 2 and 3, and skipping the normalization, pathifier's filters or its stability option, or
  giving it linear expression, does not bring them back (`experiments/pds_variants.txt`). The
  paper's gene mapping (biomaRt, release not given), its MSigDB release and its CONOR step are not
  available. Every pathway and combined model result that differs follows from this; the gene
  models differ too (Fig. 5), where our gene mapping and normalization are the open difference.
- **Desmedt.** Neither its pathways nor its genes carry enough relapse signal for cross-validation
  to keep any (`experiments/desmedt_penalty.txt`); the paper's Fig. 5 Desmedt results need a far
  smaller penalty.
- **Ivshina is not independent.** 232 of its 249 tumours are Miller's, with the same expression values
  gene for gene (GSE4922 re-deposits GSE3494's arrays; `output/datasets.json`), so its "test" results are mostly training results.
- **Miller's clinical data** are not in GEO. They come from Bioconductor's breastCancerUPP, with p53
  from GSE4922; two patients without a relapse time count as time 0, which gives Fig. 1's p-values.
- **Clustering.** How the paper clustered the PAM50 genes (Fig. 1A) and the pathways (Fig. 3) is
  not given; no variant we tried gives its chi-square p-values (`experiments/`).
- **Fig. S1** uses 25 cross-validation runs per model, not 250 (72 models: 4 fractions, 18 draws each).
- **Renders.** The committed `fig*_ours.png` and overlays are drawn with Pillow (no text is drawn);
  `compare_runs.py` compares them with a fresh run by decoded pixels, and the pixel scores to 1e-9.
