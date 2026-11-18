# PMC3730102 figure reproduction

Reproduction of the computed results of Lee et al. 2013, *Genome Research* 23:1283 (CoLP). The method is
the package [`../package`](../package) (`condloc`), implemented from this paper and from Lee et al. 2008
(NAR 36:e136), because the authors' server is gone and no code was released.

## Results

<!-- the table from ../results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-TABLE-->
7 agrees, 8 partly, 11 differs, 9 not attempted; 19 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1A, static protein features | not attempted | not attempted | Lists the sources of the single-protein features; nothing to recompute. |
| Table 1B, gold-standard locations from GO | partly | 2 of 15 fields as printed | The GO release is not stated, and the six experimental codes the Methods name cannot give 4,570 proteins in any release up to 2008. The 4,570 proteins are those of Lee et al. 2008 (Table S3), which come back only from a 2007 release with all non-IEA codes. Mapping 2007 accessions onto current Swiss-Prot then loses about 330 proteins (merged and deleted entries). |
| Table 1C, pooled interaction network | differs | 0 of 2 fields as printed | BIND is gone (only its 1,500 links inside Ramani's set survive) and DIP needs a login; the release dates of the other sources are not stated. The rebuilt network is 4% larger in links and 4% smaller in proteins. |
| Table 1D, expression samples | agrees | 3 of 3 fields as printed | Assumed: GEO series and sample selection for the three conditions (GSE5281 and GSE5390 controls; GSE3185 and GSE9885 low-grade; GSE3185, GSE9885 and GSE4271 high-grade) |
| Fig. 1 | not attempted | not attempted | A diagram of the method. |
| Fig. 2A, location sharing by expression correlation | agrees | 4 of 4 fields as printed | Assumed: Gold standard from the GO release of 2007-01-01 with every evidence code except IEA |
| Fig. 2B, AUC of static and network features | partly | 1 of 5 fields as printed | The four configurations come back in the paper's order, 0.03 to 0.08 lower; the gaps between them differ (ours 0.02, 0.02 and 0.08 against the paper's 0.04, 0.05 and 0.07). The gold standard (4,269 against 4,570 proteins) and the network are rebuilt, and how leave-two-out was run is not stated. |
| Fig. 2C, known links among the most correlated pairs | differs | 0 of 2 fields as printed | In normal brain the top 1,000 correlated pairs hold 21 times more known links than chance, as in the paper; in low- and high-grade glioma only 2 times. How the paper pooled several studies of different platforms into one ranking is not stated; our gliomas pool three series on five platforms, two of them small. |
| Fig. 2D, average AUC by kind of feature | partly | 1 of 6 fields as printed | S comes back at 0.63. The network kinds are 0.02 to 0.03 higher (our network and gold standard are rebuilt) and the selected models (TR) are 0.07 lower. |
| Fig. 2E, selected feature sets | agrees | 2 of 2 fields as printed | Assumed: Gold standard from the GO release of 2007-01-01 with every evidence code except IEA |
| High-confidence locations (text) | differs | 0 of 4 fields as printed | The possibility formula, applied as printed, puts the median possibility at 0.39, so 'possibility 0.40' cannot also mean P < 0.005 as the paper says. Calling locations by P < 0.005 instead gives under half the paper's locations (13,362 against 29,999) and just over half its proteins (5,091 against 9,543). The calibration (Suppl. Fig. S5) is in the unavailable supplement. |
| Fig. 3A, NKX2-2 location map | differs | 0 of 3 fields as printed | The top location of each condition comes from the whole rebuilt chain (gold standard, network, feature sets, coherence weights). Static locations come back more often than condition changes: our condition weights move few maps. |
| Fig. 3E, CPB1 location map | differs | 0 of 3 fields as printed | The top location of each condition comes from the whole rebuilt chain (gold standard, network, feature sets, coherence weights). Static locations come back more often than condition changes: our condition weights move few maps. |
| Fig. 4A, KIF13A location map | differs | 0 of 3 fields as printed | The top location of each condition comes from the whole rebuilt chain (gold standard, network, feature sets, coherence weights). Static locations come back more often than condition changes: our condition weights move few maps. |
| Fig. 5B, RNF138 location map | partly | 1 of 3 fields as printed | The top location of each condition comes from the whole rebuilt chain (gold standard, network, feature sets, coherence weights). Static locations come back more often than condition changes: our condition weights move few maps. |
| Fig. 5C, TLX3 location map | partly | 1 of 3 fields as printed | The top location of each condition comes from the whole rebuilt chain (gold standard, network, feature sets, coherence weights). Static locations come back more often than condition changes: our condition weights move few maps. |
| Fig. 6A, GFRA4 location map | partly | 1 of 3 fields as printed | The top location of each condition comes from the whole rebuilt chain (gold standard, network, feature sets, coherence weights). Static locations come back more often than condition changes: our condition weights move few maps. |
| Fig. 6B, PSPN location map | partly | 2 of 3 fields as printed | The top location of each condition comes from the whole rebuilt chain (gold standard, network, feature sets, coherence weights). Static locations come back more often than condition changes: our condition weights move few maps. |
| Fig. 6C, RET location map | agrees | 3 of 3 fields as printed | The top location of each condition comes from the whole rebuilt chain (gold standard, network, feature sets, coherence weights). Static locations come back more often than condition changes: our condition weights move few maps. |
| SMAD4 location map (text, Suppl. Fig. S6A) | agrees | 3 of 3 fields as printed | The top location of each condition comes from the whole rebuilt chain (gold standard, network, feature sets, coherence weights). Static locations come back more often than condition changes: our condition weights move few maps. |
| Figs 3B-D and 3F-H | not attempted | not attempted | Confocal imaging, Western blots, cell counts and the other wet-lab results cannot be regenerated; their observations are used only as labels. |
| Figs 4B-D | not attempted | not attempted | Confocal imaging, Western blots, cell counts and the other wet-lab results cannot be regenerated; their observations are used only as labels. |
| Figs 5D-I | not attempted | not attempted | Confocal imaging, Western blots, cell counts and the other wet-lab results cannot be regenerated; their observations are used only as labels. |
| Figs 6A-C images, 6D-G | not attempted | not attempted | Confocal imaging, Western blots, cell counts and the other wet-lab results cannot be regenerated; their observations are used only as labels. |
| Fig. 7 | not attempted | not attempted | Confocal imaging, Western blots, cell counts and the other wet-lab results cannot be regenerated; their observations are used only as labels. |
| Figs 3I and 3J, 100 location tests of 20 proteins | differs | 0 of 5 fields as printed | Our maps call fewer locations than the paper's (8 of the 28 observed against 20), so true positives fall and false negatives rise; the true negatives come back. |
| Mislocated proteins (text) | differs | 0 of 1 fields as printed | The test behind 'P < 0.01' (Suppl. Fig. S15) is in the unavailable supplement. No version of the rule we tried gives 157. |
| Fig. 5A, kinds of mislocation | differs | 0 of 7 fields as printed | Our mislocations are few and spread over many kinds; the paper's are dominated by moves into and out of the ER, which our maps rarely make. |
| Figs 4E-G, KIF13A neighbourhood | differs | 0 of 3 fields as printed | KIF13A has 6 links in our network and none to COG2; its AP1G1 link is less coherent in normal brain than in glioma, the reverse of the figure. |
| Blinded candidate test, 10 proteins (text) | partly | 3 of 10 fields as printed | Three of the five proteins predicted stable come back stable in the same location; none of the five predicted mislocations comes back. |
| 15 validated mislocations (text) | differs | 0 of 15 fields as printed | The top location of each condition comes from the whole rebuilt chain (gold standard, network, feature sets, coherence weights). Static locations come back more often than condition changes: our condition weights move few maps. |
| The paper's own numbers against each other | agrees | Table 1B counts sum to 5,252; the Fig. 3I cells read from the figure give Fig. 3J's 20, 8, 2 and 70 (90 of 100); each Fig. 5A share is a whole number of the 157 mislocations (34, 25, 19, 10, 9, 6, 5) |  |
| Random and permuted-expression controls (Suppl. Figs S12, S13, S35) | not attempted | not attempted | The supplementary figures with the numbers, and the permutation scheme, are in the Genome Research supplement, which could not be fetched; our maps do not reproduce the 15 validated mislocations to begin with. |
| Supplemental Tables S1 and S2 (all predictions, 157 mislocations) | not attempted | not attempted | The tables are on genome.cshlp.org only, behind a Cloudflare challenge; the CoLP server that also served them is gone. |
| Python package condloc and its tutorial | agrees | condloc 0.1.0: wheel installed in a fresh environment and imported from it; tests 7 passed; tutorial 6 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |
<!--/RESULTS-TABLE-->

