# PMC1523355: Multivariable risk prediction and the power of subgroup analysis (Hayward et al. 2006)

Hayward RA, Kent DM, Vijan S, Hofer TP. Multivariable risk prediction can greatly enhance the statistical
power of clinical trial subgroup analysis. *BMC Medical Research Methodology* 6:18 (2006).
[doi:10.1186/1471-2288-6-18](https://doi.org/10.1186/1471-2288-6-18) ·
[PMC1523355](https://pmc.ncbi.nlm.nih.gov/articles/PMC1523355/) · issue #77

The paper is © 2006 Hayward et al., licensee BioMed Central, under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). This folder does not contain the paper or its full
text; `figure-reproduction/published/figure-1.jpg` is its one figure (the JPEG PMC serves) for comparison,
redistributed under CC BY 2.0 with the attribution above. The printed numbers of Tables 1-5 are in
`figure-reproduction/output/published_values.json`, read from the article XML by `extract_published.py`;
Fig. 1B's 16 numbers are transcribed from the figure.

The paper simulates clinical trials of 8,800 people in which a treatment halves the 5-year risk of an
outcome but adds 3 serious complications per 1,000 treated per year, so low-risk people are harmed. It
compares the power of a conventional subgroup analysis (one risk factor at a time) with a risk-stratified
analysis (a score of several risk factors) to detect that the net benefit varies, by a logistic regression
with a treatment-by-subgroup interaction over 2,000 simulated trials per setting. No code was released and
none survives. We rebuilt the simulation from the text as the Python package [`package/`](package/)
(`stratpower`), reran every setting at 20,000 trials, and compared every printed value of Tables 1-5 and
Fig. 1.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: every simulated setting, the comparison with every printed value, Fig. 1A on the published axes and Fig. 1B's values written into its cells, the claims, the checks. |
| [`package/`](package/) | `stratpower`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure panel, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC1523355/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
4 exact, 4 agrees, 9 partly, 2 differs, 2 not attempted; 10 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Fig. 1A, net RRR against pre-treatment risk | agrees | 100.00% within 2 px (pass 95.0%, best control 70.3%) |
| Fig. 1B, power and AUROC of one RF and of a 4-RF score at four average CERs | partly | 9 of 16 fields as printed |
| Table 1, shares, CER, RRR and NNT of the subgroups | partly | 15 of 36 fields as printed |
| Table 1, power of the conventional and the two risk-index analyses, and the index's AUROC | agrees | 4 of 4 fields as printed |
| Table 2, power of one RF at three ORs and three prevalences | partly | 5 of 9 fields as printed |
| Table 3, power and AUROC of scores of 1, 3 and 6 RFs at three ORs | partly | 7 of 18 fields as printed |
| Table 4, AUROC and power of a 6-RF score under four weightings | partly | 1 of 8 fields as printed |
| Table 5, power of conventional and risk-stratified analysis at 1 to 4 complications per 1,000 patient-years | partly | 2 of 8 fields as printed |
| Table 6, glossary | not attempted | not attempted |
| Results: net harm below a 3% pre-treatment risk; a steep gain from 2% to 5% | exact | 2 of 2 fields as printed |
| Methods: N = 8,800 gives 80% power to detect an RRR of 25% | differs | 0 of 1 fields as printed |
| Results: the 4-RF score beats one RF, and power falls as the population's CER rises | exact | 3 of 3 fields as printed |
| Results: OR 2 at 50% against 25% prevalence (.22 against .21); OR 3 at 50%, 44% | partly | 2 of 4 fields as printed |
| Results: 3 RFs of 1.5 give an AUROC of 0.55; a score always beats one RF | partly | 1 of 2 fields as printed |
| Results: perfect to reverse weighting, 82% to 69%; one RF of 2.5 alone, 37% | partly | 1 of 3 fields as printed |
| Results: power rises with the rate of treatment complications | exact | 2 of 2 fields as printed |
| Abstract: conventional analysis has at best 30% to 45% power, even for a RF of OR 3 | differs | 0 of 1 fields as printed |
| Main claim: a multivariable risk-stratified analysis has much more power than conventional subgroup analysis | exact | 2 of 2 fields as printed |
| Claims recomputed from the paper's own tables and Fig. 1A's formula | agrees | 18 of 18 statements follow from the paper's own tables and Fig. 1A's formula. Table 1's RRR and NNT recomputed from its own CER column with Fig. 1A's formula: 2 of 9 rows come back; not: rf_absent RRR -.19 against -0.182, NNT -239 against -250; rf_present RRR .13 against 0.143, NNT 183 against 167; k0 RRR -1.59 against -1.500, NNT -88 against -89; k1 RRR -.51 against -0.500, NNT -132 against -133; k2 RRR -.02 against 0.000, NNT -1936 against infinite; k3 RRR .21 against 0.250, NNT 83 against 67; k_ge4 RRR .35 against 0.383, NNT 24 against 20 |
| The authors' simulation code | not attempted | not attempted |
| Python package stratpower and its tutorial | agrees | stratpower 0.1.0: wheel installed in a fresh environment and imported from it; tests 5 passed; tutorial 7 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

"Within tolerance" for a simulated power means within half a printed unit plus three combined Monte Carlo
standard errors of the paper's estimate (2,000 trials) and ours (20,000 trials), a rule fixed before the
comparison. Two runs of ours with different seeds agree with each other in every power under it.

The main claim holds: in every setting the risk-stratified analysis has far more power than the
conventional one. The claims that do not match come from one open cause: where the heterogeneity in net
benefit is large, most of our powers are higher than the paper's, and no reading of the paper we tested closes the gap.

Kept local, not committed (git-ignored): `PMC1523355/sources/` (the article XML and figure as downloaded,
the text conversion) and `PMC1523355/.venv/`.
