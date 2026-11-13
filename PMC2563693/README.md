# PMC2563693: Inferring pathway activity toward precise disease classification (Lee et al. 2008)

Lee E, Chuang HY, Kim JW, Ideker T, Lee D. Inferring pathway activity toward precise disease
classification. *PLoS Computational Biology* 4(11):e1000217 (2008).
[doi:10.1371/journal.pcbi.1000217](https://doi.org/10.1371/journal.pcbi.1000217) ·
[PMC2563693](https://pmc.ncbi.nlm.nih.gov/articles/PMC2563693/) · issue #47

The paper is © 2008 Lee et al., under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
This folder does not contain the paper, its full text or its supplements; `figure-reproduction/published/`
holds its four figures (the PNGs PLOS serves), Table 1 as an image, and Figs S1, S2, S3 and S5
rasterized from the supplementary PDFs, for comparison, redistributed under CC BY 4.0 with the
attribution above.

The paper scores each pathway of MSigDB v1.0 C2 by the combined z-score of its
"condition-responsive genes" (CORGs), the subset of its genes whose combined expression best
separates two classes of patients, and classifies patients with these pathway activities. The
authors' software is lost: no link, no availability statement and no code in the supplement. We
rebuilt the method from the Methods as the Python package [`package/`](package/) (`pacorg`),
rebuilt the seven datasets from GEO, Bioconductor and the Broad Institute's GSEA site, and reran
every computed result: the marker comparisons of Fig. 2, the 100 runs of 5-fold cross-validation
behind Figs 3, S2 and S3 and the marker frequencies of Tables 1 and S2, the CORG lists of Tables 1
and S2, the marker overlaps of Fig. S1 and the CORG counts of Fig. S5.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline, the committed outputs (with the full cross-validation run), the published figures and the comparison of every figure, table and claim. |
| [`package/`](package/) | `pacorg`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC2563693/>

## Results

<!-- summary from results.json (check_results.py); the full table: python3 figure-reproduction/pipeline/check_results.py results.json --markdown -->

52 results: 4 exact, 7 agree, 33 partly agree, 5 differ, 3 not attempted; 35 open causes.

| Result | Verdict | Ours against the paper |
| --- | --- | --- |
| Table 1, CORG lists and sizes | exact | All 18 CORG lists and all 18 "CORGs / members" counts, from the GSEA lung files (e.g. Glycolysis: ENO2 PGK1 ALDOA) |
| Table 1, frequencies | partly | Michigan to Boston: the paper's eight pathways are our eight most used, in its order but for one swap, used more often; Boston to Michigan: seven of ten pathways are outside Boston's Tian top 52 |
| Fig. 2, lung source and Michigan to Boston (E, F) | partly | 36 of 38 readable points within 0.1 (e.g. PAC 6.68 against 6.7 at 1%) |
| Fig. 2, breast and Boston panels | partly | The source panels keep the paper's order of curves; 5 to 14 of 17 to 20 points within 0.1 |
| Fig. 3, AUC bars | partly | 23 of 42 within datasets and 5 of 8 across within 0.02 (Breast Netherlands PAC 0.677 against 0.676) |
| Fig. 3, -log(p) labels | differs | None to its decimal; Breast Netherlands 19.2 against 16.9 |
| PAC beats Gene (text) | partly | 4 of 7 datasets and 2 of 4 transfers as in the paper |
| Table S1, class sizes | partly | 12 of 14; GEO's clinical table gives Breast USA 107 / 179, the paper 106 / 180 |
| Table S2, breast CORGs | partly | 3 of 15 lists exact; the breast preprocessing is not stated |
| Fig. 4, glycolysis and estrogen signalling | exact | Higher in poor prognosis in both lung datasets |
| Figs S1, S2, S3, S5 (vector values) | partly | A third to 77% of the values within tolerance per panel (S2's naive Bayes and LDA panels: under a third); S5 medians in 5 of 7 datasets |
| Other claims of the text | 4 agree, 3 partly | PAC above its CORGs and PAC_all, genes above CORGs, the trend with other classifiers and the CORG sizes hold; PAC above PAC_random fails in two datasets and Mean, Median and PCA above PAC_random in four, because our random sets run the CORG search (explained); PAC above Genes in Fig. 2 holds in 5 of 8 panels |
| Package, reruns and the paper's own arithmetic | agrees | pacorg's tests and tutorial; 22 cross-validation repeats rerun equal the committed run |
| Fig. 1, Fig. S4, the authors' code | not attempted | A schematic; a heatmap without values; the code is lost |

The main claim, that classifiers on CORG-based pathway activity beat classifiers on genes, holds in Breast Netherlands, Lung Michigan, Lung Boston and Michigan to Boston, with Leukemia and Netherlands to USA showing no PAC advantage as in the paper. It does not hold in our NF-kB, Prostate, Breast USA, USA to Netherlands and Boston to Michigan runs. Our breast and NF-kB data are not the authors' (open); Boston's pathway pre-selection differs (open; in a sensitivity run without it, PAC is above Gene from Boston to Michigan, 0.71 against 0.62, the paper's PAC being 0.66); Prostate's gap (Gene 0.961 against PAC 0.955) has no tested cause beyond the unstated classifier settings.

The rest stays buried: the authors' processed breast and NF-kB matrices, how they pre-selected Boston's
pathways, and how they computed the CORG overlap of Fig. S1 (each tested and open; see
[`results.json`](results.json)).

Kept local and gitignored: `sources/` (the paper, its supplements and figures, the downloaded
datasets and annotation files, the Chuang et al. 2007 supplement), `work/` (scratch runs, Slurm
logs, cross-validation repeats, the R library and conda environment), and `.venv/`.