The static part of the method holds: interacting proteins that are co-expressed share a location most often,
and network features predict GO locations about as well as the paper says. The condition-specific part does
not come back: our maps move few proteins between normal brain and glioma, and none of the 15 validated
mislocations. The causes are the settings the unavailable supplement holds (the possibility calibration and the
mislocation test) and a rebuilt gold standard and network.

## What the code does against the paper

| Step | Paper | Here |
| --- | --- | --- |
| Gold standard | GO cellular component via AmiGO, six experimental codes, 13 locations, 4,570 proteins (Table 1B). Release not stated. | The 4,570 proteins are Lee et al. 2008's (its Table S3 has the same count). The six codes give 1,248 to 1,512 proteins in every 2007 and early 2008 release; GO 2007-01-01 with every code but IEA gives 4,597 before mapping. Mapped onto current Swiss-Prot: 4,269. The search over 21 releases and five code sets is in [`search/gold_standard_search.json`](search/gold_standard_search.json) (a one-off record, not part of the pipeline). |
| Network | HPRD, BIND, Reactome, DIP, Rual, Stelzl, Ewing, Ramani: 80,970 links, 10,819 proteins. | HPRD and Reactome complexes (Pathway Commons 2011 archive), Rual, Stelzl and Ewing (BioGRID 2011, by PubMed ID), Ramani 2005 without orthology-only links. BIND is gone and DIP needs a login. 84,309 links, 10,351 proteins. |
| Expression | 82 normal, 23 low-grade, 134 high-grade samples from five cited studies; no accessions. | GSE5281 and GSE5390 controls; GSE3185 and GSE9885 low-grade tumours; GSE3185, GSE9885 (tumour channel) and GSE4271 high-grade. 82, 23 and 134. log2, kNN imputation under 30% missing, quantile normalisation, probe average. |
| Features | 29 sets: 9 single-protein, N and L up to distance 2 (Lee et al. 2008). | As in Lee et al. 2008: AA, dAA, gAA, cHPo, cHPi, cSCM (lags 1 to 40), pAA, InterPro, GO function and process; N1, N2, L1, L2 with w = 1/(Psi + rho), rho = 2. InterPro from current UniProt. |
| Classifier | DC-kNN, forward selection on AUC, leave-two-out cross-validation. | k = 5, Euclidean distance, mu_l = [(1/k) sum n_ml phi_m]^(1/sqrt M); leave-two-out as two random halves (one selects, the other reports, both ways). |
| Conditions | Coherence Phi = -log2 Psi[min(med)/MEDIAN r] weights the network features. | Psi is the upper-tail share of links; the weights multiply the path weights, scaled to a median of 1; studies averaged by sample count. |
| Possibility and calls | P_l(c) from the gold-standard distributions; high confidence at P >= 0.40, said to be P < 0.005. | The formula as printed puts the median possibility at 0.39, so we call a location high-confidence when its confidence is above 99.5% of the gold-standard negatives (P < 0.005). Both counts are in `output/clm.json`. |
| Mislocation | P < 0.01 between normal brain and glioma (Suppl. Fig. S15). | The top location changes between normal brain and both gliomas, and the new one is high-confidence in both gliomas but not in normal brain. Three other versions are counted in `output/clm.json`. |

