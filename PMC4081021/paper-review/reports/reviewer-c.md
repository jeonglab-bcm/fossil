# Reviewer C report: documents/s002-pcbi-1003686-s002 (pages 1-14)

Scope: page JSONs `pages/page-0001.json` to `pages/page-0014.json` only. I did not edit plan.json, bundle.json, adjudications.json or anything under s001, and I ran no build commands. All 14 pages are `reviewed: true` with specific `review_notes`. Every file is valid JSON, the 132 item IDs are unique, all bboxes lie within the page, and every table has equal-width rows of strings.

What I checked: every page preview, 200-400 dpi PyMuPDF crops of every equation block, rotated renders of the landscape tables (pages 12-14), a rendered bbox overlay for both figures, and the positioned native text of every table cell.

## Conventions used (relevant for the coordinator and verifier)

- Headings: the supplement title is `##`, sections 1-4, Contents and References are `###`, subsections such as 1.1 or 3.1 are `####`, and sub-subsections such as 3.1.1 are `#####`. All bold markup was removed from headings.
- Display equations are transcribed as LaTeX `$$...$$` in `text` items (no formula crops remain), checked symbol by symbol against high-resolution crops. Species names are plain identifiers inside math, e.g. `[TrkA:NGF]`, and reaction arrows are Unicode `→`, which keeps the source lines searchable and line-coverage clean. Inline math uses `$...$`.
- The calligraphic model symbol is written `ℳ<sub>H3,2</sub>` in prose and `ℳ_H3,2` in CSV cells. NFKD maps it to "M", so coverage still matches `MH3,2`.
- Table minus signs are kept as U+2212, as printed.

## Per-page changes

