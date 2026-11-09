# PMC2711306 — Geometric de-noising of protein-protein interaction networks (Kuchaiev et al. 2009)

Kuchaiev O, Rašajski M, Higham DJ, Pržulj N. Geometric de-noising of protein-protein interaction
networks. *PLoS Computational Biology* 5(8):e1000454 (2009).
[doi:10.1371/journal.pcbi.1000454](https://doi.org/10.1371/journal.pcbi.1000454) ·
[PMC2711306](https://pmc.ncbi.nlm.nih.gov/articles/PMC2711306/)

The paper is © 2009 Kuchaiev et al., published under
[CC BY](https://creativecommons.org/licenses/by/4.0/). In keeping with the rest of this repository,
this folder does not contain the paper, its full text or its supplement files.
`figure-reproduction/published/figure-*.png` are the paper's Figures 1–5 and S1–S3, converted to
PNG from the original TIFF files, and are redistributed under CC BY with the attribution above.

The issue that set this reproduction up (#17) said the software was lost. It was not: the
authors' three Matlab functions (`embed_novi.m`, `assign_scores.m`, `EM.m`, "free for
non-commercial purposes") are on the Wayback Machine at kuchaev.com/Denoising. So are Collins et
al.'s purification-enrichment (PE) scores for all 401,820 yeast pairs, at
interactome-cmp.ucsf.edu (2010). That file is the yeast test data the issue thought needed a
manual download from a 403 page. Neither is redistributed here. The pipeline downloads both and
checks their SHA-256.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | Figures 1–5 and S1–S3 redrawn on the published pixel grids with negative controls, Tables S1–S6 and the claims in the text, the port check against the authors' Matlab under GNU Octave. Nextflow pipeline. |
| [`package/`](package/) | `geodenoise`, the method as a Python package, with example data, tests and an executed [tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and number of the paper, with our values and the verdict computed from them. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Install the method: `pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC2711306/package"`.

## Results

<!--RESULTS-->

## Claims in the text

<!--CLAIMS-->

Kept local and gitignored: `sources/` (the paper, its supplement, the authors' code, downloads),
`work/` (scratch runs and Slurm logs), `.venv/` and `.octave/` (the Python and Octave environments).
