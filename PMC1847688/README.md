# PMC1847688 — LIMPIC, peak detection in MALDI-TOF spectra (Mantini et al. 2007)

Mantini D, Petrucci F, Pieragostino D, Del Boccio P, Di Nicola M, Di Ilio C, Federici G,
Sacchetta P, Comani S, Urbani A. LIMPIC: a computational method for the separation of protein
MALDI-TOF-MS signals from noise. *BMC Bioinformatics* 8:101 (2007).
[doi:10.1186/1471-2105-8-101](https://doi.org/10.1186/1471-2105-8-101) ·
[PMC1847688](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1847688/)

The paper is © 2007 Mantini et al., licensee BioMed Central, published under CC BY 2.0. In
keeping with the rest of this repository, this folder does not contain the paper, its
Additional Files or the authors' MATLAB code (LIMPIC 1.1, GPL v2). `figure-reproduction/published/`
holds Figs 1 to 10 of the paper for comparison, under CC BY 2.0 with the attribution above.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | LIMPIC 1.1 ported to Python and checked against the authors' code in GNU Octave. Figs 2, 3, 4c, 6a to 6d, 7 (LIMPIC) and 8 rebuilt from the paper's spectra and compared with the published figures pixel by pixel; Fig. 5's LIMPIC baseline and Figs 9a and 9b from Additional File 4. LIMPIC's rows of Tables 1 to 3 recomputed. Nextflow pipeline. |

Kept local and gitignored: `sources/` (the paper, Additional Files 1 to 5, the original figure
TIFFs), `limpic-paper/` (an agent-readable copy of the paper built with the paper2agent skill),
`paper-review/` (its review and verification records) and `staging/` (its draft build).