Fig. 3I's observed locations (+ and -) were read cell by cell from the figure; the reading gives the paper's
own Fig. 3J counts (20, 8, 2 and 70).

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. |
| `requirements.txt` | Pinned Python packages. |
| `results_notes.json` | Labels, the paper's values, sources, assumptions, causes and the page prose (written by hand). |
| `pipeline/fetch_inputs.sh` | Downloads every input and checks its SHA-256. |
| `pipeline/settings.py` | Every setting, with where it comes from. |
| `pipeline/prepare.py` | Gold standard, network and expression (Table 1). |
| `pipeline/train.py` | Feature sets, leave-two-out DC-kNN, Fig. 2. |
| `pipeline/conditional.py` | Location maps per condition, high-confidence calls, Fig. 3I/J, mislocations, Fig. 5A, the named proteins. |
| `pipeline/figures.py` | Our panels and their overlays on the published ones. |
| `pipeline/build_results.py`, `check_results.py` | `../results.json` and its verdicts. |
| `pipeline/build_page.py`, `page_template.html` | The results page. |
| `pipeline/check_reproduction.py`, `compare_runs.py`, `check_package.py` | The check step. |
| `pipeline/update_readmes.py` | Writes the results tables of the READMEs. |
| `published/` | The published panels, cropped, with the licence note. |
| `output/` | What the pipeline writes: `prepare.json`, `fig2.json`, `model.json`, `clm.json`, `figures.json`, `fig*_ours.png`, `fig*_overlay.png`. |
| `search/` | The one-off search for the gold standard's GO release. |

