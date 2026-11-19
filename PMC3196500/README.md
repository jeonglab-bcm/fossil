# PMC3196500: The number of patients and events required to limit the risk of overestimation (Thorlund et al. 2011)

Thorlund K, Imberger G, Walsh M, Chu R, Gluud C, Wetterslev J, Guyatt G, Devereaux PJ, Thabane L. The number of
patients and events required to limit the risk of overestimation of intervention effects in meta-analysis—a
simulation study. *PLoS ONE* 6(10):e25491 (2011).
[doi:10.1371/journal.pone.0025491](https://doi.org/10.1371/journal.pone.0025491) ·
[PMC3196500](https://pmc.ncbi.nlm.nih.gov/articles/PMC3196500/) · issue #71

The paper is © 2011 Thorlund et al., published under the
[Creative Commons Attribution License](https://creativecommons.org/licenses/by/4.0/) (CC BY). This folder does not
contain the paper, its full text or its supplement; `figure-reproduction/published/` holds Fig. 2 and Figs S1-S12
as lossless PNG copies of the files in the PMC open-access package, for comparison, redistributed under CC BY
with the attribution above. The printed numbers of Tables 1-4, S3 and S4 are in
`figure-reproduction/output/published_values.json`, read from the article XML and the supplement's Word files
by `extract_published.py`.

The paper asks how many patients and events a cumulative random-effects meta-analysis needs before a pooled
relative risk reduction (RRR) above 20% or 30% is unlikely to come from chance alone, when the true RRR is 0%
or 10%. It simulated 36 scenarios (two trial-size distributions, four control-risk ranges, three values of
tau², two true effects), 20,000 meta-analyses of 100 trials each, pooled with the DerSimonian-Laird model after
every trial, and compared the numbers it needed with the optimal information size (OIS). No code was
released. We rebuilt the simulation from the text and Appendices S1 and S2 as the Python package
[`package/`](package/) (`oisim`), reran all 36 scenarios, and compared every printed cell of Tables 1-4, S3 and
S4 and every panel of Fig. 2 and Figs S1-S12.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the downloads, the simulation, the tables, the figure panels redrawn on the published pixel grids with their controls, the claims, the checks. |
| [`package/`](package/) | `oisim`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure panel, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC3196500/>

## Results

<!-- summary from results.json (check_results.py); the full table, with the causes: figure-reproduction/README.md -->

<!--RESULTS-SUMMARY-->
13 agrees, 18 partly, 40 inconclusive, 16 differs, 4 not attempted; 55 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Fig. 1 (flowchart of the 36 scenarios) | not attempted | not attempted |
| Fig. 2, upper panel (Cochrane trial sizes, PC 5-15%, tau2 0.15, true RRR 0%, cumulative patients) | inconclusive | 56.15% within 2 px (pass 73.6%, best control 72.5%) |
| Fig. 2, lower panel (Cochrane trial sizes, PC 5-15%, tau2 0.15, true RRR 0%, cumulative events) | inconclusive | 36.99% within 2 px (pass 78.4%, best control 50.8%) |
| Fig. S1, top left (Cochrane trial sizes, PC 1-5%, tau2 0.05, true RRR 0%, cumulative patients) | inconclusive | 42.11% within 2 px (pass 84.4%, best control 77.3%) |
| Fig. S1, top middle (Cochrane trial sizes, PC 1-5%, tau2 0.15, true RRR 0%, cumulative patients) | inconclusive | 65.15% within 2 px (pass 85.9%, best control 80.4%) |
| Fig. S1, top right (Cochrane trial sizes, PC 1-5%, tau2 0.25, true RRR 0%, cumulative patients) | partly | 64.39% within 2 px (pass 88.4%, best control 56.7%) |
| Fig. S1, bottom left (Cochrane trial sizes, PC 5-15%, tau2 0.05, true RRR 0%, cumulative patients) | partly | 70.22% within 2 px (pass 89.7%, best control 68.5%) |
| Fig. S1, bottom middle (Cochrane trial sizes, PC 5-15%, tau2 0.15, true RRR 0%, cumulative patients) | inconclusive | 70.22% within 2 px (pass 89.0%, best control 88.0%) |
| Fig. S1, bottom right (Cochrane trial sizes, PC 5-15%, tau2 0.25, true RRR 0%, cumulative patients) | agrees | 85.97% within 2 px (pass 82.8%, best control 62.4%) |
| Fig. S2, top left (Cochrane trial sizes, PC 1-5%, tau2 0.05, true RRR 0%, cumulative events) | partly | 77.68% within 2 px (pass 90.0%, best control 73.4%) |
| Fig. S2, top middle (Cochrane trial sizes, PC 1-5%, tau2 0.15, true RRR 0%, cumulative events) | inconclusive | 79.75% within 2 px (pass 90.0%, best control 83.2%) |
| Fig. S2, top right (Cochrane trial sizes, PC 1-5%, tau2 0.25, true RRR 0%, cumulative events) | inconclusive | 53.57% within 2 px (pass 90.0%, best control 83.2%) |
| Fig. S2, bottom left (Cochrane trial sizes, PC 5-15%, tau2 0.05, true RRR 0%, cumulative events) | inconclusive | 51.92% within 2 px (pass 88.0%, best control 76.3%) |
| Fig. S2, bottom middle (Cochrane trial sizes, PC 5-15%, tau2 0.15, true RRR 0%, cumulative events) | inconclusive | 59.69% within 2 px (pass 89.7%, best control 80.1%) |
| Fig. S2, bottom right (Cochrane trial sizes, PC 5-15%, tau2 0.25, true RRR 0%, cumulative events) | inconclusive | 52.29% within 2 px (pass 81.1%, best control 76.9%) |
| Fig. S3, top left (Cochrane trial sizes, PC 1-5%, tau2 0.05, true RRR 10%, cumulative patients) | inconclusive | 64.96% within 2 px (pass 84.1%, best control 70.4%) |
| Fig. S3, top middle (Cochrane trial sizes, PC 1-5%, tau2 0.15, true RRR 10%, cumulative patients) | agrees | 85.96% within 2 px (pass 65.4%, best control 58.9%) |
| Fig. S3, top right (Cochrane trial sizes, PC 1-5%, tau2 0.25, true RRR 10%, cumulative patients) | agrees | 89.11% within 2 px (pass 86.6%, best control 50.9%) |
| Fig. S3, bottom left (Cochrane trial sizes, PC 5-15%, tau2 0.05, true RRR 10%, cumulative patients) | partly | 77.16% within 2 px (pass 77.6%, best control 62.1%) |
| Fig. S3, bottom middle (Cochrane trial sizes, PC 5-15%, tau2 0.15, true RRR 10%, cumulative patients) | partly | 84.89% within 2 px (pass 85.0%, best control 66.2%) |
| Fig. S3, bottom right (Cochrane trial sizes, PC 5-15%, tau2 0.25, true RRR 10%, cumulative patients) | agrees | 91.26% within 2 px (pass 81.1%, best control 55.0%) |
| Fig. S4, top left (Cochrane trial sizes, PC 1-5%, tau2 0.05, true RRR 10%, cumulative events) | partly | 85.67% within 2 px (pass 89.7%, best control 68.6%) |
| Fig. S4, top middle (Cochrane trial sizes, PC 1-5%, tau2 0.15, true RRR 10%, cumulative events) | inconclusive | 74.10% within 2 px (pass 88.6%, best control 87.6%) |
| Fig. S4, top right (Cochrane trial sizes, PC 1-5%, tau2 0.25, true RRR 10%, cumulative events) | inconclusive | 78.08% within 2 px (pass 88.0%, best control 78.6%) |
| Fig. S4, bottom left (Cochrane trial sizes, PC 5-15%, tau2 0.05, true RRR 10%, cumulative events) | inconclusive | 64.69% within 2 px (pass 86.8%, best control 82.1%) |
| Fig. S4, bottom middle (Cochrane trial sizes, PC 5-15%, tau2 0.15, true RRR 10%, cumulative events) | inconclusive | 55.41% within 2 px (pass 87.2%, best control 74.3%) |
| Fig. S4, bottom right (Cochrane trial sizes, PC 5-15%, tau2 0.25, true RRR 10%, cumulative events) | inconclusive | 59.94% within 2 px (pass 78.1%, best control 77.1%) |
| Fig. S5, top left (common trial sizes, PC 1-5%, tau2 0.05, true RRR 0%, cumulative patients) | differs | 11.28% within 2 px (pass 89.5%, best control 23.8%) |
| Fig. S5, top middle (common trial sizes, PC 1-5%, tau2 0.15, true RRR 0%, cumulative patients) | differs | 18.32% within 2 px (pass 90.0%, best control 27.5%) |
| Fig. S5, top right (common trial sizes, PC 1-5%, tau2 0.25, true RRR 0%, cumulative patients) | differs | 12.33% within 2 px (pass 85.5%, best control 20.1%) |
| Fig. S5, bottom left (common trial sizes, PC 5-15%, tau2 0.05, true RRR 0%, cumulative patients) | differs | 28.15% within 2 px (pass 90.0%, best control 38.1%) |
| Fig. S5, bottom middle (common trial sizes, PC 5-15%, tau2 0.15, true RRR 0%, cumulative patients) | differs | 27.64% within 2 px (pass 89.8%, best control 33.9%) |
| Fig. S5, bottom right (common trial sizes, PC 5-15%, tau2 0.25, true RRR 0%, cumulative patients) | differs | 17.88% within 2 px (pass 89.1%, best control 30.8%) |
| Fig. S6, top left (common trial sizes, PC 1-5%, tau2 0.05, true RRR 0%, cumulative events) | differs | 16.72% within 2 px (pass 89.4%, best control 50.5%) |
| Fig. S6, top middle (common trial sizes, PC 1-5%, tau2 0.15, true RRR 0%, cumulative events) | differs | 21.47% within 2 px (pass 89.8%, best control 39.9%) |
| Fig. S6, top right (common trial sizes, PC 1-5%, tau2 0.25, true RRR 0%, cumulative events) | differs | 17.37% within 2 px (pass 89.6%, best control 39.5%) |
| Fig. S6, bottom left (common trial sizes, PC 5-15%, tau2 0.05, true RRR 0%, cumulative events) | differs | 33.24% within 2 px (pass 90.0%, best control 42.7%) |
| Fig. S6, bottom middle (common trial sizes, PC 5-15%, tau2 0.15, true RRR 0%, cumulative events) | inconclusive | 32.44% within 2 px (pass 90.0%, best control 33.6%) |
| Fig. S6, bottom right (common trial sizes, PC 5-15%, tau2 0.25, true RRR 0%, cumulative events) | inconclusive | 22.22% within 2 px (pass 89.4%, best control 23.0%) |
| Fig. S7, top left (common trial sizes, PC 1-5%, tau2 0.05, true RRR 10%, cumulative patients) | differs | 2.42% within 2 px (pass 64.7%, best control 17.9%) |
| Fig. S7, top middle (common trial sizes, PC 1-5%, tau2 0.15, true RRR 10%, cumulative patients) | inconclusive | 16.78% within 2 px (pass 84.7%, best control 17.7%) |
| Fig. S7, top right (common trial sizes, PC 1-5%, tau2 0.25, true RRR 10%, cumulative patients) | differs | 5.72% within 2 px (pass 89.2%, best control 9.1%) |
| Fig. S7, bottom left (common trial sizes, PC 5-15%, tau2 0.05, true RRR 10%, cumulative patients) | differs | 10.39% within 2 px (pass 87.6%, best control 31.4%) |
| Fig. S7, bottom middle (common trial sizes, PC 5-15%, tau2 0.15, true RRR 10%, cumulative patients) | differs | 18.99% within 2 px (pass 87.4%, best control 20.2%) |
| Fig. S7, bottom right (common trial sizes, PC 5-15%, tau2 0.25, true RRR 10%, cumulative patients) | differs | 10.14% within 2 px (pass 89.5%, best control 16.8%) |
| Fig. S8, top left (common trial sizes, PC 1-5%, tau2 0.05, true RRR 10%, cumulative events) | inconclusive | 79.82% within 2 px (pass 90.3%, best control 89.3%) |
| Fig. S8, top middle (common trial sizes, PC 1-5%, tau2 0.15, true RRR 10%, cumulative events) | agrees | 93.97% within 2 px (pass 88.6%, best control 72.3%) |
| Fig. S8, top right (common trial sizes, PC 1-5%, tau2 0.25, true RRR 10%, cumulative events) | inconclusive | 76.94% within 2 px (pass 99.4%, best control 98.4%) |
| Fig. S8, bottom left (common trial sizes, PC 5-15%, tau2 0.05, true RRR 10%, cumulative events) | partly | 79.51% within 2 px (pass 89.8%, best control 79.1%) |
| Fig. S8, bottom middle (common trial sizes, PC 5-15%, tau2 0.15, true RRR 10%, cumulative events) | partly | 84.27% within 2 px (pass 89.8%, best control 83.7%) |
| Fig. S8, bottom right (common trial sizes, PC 5-15%, tau2 0.25, true RRR 10%, cumulative events) | partly | 81.25% within 2 px (pass 90.0%, best control 70.0%) |
| Fig. S9, top left (common trial sizes, PC 15-40%, tau2 0.05, true RRR 0%, cumulative patients) | inconclusive | 64.96% within 2 px (pass 89.1%, best control 83.3%) |
| Fig. S9, top middle (common trial sizes, PC 15-40%, tau2 0.15, true RRR 0%, cumulative patients) | inconclusive | 65.78% within 2 px (pass 90.0%, best control 73.0%) |
| Fig. S9, top right (common trial sizes, PC 15-40%, tau2 0.25, true RRR 0%, cumulative patients) | partly | 75.77% within 2 px (pass 89.7%, best control 74.8%) |
| Fig. S9, bottom left (common trial sizes, PC 40-80%, tau2 0.05, true RRR 0%, cumulative patients) | inconclusive | 71.00% within 2 px (pass 89.8%, best control 72.9%) |
| Fig. S9, bottom middle (common trial sizes, PC 40-80%, tau2 0.15, true RRR 0%, cumulative patients) | inconclusive | 70.38% within 2 px (pass 90.0%, best control 71.9%) |
| Fig. S9, bottom right (common trial sizes, PC 40-80%, tau2 0.25, true RRR 0%, cumulative patients) | partly | 74.80% within 2 px (pass 89.9%, best control 66.6%) |
| Fig. S10, top left (common trial sizes, PC 15-40%, tau2 0.05, true RRR 0%, cumulative events) | inconclusive | 57.19% within 2 px (pass 89.4%, best control 79.0%) |
| Fig. S10, top middle (common trial sizes, PC 15-40%, tau2 0.15, true RRR 0%, cumulative events) | inconclusive | 66.61% within 2 px (pass 90.0%, best control 81.8%) |
| Fig. S10, top right (common trial sizes, PC 15-40%, tau2 0.25, true RRR 0%, cumulative events) | inconclusive | 67.52% within 2 px (pass 89.3%, best control 82.0%) |
| Fig. S10, bottom left (common trial sizes, PC 40-80%, tau2 0.05, true RRR 0%, cumulative events) | inconclusive | 58.16% within 2 px (pass 88.3%, best control 68.5%) |
| Fig. S10, bottom middle (common trial sizes, PC 40-80%, tau2 0.15, true RRR 0%, cumulative events) | inconclusive | 47.46% within 2 px (pass 89.6%, best control 61.5%) |
| Fig. S10, bottom right (common trial sizes, PC 40-80%, tau2 0.25, true RRR 0%, cumulative events) | inconclusive | 50.53% within 2 px (pass 85.7%, best control 66.7%) |
| Fig. S11, top left (common trial sizes, PC 15-40%, tau2 0.05, true RRR 10%, cumulative patients) | inconclusive | 38.82% within 2 px (pass 90.0%, best control 74.3%) |
| Fig. S11, top middle (common trial sizes, PC 15-40%, tau2 0.15, true RRR 10%, cumulative patients) | inconclusive | 35.66% within 2 px (pass 89.6%, best control 71.7%) |
| Fig. S11, top right (common trial sizes, PC 15-40%, tau2 0.25, true RRR 10%, cumulative patients) | inconclusive | 38.15% within 2 px (pass 89.1%, best control 65.4%) |
| Fig. S11, bottom left (common trial sizes, PC 40-80%, tau2 0.05, true RRR 10%, cumulative patients) | inconclusive | 46.83% within 2 px (pass 89.5%, best control 78.0%) |
| Fig. S11, bottom middle (common trial sizes, PC 40-80%, tau2 0.15, true RRR 10%, cumulative patients) | differs | 45.82% within 2 px (pass 83.5%, best control 75.4%) |
| Fig. S11, bottom right (common trial sizes, PC 40-80%, tau2 0.25, true RRR 10%, cumulative patients) | inconclusive | 57.97% within 2 px (pass 77.1%, best control 62.0%) |
| Fig. S12, top left (common trial sizes, PC 15-40%, tau2 0.05, true RRR 10%, cumulative events) | inconclusive | 63.06% within 2 px (pass 90.0%, best control 84.2%) |
| Fig. S12, top middle (common trial sizes, PC 15-40%, tau2 0.15, true RRR 10%, cumulative events) | partly | 78.38% within 2 px (pass 88.3%, best control 69.0%) |
| Fig. S12, top right (common trial sizes, PC 15-40%, tau2 0.25, true RRR 10%, cumulative events) | agrees | 98.59% within 2 px (pass 90.0%, best control 66.3%) |
| Fig. S12, bottom left (common trial sizes, PC 40-80%, tau2 0.05, true RRR 10%, cumulative events) | inconclusive | 57.69% within 2 px (pass 82.2%, best control 71.3%) |
| Fig. S12, bottom middle (common trial sizes, PC 40-80%, tau2 0.15, true RRR 10%, cumulative events) | inconclusive | 66.67% within 2 px (pass 78.0%, best control 73.6%) |
| Fig. S12, bottom right (common trial sizes, PC 40-80%, tau2 0.25, true RRR 10%, cumulative events) | inconclusive | 36.90% within 2 px (pass 85.5%, best control 72.2%) |
| Table 1 (Cochrane trial sizes, PC 1-5% and 5-15%: patients and events required) | partly | 81 of 144 fields as printed |
| Table S3 ('common' trial sizes, PC 15-40% and 40-80%) | partly | 71 of 144 fields as printed |
| Table S4 ('common' trial sizes, PC 1-5% and 5-15%) | partly | 101 of 144 fields as printed |
| Table 2 (72 optimal information sizes, patients and events) | partly | 123 of 144 fields as printed |
| Table 3, OIS columns (ranges over I2 from Table 2) | partly | 15 of 24 fields as printed |
| Table 3, simulation columns (acceptability ranges, Cochrane trial sizes) | not attempted | not attempted |
| Table 4, OIS columns | partly | 31 of 48 fields as printed |
| Table 4, simulation columns (acceptability ranges, 'common' trial sizes) | not attempted | not attempted |
| Table S1, Table S2 and Fig. S13 (survey of Cochrane Heart Group meta-analyses) | not attempted | not attempted |
| Text: the larger the overestimation, the fewer patients and events required | agrees | 1 of 1 fields as printed |
| Text: low control risk needs more patients but fewer events | agrees | 2 of 2 fields as printed |
| Text: tau2 0.05 needs fewer than 0.25, reversed for 'common' sizes with PC 1-5% | agrees | 2 of 2 fields as printed |
| Text (main claim): surpassing the OIS generally protects against overestimation | agrees | 1 of 1 fields as printed |
| Text: the probability of overestimation was above 25% when patients were few, in most scenarios | agrees | 1 of 1 fields as printed |
| Text claims recomputed from the paper's own tables | agrees | 6 of 6 statements follow from the paper's own Tables 1, S3, S4 and 2: text.larger_overestimation (>30% needs no more than >20% (all three tables)): yes, 100% of cases; text.control_risk (PC 1-5% needs more patients than 5-15% (Tables 1, S4)): yes, 100% of cases; text.control_risk (PC 1-5% needs fewer events than 5-15% (Tables 1, S4)): yes, 89% of cases; text.heterogeneity (tau2 0.05 needs fewer than 0.25 (except common sizes, PC 1-5%)): yes, 92% of cases; text.heterogeneity (common sizes, PC 1-5%: tau2 0.05 needs more than 0.25): yes, 100% of cases; text.ois_protects (P(RRR > T) below 5% at or before the OIS for RRR = T, 90% power): yes, 76% of cases. The claim about early probabilities above 25% rests on the figures only. |
| Python package oisim and its tutorial | agrees | oisim 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 7 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

**What agrees.** The method: Appendix S2's trial generator and Appendix S1's DerSimonian-Laird pooling,
as `oisim`. Table 2's OIS formula: the unrounded values are within one rounding step of 140 of the 144
printed cells (two-sided z for α = 5%). Tables 1, S3 and S4, the numbers of patients and events needed for the
share of overestimates to drop below 10%, 5% and 1%: 81, 71 and 101 of 144 cells as printed, and 135, 123
and 138 within one bin. Every statement the text makes about these tables holds on our run, as it does on
the paper's own tables, including the main claim: in most scenarios the share of overestimates drops below
5% before the OIS at 90% power is reached (78% of 72 cases on our run, 76% on the paper's tables).

**What did not, and why.**

- *Chance does not explain everything.* Our two runs with different seeds agree with each other on 87, 86
  and 124 of the 144 cells of Tables 1, S3 and S4; the paper agrees with ours on 81, 71 and 101. Where ours
  misses, it is higher more often than lower (51 against 12 in Table 1; 34 against 5 for patients alone).
- *The curves differ by a few per cent.* On the published pixel grids, outside Figs S5-S7, our two runs are
  73% to 100% alike (most above 85%); ours and the paper's 36% to 99%, most between 42% and 86%. A near miss (ours ×1.05 or ×0.95, or shifted one point) often scores
  as well as ours, so 40 panels are inconclusive. In the panels, ours ×0.95 often scores better on the event axis and ours ×1.05 on the patient axis.
- *How the curves were binned is not stated.* The tables fit best when every pooled estimate counts in the
  interval its cumulative count falls in (253 of 432 cells; counting at the nearest point 225; once per
  meta-analysis at an edge 150). The figures fit best with the nearest point for patients and the interval
  for events. Both are searched settings, recorded as such.
- *Tested, and none closes the gap:* keeping double-zero trials with the 0.5 correction (Table 1: 82 of 144
  against 81, about as well), events drawn as Binomial(n, P) on the whole trial as Appendix S2 writes it (10
  of 144); and, in scratch tests outside the pipeline on the Cochrane scenarios with tau² 0.05, leaving out
  one-trial meta-analyses, other correction sizes and offset bins.
- *Tables 3 and 4 group the scenarios 'post hoc'.* No rule we tried rebuilds their simulation columns from
  the paper's own Tables 1, S3 and S4 (54 range rules: at most 8 of 72 cells; the Methods' own definitions of
  good, very good and excellent: at most 8). Their OIS columns agree: 46 of 72 ranges as printed, the rest
  within one rounding step of 1,000 patients or 50 events.

**Slips in the paper:**

- Figs S5, S6 and S7 are byte copies of Figs S1, S2 and S3 (identical TIFF files): they show the Cochrane
  trial sizes, not the 'common' sizes their captions name. Our Cochrane curves score 42% to 91% on them, our
  'common' curves 2% to 33%.
- Table 2's footnote rounds patients up to 1,000 (PC 3%, 10%) or 100 and events up to 50; the printed cells
  follow that rule in 78 of 144 cases. They are rounded to the nearest 500 or 100, with no single rule.
- Table 3 prints PC "3%" for the 5%-15% row, whose OIS values are those of PC 10%.
- Table 4's caption repeats Table 3's ("Cochrane Heart Group"); its rows are the 'common' sizes of Tables S3
  and S4. Table 4 prints the PC 3% patient ranges as "10–20000".
- Tables S3 and S4 have the same caption. The text names 23 Cochrane Heart Group meta-analyses; Table S1
  lists 20.

The main finding of the paper holds: on our run, surpassing the optimal information size protects against
overestimation in most scenarios, and the patterns the text describes come back. The read-off tables agree
within one bin for most cells; the remaining differences and the curves' offsets are open.

## Package

`oisim` is in Python, by the default rule: the paper names no software and the method needs no R or
Bioconductor package. Install:

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3196500/package"
```

Tutorial: [package/tutorial/TUTORIAL.md](package/tutorial/TUTORIAL.md).

## Run

```bash
pip install -r PMC3196500/figure-reproduction/requirements.txt ./PMC3196500/package
nextflow run PMC3196500/figure-reproduction/main.nf --outdir results
```

About 4 minutes on 4 cores. `.github/workflows/reproduce-pmc3196500.yml` runs it on every pull request that
touches this folder. See [figure-reproduction/README.md](figure-reproduction/README.md) for the steps.

Kept local and gitignored: `sources/` (the article XML, the supplement zip and its files, the text
conversions), `work/` and `.venv/`.
