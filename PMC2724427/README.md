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
<!--/RESULTS-SUMMARY-->

<!--CLAIMS-LINE-->
<!--/CLAIMS-LINE-->

## Kept local, not in the repository

`PMC2724427/sources/` (git-ignored) holds the paper's full text (Europe PMC XML), Additional file 1
and the figure files. `figure-reproduction/pipeline/fetch_inputs.sh` downloads Additional file 1 and
the figures again and checks their SHA-256. The study simulates its own data, so there is no dataset
to download; the package's example data are synthetic.

## Session

`session/ledger.json` and `session/conversation.md` record the Claude Code session that made this
reproduction. It began with one prompt asking to install the Paper2Agent skills, then the kickoff
prompt; no other message was typed by a person.
