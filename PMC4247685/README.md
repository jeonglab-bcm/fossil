# PMC4247685 — GABi, generalized subspace pattern mining (Curry 2014)

Curry EWJ. A framework for generalized subspace pattern mining in high-dimensional datasets.
*BMC Bioinformatics* 15:355 (2014). [doi:10.1186/s12859-014-0355-5](https://doi.org/10.1186/s12859-014-0355-5) ·
[PMC4247685](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4247685/)

The paper is © 2014 Curry, licensee BioMed Central, published under CC BY 4.0. In keeping with the rest of
this repository, this folder does not contain the paper, its supplements, or the authors' R package (GABi
0.1, GPL ≥ 2, archived on CRAN). `figure-reproduction/published/` holds Figs 2–5 of the paper for
comparison, under CC BY 4.0 with the attribution above.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | Figs 2–5 rebuilt and compared with the published versions pixel by pixel. Fig. 5 uses the paper's own data; Figs 3–4 are reconstructed from public TCGA data; Fig. 2 reruns the synthetic benchmark. Nextflow pipeline. |
| [`gabi-implementation-analysis/`](gabi-implementation-analysis/) | What GABi 0.1 and the S1 model code compute, and how they differ from the paper. 77 executable checks. |

Kept local and gitignored: `sources/` (the paper, Additional files 1–3, the GABi and biclust tarballs),
`gabi-paper/` (an agent-readable copy of the paper built with the paper2agent skill) and `paper-review/`
(its review and verification records).
