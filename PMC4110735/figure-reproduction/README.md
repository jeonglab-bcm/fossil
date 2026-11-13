# PMC4110735 figure reproduction

Roy S, Bhattacharyya DK, Kalita JK. Reconstruction of gene co-expression network from microarray data using
local expression patterns. *BMC Bioinformatics* 15(Suppl 7):S10 (2014).
[doi:10.1186/1471-2105-15-S7-S10](https://doi.org/10.1186/1471-2105-15-S7-S10). CC BY 2.0.

The published figures in `published/` are the paper's (CC BY 2.0, attribution above), the publisher's original
1200-pixel JPEGs. Nothing else of the paper is in this folder. GeneNetWeaver (MIT) is not copied either: the
pipeline downloads its network file archive and reads the kinetic parameters from it; `pipeline/gnw_sim.py` is
our port of its simulation, written from its source. Downloaded data (DREAM4, GEO, the yeast matrices, GO) stay
in the run's work folder.

## Results

<!-- generated from ../results.json by check_results.py --markdown -->
<!--RESULTS-->

28 results. 5 exact, 10 agrees, 5 partly, 6 differs, 2 not attempted; 8 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Fig. 1, shifting and scaling patterns | not attempted | not attempted | A sketch of two kinds of pattern; it plots no data. |
| Fig. 2, inverted profiles of Mrps26 and Pfn2 (GDS3702) | agrees | 92.92% within 2 px (pass 90.0%, best control 85.3%) | Assumed: Line width 5 px and marker size 20 px (presentation) |
| Fig. 3, mixed patterns of YBL002W, YBL003C and YBL006W (yeast) | agrees | 96.26% within 2 px (pass 90.0%, best control 75.4%) | Assumed: The data are Cheng and Church's yeast matrix (ref. 25, yeast.matrix and yeast.genes), whose rows match the figure value for value; the figure's YBL006W is the matrix's YBL006C; Line width 2 px and marker size 16 px (presentation) |
| Fig. 4a, AUPR bars against Table 2 | agrees | 51 of 51 fields as printed | Assumed: Bar heights read off the published panel (axes fitted to the frame and tick marks; one pixel is 0.0015) |
| Fig. 4b, AUROC bars against Table 2 | agrees | 50 of 50 fields as printed, 1 paper errors | Assumed: Bar heights read off the published panel (one pixel is 0.0013) |
| Fig. 4c, F0.5 bars against Table 2 | agrees | 51 of 51 fields as printed | Assumed: Bar heights read off the published panel (one pixel is 0.0015) |
| Fig. 5, run time of GeCON and ARACNE | agrees | 6 of 6 fields as printed | Assumed: The six sizes (250, 1000, 1500, 2000, 2585, 3000 genes) read off the figure's markers |
| Fig. 6, networks, profiles and heat maps of selected modules | not attempted | not attempted | Pictures of selected modules from the real datasets; the paper does not say which modules, which theta, or how a module was cut from the network, and gives no module's gene list except three GDS3702 modules in the text. |
| Fig. 7, the worked example drawn | agrees | 95.36% within 2 px (pass 90.0%, best control 25.5%) | Assumed: Line width 3 px (presentation) |
| Fig. 7 and Eq. (5): G = {343, 314, 409} becomes {138, -1; 52, 1} | exact | 4 of 4 fields as printed |  |
| Table 1, the 13 in silico networks and their sizes | exact | 13 of 13 fields as printed |  |
| Table 2, AUPR of GeCON, ARACNE, CLR and MRNET on D1 to D13 | differs | 0 of 52 fields as printed | GeCON as the paper describes it ranks pairs no better than chance on these data (mean AUPR 0.203, the share of true pairs is 0.203; mean AUROC 0.485), while minet's methods reach AUPR 0.275 to 0.291 and AUROC 0.535 to 0.61. At theta 0.5 and tau 20 it connects 84% to 100% of all pairs, because on positive values almost every edge angle of Eq. (5) sits near 45 or 135 degrees. No variant we tried brings GeCON's mean scores near the paper's (best mean AUPR 0.255 against 0.633); the few single cells that fall within printed precision are not counted as agreement. The comparators' values differ too, so the authors' simulations and scoring cannot be recovered. |
| Table 2, AUROC | partly | 1 of 52 fields as printed | GeCON as the paper describes it ranks pairs no better than chance on these data (mean AUPR 0.203, the share of true pairs is 0.203; mean AUROC 0.485), while minet's methods reach AUPR 0.275 to 0.291 and AUROC 0.535 to 0.61. At theta 0.5 and tau 20 it connects 84% to 100% of all pairs, because on positive values almost every edge angle of Eq. (5) sits near 45 or 135 degrees. No variant we tried brings GeCON's mean scores near the paper's (best mean AUPR 0.255 against 0.633); the few single cells that fall within printed precision are not counted as agreement. The comparators' values differ too, so the authors' simulations and scoring cannot be recovered. |
| Table 2, F0.5 | differs | 0 of 52 fields as printed | GeCON as the paper describes it ranks pairs no better than chance on these data (mean AUPR 0.203, the share of true pairs is 0.203; mean AUROC 0.485), while minet's methods reach AUPR 0.275 to 0.291 and AUROC 0.535 to 0.61. At theta 0.5 and tau 20 it connects 84% to 100% of all pairs, because on positive values almost every edge angle of Eq. (5) sits near 45 or 135 degrees. No variant we tried brings GeCON's mean scores near the paper's (best mean AUPR 0.255 against 0.633); the few single cells that fall within printed precision are not counted as agreement. The comparators' values differ too, so the authors' simulations and scoring cannot be recovered. |
| Table 3, gene and sample counts of the real datasets | partly | 4 of 7 fields as printed | The public files have 17 conditions for Yeast KY and the cell cycle set, not 18, and GEO's GDS825 has 4 samples, not 8. The sporulation file (TLS failure from our runner, no reachable archive) and the 517-gene Arabidopsis matrix could not be obtained, so they have no field. The subset sizes of GDS958 and GDS3702 are our filter's. |
| Table 4, GO terms of selected modules (GeneMANIA) | partly | 4 of 10 fields as printed | Terms not found in our modules: GeneMANIA's and FuncAssociate's 2014 annotations and the authors' modules are gone, and our module cut and filters are guesses. Rows of Sporulation, Thaliana are left out: the sporulation file failed TLS verification from our runner and no archive was reachable, and the 517 x 13 Arabidopsis matrix was not located. |
| Table 5, GO terms of selected modules (FuncAssociate) | partly | 3 of 7 fields as printed | Terms not found in our modules: GeneMANIA's and FuncAssociate's 2014 annotations and the authors' modules are gone, and our module cut and filters are guesses. Rows of GDS825, Sporulation are left out: GEO's GDS825 has 4 samples, not the paper's 8, and the sporulation file could not be fetched. |
| Claims recomputed from the paper's own Table 2 | agrees | Average row: 7 of 12 exact, 12 within one unit in the last digit; improvements from the row means: 4 of 9 exact, 9 within one unit (from the printed averages 0 of 9). The table itself has GeCON best in 38 of 39 dataset-score cells (not: D13 AUROC), against "in all cases". "More than 200 times better" in AUPR is 3.7 times (269.72%). |  |
| "GeCON outperforms all other algorithms ... on all three scores" (Fig. 4, Table 2) | differs | 0 of 3 fields as printed | GeCON as the paper describes it ranks pairs no better than chance on these data (mean AUPR 0.203, the share of true pairs is 0.203; mean AUROC 0.485), while minet's methods reach AUPR 0.275 to 0.291 and AUROC 0.535 to 0.61. At theta 0.5 and tau 20 it connects 84% to 100% of all pairs, because on positive values almost every edge angle of Eq. (5) sits near 45 or 135 degrees. No variant we tried brings GeCON's mean scores near the paper's (best mean AUPR 0.255 against 0.633); the few single cells that fall within printed precision are not counted as agreement. The comparators' values differ too, so the authors' simulations and scoring cannot be recovered. |
| Average improvement of GeCON over ARACNE, CLR and MRNET (Table 2, last row) | differs | 0 of 9 fields as printed | GeCON as the paper describes it ranks pairs no better than chance on these data (mean AUPR 0.203, the share of true pairs is 0.203; mean AUROC 0.485), while minet's methods reach AUPR 0.275 to 0.291 and AUROC 0.535 to 0.61. At theta 0.5 and tau 20 it connects 84% to 100% of all pairs, because on positive values almost every edge angle of Eq. (5) sits near 45 or 135 degrees. No variant we tried brings GeCON's mean scores near the paper's (best mean AUPR 0.255 against 0.633); the few single cells that fall within printed precision are not counted as agreement. The comparators' values differ too, so the authors' simulations and scoring cannot be recovered. |
| D6: AUPR .84, AUROC .78, F .86 | differs | 0 of 3 fields as printed | GeCON as the paper describes it ranks pairs no better than chance on these data (mean AUPR 0.203, the share of true pairs is 0.203; mean AUROC 0.485), while minet's methods reach AUPR 0.275 to 0.291 and AUROC 0.535 to 0.61. At theta 0.5 and tau 20 it connects 84% to 100% of all pairs, because on positive values almost every edge angle of Eq. (5) sits near 45 or 135 degrees. No variant we tried brings GeCON's mean scores near the paper's (best mean AUPR 0.255 against 0.633); the few single cells that fall within printed precision are not counted as agreement. The comparators' values differ too, so the authors' simulations and scoring cannot be recovered. |
| Mrps26 and Pfn2 "clearly show negative behaviour" (Fig. 2) | exact | 1 of 1 fields as printed |  |
| YBL002W and YBL003C co-regulated, YBL006W inverted (Fig. 3) | partly | 1 of 2 fields as printed | Over all 16 steps GeCON finds YBL006W positively, not negatively, related to the other two (positive support 0.69, negative 0.31); the inversion the text describes holds only at some steps, which the paper calls mixed regulation in the same paragraph. |
| "GeCON is much faster than ARACNE" (Fig. 5) | exact | 1 of 1 fields as printed |  |
| GeCON "is insensitive to normalization of data" (Methods, advantage iv) | differs | 0 of 1 fields as printed | Eq. (5) applies atan2 to the two raw values, so the angle depends on their ratio, not their difference. On Yeast KY's log values (around 7) almost every angle sits near 45 or 135 degrees and GeCON connects all 27,966 pairs; on the site's normalised version of the same genes it connects 1,226 (tau 20, theta 0.6). 97% of the log data's angles lie within 5 degrees of 45 or 135. |
| "GeCON can extract functionally enriched network modules from real expression data" | exact | 3 of 3 fields as printed |  |
| Python port of GeneNetWeaver's simulation against the DREAM4 release | agrees | All 10 DREAM4 networks: gold standards from the network files equal the released ones; the port's wild-type steady state tracks the released wild type with log correlation 0.95 to 0.99 |  |
| Python package gecon and its tutorial | agrees | gecon 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |

The paper's main claim does not hold on our run. GeCON, built as the paper describes it, ranks gene pairs no better than chance on the DREAM data, and the best of ARACNE, CLR and MRNET beats it on 12 of 13 datasets in every score. The likely reason is in Eq. (5): on positive data almost every edge angle sits near 45 or 135 degrees, so almost every pair is connected. Why the paper's scores are so much higher is open.

<!--/RESULTS-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| Eqs. (4) and (5): regulation and angle of each edge | `gecon.edge_patterns`; ties (O_{k-1} = O_k), which Eq. (4) leaves out, count as up. Fig. 7's example gives 137.5 and 52.5 degrees, printed 138 and 52. |
| Eqs. (6) to (9): positive and negative similarity and support | `gecon.supports`. Eq. (7) is printed as \|180 − a_i + a_j\| < τ but the text says to subtract 180 from the sum; we use \|a_i + a_j − 180\| < τ and test the printed form as a variant. |
| Eqs. (10) and (11): strongly connected pairs and the sign | `gecon.network`; a connected pair where neither support alone exceeds θ (unstated) takes the sign of the larger. |
| θ "above 50% of the edges", τ "15 to 25" | θ = 0.5 and τ = 20 for Table 2; τ 15 and 25 as variants. θ = 0.8 for the real-data modules (at 0.7 the 12-sample GEO sets form one giant component; `enrich.json`, `theta_largest_module`). |
| The DREAM datasets, "generated based on" GNW | D9 to D13: the DREAM4 release (Bioconductor DREAM4 1.30.0). D1 to D8: `gnw_sim.py`, the DREAM4 time-series protocol on the DREAM3 network files, 5 series of 21 points for size 10 and 10 for size 50. |
| ARACNE, CLR and MRNET "with the parameters as used in [28]" | minet 3.60.0, `minet(estimator = "spearman", disc = "none")`, its defaults. |
| AUPR, AUROC and F0.5 | One scorer for every method (`gecon.score_network`): undirected pairs, trapezoidal areas, the largest F0.5 over thresholds. GeCON is ranked by its total support. |
| Fig. 5, Java GeCON and Java ARACNE | The `gecon` package (Python) and minet's ARACNE (C++ via R), on random matrices of 50 time points. |
| Tables 4 and 5, GeneMANIA and FuncAssociate | A hypergeometric test with Benjamini-Hochberg Q on GO (release 2026-08-05), per module; a module is a connected component of 5 or more genes. |

## The benchmark

GeCON at the paper's settings connects 84% to 100% of all gene pairs on the 13 datasets. Eq. (5) takes the
arctangent of the two values themselves, so for positive values of similar size every up edge sits near 45
degrees and every down edge near 135 (97% of Yeast KY's log-value angles lie within 5 degrees of one of them); almost every edge then matches either positively or negatively.
Ranked by its supports, GeCON scores like a random ranking (mean AUPR 0.203 against a chance level of 0.203).
`output/dream.json` keeps every variant we tried (log2 inputs at τ 5, 10 and 20; τ 15 and 25; the printed Eq. (7);
binary scoring; no series split; directed scoring); none brings GeCON above all three minet methods on more than 4 of
the 13 datasets in AUPR or F0.5, or more than 5 in AUROC (log2 inputs, τ 5). On the real datasets we standardised each gene first, which gives sparse networks
(`output/normalisation.json`).

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. |
| `requirements.txt`, `pipeline/install_r.R` | Pinned Python packages; minet from Bioconductor 3.18 (R 4.3.3). |
| `paper_values.json` | The paper's printed values (Tables 1 to 5, the text), typed once. |
| `results_notes.json` | Labels, assumptions, causes and the page's prose, written by hand; merged with the run into `../results.json`. |
| `inputs.json` | Every input with its URL and SHA-256. |
| `results.json` | The repository's results check (`tools/check_results.py`): our value for every compared number. |
| `pipeline/` | `fetch_inputs.sh`; `gnw_sim.py` and `gnw_check.py` (the GNW port and its check); `dream_data.py`, `dream_eval.py`, `minet_run.R` (Table 2); `figscore.py`, `profile_figures.py` (Figs 2, 3, 7), `fig4_bars.py`, `timing.py`, `timing.R`, `fig5_plot.py`; `enrichment.py`, `real_data.py` (Tables 3 to 5); `claims.py`; `build_results.py`, `check_reproduction.py`, `build_page.py`, `page_template.html`; copies of the skill's `check_results.py`, `compare_runs.py`, `check_package.py`. |
| `published/` | The paper's seven figures (CC BY 2.0). |
| `output/dream/` | The 13 datasets as run (genes x conditions) and their gold standards. |
| `output/figures/` | `fig*_ours.png` (ours drawn on the published frame, the published trace removed), `fig*_overlay.png` (cyan: paper only, red: ours only, black: both), `fig4_run.png` (our run's scores in Fig. 4's layout). |
| `output/` | `dream.json`, `datasets.json`, `profiles.json`, `fig4.json`, `fig5.json`, `timing.json`, `enrich.json`, `table3.json`, `normalisation.json`, `port_check.json`, `claims.json`, `package.json`. |

## Run

```bash
pip install -r PMC4110735/figure-reproduction/requirements.txt
Rscript PMC4110735/figure-reproduction/pipeline/install_r.R
nextflow run PMC4110735/figure-reproduction/main.nf --outdir results            # about 15 minutes on 4 cores
nextflow run PMC4110735/figure-reproduction/main.nf --outdir results --timing   # + Fig. 5 timed again
```

The default run downloads the inputs (about 80 MB, SHA-256 checked), simulates D1 to D8 again, scores all four
methods on the 13 datasets, reads and redraws the figures, builds the real-data modules, checks the GNW port and
the package, and compares everything with the committed `output/`. The Fig. 5 run times come from the committed
`output/timing.json` unless `--timing` is given; times depend on the machine, so a `--timing` run reports them
and does not compare them. `.github/workflows/reproduce-pmc4110735.yml` runs the default on every change to this
folder, and `--timing` when started by hand with `timing = true`.

## Pipeline steps

1. `FETCH`: GNW's network file archive, the DREAM4 package, the yeast matrices, the GEO data sets and GO (SHA-256 checked).
2. `DREAM_DATA`, `MERGE_DATA`: the 13 datasets of Table 1, one task each.
3. `DREAM_EVAL`: GeCON and minet's ARACNE, CLR and MRNET on each, scored, with GeCON's variants.
4. `PROFILES`: Figs 2, 3 and 7 redrawn on the published pixels, scored with wrong-input and near-miss controls.
5. `FIG4`: Fig. 4's bar heights read against Table 2; Table 2 and our run drawn in its layout.
6. `TIMING`, `FIG5`: the run times (committed, or measured with `--timing`) placed on Fig. 5's axes.
7. `REAL_DATA`: Table 3 counts, the normalisation test, the modules and their GO enrichment.
8. `PORT_CHECK`: the GNW port against the 10 DREAM4 networks.
9. `CLAIMS`: the text's claims, from the paper's Table 2 and from our run.
10. `PACKAGE`: `check_package.py` on `../package`.
11. `RESULTS`: `results.json`, the check step (`report.md`) and the results page.

## Limits

- **The authors' DREAM data are lost.** D1 to D8 are our simulations of the DREAM3 networks; their challenge
  data sit behind a Synapse login and the paper says it generated its own. D9 to D13 are the DREAM4 release, which
  may or may not be what the paper used. GeCON loses to the minet methods on D9 to D13 too, so our simulation is not
  what separates our Table 2 from the paper's.
- **The comparators' scores differ from the paper's too** (mean gap 0.10 to 0.13, against 0.14 to 0.43 for GeCON); on
  the size 50 and 100 networks the paper's AUPR is at or below chance (0.02 to 0.11 against chance levels of 0.03 to
  0.13) and its AUROC is around chance (0.41 to 0.55). How the paper scored them
  is not stated.
- **The GNW port** uses Euler-Maruyama with step 0.1 instead of GNW's Milstein-Stratonovich with step 1, and
  NumPy's random numbers. Running the GeneNetWeaver jar was not possible in our session, so the port is checked
  against the DREAM4 release (gold standards identical, wild-type log correlation 0.95 to 0.99), not against a
  fresh GNW run.
- **Fig. 5** is re-measured with other implementations on another machine: only the ordering and the growth can be
  compared. The six sizes are read off the figure.
- **Tables 4 and 5** are compared in kind only. GeneMANIA's 2014 networks and FuncAssociate are gone; the paper does
  not give its gene filters, θ or how modules were cut. The sporulation file failed TLS verification from our
  runner and the Wayback Machine was unreachable; a GitHub runner may fetch it, but we did not use it. The 517 x 13
  Arabidopsis matrix was not found.
- **Fig. 6** is not attempted: the paper does not say which modules it shows.
