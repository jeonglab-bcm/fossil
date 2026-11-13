# Reproducing the figures and numbers of PMC2813257

Neher and Leitner (2010), [doi:10.1371/journal.pcbi.1000660](https://doi.org/10.1371/journal.pcbi.1000660).
The paper's own Python scripts were never released, so every step here is written from its text. The method
itself lives in the package [`../package/`](../package/) (`hivrecomb`); this folder holds the pipeline that
runs it on the paper's data, draws the figures and scores them.

## Results

The verdicts are computed by `check_results.py` from [`../results.json`](../results.json); the table is in
[`../README.md`](../README.md). In one line: both findings come back, the recombination rate is 9.8e-06 per
site and generation against the paper's 1.4e-05 (inside its own standard deviation), and two gaps are open:
the divisor `<M pA pB>`, which the paper reports as 0.93 and which no averaging convention we tried puts
below 1.04, and the observation counts behind Figure 4, where our hitch-hiking filter leaves 195 synonymous
observations against about 1,850 in the published inset.

## What the code does against the paper

| The paper says | What we do |
| --- | --- |
| "obtained from the Los Alamos National Lab HIV data base (Special interest alignments, accession numbers: AF137629-AF138703, AF204402-AF204670, AY449806-AY450055 & AY450056-AY450257)" | Fetch the four ranges from GenBank through E-utilities and keep the 1,753 HIV-1 records (the ranges also hold 43 records of other organisms). LANL's set 1 holds 212 more clones (Shriner et al. 2004) and 5 unpublished ones, outside the accession list; `--studies` shows that adding them moves the rate away from the paper, so they are left out. |
| Sampling times | From the clone name (`pNcMMM-NN` and `pNpMMM-NN` give months after seroconversion). Patients 4 and 10 are named by visit (`4v2px1`), which LANL's `set1_clinical_data.txt` maps to months. The paper does not mention this step. |
| "translated into amino acid sequences and aligned for each patient separately using MUSCLE v3.6 with default settings"; a 3 bp gap for each amino-acid gap | The same, with MUSCLE 3.6 built from its own source (the 2005 download is a 32-bit binary). Each record is translated from its own `codon_start`. Eight p9 records that GenBank marks as pseudogenes and that are not in frame are left out, which is why p9 has 113 of its 121 clones. |
| "generation time 2 days", "6 month ~ 100 generations" | 365.25 / 24 = 15.22 generations per month. |
| Pairs of biallelic, gapless sites with three of the four haplotypes at t_i, both alleles seen at least three times; does the fourth haplotype appear at t_{i+1}? | The same, over every pair of consecutive samples of every patient. |
| Error bars: "the product of the estimated value and 1 +- #counts^-0.5" | The same. |
| "The fit is done by minimizing the squared deviation, weighted by the relative uncertainty of the data points indicated by the error bars" | We read "relative uncertainty" as 1 / sqrt(counts), not as the error bar p / sqrt(counts). Weighting by the error bar gives a bootstrap spread ten times the paper's; this reading gives 0.39e-05 against its 0.55e-05, and fit parameters that match the published legend. |
| `f(d dt) = c0 + c1 (1 - exp(-c2 d dt))`, `rho = c1 c2 / (<M pA pB> - c0)` | The same, with c0 and c1 bounded to [0, 1] (f is a probability) and c2 to non-negative values. |
| "<M p_A p_B> ~ 0.93 observed in the data", "A and B being the minor alleles" | M at t_{i+1} times the two minor-allele frequencies at t_i, averaged over the contributing pairs: 1.19. Four other conventions give 1.04 to 1.60. |
| 500 bootstrap resamples of the 11 patients | The same, with numpy's `default_rng(0)`; the paper gives no seed. |
| Figure 2A against distance, Figure 2B against distance times time | The bins are not stated. The published points put Figure 2A in seven bins of 76.6 bp to 536 bp and Figure 2B in bins of 8,000 bp x generations; both are recorded as read from the figure, with their sensitivity. |
| Selection: cases (i) biallelic without indels at t_i, (ii) monomorphic at t_i and biallelic at t_{i+1}, dp = 1 for a nucleotide that changed with no polymorphism seen, both samples larger than 10 | The same. A site is synonymous when its two alleles give one amino acid in the consensus codon of the earlier sample; the paper does not say which codon background it used. |
| Hitch-hiking: drop synonymous polymorphisms closer than 100 bp to a non-synonymous one changing faster than 0.002 per generation | The same. |
| "The Kolmogorov-Smirnov test was performed using the statistics module of SciPy" | `scipy.stats.ks_2samp`. The paper's D / sqrt(1/m_s + 1/m_n) is the statistic SciPy puts into its asymptotic p value. |
| "Scripting and plotting was done in Python using the NumPy and Matplotlib environment" | Python 3.12 with NumPy, SciPy and Matplotlib, pinned in `requirements.txt`. |

## Layout

| Path | What it is |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline. `run_skyriver.sbatch` runs it as Slurm jobs. |
| `pipeline/fetch_inputs.sh` | The downloads and their checksums; builds MUSCLE 3.6. |
| `pipeline/prepare_data.py` | Parses the records, assigns patient and month, codon-aligns each patient, writes the digest of the parsed input. |
| `pipeline/analyze.py` | Both analyses and the sensitivity variants: `analysis.json`. |
| `pipeline/render.py` | The four panels and their controls, on the published pixel grid. |
| `pipeline/read_published.py` | Cuts the published panels out and reads their points and curves back in data units. |
| `pipeline/compare.py` | Scores each panel both ways against the published one, with the controls; writes the overlays. |
| `pipeline/studies.py` | The hypothesis tests behind the causes (`--studies`). Not part of the run that writes the results. |
| `pipeline/build_results.py`, `results_notes.json` | Merge this run's numbers with the hand-written labels, assumptions and causes into `results.json`. |
| `pipeline/check_reproduction.py` | The check step: `check_results.py`, the package report, and this run against `output/`. |
| `pipeline/build_page.py`, `page_template.html` | The results page, generated from `results.json`. |
| `published/` | The paper's four figures at the publisher's resolution (CC0). |
| `output/` | The committed outputs a rerun is compared with. |

## Run

```bash
nextflow run PMC2813257/figure-reproduction/main.nf --outdir results
```

Options: `--sources DIR` reuses a local copy of the downloads, `--studies` also runs the hypothesis tests,
`--boot N` and `--seed N` change the bootstrap. About 4 minutes on four cores.

## Pipeline steps

`FETCH` (GenBank, LANL, MUSCLE source, built here) → `ALIGN` (translate, MUSCLE, back-translate) →
`ANALYZE` (pairs, bins, fit, bootstrap, frequency changes, Kolmogorov-Smirnov, sensitivity) →
`READ_PUBLISHED` (panel crops and their points) → `RENDER` (our panels and the controls) → `COMPARE`
(two-way pixel scores, overlays) → `PACKAGE` (`check_package.py`) → `RESULTS` (merge and compute the
verdicts) → `CHECK` (rules, the package, this run against `output/`) → `BUILD_PAGE`.

## Limits

* The pixel comparison of Figures 2 and 4 cannot separate our curves from a near-miss control. For Figure 2
  the published lines are 5 px wide and the real differences are of that order; for Figure 4 the legend, the
  inset frame and the tallest histogram of each bin are ink both figures share, so they carry the score
  (ours 0.911, the control with the two curves exchanged 0.912). The points, the curves and the inset counts
  are therefore read off the published panels in data units and compared as values; the pixel scores stay in
  `comparison.json` and on the page. Only Figure 3 carries a pixel verdict, and there a wrong-input control
  scores better than our histogram.
* Figure 4 is drawn whole: the three cumulative curves, the legend, the inset histograms and the bracket at
  0.002 per generation. The published panel carries all of them, and they cover a third of it, so a
  reproduction without them cannot be laid over the published figure. Only the lettering (the legend box,
  the inset's axis labels) is left out of the score.
* The inset of Figure 4 is read class by class. The three histograms are drawn over each other, so in each
  bin only the classes that are taller than the ones drawn after them can be read; the three come back in
  15, 10 and 6 of the 21 bins.
* The published figures were drawn with Matplotlib of 2009. We draw with 3.10 at the published stroke
  widths; fonts and tick labels are left out of the comparison by the masks in `compare.py`.
* The GenBank download has no stable checksum: E-utilities returns the records in no fixed order and the
  accession ranges hold unrelated records. `prepare_data.py` writes a digest of the parsed records
  (accession, patient, month and sequence, sorted) instead, and that digest is the input's `sha256` in
  `results.json`.
* MUSCLE's progressive alignment depends on the order of its input, and E-utilities does not
  return the GenBank records in a fixed order. `prepare_data.py` sorts each patient's sequences by
  accession before aligning, so a rerun gives the same alignment; without that the rate moved by 5
  percent between two downloads of the same records.
* `studies.py` is not part of the run that writes the results: it rebuilds alignments and refits, and its
  output (`studies.json`) is the evidence behind the causes, not a result.