## Run

From the repository root:

```bash
pip install -r PMC3730102/figure-reproduction/requirements.txt
```

```bash
nextflow run PMC3730102/figure-reproduction/main.nf --outdir results
```

About 15 minutes on 4 cores. `--sources DIR` reuses local copies of the inputs. CI runs the same command
(`.github/workflows/reproduce-pmc3730102.yml`) on every pull request that touches this paper.

## Pipeline steps

1. `FETCH`: download the inputs, check SHA-256.
2. `PREPARE`: Table 1B to 1D.
3. `TRAIN`: the 29 feature sets, leave-two-out, Figs 2A to 2E, the models chosen on the whole gold standard.
4. `CONDITIONAL`: coherence per condition, location maps, calls and mislocations.
5. `FIGURES`: our panels and overlays.
6. `PACKAGE`: `check_package.py` on `../package`.
7. `RESULTS`: `results.json`, verdicts by `check_results.py`.
8. `PAGE`: the results page and `report.md`.
9. `CHECK`: `check_results.py`, verdicts against the committed `../results.json`, and `compare_runs.py` against `output/`.

## Limits

- UniProt has no download pinned by release. The pipeline takes the current human Swiss-Prot entries, checks
  them against release 2026_04, and reports a new release as a warning; when one comes, the check step will
  flag any number that moves. InterPro motifs and gene mappings come from that release, not from 2012.
- The GO release, the evidence codes, the network sources' versions and the expression accessions are found,
  not given; each is an assumption in `../results.json`.
- How leave-two-out was run, the possibility calibration, the test for mislocations and the permutation scheme
  are in the supplement we could not fetch. Our choices are listed above and in `pipeline/settings.py`.
- The wet-lab panels (Figs 3B to 3D, 3F to 3H, 4B to 4D, 5D to 5I, 6D to 6G and 7) cannot be regenerated.
