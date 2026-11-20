# PMC1523355 figure reproduction

Hayward RA, Kent DM, Vijan S, Hofer TP. Multivariable risk prediction can greatly enhance the statistical
power of clinical trial subgroup analysis. *BMC Medical Research Methodology* 6:18 (2006).
[doi:10.1186/1471-2288-6-18](https://doi.org/10.1186/1471-2288-6-18). CC BY 2.0.

`published/figure-1.jpg` is the paper's Fig. 1 (CC BY 2.0, attribution above), the JPEG PMC serves. Nothing
else of the paper is in this folder: the pipeline downloads the figure and the article XML and checks their
SHA-256. `output/published_values.json` holds the printed numbers of Tables 1-5, read from the XML by
`pipeline/extract_published.py`, and Fig. 1B's 16 numbers, transcribed from the figure (a table drawn as an
image).

## Results

<!-- full table from results.json (check_results.py --markdown); regenerate with pipeline/update_readmes.py -->

<!--RESULTS-TABLE-->
4 exact, 4 agrees, 9 partly, 2 differs, 2 not attempted; 10 open causes.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Fig. 1A, net RRR against pre-treatment risk | agrees | 100.00% within 2 px (pass 95.0%, best control 70.3%) | Assumed: The curve's CER range, 0.016 to 0.075, is read from the published curve's ends. |
| Fig. 1B, power and AUROC of one RF and of a 4-RF score at four average CERs | partly | 9 of 16 fields as printed | Where the paper's settings give much heterogeneity (larger ORs, the weighted indices of Table 4, Table 5's higher harm rates, Fig. 1B at 9%), our powers are higher than the paper's, by up to 13 points; elsewhere they agree. Our two runs agree with each other in 41 of 41 powers, so the gap is not our Monte Carlo error. None of the tested readings of the paper closes it; a finite simulated population, which the paper's 'drawing observations with replacement from a population' allows, would move each power by chance (SD 0.05 to 0.08 with 100,000 people, 0.16 to 0.25 with 8,800), but its size is not given. |
| Table 1, shares, CER, RRR and NNT of the subgroups | partly | 15 of 36 fields as printed | Table 1's subgroup shares follow from six independent RFs of prevalence 25%, but its CER, RRR and NNT columns follow neither from the odds scale (15 of 36 values), nor from the relative-risk scale (12 of 36), nor do its RRR and NNT follow from its own CER column with Fig. 1A's formula (4 of 18). The 0-1 and 2-or-more rows do follow from their printed CERs (1.4 and 4.4), which no population of the stated RFs gives. The columns read like rates realized in a finite simulated population, whose size and seed are not given. |
| Table 1, power of the conventional and the two risk-index analyses, and the index's AUROC | agrees | 4 of 4 fields as printed | Assumed: The AUROC of a risk index is that of the index for the 5-year outcome over both arms of the trial (control and treated people together), from the population. The paper says only 'from a logistic regression model'. Chosen after comparing with the control arm alone. |
| Table 2, power of one RF at three ORs and three prevalences | partly | 5 of 9 fields as printed | Where the paper's settings give much heterogeneity (larger ORs, the weighted indices of Table 4, Table 5's higher harm rates, Fig. 1B at 9%), our powers are higher than the paper's, by up to 13 points; elsewhere they agree. Our two runs agree with each other in 41 of 41 powers, so the gap is not our Monte Carlo error. None of the tested readings of the paper closes it; a finite simulated population, which the paper's 'drawing observations with replacement from a population' allows, would move each power by chance (SD 0.05 to 0.08 with 100,000 people, 0.16 to 0.25 with 8,800), but its size is not given. |
| Table 3, power and AUROC of scores of 1, 3 and 6 RFs at three ORs | partly | 7 of 18 fields as printed | Where the paper's settings give much heterogeneity (larger ORs, the weighted indices of Table 4, Table 5's higher harm rates, Fig. 1B at 9%), our powers are higher than the paper's, by up to 13 points; elsewhere they agree. Our two runs agree with each other in 41 of 41 powers, so the gap is not our Monte Carlo error. None of the tested readings of the paper closes it; a finite simulated population, which the paper's 'drawing observations with replacement from a population' allows, would move each power by chance (SD 0.05 to 0.08 with 100,000 people, 0.16 to 0.25 with 8,800), but its size is not given. |
| Table 4, AUROC and power of a 6-RF score under four weightings | partly | 1 of 8 fields as printed | Where the paper's settings give much heterogeneity (larger ORs, the weighted indices of Table 4, Table 5's higher harm rates, Fig. 1B at 9%), our powers are higher than the paper's, by up to 13 points; elsewhere they agree. Our two runs agree with each other in 41 of 41 powers, so the gap is not our Monte Carlo error. None of the tested readings of the paper closes it; a finite simulated population, which the paper's 'drawing observations with replacement from a population' allows, would move each power by chance (SD 0.05 to 0.08 with 100,000 people, 0.16 to 0.25 with 8,800), but its size is not given. |
| Table 5, power of conventional and risk-stratified analysis at 1 to 4 complications per 1,000 patient-years | partly | 2 of 8 fields as printed | Where the paper's settings give much heterogeneity (larger ORs, the weighted indices of Table 4, Table 5's higher harm rates, Fig. 1B at 9%), our powers are higher than the paper's, by up to 13 points; elsewhere they agree. Our two runs agree with each other in 41 of 41 powers, so the gap is not our Monte Carlo error. None of the tested readings of the paper closes it; a finite simulated population, which the paper's 'drawing observations with replacement from a population' allows, would move each power by chance (SD 0.05 to 0.08 with 100,000 people, 0.16 to 0.25 with 8,800), but its size is not given. |
| Table 6, glossary | not attempted | not attempted | Definitions of terms; nothing computed. |
| Results: net harm below a 3% pre-treatment risk; a steep gain from 2% to 5% | exact | 2 of 2 fields as printed |  |
| Methods: N = 8,800 gives 80% power to detect an RRR of 25% | differs | 0 of 1 fields as printed | The paper does not say at what control event rate N = 8,800 gives 80% power for an RRR of 25%. At the Table 1 population's average CER (2.73%) it gives 0.56; it reaches 80% at a CER of 4.8% (two-sided alpha .05, 4,400 per arm), so the claim holds for a trial whose control arm has about 5% events. |
| Results: the 4-RF score beats one RF, and power falls as the population's CER rises | exact | 3 of 3 fields as printed |  |
| Results: OR 2 at 50% against 25% prevalence (.22 against .21); OR 3 at 50%, 44% | partly | 2 of 4 fields as printed | Where the paper's settings give much heterogeneity (larger ORs, the weighted indices of Table 4, Table 5's higher harm rates, Fig. 1B at 9%), our powers are higher than the paper's, by up to 13 points; elsewhere they agree. Our two runs agree with each other in 41 of 41 powers, so the gap is not our Monte Carlo error. None of the tested readings of the paper closes it; a finite simulated population, which the paper's 'drawing observations with replacement from a population' allows, would move each power by chance (SD 0.05 to 0.08 with 100,000 people, 0.16 to 0.25 with 8,800), but its size is not given. |
| Results: 3 RFs of 1.5 give an AUROC of 0.55; a score always beats one RF | partly | 1 of 2 fields as printed | Where the paper's settings give much heterogeneity (larger ORs, the weighted indices of Table 4, Table 5's higher harm rates, Fig. 1B at 9%), our powers are higher than the paper's, by up to 13 points; elsewhere they agree. Our two runs agree with each other in 41 of 41 powers, so the gap is not our Monte Carlo error. None of the tested readings of the paper closes it; a finite simulated population, which the paper's 'drawing observations with replacement from a population' allows, would move each power by chance (SD 0.05 to 0.08 with 100,000 people, 0.16 to 0.25 with 8,800), but its size is not given. |
| Results: perfect to reverse weighting, 82% to 69%; one RF of 2.5 alone, 37% | partly | 1 of 3 fields as printed | Where the paper's settings give much heterogeneity (larger ORs, the weighted indices of Table 4, Table 5's higher harm rates, Fig. 1B at 9%), our powers are higher than the paper's, by up to 13 points; elsewhere they agree. Our two runs agree with each other in 41 of 41 powers, so the gap is not our Monte Carlo error. None of the tested readings of the paper closes it; a finite simulated population, which the paper's 'drawing observations with replacement from a population' allows, would move each power by chance (SD 0.05 to 0.08 with 100,000 people, 0.16 to 0.25 with 8,800), but its size is not given. |
| Results: power rises with the rate of treatment complications | exact | 2 of 2 fields as printed |  |
| Abstract: conventional analysis has at best 30% to 45% power, even for a RF of OR 3 | differs | 0 of 1 fields as printed | Where the paper's settings give much heterogeneity (larger ORs, the weighted indices of Table 4, Table 5's higher harm rates, Fig. 1B at 9%), our powers are higher than the paper's, by up to 13 points; elsewhere they agree. Our two runs agree with each other in 41 of 41 powers, so the gap is not our Monte Carlo error. None of the tested readings of the paper closes it; a finite simulated population, which the paper's 'drawing observations with replacement from a population' allows, would move each power by chance (SD 0.05 to 0.08 with 100,000 people, 0.16 to 0.25 with 8,800), but its size is not given. |
| Main claim: a multivariable risk-stratified analysis has much more power than conventional subgroup analysis | exact | 2 of 2 fields as printed |  |
| Claims recomputed from the paper's own tables and Fig. 1A's formula | agrees | 18 of 18 statements follow from the paper's own tables and Fig. 1A's formula. Table 1's RRR and NNT recomputed from its own CER column with Fig. 1A's formula: 2 of 9 rows come back; not: rf_absent RRR -.19 against -0.182, NNT -239 against -250; rf_present RRR .13 against 0.143, NNT 183 against 167; k0 RRR -1.59 against -1.500, NNT -88 against -89; k1 RRR -.51 against -0.500, NNT -132 against -133; k2 RRR -.02 against 0.000, NNT -1936 against infinite; k3 RRR .21 against 0.250, NNT 83 against 67; k_ge4 RRR .35 against 0.383, NNT 24 against 20 |  |
| The authors' simulation code | not attempted | not attempted | The paper names no software and released no code ('TH created the initial statistical code'; a referee reads the references as Stata). No copy was found (issue #77 lists the search). The method was rebuilt from the text as stratpower and checked against the paper's tables and figure only. |
| Python package stratpower and its tutorial | agrees | stratpower 0.1.0: wheel installed in a fresh environment and imported from it; tests 5 passed; tutorial 7 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |
<!--/RESULTS-TABLE-->

