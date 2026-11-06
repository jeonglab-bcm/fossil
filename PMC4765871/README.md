# PMC4765871: Reconstructing gene regulatory dynamics from high-dimensional single-cell snapshot data (Ocone et al. 2015)

Ocone A, Haghverdi L, Mueller NS, Theis FJ. Reconstructing gene regulatory dynamics from
high-dimensional single-cell snapshot data. *Bioinformatics* 31(12):i89–i96 (2015).
[doi:10.1093/bioinformatics/btv257](https://doi.org/10.1093/bioinformatics/btv257) ·
[PMC4765871](https://pmc.ncbi.nlm.nih.gov/articles/PMC4765871/)

The paper is © The Author 2015, published by Oxford University Press under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). In keeping with the rest of this
repository, this folder does not contain the paper, its supplement or their full text.
`figure-reproduction/published/figure-*.png` are the paper's Figures 1 to 9, rendered from its PDF
at 600 dpi for comparison only, and redistributed non-commercially under CC BY-NC 4.0 with the
attribution above. A few numbers of the supplement are transcribed in
`figure-reproduction/pipeline/params/` with their source.

The haematopoietic data are Supplementary Table 3 of Moignard et al., *Nat. Cell Biol.* 15:363
(2013), [doi:10.1038/ncb2709](https://doi.org/10.1038/ncb2709). The pipeline downloads them and
checks their SHA-256; they are not redistributed.

The authors' code (C++ and Matlab, `inferenceSnapshot.zip`) is lost. The framework is rebuilt here
from the paper: diffusion maps, branch clustering, Wanderlust, GENIE3, Hill ODE models with AND and
OR gates, Metropolis MCMC, thermodynamic integration and AIC/BIC.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The rebuilt framework, the FFL and toggle switch simulations, the haematopoietic analysis, every figure redrawn on the published pixel grid and scored, and the Nextflow pipeline. |
| [`results.json`](results.json) | Every figure panel, table and claim of the paper, with our numbers, the verdicts computed from them and the cause of each mismatch. |
| [`session/`](session/) | The record of the session that made this reproduction. |

<!-- RESULTS -->

Kept local and gitignored: `sources/` (the paper, its supplement and their text), `work/`
(downloads, scratch runs and Slurm logs) and `.venv/` (the Python environment).
