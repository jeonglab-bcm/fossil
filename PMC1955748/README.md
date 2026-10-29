# PMC1955748 — ASH, structure alignment and domain classification (Standley et al. 2007)

Standley DM, Toh H, Nakamura H. ASH structure alignment package: Sensitivity and selectivity in
domain classification. *BMC Bioinformatics* 8:116 (2007).
[doi:10.1186/1471-2105-8-116](https://doi.org/10.1186/1471-2105-8-116) ·
[PMC1955748](https://pmc.ncbi.nlm.nih.gov/articles/PMC1955748/)

The paper is © 2007 Standley et al., licensee BioMed Central, published under CC BY 2.0. In
keeping with the rest of this repository, this folder does not contain the paper or its
Additional Files. `figure-reproduction/af2_matrix.txt` (our transcription of Additional File 2)
and `figure-reproduction/output/af4_overlay.png` (drawn on Additional File 4) reuse the paper's
material under CC BY 2.0 with the attribution above.

| Folder | Content |
| --- | --- |
| [`ash-rebuild/`](ash-rebuild/) | ASH rewritten from the 2005 and 2007 papers (TM-align seeds in place of the lost Local ASH) and tested on Additional File 3: the paper's score formula gives the published scores at r = 0.977 from the published NER and SAS; our own alignments reach r = 0.80. Nextflow pipeline. |
| [`figure-reproduction/`](figure-reproduction/) | Why no figure or table can be redrawn (ASH and the test set are gone), and the checks the published files still allow: the training set against CATH 3.0.0 and SCOP 1.69, Additional File 3, Additional File 2 against BLOSUM62, AAindex2 and Additional File 4, and the paper's derived numbers. Nextflow pipeline. |

Kept local and gitignored: `sources/` (the paper, Additional Files 1 to 4, and our CSV copies of
Additional Files 2 and 3), `ash-paper/` (an agent-readable copy of the paper built with the
paper2agent skill), `paper-review/` (its review and verification records) and `staging/` (its
draft build).
