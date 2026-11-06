# PMC4015815 — Distances between Top-n-gram and residue pairs for remote homology (Liu et al. 2014)

Liu B, Xu J, Zou Q, Xu R, Wang X, Chen Q. Using distances between Top-n-gram and residue pairs
for protein remote homology detection. *BMC Bioinformatics* 15(Suppl 2):S3 (2014).
[doi:10.1186/1471-2105-15-S2-S3](https://doi.org/10.1186/1471-2105-15-S2-S3) ·
[PMC4015815](https://pmc.ncbi.nlm.nih.gov/articles/PMC4015815/)

The paper is © 2014 Liu et al., licensee BioMed Central Ltd., published under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). In keeping with the rest of this
repository, this folder does not contain the paper or its full text.
`figure-reproduction/published/` holds Figures 3, 4 and 5 of the paper, as embedded in the PMC
open-access PDF, for comparison, under CC BY 2.0 with the attribution above.

The SCOP 1.53 benchmark (Liao and Noble), the Gist 2.3 source, the paper's PDF and, for the
profiles, the lab's Pse-in-One 2.0 (its 2016 nrdb90) and NCBI BLAST+ 2.17.0 are downloaded by
the pipeline and checked against SHA-256 sums; they are not redistributed here.
`figure-reproduction/pipeline/inputs/top1_nrdb90_i3.fasta.gz` holds our Top-1-gram sequences,
computed from them.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | Table 1 (SVM-DR and SVM-DT), Figures 3, 4 and 5 and the claims in the text, rerun on the SCOP 1.53 benchmark with a port of Gist 2.3 and regenerated PSI-BLAST profiles. Figures drawn on the published pixel grid. Nextflow pipeline. |
| [`results.json`](results.json) | Every figure, table and claim with its computed verdict (Paper2Repro schema). |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

## Results

Verdicts are computed by `check_results.py` from [`results.json`](results.json): 1 exact, 9 agree,
9 partly, 2 inconclusive, 3 differ, 3 not attempted; 6 open causes.

| Item | Status | Evidence |
| --- | --- | --- |
| Gist 2.3 port | Checked against Gist's own run | Gist's sample weights through our kernel give its training discriminants within 0.003 (4-digit rounding); retrained with its settings and seed, the objective comes within 1.6e-6. The sample was written by Gist 2.0. |
| Table 1, SVM-DR ROC | Same setup, identical at printed precision | 0.919 (ours 0.9189). Family 2.5.1.3: 0.844 (ours 0.8444). |
| Fig. 3, SVM-DR | Same setup | 9 of 10 points within 0.0005 ROC of the published markers; dMAX 20 is 0.9004 against 0.8991. Seed noise is 0.0002. 84.4% of the curve's ink within 2 px (pass mark 85%, best control 75.9%). |
| Figs 4B, 5C, 5D (SVM-DR weights, family 2.5.1.3) | Same setup | Heatmap: Spearman 0.9999 with the published cells, all 400 within 24 grey levels, maximum 78.1 (paper 78), (G,G) and (L,L) first and second. Bars: all 148 ends within 2 px in both panels, r = 0.9999 and 0.9997. |
| Table 1, ROC50 (both methods) | Not reproduced | Ours 0.497 (SVM-DR) and 0.673 (SVM-DT) against 0.715 and 0.800. Full ROC matches, so the ranking agrees; the paper's ROC50 is computed some other way than its one-line definition. Three readings tested; none is the paper's. |
| Table 1, SVM-DT ROC | Re-measured with regenerated profiles | 0.950 against 0.948. Profiles: PSI-BLAST against the lab's 2016 nrdb90 with settings from its 2017 code; the 2014 database is gone. |
| Fig. 3, SVM-DT | Re-measured | The curve rises to dMAX 20 and is flat after 100, as published, but sits 0.002 to 0.010 above the published points (with Pse-in-One's own rule for empty profile columns, from 0.007 below to 0.001 above). |
| Figs 4A, 5A, 5B (SVM-DT weights) | Re-measured, differ | (G,G) is first again but (L,L) sixth; heatmap Spearman 0.77 (the SVM-DR panel in its place: 0.74); bars r = 0.39 and 0.28. Everything after the profiles is the code that reproduces the SVM-DR panels. |
| Claims in the text | 6 of 11 hold or come back | Benchmark counts exact; the claims recomputed from the paper's own Table 1 come back; the plateau, the ladder, distance 0 being largest and SVM-DR having more positive (G,G) weights than SVM-DT hold. Partly: top pairs (SVM-DT), family 2.5.1.3 (SVM-DT 0.961 against 0.993), the comparisons with Monomer-dist (ROC50) and SVM-PDT-Profile (0.9502 against 0.950). Differs: the 4.1 / 10.4 point gain over the quoted SVM-Top-n-gram (our ROC50 is lower across the board; against our own position-independent baseline the gain is 4.0 ROC and 25.7 ROC50 points). |
| Two slips in the text | Paper errors | "Most of the distances between (G,G) show positive discriminative power": 90% of Fig. 5A's bars are negative (ours: 88%). Distance 0 is "always" largest: not in Fig. 5C, where distance 1 is (ours too). |
| Figs 1, 2 | Not applicable | A worked example and the algorithm's pseudocode. |
| Table 1, the other nine rows | Not applicable | Quoted from earlier papers. |

**Result:** the main claim holds. Counting residue pairs at each distance improves on a
position-independent baseline, and SVM-DR comes back as published, down to its discriminant
weights. Two causes explain the items that do not match: the paper's ROC50 is not the standard
one, and the SVM-DT profiles had to be regenerated from a later database.


Kept local and gitignored: `sources/` (the paper, the downloads), `work/` (PSI-BLAST runs, scratch
runs) and `.venv/` (the Python environment).
