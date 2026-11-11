# PMC1274252: Speeding disease gene discovery by sequence based candidate prioritization (Adie et al. 2005)

Adie EA, Adams RR, Evans KL, Porteous DJ, Pickard BS. Speeding disease gene discovery by sequence based
candidate prioritization. *BMC Bioinformatics* 6:55 (2005).
[doi:10.1186/1471-2105-6-55](https://doi.org/10.1186/1471-2105-6-55) ·
[PMC1274252](https://pmc.ncbi.nlm.nih.gov/articles/PMC1274252/) · issue #49

The paper is © 2005 Adie et al., licensee BioMed Central, under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). This folder does not contain the paper or its full
text; `figure-reproduction/published/` holds its four figures (the authors' original files that BMC serves as
additional files 2 to 5, and BMC's 1200-pixel rendering of the Figure 2 EPS) for comparison, redistributed
under CC BY 2.0 with the attribution above.

PROSPECTR scored genes with a 15-rule alternating decision tree built in Weka. Its Perl scorer
(`classifier.pl`, `adtrees.pm`) and its web site (genetics.med.ed.ac.uk/prospectr) are gone; the Wayback
Machine kept the training and test sets as Weka ARFF files, the download page with the Weka command, and a
genome-wide score dump. The archived sets are a 2006 version of the paper's sets: 1,080 + 1,080, 713 + 713 and
50 + 50 genes (the paper: 1,084 + 1,084, 675 + 675 and 54 + 54), 64 features from a later Ensembl build (Table 1
lists 23), and no gene IDs. We ran the paper's own tree (Figure 2, complete with every threshold and value) on
them, reran the download page's recipe in Weka 3.4.3, and ported Weka's ADTree to Python, checked to the last
bit against Weka.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: downloads, Weka 3.4.3, the port check, Tables 2-4, Figs 1-3 against the paper, the claims. |
| [`package/`](package/) | `prospectr_adtree`, the method as an installable Python package (the published tree as a scorer, Weka 3.4's ADTree), with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC1274252/>

## Results

<!-- summary from results.json (check_results.py); the full table: python3 figure-reproduction/pipeline/check_results.py results.json --markdown -->

35 results: 6 agree, 15 partly agree, 1 inconclusive, 6 differ, 7 not attempted; 1 open cause.

| Result | Verdict | Ours against the paper |
| --- | --- | --- |
| Table 3, the published tree on the archived sets | partly | Training: accuracy 67.2% (67%), AUC 0.744 (0.75), kappa 0.34 (0.35), recall 80% (77%). HGMD: 63.0% (64.5%), AUC 0.693 (0.69). Oligogenic: 67% (65%), AUC 0.767 (0.76); 39 disease genes found and 22 controls called disease, the text's counts, but of 50 + 50 genes, not 54 + 54 |
| Table 3, 10-fold cross-validation (retrained) | differs | 66.6% (63%), AUC 0.740 (0.70), kappa 0.33 (0.27): the archived features separate the classes better |
| Table 3, the tree retrained with the download page's recipe | differs or partly | Training 70.7% (67%), HGMD 64.2% (64.5%), oligogenic 70% (65%) |
| Fig. 2, the tree | partly | Retrained, the first rules are mouse identity (37.5 against 41.082; 1.031 / -0.13 against 0.827 / -0.163), signal peptide, gene length (996.5, printed 997) and exons > 32, as in the paper; the other 11 rules differ (6 of 59 fields) |
| Fig. 3, ROC curves | A agrees, B inconclusive, C partly | A: 92.6% of pixels within 2 px both ways (best control 76%). B: close, but the retrained tree's curve is as close. C: same hull, points on a 50-gene grid |
| Table 4, feature shares | partly | 5 of 11 at printed precision, 9 of 11 if truncated; paralog identity is empty in the archived files |
| Table 2 and Fig. 1, disease against control genes | partly | Every significant difference is significant; disease medians come back (gene length 27 k, exons 10, mouse identity 87%, signal peptide 36% against 35%); 54 of 119 histogram bars as printed |
| Text claims on our run | differs or partly | Spearman 0.70 and 0.39 (0.71, 0.35); 10 and 20 rules worse than 15 on AUC, 10 rules not on accuracy; length-only tree 84% / 58% (69% / 51%, open) |
| The authors' genome-wide dump | differs | 2 genes over 0.75 (97), 5,155 under 0.3 (4,357): another model than Figure 2 |
| Claims against the paper's own numbers | agrees | 52 of 58 follow. Slips: 36/97 is 37%, not ~33%; 29/219 is 13.2%, not 13.4%; the abstract's "twenty-fold" is the conclusion's 25-fold (Fig. 4 at the top 4%); the Lopez-Bigas kappas do not follow from the stated rates; "Euler's constant" is e |
| Port and Weka versions | agrees | `prospectr_adtree` gives Weka 3.4.3's trees, scores, folds and statistics exactly; Weka 3.4.1-3.4.4 build the same tree |
| Fig. 4, artificial loci, Lopez-Bigas, mutation types, Additional File 1, Table 1 | not attempted | No gene IDs, positions, HGMD records or genome-wide features survive; Table 1 is a feature list |

The main claim holds on the surviving data: the published tree separates disease genes from controls about as
well as Table 3 says, and its training-set ROC curve lies on the published one. The differences come from the
archived sets, a 2006 version of the paper's with other genes and features; the paper's slips are in its
arithmetic, not its method.

Kept local and gitignored: `sources/` (the paper, its figures and supplement, the archived files), `work/`
(downloads, Weka runs, Slurm and Nextflow logs, scratch) and `.venv/`.
