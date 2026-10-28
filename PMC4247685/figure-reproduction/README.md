# Figure reproduction (PMC4247685)

We rebuild Figs 2 to 5 of Curry (2014) with the tools the figures show: R base graphics for Figs 3 to 5
and ggplot2 for Fig. 2. Each render is mapped onto the published figure's pixel grid using its plot frame
alone, so the two images overlay directly and nothing inside the frame is fitted.

Site: <https://jeonglab-bcm.github.io/fossil/PMC4247685/> (side by side, swipe, blink, overlay and
difference views).

## Results

| Item | Result |
| --- | --- |
| Fig. 5 | Same data as the paper: the clinical rows of Table S3 (the validation cohort, 20 + 20 patients). 100% of the published curve pixels lie within 2 px of ours and the reverse. Logrank p = 0.12 for progression-free and 0.12 for overall survival; the paper prints 0.15 and 0.1. |
| Fig. 2 | Rerun of the synthetic benchmark: 40 new Algorithm 2 datasets per structure, GABi 0.1 with the S1 models, ISA, CC, Plaid and Bimax. cor: GABi.cor has the highest median (0.59, paper 0.64) and beats all six other methods (paired Wilcoxon p < 0.001). highvar: GABi.highvar beats five of six; Bimax has a higher median (p = 0.027). block: GABi.block's median is 0.02 against the paper's 0.40; Algorithm 2's offset is negative in 21 of 40 datasets, where the block model cannot see the block. |
| Fig. 3 | Reconstructed. GABi with S1's dysregulation-vs-outcome model on the Table S3 probes in 477 high-grade TCGA OV tumours (UCSC Xena) finds 146 bicluster and 146 control tumours over 3,682 CpG sites (paper: 21, 21 and 14,382). The bicluster's sites co-vary more than the control set's, with the small negative mode near -0.55 the paper shows, but the peaks sit at 0.62 and 0.43 against the paper's about 0.8 and 0.25. |
| Fig. 4 | Same reconstruction. Progression-free intervals differ strongly (logrank p = 3 × 10⁻¹⁴) but the other way from the paper: median 11.5 months for the bicluster against 22.3 for the control set (paper: 85.4 against 32). GABi's survival term uses a two-sided logrank p, so the search can land on either direction. |
| Tables S2 and S3 | Both list "the 14,382 CpG sites" of the bicluster but share 8,904. S3's probes co-vary in TCGA (mean \|r\| 0.27, like the shared probes); S2's own behave like random probes (0.10). The TCGA run uses S3's list. |

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | Nextflow pipeline that runs every step below. |
| `pipeline/` | Scripts (R, Python, shell). |
| `data/` | What each step writes and the committed results the check compares against. |
| `published/` | Figs 2 to 5 of the paper, © 2014 Curry, CC BY 4.0, used for comparison. Figs 3 to 5 are inverted from the PDF's separation colour space. |
| `output/` | Our renders on the published pixel grid, and a comparison summary per figure. |

## Run

Requirements: R with ggplot2, survival, data.table, jsonlite, isa2, hash, and the archived CRAN packages
biclust 2.0.3.1 and GABi 0.1; Python 3 with numpy, scipy and pillow; Nextflow with Java 17 or later.

```sh
nextflow run PMC4247685/figure-reproduction/main.nf --outdir results
nextflow run PMC4247685/figure-reproduction/main.nf --outdir results --rerun_ga --cores 6   # also rerun both genetic algorithms
```

The run downloads Additional files 1 to 3 (Springer) and the TCGA OV data (UCSC Xena) and checks each
file's SHA-256 (`--sources DIR` reuses local copies). It writes the data, the renders, the comparison
page and `results/report.md`, and fails if Fig. 5 no longer matches the published figure. The GitHub
workflow `.github/workflows/reproduce-pmc4247685.yml` does the same run on Ubuntu.

## Pipeline steps

| Step | Script | Output |
| --- | --- | --- |
| Fetch and check inputs | `fetch_inputs.sh` | S1 to S3, HumanMethylation27, clinical and survival tables |
| Measure the published figures | `paper_measure.py`, `fig2_measure.py` | frames and ticks of Figs 3 to 5; Fig. 2 box statistics read from its pixels |
| Fig. 5 data | `make_fig5_data.R` | `fig5_clinical.csv`, `fig5_tests.json` |
| Fig. 2 benchmark | `fig2_benchmark.R` (with `--rerun_ga`) | `fig2_scores.csv` |
| Fig. 2 comparison | `fig2_compare.R`, `fig2_block_check.R` | `fig2_boxes.csv`, `fig2_tests.json`, `fig2_block_check.json` |
| Tables S2 and S3 | `s2_s3_check.R` | `s2_s3_check.json` |
| TCGA input | `tcga_prepare.R` | the matrix of Table S3 probes by 477 high-grade primary tumours, `tcga_samples.csv` |
| TCGA bicluster | `tcga_gabi.R`, `gabi_parallel.R` (with `--rerun_ga`) | `tcga_bicluster_seed1.json` |
| Figs 3 and 4 data | `make_fig34_data.R` | densities, groups, summary |
| Renders | `plot_base.R`, `plot_fig2.R`, `align.py` | `output/fig*_ours.png`, `output/fig*.json` |
| Comparison page | `build_page.py`, `page_template.html` | `site/PMC4247685/index.html` |
| Check | `check_reproduction.py` | `report.md` |

## Limits

- The paper reports neither GABi's thresholds (consistency, ρ, α) nor the comparison methods' settings.
  We use GABi 0.1's defaults with consistency 0.8, ρ 0.5 and α 0.05, and the packages' defaults.
- As published, S1's `getFitnesses` takes −log p of R's Spearman test without a floor; R returns p = 0 for
  the seed row against itself and, at 16 to 21 samples, for a band of ρ below 1, and GABi scores the
  resulting infinity as 0. `tcga_gabi.R` adds the 2e-16 floor that S1's own selection function uses.
- The 2013 TCGA level-3 files are no longer served. UCSC Xena's copy rounds β-values to 4 decimals; we
  spread each value over its rounding interval. Progression-free intervals come from the TCGA Pan-Cancer
  clinical resource, not the 2013 portal.
- Figs 3 and 4 use the floored S1 model as published. A second run that also maps S1's correlation
  features to rows before choosing the comparison columns (`tcga_gabi.R ... floor+jprime`,
  `data/tcga_bicluster_seed1_jprime.json`, `data/fig34_summary_jprime.json`) finds 143 + 143 tumours over
  3,706 CpG sites, 3,435 of them shared with the first run, with the same result: correlation modes 0.60
  and 0.48, and a progression-free split the other way from the paper (11.5 against 24.0 months, logrank
  p = 1 × 10⁻¹⁶).
- `gabi_parallel.R` spreads GABi's fitness evaluations over forked workers; on a test problem its output
  is identical to the serial function's.