The main claim holds: in every setting the risk-stratified analysis has far more power than the
conventional one. The claims that do not match come from one open cause: where the heterogeneity in net
benefit is large, our powers are higher than the paper's, and no reading of the paper we tested closes the gap.

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| "N = 8800 (n1 = 4400 and n2 = 4400)" | 4,400 per arm in every trial. |
| Treatment decreases the 5-year CER by 50% with 0.003 harms per treatment-year; Fig. 1A prints EER = (CER x .5) + (.003 x 5) | `stratpower.treated_risk`: as printed (`harm_model="additive"`). Outcome and complication as independent events is a hypothesis variant. |
| Six independent RFs of prevalence 25%; "the 5-year CER for those without any risk factors is .75%" | `stratpower.population`: all 64 RF patterns, their shares and CERs. |
| Odds ratios (Tables 2, 3, Fig. 1B) and relative risks (Tables 4, 5, text) | The odds scale everywhere. Six RFs of relative risk 3.0 (Table 3) would give risks above 1. The relative-risk scale is a hypothesis variant. |
| "randomly drawing observations, with replacement, from a population" | Each trial draws 4,400 people per arm from the population's pattern shares (multinomial), and events from each pattern's CER or EER (binomial). A finite population of 8,800 or 100,000 people is a hypothesis variant. |
| Logistic regression of the outcome on the subgroup variable, arm and their interaction (Brookes et al.); power is the share of 2,000 iterations with p < .05 | `stratpower.simulate_power`: Newton-Raphson on the trial's pattern-by-arm table (the same likelihood as the 8,800 rows), Wald test of the interaction, 20,000 trials. The fit matches statsmodels to 1e-12 (the package's example data). A likelihood-ratio test is a hypothesis variant. |
| Risk index: dichotomized (0-1 vs 2 or more RFs), continuous (the RF count), weighted (Table 4) | As printed; Table 4's weights 1.5/2.0/2.5, 1/1/1, 2.5/2.0/1.5 and 2.5/0/1.5 summed over the RFs present. |
| AUROC "from a logistic regression model" | The AUROC of the index for the outcome over both arms, from the population (the control arm alone is a hypothesis variant). |
| Table 3: scores of 1, 3 and 6 RFs | The population keeps six RFs; those outside the score have OR 2, so the 1-RF column is Table 2's 25% column, as printed. A population of only the score's RFs is a hypothesis variant. |
| Fig. 1B: average CER 1.5%, 3%, 6%, 9% with four RFs of OR 2 | The baseline (no-RF) CER solved so the population's average is each value. |
| Software not named; seeds not given | NumPy 2.2.6 PCG64; seed 20061 (+1000 per setting), a second run with seed 20062. |

