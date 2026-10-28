# Figure and Table 1 reproduction (PMC4081639)

We rebuild Figs 2, 4, 5 and 6 and Table 1 of Yu & Shaw (2014). We draw the figures with the same tools
that the paper's figures show: R, ggplot2 with its 2013 default theme, and tikzDevice with pdfLaTeX.
Each render has the published figure's exact pixel size, so the two images overlay directly.

Site: <https://jeonglab-bcm.github.io/fossil/PMC4081639/> (side by side, swipe, blink, overlay and
difference views, and Table 1).

## Results

| Item | Result |
| --- | --- |
| Fig. 2 | Same data as the paper: ψ = `seq(1e-11, 1e-10, length.out = 300)`, Eq. (6) with R's `lgamma` in x86 arithmetic (no FMA, 80-bit `sum`). Our curve covers 100% of the published curve pixels, and the paper's curve covers 100% of ours. |
| Fig. 4 | Same data as the paper. The mesh values come from the authors' compiled library. |
| Fig. 5 | Same n grid and same error unit (whole ulps). 26 of 50 VGAM marks are identical. The authors' mesh library, run here under Rosetta, gives 1–3 ulp errors where the paper shows 0. |
| Fig. 6 | Re-timed on Apple Silicon. Our mesh code is 13.2–13.3× slower than the paper's at every n, so one constant puts it on the paper's axis. The VGAM ratio goes from 4× to 77×: our R code grows linearly with n, but the published VGAM times do not. |
| Table 1 | ψ = 0.003892, 0.006394, 0.008016, 0.010388. All four round to the published 0.00389, 0.00639, 0.00802, 0.01039. |

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | Nextflow pipeline that runs every step below. |
| `pipeline/` | Scripts (R, Python, C), the data each step reads and writes, and `params/` (render settings per figure). |
| `published/` | The four published figures, used only for comparison. © Oxford University Press. |
| `hmp-data/` | HMP 16S count matrices (saliva, throat, tongue, tonsils; 21 taxa), from the CRAN package HMP 2.0.1 (Apache-2.0). |
| `output/` | Our renders: PDF, TeX, PNG aligned to the published pixels, and a fit summary per figure. |

## Run

Requirements: R with ggplot2, tikzDevice, jsonlite and microbenchmark; pdfLaTeX with `tikz` and
`preview`; Poppler (`pdftoppm`); Python 3 with numpy, scipy, mpmath and pillow; a C compiler; Nextflow
with Java 17 or later.

```sh
nextflow run PMC4081639/figure-reproduction/main.nf --outdir results
```

The run writes the data, the renders, the comparison page and `results/report.md`. The report
compares the run with the committed results. The run fails if Table 1 does not match the paper. The
GitHub workflow `.github/workflows/reproduce.yml` does the same run on Ubuntu (x86_64).

## Pipeline steps

| Step | Script | Output |
| --- | --- | --- |
| Measure the published figures | `paper_measure.py` | curve traces, Fig. 5 and Fig. 6 axis limits, Fig. 6 box medians |
| Candidate ψ grids for Fig. 2 | `eq6_grids.R`, `score_eq6.py` | ranking of grids against the published curve |
| Fig. 2 data | `make_fig2_data.py` | `fig2_data.csv` (x86 arithmetic), `fig2_data_native.csv` (this platform's R) |
| Fig. 4 data | `make_fig4_data.py` | `fig4_data.csv` |
| Fig. 5 data | `fig5_score2.py`, `fig5_vgam_variants.py`, `make_fig5_data.py` | `fig5_data.csv` |
| Fig. 6 timing | `mesh_native.c`, `fig6_vgam.R`, `make_fig6_data.py` | `fig6_data.csv`, `fig6_data_scaled.csv` |
| Table 1 | `mesh_lib.c`, `table1_native.py` | `table1_result.json` |
| Renders | `final.py`, `fit_render.py`, `plot_fig.R` | `output/fig*.{pdf,tex,png,json}` |
| Comparison page | `build_page.py`, `page_template.html` | `site/PMC4081639/index.html` |
| Check | `check_reproduction.py` | `report.md` |

## Limits

- `fig4_mesh.txt` and `fig5_lib.txt` are outputs of the authors' `lldmn` library (x86_64 macOS build,
  run under Rosetta). This repository does not include that library. The pipeline reads these files and
  does not recompute them.
- `fig6_mesh.csv` and `timing.c` record a timing run of the authors' library under Rosetta. Rosetta
  makes it about 80 µs slower per call, so Fig. 6 does not use it.
- Fig. 6 timings change with the machine. The CI run on GitHub hardware gives other scale factors.
- The render settings in `params/` came from a fitting step against the published images
  (`fit3.py`, `fit4.py`, `fit6.py`, `autotune.py`, `offsets.py`, `title_sizes.py`, `overlay.py`). The
  pipeline uses the saved settings and does not run that search again.
