# PMC2853684: The power of protein interaction networks for associating genes with diseases (Navlakha and Kingsford 2010)

Navlakha S, Kingsford C. The power of protein interaction networks for associating genes with
diseases. *Bioinformatics* 26(8):1057-1063 (2010).
[doi:10.1093/bioinformatics/btq076](https://doi.org/10.1093/bioinformatics/btq076) ·
[PMC2853684](https://pmc.ncbi.nlm.nih.gov/articles/PMC2853684/) · issue #46

The paper is © The Author(s) 2010, published by Oxford University Press under
[CC BY-NC 2.5](https://creativecommons.org/licenses/by-nc/2.5). This folder does not contain the paper, its
supplement or their full text. `figure-reproduction/published/` holds its Figures 2-4 and Supplementary
Figures S1-S2, cut from the open-access PDFs at 300 dpi for comparison, redistributed for non-commercial use
under CC BY-NC 2.5 with the attribution above.

The paper compared seven network methods (and variants, 13 in all) for predicting gene-disease associations
from the HPRD and OPHID interaction networks and OMIM linkage intervals. The authors released their
predictions and networks on cbcb.umd.edu/DiseaseNet (gone; the Wayback Machine kept a 2010 copy) but not
their code. We rebuilt Neighborhood, Oti, the random walk (RW) and network propagation (Prop) from the paper
as the Python package [`package/`](package/) (`diseasenet`), ran MCL 14-137 for the MCL clusters, and with
them reproduced the authors' published scores on every candidate pair of both networks. The graph
summarization (GS) code is lost, so the GS and VI-Cut scores come from the authors' prediction files. From
these scores we recomputed every figure, table and number we could, and compared each with the values
the paper prints or draws (Figs 2 and 4 and Supp. Figs S1 and S2 are vector drawings in the PDFs, so their
plotted values can be read exactly).

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: downloads, the methods rerun, the consensus forest (Weka), the comparison with every value the paper prints or draws, renders, overlays and checks. |
| [`package/`](package/) | `diseasenet`, the methods as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC2853684/>

Kept local and git-ignored: `sources/` (the paper, supplement, data, prediction files, the authors' VI-Cut code,
Weka), `scratch/`, `work/` (Slurm runs), `.venv/` and `.mcl/`. The networks and prediction files are
downloaded at run time: HPRD is free for academic use only and the disease annotations derive from OMIM.

## Results

<!-- summary from results.json (check_results.py); the full table: python3 figure-reproduction/pipeline/check_results.py results.json --markdown -->

25 results: 2 exact, 11 agree, 6 partly agree, 0 differ, 6 not attempted; 6 open causes.

| Result | Verdict | Ours against the paper |
| --- | --- | --- |
| Methods rerun | agrees | 1,935,350 of 1,935,350 candidate-pair scores (Neighborhood, Oti, RW, Prop, MCL; HPRD and OPHID) equal the authors' files; 49,538 of 49,538 in the no-interval files |
| Sec. 2.1 counts | exact | 11 of 11 (8776 proteins, 35 820 interactions, 450 diseases, 1415 genes, 4.60, 1.46, 397, 7361, ...) |
| Fig. 2a | partly | All 224 coordinates the paper draws for the 13 single methods; our curves have 3 points the figure leaves out (GS1 and VI-CutS) |
| Fig. 2b | partly | All 132 drawn coordinates; the same 3 extra points |
| Fig. 2a consensus | partly | Weka forest near, not on, the 5 points (θ = 0.7: 14.4/70.2 against 13.2/66.1); all 5 Pareto optimal, as the paper says |
| Sec. 3.1 ranges | partly | 21 of 22 fields, with 3 more excepted as paper errors (ranges that are not the extremes of the paper's own Fig. 2a); VI-CutS mean precision 66.1 against 66.0 |
| Sec. 3.2 baselines | exact | 1.6/1.6 random; 100.0/1.2 all genes |
| Sec. 3.2 without intervals | partly | 11 of 12; random walks' highest recall 37.6 against 29.0 |
| Fig. 3 | agrees | All 20 row and column sums (318 diseases) |
| Sec. 3.3, Supp. Sec. 4 | agrees | 124, 144, 19 diseases; the same 14 and the same 19 named diseases; Fanconi anemia 100/69.2 |
| Fig. 4a, 4b | agrees | All 15 bar counts, 15 bar heights, 15 error bars and 10 legend values |
| Sec. 3.5 | agrees | 18.9, 7.6, 5.0, 3.1, 30.7%; 976 predictions; 19 (1.9%) wrong by all five |
| Supp. Fig. S1 | agrees | All 340 drawn coordinates on OPHID |
| Supp. Fig. S2 | agrees | All 30 bars, 20 legend values and the caption's "about 95%" |
| Supp. Table 1 | partly | 28 of 31 fields, with 4 more excepted as paper errors (decimal slips, e.g. Prop 0.12 printed for 0.0123); three RW values truncated in the last digit |
| GS and VI-Cut rerun, Table 1, Fig. 1, full HPRD, 189 out-of-interval genes | not attempted | Code or data not distributed; Table 1 and Fig. 1 are not results |
| Package | agrees | `diseasenet`: wheel, fresh install, 8 tests, executed tutorial |

"Agrees" rather than "exact" means a setting the paper does not give was found by matching: the threshold
grids, the homophily denominator and how Fig. 4 averages (see `figure-reproduction/README.md`).

The main findings of the paper hold: random walks are the most precise single methods, the consensus is Pareto
optimal, and homophilic diseases are predicted better. Three Sec. 3.1 ranges and four Supp. Table 1 scores are
slips in the paper; the consensus points differ because the forest's settings are not stated.