## Comparing Monte Carlo powers

No power can come back exactly: the paper's seeds are not given. Each power is compared at a tolerance
fixed before the comparison: half a printed unit plus 3 combined standard errors, sqrt(p(1-p)/2000 +
q(1-q)/20000), p the paper's value and q ours. Two runs of ours agree with each other under it in every power
(`own_runs` in `output/comparison.json`). Values that do not come from a simulation (Table 1's shares, CERs,
RRRs and NNTs; every AUROC, which we compute from the population) are compared at their printed precision.
Each hypothesis variant is compared with the same rules and counted in `hypotheses`, never mixed into our values.

Fig. 1A is scored by pixels: the axes are calibrated from the published tick marks (residual under 0.3 px),
the published curve is erased and ours drawn in its place, and the share of curve pixels within 2 px is taken
both ways, with the boxed equation masked. Controls: the curve at 2 and at 4 complications per 1,000 per year
(wrong inputs), net RRR x 0.95 and x 1.05, and the CER shifted by 1% of the axis (near misses). The pass mark,
95%, is above every control.

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. |
| `requirements.txt` | Pinned Python packages; the package `stratpower` is installed from `../package`. |
| `results_notes.json` | Labels, assumptions, causes and the page's prose, written by hand; merged with the run into `../results.json`. Numbers in the prose are filled from the run. |
| `results.json` | The repository's results check (`tools/check_results.py`): our value for every compared cell, score and claim. |
| `pipeline/` | `fetch_inputs.sh`, `extract_published.py`, `simulate.py`, `compare.py`, `figures.py`, `claims.py`, `build_results.py`, `make_results_check.py`, `build_page.py` with `page_template.html`, `check_reproduction.py`, `update_readmes.py`, `env_versions.py`; copies of the skill's `check_results.py`, `compare_runs.py`, `check_package.py` and `compare_figure.py`. |
| `published/figure-1.jpg` | The paper's figure (CC BY 2.0). |
| `output/published_values.json` | Every printed number of Tables 1-5 and Fig. 1B. |
| `output/simulation.json` | Every setting: the main run, a second run, the hypothesis variants, the finite-population runs, the closed-form values. |
| `output/comparison.json` | Every value against the paper, with tolerances and z-scores; the hypotheses. |
| `output/fig1a_ours.png`, `fig1a_overlay.png`, `fig1b_ours.png`, `fig1b_overlay.png`, `figures.json` | Our Fig. 1 on the published picture; overlays in green; calibration, scores and controls. |
| `output/claims.json`, `package.json` | Every claim of the text against the paper's own tables and our run; the package check. |