| Page | Changes | Remaining doubts |
|---|---|---|
| 1 | Merged "Supplement:" and the title into one `##` heading (deleted item p0001-b001; its text is in b000). Restored superscript affiliation markers and the ∗ marker, and removed the `>` blockquotes. Contents set to `###`. The TOC had been mis-extracted as a 3-column dot-leader table with split words ("Ma / terial"). Converted it to a nested text list that keeps every entry and its printed page number. Page number omitted. | None. |
| 2 | Headings `###`/`####`. Restored CO<sub>2</sub> (3x), "37 °C" (3x) and the µl/µg spacing. Restored the real compound hyphen "laminin-precoated", which was lost at a line wrap. Page number omitted. | "LaGeSo" vs "LAGeSo" is a source inconsistency and is kept. |
| 3 | Headings. Fixed ×, µm<sup>2</sup>, the `data_scaling.m` file name (extraction had split it into code and strike-through fragments), and the italics spacing. Page number omitted. | None. |
| 4 | Headings 3.1.1-3.1.3 `#####`, 3.2 `####`. Replaced 4 formula crops and the flattened reaction list with LaTeX. Inline math fixed, including the bounds [10^-10, 10^10]. | Source quirk kept as printed: x1 = [TrkA:NGF]/k3 contradicts its own ODE and the main text, both of which imply x1 = k3[TrkA:NGF]. |
| 5 | Headings. Reaction list R1-R11, mass conservation, rate equations and the RRE model are now LaTeX. | Source quirk kept as printed: R10 rate = k10[Erk], while the ODE uses k10[pMek]. Page 6 starts a new paragraph after display math, so join_previous is not set. |
| 6 | Headings 3.2.3/3.3.1 `#####`, 3.3 `####`. Transcribed the long nested-fraction initial conditions x1(0)-x5(0) term by term. Rebuilt the R3 Hill-type rate, which extraction had garbled into superscripts: k3[TrkA:NGF][Ras:GDP]K3^n/(K3^n + [pErk]^n). | None. |
| 7 | Headings. Replaced 4 formula crops (ODEs with feedback, full parameter vector, RRE model, reduced vector) with LaTeX. Restored "non-identifiable". | Source quirks kept as printed: an unmatched "(" in the d[Ras:GTP]/dt numerator, and K3 listed twice in the full parameter vector. |
| 8 | Headings `###`. Removed the space before "." after `fmincon.m`. Checked the references (a 400-dpi crop confirms "Dina OA"). | "MATLAB R2103a" is a source typo (presumably R2013a) and is kept. |
| 9 | The page holds Supplement Table 1 as three printed blocks (Pathway model A/B/C) with identical columns. Extraction gave three tables plus two `#` headings. Merged them into one CSV, `supplementary-table-1` (28 rows × 12 columns), with a leading "Pathway model" column that repeats the block subheading. Headers: blank → "Model"; `ℓ(θ*) (10^4)`, `BIC (10^4)`, `ΔBIC`. Rebuilt from positioned native text. Caption is a separate caption item, with "log-normal" restored. | None. |
| 10 | Figure label "Supplement Figure 1", asset `supplementary-figure-1`. Tightened the bbox to [62, 66, 533, 715]: the content spans 68.5-526.5 × 72.5-709.5 pt, so the crop includes the legend and all panels and excludes the caption. Cleared the plot-label dump from the figure markdown. Caption is a separate item. | None. |
| 11 | Same treatment as page 10: `supplementary-figure-2`, same bbox. | **Caption error in the source:** it says ℳH3,2 (verified at 250 dpi), but the panel maxima (log10 k3[TrkA]0,1 ≈ −2.0, w1 ≈ 0.688) match Table 2 row ℳ_H3,3, and page 4 says Figures 1 and 2 show ℳH3,2 and ℳH3,3. Kept as printed and noted. |
| 12 | Rotated landscape page. The extraction had an empty caption item and one scrambled 14-column table. Transcribed the caption in full and rebuilt two CSVs from positioned text: `supplementary-table-2-weights-k1-k2-k4` (10×7) and `supplementary-table-2-k3trka0-k5-serk0` (10×8). A value centred across both subpopulation sub-columns (weights "1" for H1; k3[TrkA]0 for H1/H2; s[Erk]0 for H1/H3, confirmed by the missing inner rules) goes in a parent column whose header ends in "(merged cell)". | Source quirk kept: for ℳ_H3,1 the w1/w2 confidence intervals look swapped (+0.687 (+0.302, +0.324)). |
| 13 | Rotated page. Transcribed the caption (bold through "[NGF]0 = 1 nM."). Added "Subpopulation 1/2" as bold text items. Two CSVs: `supplementary-table-3-subpopulation-1` and `-2` (10×6 each). Item IDs p0013-b000 to b000d. The H1 "−" cells are kept. | None. |
| 14 | Same treatment as page 13: `supplementary-table-4-subpopulation-1` and `-2` (10×7 each). The page-level extraction warning ("needs cell review") is kept in `warnings` for the record; the rebuild resolves it. | None. |

## Local verification simulation

I ran the builder's own `canonical`/`number_tokens` functions against my page text and CSV rows (not the real build):

- Pages 1-3, 5, 8 and 10-14 are clean on both missing lines and number tokens.
- These pages will need adjudications. All are parser-only artefacts of fraction and superscript layout:
  - **Page 4:** 1 missing line (`x2(0) = k4(s[Erk]0)`, split by `\frac`). Number differences come from exponents flattened in the text layer (`1010` = 10^10, `−10`, `102`, `101`) and from LaTeX `-` vs U+2212.
  - **Page 6:** 6 missing lines from the x_i(0) fractions and the R3 Hill rate. Number differences as on page 4 ([10^-3, 10^3]).
  - **Page 7:** 3 missing lines from the Hill-term fractions. Same exponent number differences.
  - **Page 9:** no missing lines. Number difference: `104` ×6 (= 10^4 in the headers) vs `10`/`4`.
- I did not simulate the independent pypdf check.

## Proposed shared changes (coordinator)

