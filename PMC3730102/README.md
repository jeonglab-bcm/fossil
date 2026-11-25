# PMC3730102: Proteome-wide discovery of mislocated proteins in cancer (Lee et al. 2013)

Lee K, Byun K, Hong W, Chuang HY, Pack CG, Bayarsaikhan E, Paek SH, Kim H, Shin HY, Ideker T, Lee B.
Proteome-wide discovery of mislocated proteins in cancer. *Genome Research* 23(8):1283–1294 (2013).
[doi:10.1101/gr.155499.113](https://doi.org/10.1101/gr.155499.113),
[PMC3730102](https://pmc.ncbi.nlm.nih.gov/articles/PMC3730102/), issue
[jeonglab-bcm/fossil#92](https://github.com/jeonglab-bcm/fossil/issues/92).

The paper is © 2013, Published by Cold Spring Harbor Laboratory Press, and available after six months under
CC BY-NC 3.0. This folder does not contain the paper, its full text or its supplement;
`figure-reproduction/published/` holds crops of its computed panels for comparison, with that notice.

CoLP (conditional location predictor) scores how possible each of 13 subcellular locations is for a protein,
from its sequence, motifs and GO terms, its interaction neighbours, and how coherently the neighbours are
expressed in a condition (normal brain, low- and high-grade glioma). Proteins whose most possible location
changes in glioma are called mislocations. The CoLP web server (nbm.ajou.ac.kr/colp) is gone and its code was
never released; the Genome Research supplement (Tables S1 and S2, the calibration and the mislocation test) sits
behind a Cloudflare challenge and could not be fetched. We rebuilt the method from this paper and the DC-kNN
paper it reuses (Lee et al. 2008, NAR, PMC2582614) as the Python package [`package/`](package/) (`condloc`) and
reran it on archived data: GO 2007-01, the Pathway Commons 2011 archive, Ramani et al. 2005, and five GEO series.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: inputs, Table 1, the leave-two-out DC-kNN of Fig. 2, the conditional location maps, mislocations and named proteins of Figs 3 to 6, and the check against the committed outputs. |
| [`package/`](package/) | `condloc`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and number of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC3730102/>

## Results

<!-- summary and table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-SUMMARY-->
7 agrees, 8 partly, 11 differs, 9 not attempted; 19 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Table 1A, static protein features | not attempted | not attempted |
| Table 1B, gold-standard locations from GO | partly | 2 of 15 fields as printed |
| Table 1C, pooled interaction network | differs | 0 of 2 fields as printed |
| Table 1D, expression samples | agrees | 3 of 3 fields as printed |
| Fig. 1 | not attempted | not attempted |
| Fig. 2A, location sharing by expression correlation | agrees | 4 of 4 fields as printed |
| Fig. 2B, AUC of static and network features | partly | 1 of 5 fields as printed |
| Fig. 2C, known links among the most correlated pairs | differs | 0 of 2 fields as printed |
| Fig. 2D, average AUC by kind of feature | partly | 1 of 6 fields as printed |
| Fig. 2E, selected feature sets | agrees | 2 of 2 fields as printed |
| High-confidence locations (text) | differs | 0 of 4 fields as printed |
| Fig. 3A, NKX2-2 location map | differs | 0 of 3 fields as printed |
| Fig. 3E, CPB1 location map | differs | 0 of 3 fields as printed |
| Fig. 4A, KIF13A location map | differs | 0 of 3 fields as printed |
| Fig. 5B, RNF138 location map | partly | 1 of 3 fields as printed |
| Fig. 5C, TLX3 location map | partly | 1 of 3 fields as printed |
| Fig. 6A, GFRA4 location map | partly | 1 of 3 fields as printed |
| Fig. 6B, PSPN location map | partly | 2 of 3 fields as printed |
| Fig. 6C, RET location map | agrees | 3 of 3 fields as printed |
| SMAD4 location map (text, Suppl. Fig. S6A) | agrees | 3 of 3 fields as printed |
| Figs 3B-D and 3F-H | not attempted | not attempted |
| Figs 4B-D | not attempted | not attempted |
| Figs 5D-I | not attempted | not attempted |
| Figs 6A-C images, 6D-G | not attempted | not attempted |
| Fig. 7 | not attempted | not attempted |
| Figs 3I and 3J, 100 location tests of 20 proteins | differs | 0 of 5 fields as printed |
| Mislocated proteins (text) | differs | 0 of 1 fields as printed |
| Fig. 5A, kinds of mislocation | differs | 0 of 7 fields as printed |
| Figs 4E-G, KIF13A neighbourhood | differs | 0 of 3 fields as printed |
| Blinded candidate test, 10 proteins (text) | partly | 3 of 10 fields as printed |
| 15 validated mislocations (text) | differs | 0 of 15 fields as printed |
| The paper's own numbers against each other | agrees | Table 1B counts sum to 5,252; the Fig. 3I cells read from the figure give Fig. 3J's 20, 8, 2 and 70 (90 of 100); each Fig. 5A share is a whole number of the 157 mislocations (34, 25, 19, 10, 9, 6, 5) |
| Random and permuted-expression controls (Suppl. Figs S12, S13, S35) | not attempted | not attempted |
| Supplemental Tables S1 and S2 (all predictions, 157 mislocations) | not attempted | not attempted |
| Python package condloc and its tutorial | agrees | condloc 0.1.0: wheel installed in a fresh environment and imported from it; tests 7 passed; tutorial 6 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

The static part of the method holds: interacting proteins that are co-expressed share a location most often,
and network features predict GO locations about as well as the paper says. The condition-specific part does
not come back: our maps move few proteins between normal brain and glioma, and none of the 15 validated
mislocations. The causes are the settings the unavailable supplement holds (the possibility calibration and the
mislocation test) and a rebuilt gold standard and network.

## What is kept local

`sources/` (the paper, its figure files, Lee et al. 2008's supplement and every downloaded input) and `work/`
(scratch runs) are git-ignored. `figure-reproduction/pipeline/fetch_inputs.sh` downloads every input again.

## Install the package

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3730102/package"
```
