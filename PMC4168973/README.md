# PMC4168973: A novel model to combine clinical and pathway-based transcriptomic information for the prognosis prediction of breast cancer (Huang et al. 2014)

Huang S, Yee C, Ching T, Yu H, Garmire LX. A novel model to combine clinical and pathway-based
transcriptomic information for the prognosis prediction of breast cancer. *PLoS Comput Biol*
10(9):e1003851 (2014). [doi:10.1371/journal.pcbi.1003851](https://doi.org/10.1371/journal.pcbi.1003851),
[PMC4168973](https://pmc.ncbi.nlm.nih.gov/articles/PMC4168973/), issue
[jeonglab-bcm/fossil#70](https://github.com/jeonglab-bcm/fossil/issues/70).

The paper is © 2014 Huang et al., published under the
[Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/). This folder
does not contain the paper, its full text or its supplements; `figure-reproduction/published/` holds
Figs 1, 3 to 6 and S1 to S4 (the PLOS original files, converted to PNG, unchanged) for comparison,
under that licence and with this attribution.

The paper scores 403 KEGG and BioCarta pathways in each tumour with pathifier's pathway deregulation
score (PDS), selects pathways with an L1-penalized Cox model on one breast cancer data set (Miller,
236 patients) and tests the prognostic index on three others (Pawitan, Ivshina, Desmedt); it then
compares the pathway model with gene-based, clinical, combined and NKI70 models (Figs 4 to 6, S1 to
S4, Tables 2 and 3). The analysis was done in R and the code was not released. We rebuilt it from the
paper's text as the R package [`package/`](package/) (`pdscox`) and reran every step on the public
data.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: inputs, PDS, Table 1, Figs 1 and 3 to 6, Tables 2 and 3, Figs S1 to S4, the text's claims, pixel scores of every Kaplan-Meier and ROC panel, and the check against the committed outputs. |
| [`package/`](package/) | `pdscox`, the method as an installable R package, with example data, tests and a [tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC4168973/>

Install the package: `remotes::install_github("jeonglab-bcm/fossil/PMC4168973/package")`.

## Results

<!-- summary and table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-SUMMARY-->
14 agrees, 21 partly, 7 inconclusive, 11 differs, 4 not attempted; 35 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Table 1, training set (Miller) | agrees | 39 of 39 fields as printed, 6 paper errors |
| Table 1, test set 1 (Pawitan) | agrees | 14 of 14 fields as printed |
| Table 1, test set 2 (Ivshina) | partly | 37 of 40 fields as printed |
| Table 1, test set 3 (Desmedt) | partly | 29 of 30 fields as printed |
| Fig. 1A, PAM50 heatmap | not attempted | not attempted |
| Fig. 1A, chi-square p of ER, PG, p53, grade and LN against relapse (Miller) | agrees | 5 of 5 fields as printed |
| Fig. 1A and text, chi-square p of the two PAM50 clusters against relapse | differs | 0 of 1 fields as printed |
| Fig. 1B to E and text, log-rank p of LN, grade, p53, size, ER and PG (Miller) | agrees | 6 of 6 fields as printed |
| Fig. 1B, Kaplan-Meier by lymph node status | agrees | 97.90% within 2 px (pass 90.0%, best control 78.7%) |
| Fig. 1C, Kaplan-Meier by grade | agrees | 96.16% within 2 px (pass 90.0%, best control 77.6%) |
| Fig. 1D, Kaplan-Meier by p53 status | agrees | 98.37% within 2 px (pass 90.0%, best control 79.7%) |
| Fig. 1E, Kaplan-Meier by tumour size | agrees | 96.72% within 2 px (pass 90.0%, best control 77.1%) |
| Fig. 2, workflow of the model | not attempted | not attempted |
| Fig. 3, heatmap of the 15 selected pathways | not attempted | not attempted |
| Fig. 3, chi-square p of ER, PG, p53, grade and LN against relapse (more digits) | agrees | 5 of 5 fields as printed |
| Fig. 3 and text, PDS clusters against relapse and median-PDS correlation | differs | 0 of 3 fields as printed |
| Table 2, pathway-based genomic model: pathways and coefficients | partly | 3 of 30 fields as printed |
| Table 2, univariate Cox p of the 15 pathways on our scores | partly | 4 of 15 fields as printed |
| Table 2, clinical model: features and coefficients | partly | 5 of 9 fields as printed |
| Table 2, univariate Cox p of LN, size, grade and p53 | agrees | 4 of 4 fields as printed |
| Table 2 and text, combined model: pathways kept and clinical features | partly | 4 of 5 fields as printed |
| Fig. 4 and text, log-rank p and AUC of the genomic model on the four sets | partly | 1 of 8 fields as printed |
| Fig. 4A, training set (Miller) | partly | 36.83% within 2 px (pass 90.0%, best control 33.6%) |
| Fig. 4B, test set 1 (Pawitan) | partly | 47.02% within 2 px (pass 90.0%, best control 43.1%) |
| Fig. 4C, test set 2 (Ivshina) | partly | 39.68% within 2 px (pass 90.0%, best control 35.1%) |
| Fig. 4D, test set 3 (Desmedt) | inconclusive | 13.62% within 2 px (pass 90.0%, best control 24.8%) |
| Fig. 4E, ROC curves of the genomic model | partly | 9.96% within 2 px (pass 90.0%, best control 8.8%) |
| Fig. S1 and text, AUC falls as fewer pathways are kept | differs | median AUC 1/2 0.715, 1/4 0.722, 1/8 0.712, 1/16 0.707; 1/2 against 1/4 t-test p 0.222; AUC range 0.661 to 0.794 (paper: decreasing, p < 0.05, 0.69 to 0.81) |
| Fig. 5 and text, log-rank p and AUC of the gene- and pathway-based models | partly | 2 of 16 fields as printed |
| Fig. 5A, Miller gene-based model | inconclusive | 72.29% within 2 px (pass 90.0%, best control 74.7%) |
| Fig. 5B, Miller pathway-based model | inconclusive | 56.75% within 2 px (pass 90.0%, best control 57.3%) |
| Fig. 5C, Pawitan gene-based model | partly | 56.01% within 2 px (pass 90.0%, best control 49.7%) |
| Fig. 5D, Pawitan pathway-based model | partly | 55.83% within 2 px (pass 90.0%, best control 50.9%) |
| Fig. 5E, Ivshina gene-based model | inconclusive | 15.04% within 2 px (pass 90.0%, best control 45.1%) |
| Fig. 5F, Ivshina pathway-based model | partly | 53.57% within 2 px (pass 90.0%, best control 52.6%) |
| Fig. 5G, Desmedt gene-based model | differs | 0.69% within 2 px (pass 90.0%, best control 6.6%) |
| Fig. 5H, Desmedt pathway-based model | differs | 0.85% within 2 px (pass 90.0%, best control 26.1%) |
| Text: pathway-based models beat gene-based models on all four sets | differs | pathway-based better than gene-based (lower p and higher AUC) in 1 of 4 sets: pawitan |
| Fig. S2: LOOCV, pathway-based above gene-based on all four sets (t-test p < 0.001) | differs | LOOCV: pathway-based above gene-based with t-test p < 0.001 for both p and AUC in 2 of 4 sets |
| Fig. S3 and text, NKI70 on the training set: log-rank p and AUC | agrees | 2 of 2 fields as printed |
| Fig. S3, ROC of NKI70 and the pathway-based model | inconclusive | 14.38% within 2 px (pass 90.0%, best control 14.5%) |
| Fig. 6 and text, log-rank p and AUC of the genomic, combined and clinical models | partly | 6 of 12 fields as printed |
| Fig. 6A, Miller genomic model | partly | 37.55% within 2 px (pass 90.0%, best control 33.6%) |
| Fig. 6B, Ivshina genomic model | partly | 35.47% within 2 px (pass 90.0%, best control 32.3%) |
| Fig. 6C, Miller combined model | partly | 43.70% within 2 px (pass 90.0%, best control 38.0%) |
| Fig. 6D, Ivshina combined model | inconclusive | 52.59% within 2 px (pass 90.0%, best control 52.6%) |
| Fig. 6E, Miller clinical model | partly | 69.09% within 2 px (pass 90.0%, best control 56.3%) |
| Fig. 6F, Ivshina clinical model | inconclusive | 25.36% within 2 px (pass 90.0%, best control 29.1%) |
| Fig. 6G, ROC curves of the three models | partly | 25.16% within 2 px (pass 90.0%, best control 21.4%) |
| Text: combined beats genomic beats clinical, on Miller and Ivshina | differs | combined > genomic > clinical by AUC, combined below genomic by p: miller no, ivshina yes |
| Fig. S4: LOOCV, combined above pathway above clinical (t-test p < 0.001) | differs | LOOCV: combined > pathway > clinical by AUC with t-test p < 0.001: miller no, ivshina yes |
| Table 3, genomic-model counts and weighted counts of the top 30 genes | agrees | 60 of 60 fields as printed |
| Table 3, combined-model counts and weighted counts, and the 265 shared genes | not attempted | not attempted |
| Discussion: genes covered by the 403 pathways and expressed | differs | 403 pathways: 403; over 4500 genes in them: 5555; over 3200 expressed (mean log2 > 7): 1502; U133A over 14,000 genes: 12502; over 10,000 expressed: 3936 |
| Claims recomputed from the paper's own tables and figure titles | agrees | 9 of 9 claims come back from the paper's own tables and figure titles |
| Text: the main claims on our run (test p < 0.0005, average test AUC 0.68, combined 3 orders better) | differs | 0 of 3 fields as printed |
| R package pdscox and its tutorial | agrees | R package pdscox: R CMD check OK; tests 17 passed, 0 failed, 0 skipped; tutorial rendering equals the committed TUTORIAL.md (figures by name) |
<!--/RESULTS-SUMMARY-->

The clinical side comes back: Table 1, Fig. 1's p-values and curves, the clinical model, Table 3's
genomic genes and NKI70. The pathway model does not: on our pathway scores the paper's 15 pathways
are much weaker, our model keeps 5 of them, and it does not carry to Desmedt. Adding clinical
features still helps on both sets the paper shows. Test set 2 (Ivshina) shares 232 of its 249
arrays with the training set.

## Kept local, not in the repository

`sources/` (the paper, its text, figure and supplement files, the downloaded data) and `work/`
(scratch runs) are git-ignored. The data are downloaded by
`figure-reproduction/pipeline/fetch_inputs.sh`.