1. **Source title (bundle.json and plan.json):** the main paper calls this document "Supporting Information S1" (file pcbi.1003686.s002; s001 is the Code S1 zip). Suggested title: "Supporting Information S1 (pcbi.1003686.s002): Supplemental notes regarding the computational modelling". The coordinator's brief calls it "Text S2", but the main text's references to "Figures 1 and 2 / Tables 2, 3 and 4 in Supporting Information S1" point to this file.
2. **Plan note for s002** (suggested wording): "Display equations transcribed to LaTeX with species names as plain identifiers; calligraphic ℳ_Hx,y model labels. Supplement Table 1 merged from three printed blocks into one CSV with a 'Pathway model' column. Tables 2-4 are kept as printed sub-tables (two CSVs each). A '(merged cell)' column holds values printed centred across both subpopulation sub-columns. Source errors are kept as printed: Supplement Figure 2's caption names ℳH3,2, but its panels match ℳH3,3 (Supplement Table 2); x1 = [TrkA:NGF]/k3 on page 4; MATLAB 'R2103a'."
3. **Adjudications:** expect entries for s002 pages 4, 6, 7 and 9 as described above.
4. **Asset names in use:** supplementary-table-1; supplementary-table-2-weights-k1-k2-k4; supplementary-table-2-k3trka0-k5-serk0; supplementary-table-3-subpopulation-1/-2; supplementary-table-4-subpopulation-1/-2; supplementary-figure-1/-2. There are no formula assets (all equations are transcribed). None of these collide with s001's names (figure-N, table-N).

## Contents of S2

S2 covers only the NGF/Erk1/2 application. It has **nothing on the conversion-reaction (simulation) example**; those settings must come from the main text or Code S1.

### 1 Material and Methods (pp. 2-3)

Supports the main-text Methods and the co-labelling validation (main Fig. 6):

- **Reagents and antibodies:** anti-pErk (Thr-202/Tyr-204) 1:200; anti-Erk 1:500; Alexa-594/633 secondaries 1:1000/1:500.
- **Cell culture and stimulation:** male Sprague Dawley rats; L1-L6 DRG neurone culture; 15-20 h culture before NGF stimulation; fixed with PFA 4%.
- **QuAM:**
  - Zeiss Axioplan 2 with Metacyte, 10× objective, 1280×1024 images.
  - Exposure time set automatically (≤ 1000 saturated pixels per 100 µm²), with a maximum of 0.96 s.
  - Neurone selection: size 150-1500 µm², aspect ratio 2, concavity depth 0.25, object threshold 30%.
  - Intensity is normalised by area and exposure.
- **1.8 Data preprocessing:** all values from one day are scaled by a constant chosen to minimise the quadratic mismatch of mean intensities across replicates, using all data rather than controls only (`data_scaling.m` in Code S1).

### 2 Estimation, uncertainty, model selection (p. 3)

- **Estimation:**
  - Multi-start local optimisation with at least 100 runs per model; more runs are added if the best value is not hit at least 5 times.
  - All parameters except the weights are log-transformed.
- **Uncertainty:**
  - Asymptotic CIs from the Hessian.
  - Finite-sample CIs from profile likelihoods (ref. Raue 2009).
- **Model selection:** BIC. The decision rule visible in Table 1 is "rejected" if ΔBIC > 10.

### 3 Pathway models (pp. 3-7)

Supports main Fig. 3A/4A (model A) and Fig. 5 (models A/B/C).

- **Model A:**
  - Reactions R1-R5: TrkA/NGF binding and unbinding, TrkA:NGF-induced and basal Erk phosphorylation, dephosphorylation.
  - Assumes [NGF]0 ≫ [TrkA]0.
  - Reformulated states are x1 and x2 = s[pErk].
  - Reduced parameters: k = (k1, k2, k4, k5, k3[TrkA]0, s[Erk]0).
  - Initial condition is the steady state at [NGF]0 = 0: x1(0) = 0, x2(0) = k4 s[Erk]0/(k4 + k5).
- **Model B:** cascade TrkA → Ras → Raf → Mek → Erk (R1-R11), with x1..x5 = k3[TrkA:NGF], k6[Ras:GTP], k8[pRaf], k10[pMek], s[pErk].
  - Reduced parameters: (k1, k2, k4, k5, k7, k9, k11, k3[TrkA]0, k6[Ras]0, k8[Raf]0, k10[Mek]0, s[Erk]0).
  - Closed-form steady-state initial conditions x1(0)..x5(0).
