# PMC3098087: Class prediction for high-dimensional class-imbalanced data (Blagus and Lusa 2010)

Blagus R, Lusa L. Class prediction for high-dimensional class-imbalanced data. *BMC Bioinformatics*
11:523 (2010). [doi:10.1186/1471-2105-11-523](https://doi.org/10.1186/1471-2105-11-523) ·
[PMC3098087](https://pmc.ncbi.nlm.nih.gov/articles/PMC3098087/) · issue #69

The paper is © 2010 Blagus and Lusa, licensee BioMed Central, under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). This folder does not contain the paper, its
full text or its supplements (Additional files 1-14). `figure-reproduction/published/` holds the
paper's figures and the supplement figures we compare against, rasterized from the published PDFs and
redistributed under CC BY 2.0 with the attribution above. The plotted values and printed table cells
are in `figure-reproduction/output/published_values.json`, read from the PDFs by
`pipeline/extract_published.py`. The breast cancer data (Sotiriou et al. 2003, NCI BRB data archive)
are downloaded by the pipeline and not kept here.

The paper studies classifiers trained on class-imbalanced, high-dimensional data: nine classifiers
(1-, 3- and 5-NN, DLDA, DQDA, random forest, linear SVM, PAM, penalized logistic regression), t-test
selection of 40 variables, and three corrections (over-sampling, down-sizing and multiple
down-sizing, MultDS), on simulated data (1,000 replicates per setting) and on the Sotiriou breast
cancer data (ER status, 500 random splits per design). It ran in R 2.8.1 and released no code. We
rebuilt the classifiers, corrections, measures and simulation design from the text as the R package
[`package/`](package/) (`multds`), reran 462 simulation settings and 60 breast cancer designs, and
compared every plotted point of Figs 1-6 and of Additional files 4-12, and every printed cell of
Additional files 1, 3, 13 and 14.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the downloads, the published values read from the vector figures and tables, the simulation and the breast cancer analysis, the comparison, our figures on the published frames, the claims, the checks. |
| [`package/`](package/) | `multds`, the method as an installable R package, with example data, tests and a [rendered tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC3098087/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
<!--/RESULTS-SUMMARY-->

<!--CLAIMS-LINE-->
The paper's conclusions hold in our run: the classifiers are biased towards the majority class,
variable selection adds to the bias, over-sampling hardly helps, and down-sizing and above all
multiple down-sizing remove most of it, on the simulations and on the breast cancer data alike. The
gaps are the SVM (no cost given; no single cost and class weighting fits all its results), PAM near
balance, the p = 40 panels of Fig. 3 (computed without the stated sample centring), the over-sampling
details, and a few prediction-interval tails; each has a tested cause in
[`figure-reproduction/README.md`](figure-reproduction/README.md).
<!--/CLAIMS-LINE-->

## Install the package

```r
remotes::install_github("jeonglab-bcm/fossil/PMC3098087/package")
```

## Run

From the repository root, with R 4.3 and the packages of `package/DESCRIPTION` (Ubuntu 24.04:
`bash PMC3098087/figure-reproduction/pipeline/install_r_deps.sh`), Python 3.12, Java 21 and
Nextflow:

```bash
R CMD INSTALL PMC3098087/package
pip install -r PMC3098087/figure-reproduction/requirements.txt
nextflow run PMC3098087/figure-reproduction/main.nf --outdir results
```

The default run reruns the first 3 replicates of every setting and design from their seeds and
builds everything else from the committed summary of all replicates (about 15 minutes); `--full`
reruns every replicate (about 4 hours on 4 cores). See
[`figure-reproduction/README.md`](figure-reproduction/README.md).
