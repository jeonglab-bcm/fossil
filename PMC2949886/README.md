# PMC2949886: Filtering, FDR and power (van Iterson et al. 2010)

van Iterson M, Boer JM, Menezes RX. Filtering, FDR and power. *BMC Bioinformatics* 11:450 (2010).
[doi:10.1186/1471-2105-11-450](https://doi.org/10.1186/1471-2105-11-450) ·
[PMC2949886](https://pmc.ncbi.nlm.nih.gov/articles/PMC2949886/) · issue #53

The paper is © 2010 van Iterson et al., licensee BioMed Central, under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). This folder does not contain the paper, its
Additional File 1 or the authors' figure files. `figure-reproduction/output/figures/*_published.png` are
renders of the authors' original figure files (BMC electronic supplementary material 2 to 8) and of the
figure pages of Additional File 1, kept for comparison and redistributed under CC BY 2.0 with the
attribution above. The leukemia data are GEO series GSE13425 (Den Boer et al. 2009), downloaded by the
pipeline.

The paper asks what filtering genes before multiple-testing correction does to the FDR and to power. Its R
scripts were on a group page that now answers 404; the archive it linked (`FilteringFDRandpower.zip`) was
never captured. We rebuilt the method from the paper and its Additional File 1 as the R package
[`package/`](package/) (`filterfdr`), reran the simulation study (1000 data sets) and the leukemia analysis, and
laid every curve over the authors' own figures. BMC serves those as vector PDFs, so each published curve was
read back as numbers.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the published figures read back, the simulation, the single-data-set analyses, the leukemia analysis, renders, scores, claims and the results page. |
| [`package/`](package/) | `filterfdr`, the method as an installable R package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure panel and claim of the paper and its Additional File 1, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC2949886/>

## Results

<!-- summary from results.json (check_results.py); the full table: python3 figure-reproduction/pipeline/check_results.py results.json --markdown -->

47 results: 6 exact, 7 agree, 22 partly agree, 8 inconclusive, 2 differ, 2 not attempted; 25 open causes.
A figure panel agrees when 95% of the published curve lies within 2 px of ours and ours of it (300 dpi, on
the published panel's own axes) and no wrong or near-miss version scores as well.

| Result | Verdict | Ours against the paper |
| --- | --- | --- |
| Fig. 1, p-value densities | agrees (null), partly (alternative) | The three null curves within 0.001; under the alternative the no-filter and fold-change curves within 0.002 for p from 0.01 (0.004 below), the variance-filter curve up to 0.71 apart (0.54 for p from 0.01; open) |
| Fig. 2, filter statistics of one data set | partly, 1 inconclusive | Our data set 1 against the paper's unseeded one; the deciles from 10% to 90% agree within 2% (variance median 5.17 against 5.10) |
| Fig. 3, pi0 against fraction removed | agrees | 98.8%; every point within 0.004 once the caption's swapped signal and variance labels are put back |
| Fig. 4, achieved FDR | 1 agrees, 3 partly | Every point but one within 0.004; the paper draws fold change at x = 0.99 at 0.0201 for three methods, which its own Fig. 3 rules out. Without that point all four panels pass |
| Fig. 5, power against BH level | partly | Within 0.016 (open: more than Monte Carlo error) |
| Fig. 6, FDR-bias test | inconclusive; test labels partly | Box medians back (0.50, 0.45, ..., 0.01 against 0.51, 0.46, ..., 0.01) from data without the noise term; 10 of 11 test labels back |
| Fig. 7, leukemia achieved FDR | inconclusive | One random subset per size; 71 of 90 published points within the range of our 20 other subsets |
| Figures S2, S3 (power) | 2 agree, 5 partly | As Fig. 5 (S3 fold change within 0.050); S2 BY partly because 5% of its small power is below the 2 px resolution |
| Figure S4 (bias test, three filters) | 1 differs, 2 inconclusive | One data set: the FDR lines differ by sampling noise |
| Figure S5 (leukemia power) | differs | The paper's power is higher (0.65 against 0.48 at n = 24); three causes ruled out |
| Figure S6 (Wilcoxon) | partly (FDR), inconclusive (power) | FDR within 0.006 but for the x = 0.99 point; our power 5% higher (open) |
| Figures S8, S9 and the section 13 claims (filtering after the correction) | partly or inconclusive | How "situation C" filters the selected list is not stated; two readings ruled out |
| Figures S1, S7 | not attempted | S1 is a raster scatter of one unseeded data set; S7's bootFDR and permFDR settings are not given |
| Claims in the text | 6 exact, 1 partly (leukemia), 1 agrees | 22 rules; 18 hold on the paper's own figure values. The four that do not: the text's "signal worst" (against the curves as the caption labels them), variance "always" losing power, the leukemia "signal and variance no effect on power", and fold change the "only" filter gaining power before correction. Separately, "4000 non-null features" (1000) and 7/33 printed as 20% are arithmetic slips (excepted) |
| Package `filterfdr` | agrees | R CMD check OK, 109 test expectations pass, the tutorial reruns unchanged |

What came back and how:

- **The noise reading.** Additional File 1 writes the noise as N(0, 0.01). Read as a variance (SD 0.1) and drawn
  once per feature, as the first author's SSPA package draws it, it gives the published achieved FDR at x = 0
  (BH 0.052 against 0.054); SD 0.01 gives 0.032. The bitriangular effect sizes are SSPA's defaults.
- **Fig. 3's caption** swaps the signal and variance curves: our variance filter matches the curve the caption
  calls signal within 0.004 (0.38 as labelled). The text ("the worst performance is yielded by the signal
  filter") is right; the issue's spec noted the disagreement.
- **Fig. 1** needs the pooled within-group variance as the variance filter, not the variance of all samples
  the text defines (which leaves null p-values uniform), and thresholds set under the null.
- **Fig. 6** was drawn from data without the noise term; Figure S4 from data with it. Our test with the
  smallest BH-adjusted p-value per permutation and a one-sided final test gives the box medians of both.

The main finding holds: the fold-change filter biases the FDR and raises power, and the signal and variance
filters do not bias it; the test flags the fold-change filter at 10% removed. Three sentences overstate the
paper's own figures (variance "always" losing power, fold change the "only" filter gaining power before
correction, and "4000 non-null features" for 1000) and Fig. 3's caption swaps two curves; the power gaps of
Figs 5, S2, S5 and S6 are open.

Kept local and gitignored: `sources/` (the paper, Additional File 1, the figure PDFs, GEO data), `work/`
(scratch runs, Slurm logs, the Nextflow work folder), `.Rlib/` (the R library) and `.venv/`.