- **Model C:** model B plus negative feedback from pErk onto R3, as the Hill factor K3^n/(K3^n + [pErk]^n).
  - In scaled form: x1(sK3)^n/((sK3)^n + x5^n).
  - Extra parameters: sK3 and n.
  - Same initial condition as model B.
- **Parameter bounds:**
  - Model A: k_i ∈ [10^-10, 10^10].
  - Models B and C: k_i ∈ [10^-3, 10^3]; the range was narrowed because of ODE solver failures.
  - All models: w_i ∈ [0, 1]; normal SDs ∈ [10^-1, 10^2]; log-normal shape parameters ∈ [10^-1, 10^1].
- **Model C filter:** fits whose simulated 1 ng/ml NGF trajectory has more than 5 peaks in 0-60 min are discarded.

### 4 Implementation (p. 8)

MATLAB ("R2103a", for Mac), `fmincon`, an in-house profile-likelihood code, SUNDIALSTB/SUNDIALS. The m-files are in the supporting material (Code S1).

### Supplement Table 1 (p. 9)

- ℓ(θ*), BIC, rank, ΔBIC and decision for the 9 ODE-MMs (H1-H3 × normal-mean, log-normal-mean, log-normal-median) under each of pathway models A, B and C.
- **Main Fig. 5B (BIC comparison across pathway models)** can be plotted directly from this CSV.
- Block A is identical to **main Table 2**.
- Parameter counts: A = 17/30, B = 23/36, C = 25/38 (H1 / H2-H3).
- The optimal model is ℳH3,3 for every pathway model; ℳH3,2 is "not rejected" only for model A (ΔBIC 2.189).

### Supplement Figures 1-2 (pp. 10-11)

- Profile-likelihood and local-approximation likelihood-ratio curves (95% level line) for all 28 parameters of pathway model A.
- Parameters shown: k1, k2, k4, k5, k3[TrkA]0,1/2, s[Erk]0, w1, and the SDs for the kinetic series (t = 0/5/15/30/60 min at 1 nM NGF) and the dose response (0/0.001/0.01/0.1/1/10 nM at 30 min) for both subpopulations.
- Fig. 1 is ℳH3,2; Fig. 2 is captioned ℳH3,2 but its panels match ℳH3,3.
- Main text cites them for the identifiability claim next to **main Fig. 4D**.

### Supplement Tables 2-4 (pp. 12-14)

- MLEs and 99% profile-likelihood CIs for pathway model A only, all 9 models; bounds outside [−6, 6] are written as < −6.0 / > +6.0.
- **Table 2:** weights, log10 k1, k2, k4, k3[TrkA]0 (per subpopulation for H3), k5, s[Erk]0 (per subpopulation for H2).
- **Values for reproduction (ℳH3,2 / ℳH3,3):**

  | Parameter | ℳH3,2 | ℳH3,3 |
  |---|---|---|
  | w1 | 0.697 | 0.688 |
  | log10 k1 | −0.589 | −0.556 |
  | log10 k2 | −1.309 | −1.190 |
  | log10 k4 | −1.347 | −1.368 |
  | log10 k3[TrkA]0,1 | −1.899 | −2.009 |
  | log10 k3[TrkA]0,2 | −0.416 | −0.489 |
  | log10 k5 | −0.511 | −0.526 |
  | log10 s[Erk]0 | +0.904 | +0.884 |

  Subpopulation 1 (about 70%) has low TrkA. The k3[TrkA]0 difference is about 1.5 log units, consistent with the "30-fold" TrkA claim in the main text.
- **Table 3:** log10 SDs for the 1 nM NGF kinetic at t = 0, 5, 15, 30, 60 min.
- **Table 4:** log10 SDs for the t = 30 min dose response at [NGF]0 = 0, 0.001, 0.01, 0.1, 1, 10 nM.
- Tables 3-4 give the per-condition σ values, i.e. the data conditions of main Figs. 3-4.
- **Not provided in S2:**
  - MLEs for pathway models B and C, so the per-model subpopulation sizes in main Fig. 5C are not tabulated here and must come from Code S1 result files.
  - Measured data values.
