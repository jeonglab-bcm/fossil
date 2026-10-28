# Figure reproduction (PMC1847688)

We rerun LIMPIC 1.1, the MATLAB code the paper ships as Additional File 1, on the paper's own
spectra (Additional Files 2 and 3) and draw the results on the published figures' pixel grids.
The authors' original 600 dpi figure files are used for the comparison. Each panel's pixel to
data map comes from its axes box and tick marks alone; nothing inside the box is fitted.

LIMPIC runs here as a Python port (`pipeline/limpic.py`). Each function follows the MATLAB
file of the same name statement by statement. The port gives the same result as the authors'
code run in GNU Octave: every intermediate signal, all 9,071 plasma peaks, all 20,001 in-vitro
peaks and every peak class, identical to six decimals (`output/port_check.json`).

## Results

| Item | Result |
| --- | --- |
| Fig. 2 | The example spectrum is plasma file `P_15`. The figure plots its raw counts divided by 5. 99.99% of the published trace pixels lie within 2 px of ours, and 99.96% of ours within 2 px of theirs. |
| Fig. 3 (a to d) | Raw minus LIMPIC's smoothing at window 10, 20, 30 and 40, divided by 5. 99.99% both ways, ours 99.1% or better. |
| Fig. 4c | Same as Fig. 3b: 99.97% and 98.99%. |
| Fig. 5, peak-elimination | LIMPIC's baseline, divided by 5: 99.38% and 94.69%. The curves overlay except at one block near 7.25 kDa, where ours dips to 1.5 and the published one does not; the rest of the gap is the published blue curve covering the red. |
| Fig. 5, monotone-minimum | The comparison baseline: 99.99% and 98.45%. The paper gives no settings for it. A wavelet-denoised running minimum, CROMWELL's approach, reproduces it with one combination found by search (`pipeline/monotone_min.py`); neighbouring settings fall to 72% or below. |
| Fig. 6 (a to d) | Raw spectrum and what LIMPIC removes from it (smoothing residual plus baseline), divided by 5: 97.6% or better in a, b and d, 97.9% and 96.9% in c. |
| Fig. 7, LIMPIC | The processed spectrum, 8.73 to 9.02 kDa: 99.57% and 99.93%. The same 16 peaks, each with a published marker at our position, and no published marker without one of ours. |
| Fig. 8 | Same curve and the same 16 peaks (100% and 99.96%). Our 30-spectrum classification colours 9 of the 16 the same way as the paper. |
| Fig. 9a, 9b | Drawn from Additional File 4 (the authors' plasma peak classes), not from our run: 9a 98.6% and 99.5%. 9b, `hist(PDR, 10)`: the bar edges fall on the published ones, and the counts [801, 359, 207, 106, 49, 28, 7, 6, 6, 12] against published bars read as [811, 359, 208, 108, 47, 21, 7, 6, 6, 12]. |
| Tables 1 to 3, LIMPIC rows | Not reproduced. In the in-vitro spectra LIMPIC 1.1 finds about 667 peaks per spectrum (paper: 16) and 500 to 717 classes per concentration (paper: 7 to 11). Plasma: 302 peaks per spectrum and 104 classes (paper: 146 and 62). Both sets are in `output/report.md`. |

Figs 1 and 10 and the APEX, CENTROID and CROMWELL panels of Figs 4, 6 and 7 are not attempted. Fig. 1 is a
diagram. APEX and CENTROID are Bruker FlexAnalysis, which is proprietary; the paper does not give
CROMWELL's settings, and Fig. 10 also needs the masses of the 68 reference proteins, which
Additional File 5 does not list. Figs 9c and 9d are not reproduced either; see below.

## What the code does, against the paper

- **Kurtosis.** `find_intervals.m` keeps 100 Da blocks with `kurtosis(block, 0) < 1`. MATLAB's
  `kurtosis` is 3 for Gaussian noise and never below 1, so no block passes and `rem_baseline.m`
  stops with an index error: the published code does not run. With an excess kurtosis (0 for
  Gaussian noise) Figs 7 and 8 come back peak for peak. The paper's Eq. 3,
  E{v⁴} − 3(E{v²})², is the same quantity before normalization, and its text says 150 Da blocks.
- **"Kaiser filter".** `kaiser.m` is a Savitzky-Golay smoother (degree 2), the moving
  least-squares code of MATLAB's `smooth`; `prepro.m` runs it forward and backward with a frame
  of half the window length. The paper's Figs 3 and 4 label this filter "Kaiser".
- **Baseline and noise.** The baseline runs through the minima of the kept blocks and the noise
  level is the block mean minus minimum plus 3 standard deviations, both pinned to 0 at the
  highest m/z. The paper says the baseline uses block averages and the noise level the standard
  deviations.
- **PDR selection.** `multiple_spectra.m` selects classes with more than half the spectra; the
  figure captions say "larger than or equal to 0.5". In Additional File 4 that is 59 classes
  against 62, and the paper reports 62.

## Additional File 4 cannot be regenerated

Additional File 4 lists 7,893 peaks in 1,581 classes; the paper's text says 4,382 peaks in 1,581
classes. Running LIMPIC 1.1 on the 30 plasma files gives 9,071 peaks in 2,077 classes. Over a
search of kurtosis definitions (Eq. 3 as printed, excess, unbiased excess), block widths (100,
150 Da) and baselines (block minima, block means), at most 17% of our peak intensities equal an
Additional File 4 value to three decimals, where an identical run would match nearly all of
them. Its 30 subjects cannot be matched to the 30 files by peak positions or intensity profiles
either. Fig. 9a and 9b agree with Additional File 4, and Fig. 8's colours agree
with neither it nor our run, so the published classification came from a run we cannot repeat.

## Figs 9c and 9d use a noise model the code does not have

Each stem of Fig. 9c is an Additional File 4 class's mean intensity (its MEAN column) divided by
a smooth noise curve. Read off the 62 stems, that curve is close to
0.137 + 1.57 · exp(−(m/z − 6000) / 873), with m/z in Da: it falls from about 1.1 at 6.4 kDa to a
floor of about 0.137 above 11 kDa. LIMPIC 1.1's noise estimate is jagged, because it interpolates
between 100 Da blocks, and the paper describes no smooth model. Fitting the same curve to our noise
estimates, for the average spectrum or for each spectrum, gives other constants. Drawing 9c and 9d
would mean taking the curve from the figure itself, so they are left out.

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | Nextflow pipeline that runs every step below. |
| `pipeline/limpic.py` | LIMPIC 1.1 ported to Python. |
| `pipeline/monotone_min.py` | Fig. 5's monotone-minimum baseline (the comparison method). |
| `pipeline/octave/` | Driver for the authors' MATLAB code in GNU Octave, with two stand-ins: `read_txt.m` (the original opens a file dialog) and `kurtosis.m`. |
| `pipeline/` | The other scripts (Python, shell). |
| `published/` | Figs 1 to 10 of the paper: the authors' original files, © 2007 Mantini et al., licensee BioMed Central, CC BY 2.0, converted from TIFF to PNG. |
| `output/` | `fig*_ours.png` (our traces on the published axes; panels made with other software are cut away), `fig*_overlay.png` (published blue, ours orange where they differ), `comparison.json`, `tables.json`, `port_check.json`, `report.md`. |

## Run

Requirements: Python 3 with numpy, scipy, pandas, pillow, pywavelets and xlrd; Nextflow with Java 17 or
later; GNU Octave only for `--octave`.

```sh
nextflow run PMC1847688/figure-reproduction/main.nf --outdir results
nextflow run PMC1847688/figure-reproduction/main.nf --outdir results --octave   # also check the port against the authors' code
```

The run downloads Additional Files 1 to 4 (Springer) and checks each file's SHA-256
(`--sources DIR` reuses local copies). It takes under a minute without `--octave`. It writes
the data, the renders, the comparison and `results/report.md`, and fails if a reproduced panel
drops below its required match. The GitHub workflow `.github/workflows/reproduce-pmc1847688.yml`
does the same run, with `--octave`, on Ubuntu.

## Pipeline steps

| Step | Script | Output |
| --- | --- | --- |
| Fetch and check inputs | `fetch_inputs.sh` | Additional Files 1 to 4 |
| Additional File 4 as CSV | `export_s4.py` | `S4_LIMPIC.csv` |
| LIMPIC on all 60 spectra | `run_limpic.py`, `limpic.py` | peaks, classes and the `P_15` signals |
| Port check (with `--octave`) | `octave/run_limpic.m`, `check_port.py` | `port_check.json` |
| Figures | `compare.py`, `figmeasure.py`, `monotone_min.py` | `fig*_ours.png`, `fig*_overlay.png`, `comparison.json` |
| Tables | `make_tables.py` | `tables.json` |
| Check | `check_reproduction.py` | `report.md` |

## Limits

- Line 32768 of `SOL_5_TXT/SOL_calib_08e.txt` is damaged in the publisher's archive (the zip's
  CRC check fails on that file): it reads `22056.02642`. Both the port and the Octave driver skip
  it. It lies at 22 kDa, outside the 5 to 20 kDa range of the figures.
- The divisor 5 for Figs 2, 3, 4c, 5 and 6 is read from the figures; the paper does not state it.
  At 0.19 or 0.21 times the counts, Fig. 2 drops from 99.99% to 98.97% and 98.26%.
- The comparison draws our traces 3 px wide (5 and 6 px in Figs 7 and 8, as published) and
  counts a pixel as matched within 2 px.
