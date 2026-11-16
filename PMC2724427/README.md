# PMC2724427: Bias in odds ratios by logistic regression modelling and sample size (Nemes et al. 2009)

Nemes S, Jonasson JM, Genell A, Steineck G. Bias in odds ratios by logistic regression modelling and
sample size. *BMC Medical Research Methodology* 9:56 (2009).
[doi:10.1186/1471-2288-9-56](https://doi.org/10.1186/1471-2288-9-56),
[PMC2724427](https://pmc.ncbi.nlm.nih.gov/articles/PMC2724427/), issue
[jeonglab-bcm/fossil#72](https://github.com/jeonglab-bcm/fossil/issues/72).

The paper is © 2009 Nemes et al; licensee BioMed Central Ltd, open access under the Creative Commons
Attribution License 2.0 (<https://creativecommons.org/licenses/by/2.0>). This folder does not contain
the paper, its full text or its Additional file 1; `figure-reproduction/published/` holds its three
figures, unchanged, with that notice.

The paper shows by simulation that logistic regression pushes coefficients away from zero in small
samples, by about `b1/n`. It draws a population of 100,000 with one continuous exposure (true
coefficient 2) and one discrete exposure (-0.9), takes 1,000 samples at each size from 100 to 1500
in steps of 5, fits a logistic regression to each, and fits the mean coefficient against `1/n`
(Table 1, Fig. 1). Additional file 1 gives the R lines that draw the population; the rest of the
code was never published. We rebuilt the study as the R package [`package/`](package/)
(`logitbias`), ran it in full, and ran it again on 20 more populations to see how far a rerun moves.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the study, the seed spread, the hypothesis tests, Figs 1 to 3 redrawn on the published pixel grid, the comparison with Table 1 and the text, and the check against the committed outputs. |
| [`package/`](package/) | `logitbias`, the study as an installable R package, with example data, tests and a [rendered tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC2724427/>

## Results

<!-- summary and table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-SUMMARY-->
4 exact, 2 agrees, 4 partly, 1 inconclusive, 7 differs, 1 not attempted; 8 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Table 1, continuous variable (intercept and n⁻¹: estimate, SE, t, p) | partly | 2 of 8 fields as printed |
| Table 1, discrete variable (intercept and n⁻¹: estimate, SE, t, p) | partly | 1 of 8 fields as printed |
| Text: R² of the OLS fit, 0.963 (continuous) and 0.836 (discrete) | differs | 0 of 2 fields as printed |
| Claims recomputed from the paper's own numbers (SE = estimate / t in Table 1; P(x>2.5) of Additional file 1) | differs | 4 of 5 come back from the paper's own numbers; not back: Table 1, discrete Intercept: SE = estimate / t (paper 0.00065, recomputed 0.00066) |
| The paper against itself: Fig. 2's headings and Table 1's curve 2.011 + 23.9/n | differs | 1 of 6 Fig. 2 headings lie within 0.02 of Table 1's curve 2.011 + 23.9/n; n=100 2.262 against 2.250, n=150 2.129 against 2.170, n=300 2.051 against 2.091, n=500 2.019 against 2.059, n=750 2.011 against 2.043, n=1000 2.003 against 2.035 |
| Additional file 1: P(x>2.5) = 0.2375 | exact | 1 of 1 fields as printed |
| Abstract and Results: estimates biased away from zero, odds ratios away from one | partly | 4 of 5 fields as printed |
| Results: the fit is better for the continuous than for the discrete variable | exact | 1 of 1 fields as printed |
| Results and Fig. 2: the sampling distribution is skewed at small n and grows symmetric | exact | 2 of 2 fields as printed |
| Results and Fig. 3: extreme estimates become rarer as n grows | exact | 2 of 2 fields as printed |
| Methods: kernel regression derivatives confirm the convergence rate | partly | 2 of 4 fields as printed |
| Discussion: maximum likelihood is risky under n = 100 and adequate above 500 (Long 1997) | not attempted | not attempted |
| Fig. 1, continuous variable | inconclusive | 11.77% within 2 px (pass 16.8%, best control 16.3%) |
| Fig. 1, discrete variable | differs | 0.38% within 2 px (pass 3.5%, best control 3.0%) |
| Fig. 2, densities at n = 100, 150, 300, 500, 750 and 1000 | differs | 13.11% within 2 px (pass 17.7%, best control 17.2%) |
| Fig. 2, the mean in each panel heading | differs | 0 of 6 fields as printed |
| Fig. 3, box plots at the same six sizes | differs | 41.87% within 2 px (pass 50.0%, best control 49.5%) |
| simulate_population() against the R lines of Additional file 1 | agrees | simulate_population(seed = 2724427) is identical to the R lines of Additional file 1 run on the same seed (100,000 rows: x, z and y all equal) |
| R package logitbias and its tutorial | agrees | logitbias 0.1.0: R CMD check Status: OK; tests 23 passed, 0 failed, 0 warnings, 0 skipped; tutorial rendered, TUTORIAL.md unchanged, 1 figures |
<!--/RESULTS-SUMMARY-->

<!--CLAIMS-LINE-->
The main claim holds in part: both slopes b1 point away from zero, the continuous mean lies farther from zero than the population value at every size, and the sampling distribution is skewed at small n and grows symmetric; the discrete mean does so at 257 of 281 sizes, and leaving out separated samples pulls it toward zero at n = 100 to 120. Table 1's slopes, SEs and R squared values and the figures' spreads do not come back; those causes are open (the paper's per-size means scatter less than any population of Additional file 1's design gives), and the intercepts move with the population draw.
<!--/CLAIMS-LINE-->

## Kept local, not in the repository

`PMC2724427/sources/` (git-ignored) holds the paper's full text (Europe PMC XML), Additional file 1
and the figure files. `figure-reproduction/pipeline/fetch_inputs.sh` downloads Additional file 1 and
the figures again and checks their SHA-256. The study simulates its own data, so there is no dataset
to download; the package's example data are synthetic.

## Session

`session/ledger.json` and `session/conversation.md` record the Claude Code session that made this
reproduction. It began with one prompt asking to install the Paper2Agent skills, then the kickoff
prompt; no other message was typed by a person. The ledger also counts as prompts the automated
notifications of background runs.
