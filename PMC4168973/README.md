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
<!--/RESULTS-SUMMARY-->

<!--STATUS-NOTE-->

## Kept local, not in the repository

`sources/` (the paper, its text, figure and supplement files, the downloaded data) and `work/`
(scratch runs) are git-ignored. The data are downloaded by
`figure-reproduction/pipeline/fetch_inputs.sh`.