## Run

```bash
pip install -r PMC1523355/figure-reproduction/requirements.txt ./PMC1523355/package
nextflow run PMC1523355/figure-reproduction/main.nf --outdir results
nextflow run PMC1523355/figure-reproduction/main.nf --outdir results --extract    # also reread the printed tables
```

The whole run takes about 2 minutes here, most of it the simulation. `.github/workflows/reproduce-pmc1523355.yml`
runs it on every pull request that touches this paper.

## Pipeline steps

1. `FETCH`: the figure JPEG and the article XML from PMC's open-access bucket (its regional endpoint and Europe PMC as fallbacks), SHA-256 checked.
2. `PUBLISHED_VALUES`: the committed printed values, or with `--extract` read again from the XML and checked against them.
3. `SIMULATE`: every setting at 20,000 trials, a second run, the hypothesis variants at 10,000, the finite-population runs, the closed-form values.
4. `COMPARE`: every printed value against ours, and the hypotheses.
5. `FIGURES`: Fig. 1A drawn on the published axes and scored with controls; Fig. 1B's values written into its cells.
6. `CLAIMS`: every claim against the paper's own tables and our run.
7. `PACKAGE`: `check_package.py` on `../package` (wheel, fresh install, tests, tutorial rerun).
8. `RESULTS`: `results.json` (verdicts by `check_results.py`), the repository's results check, the results page, and `check_reproduction.py` against the committed outputs (`report.md`); `CHECK` fails the run if anything differs.

## Limits

- **The code is lost.** The method is rebuilt from the paper's text and checked against its tables and figure only (`port` is not attempted).
- **The power gap is open.** Where the heterogeneity is large, our powers run higher than the paper's. The relative-risk scale, a likelihood-ratio test, independent harm, other readings of Tables 2 and 3 and the control-arm AUROC were each tested and none closes it. A finite simulated population would move each power by chance, but the paper does not give its size.
- **Table 1's rate columns** follow from no population of the stated risk factors, nor from each other through Fig. 1A's formula; they read like rates realized in one finite simulated population.
- **The AUROC** definition (both arms of the trial) was chosen by comparing with the paper's values (`found_by_search` in `results.json`), so no item that holds an AUROC can be "exact".
- **The design claim** (80% power for an RRR of 25%) holds at a CER of about 5%, not at the base case's 2.7%; the paper does not say which CER it used.
- **Fig. 1** is a 600 x 776 px JPEG; one pixel is 0.00015 of CER and 0.004 of net RRR. Fig. 1B is a table drawn as an image and is compared as values.
