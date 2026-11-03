# PMC3322362 — RPISeq, RNA-protein interaction prediction from sequence (Muppirala et al. 2011)

Muppirala UK, Honavar VG, Dobbs D. Predicting RNA-protein interactions using only sequence
information. *BMC Bioinformatics* 12:489 (2011).
[doi:10.1186/1471-2105-12-489](https://doi.org/10.1186/1471-2105-12-489) ·
[PMC3322362](https://pmc.ncbi.nlm.nih.gov/articles/PMC3322362/)

The paper is © 2011 Muppirala et al., licensee BioMed Central, published under CC BY 2.0. In
keeping with the rest of this repository, this folder does not contain the paper or its
Additional Files. `figure-reproduction/published/` holds Figs 1 and 2 of the paper for
comparison, under CC BY 2.0 with the attribution above. The paper ships no code; the RPISeq web
server it names no longer answers.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | RPISeq's features and its two classifiers, rebuilt in scikit-learn from the paper's Methods text, rerun on RPI2241 and RPI369. Table 1 and Fig. 1 rebuilt, with Fig. 1 drawn on the published pixel grid and compared curve by curve; the SEN1 and U6 hubs of Fig. 2 tested; the arithmetic of Tables 2 and 3 checked. Nextflow pipeline. |

Kept local and gitignored: `sources/` (the paper, Additional Files 1 to 3, the figure files and
the downloaded datasets), `rpiseq-paper/` (an agent-readable copy of the paper built with the
paper2agent skill) and `paper-review/` (its review and verification records).
