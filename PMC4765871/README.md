# PMC4765871: Reconstructing gene regulatory dynamics from high-dimensional single-cell snapshot data (Ocone et al. 2015)

Ocone A, Haghverdi L, Mueller NS, Theis FJ. Reconstructing gene regulatory dynamics from
high-dimensional single-cell snapshot data. *Bioinformatics* 31(12):i89–i96 (2015).
[doi:10.1093/bioinformatics/btv257](https://doi.org/10.1093/bioinformatics/btv257) ·
[PMC4765871](https://pmc.ncbi.nlm.nih.gov/articles/PMC4765871/)

The paper is © The Author 2015, published by Oxford University Press under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). In keeping with the rest of this
repository, this folder does not contain the paper, its supplement or their full text.
`figure-reproduction/published/figure-*.png` are the paper's Figures 1 to 9, rendered from its PDF
at 600 dpi for comparison only, and redistributed non-commercially under CC BY-NC 4.0 with the
attribution above. A few numbers of the supplement are transcribed in
`figure-reproduction/pipeline/params/` with their source.

The haematopoietic data are Supplementary Table 3 of Moignard et al., *Nat. Cell Biol.* 15:363
(2013), [doi:10.1038/ncb2709](https://doi.org/10.1038/ncb2709). The pipeline downloads them and
checks their SHA-256; they are not redistributed.

The authors' code (C++ and Matlab, `inferenceSnapshot.zip`) is lost. The framework is rebuilt here
from the paper: diffusion maps, branch clustering, Wanderlust, GENIE3, Hill ODE models with AND and
OR gates, Metropolis MCMC, thermodynamic integration and AIC/BIC.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The rebuilt framework, the FFL and toggle switch simulations, the haematopoietic analysis, every figure redrawn on the published pixel grid and scored, and the Nextflow pipeline. |
| [`results.json`](results.json) | Every figure panel, table and claim of the paper, with our numbers, the verdicts computed from them and the cause of each mismatch. |
| [`session/`](session/) | The record of the session that made this reproduction. |

## Results

Every verdict below is computed by `figure-reproduction/pipeline/check_results.py` from the numbers
in [`results.json`](results.json); nothing is typed by hand. "Measure" counts the values that match
at the printed precision, or gives the share of the published line within 2 px of ours.

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Fig. 1 (diagram) | not attempted | not attempted | A diagram of the framework. Its panels B to D and H reuse toggle switch results, scored in Fig. 1H, Figs 5 and 6 and supp. Fig. 6. |
| Fig. 1H, toggle switch posterior means | partly | 1 of 6 fields as printed | Our prior on lambda (SD 0.025) does not hold lambda at 0.25: its posterior mean is 0.34, and alpha (357) moves with it. kappa+ comes within 1% of Fig. 1H, the other three parameters within 7%. |
| Toggle switch: mean relative error about 6.8% | differs | 0 of 1 fields as printed | Our posterior means give 20.3%. With a prior ten times tighter the same fit gives 7.2%, so the paper's prior was most likely much tighter than ours; the paper does not give it. |
| Fig. 2A, gZ ordered worst | agrees | 2 of 2 fields as printed | Assumed: FFL input gX(t): logistic growth from 320 towards 1000 with rate 1/7 and a floor at 300, with the system noise; the paper says only 'a sigmoid-shape stochastic function'; FFL system noise sigma_s = 2 (time step 0.01) |
| Fig. 2B (FFL structures) | not attempted | not attempted | A schematic of the I1-FFL with AND and OR gates. |
| Fig. 2C, 3D snapshot | not attempted | not attempted | A 3D scatter of the 300 simulated cells; the camera of the view is not recoverable and the cells are a different random draw. The same cells are scored in Fig. 2A and 2D. |
| Fig. 2D, OR gate fit (red) | inconclusive | 12.45% within 2 px (pass 90.0%, best control 12.9%) | Our cells are a new random draw and our Wanderlust ordering widens the gZ pulse, so the fitted curves lie off the published ones by more than 2 px over most of their length. |
| Fig. 2D, AND gate fit (green) | differs | 5.65% within 2 px (pass 90.0%, best control 9.0%) | As for the OR fit: a new draw of cells and a wider gZ pulse. |
| Supp. Fig. 13, FFL GENIE3 weights and correlations | partly | 3 of 7 fields as printed | The weights and correlations come from another random draw of 300 cells; GENIE3's weights also depend on its settings. |
| Supp. Fig. 14, AIC and BIC of the 12 FFL models | partly | 2 of 15 fields as printed | The AIC and BIC values scale with the number of observations and the likelihood SD, neither of which the paper gives (its BIC minus AIC implies about 100 to 150 observations; we fit 900). The ranking is the comparison that counts. |
| FFL: Bayes factors above 100 | partly | 2 of 4 fields as printed | Both Bayes factors exceed 100 as in the paper; the log evidences themselves scale with the number of observations and the likelihood SD, which the paper does not give. |
| FFL: mean relative error about 17% | differs | 0 of 1 fields as printed | Our MAP estimates put alpha and lambda about 35% low with their ratio near the truth, as the paper reports for Fig. 3; the Hill coefficients come out lower than the paper's, which moves the mean error. |
| FFL: 14.5% with an informative prior | differs | 0 of 1 fields as printed | Our informative prior (SD 0.025) does not move lambda against 900 observations; the paper's lambda of 0.249 implies a much tighter prior or fewer observations. |
| FFL: alpha/lambda exactly 400 | differs | 0 of 1 fields as printed | Our ratio comes back 3% below 400, not exactly 400. |
| Fig. 3, FFL posterior modes | partly | 1 of 7 fields as printed | alpha, lambda, kappa+ and kappa- come back within 5% of the paper's modes (alpha 63.7 against 62.9, lambda 0.164 against 0.1575); the Hill coefficients do not (h+ 10.1 against 16.4, h- 7.0 against 12.1). The posteriors are narrow, so the 2% tolerance tests the point estimates. |
| Supp. Table 4, FFL parameter modes | partly | 1 of 10 fields as printed | Table 4's gZ values need lambda near 0.249, which our prior does not reach (see the informative-prior item). |
| Fig. 4, gY deletion | inconclusive | 15.57% within 2 px (pass 90.0%, best control 18.0%) | Our time axis ends at T_f = 44 (the mean time for gX to pass 960), the published one at 68, and our estimated lambda is 0.17, so the predicted transients are slower and shorter. |
| Fig. 4, knockdown | inconclusive | 18.68% within 2 px (pass 90.0%, best control 23.2%) | As for the deletion: a shorter time axis and a smaller estimated lambda. |
| Fig. 4, simultaneous perturbations | inconclusive | 3.64% within 2 px (pass 90.0%, best control 3.9%) | As for the deletion: a shorter time axis and a smaller estimated lambda, which blunts the fast peak. |
| FFL: predictions fit the perturbed system | partly | 1 of 3 fields as printed | The deletion prediction fits (R^2 above 0.8); the knockdown and the simultaneous perturbation do not, because our lambda (0.17) slows the fast transients. |
| Supp. Fig. 6, four significant eigenvalues | agrees | 1 of 1 fields as printed | Assumed: Toggle switch system noise sigma_s = 6 (time step 0.01); Toggle switch start: gA = gB = 311 (the symmetric steady state), late genes 0; a cell stops when a late gene exceeds 960 |
| Fig. 5, left (3D branch) | not attempted | not attempted | A 3D view of one diffusion map branch coloured by pseudo time; the camera is not recoverable. The branch's series are scored in Fig. 5, right. |
| Fig. 5, gA series | inconclusive | 48.41% within 2 px (pass 90.0%, best control 51.5%) | Our cells are another random draw, so our dots cannot fall on the published ones; the branch length (about 140 cells) and the shape of each series come back, but a 1.5 shift of pseudo time scores about as well as ours. |
| Fig. 5, gB series | inconclusive | 55.48% within 2 px (pass 90.0%, best control 55.5%) | Our cells are another random draw, so our dots cannot fall on the published ones; the branch length (about 140 cells) and the shape of each series come back, but a 1.5 shift of pseudo time scores about as well as ours. |
| Fig. 5, gC series | inconclusive | 46.67% within 2 px (pass 90.0%, best control 47.9%) | Our cells are another random draw, so our dots cannot fall on the published ones; the branch length (about 140 cells) and the shape of each series come back, but a 1.5 shift of pseudo time scores about as well as ours. |
| Fig. 5, gD series | partly | 54.56% within 2 px (pass 90.0%, best control 53.2%) | Our cells are another random draw, so our dots cannot fall on the published ones; the branch length (about 140 cells) and the shape of each series come back, but a 1.5 shift of pseudo time scores about as well as ours. |
| Fig. 6, model scores for gC | partly | 4 of 8 fields as printed | AND(gA+, gD-) is best, as in the paper. The other scores differ: gD alone and the OR gate score 0.83 against the paper's 0.57 and 0.56, probably because their AIC gap to the best model is relatively smaller in our 837 observations. |
| Supp. Fig. 18 and text: the same for gD | agrees | 2 of 2 fields as printed | Assumed: Toggle switch system noise sigma_s = 6 (time step 0.01); Toggle switch start: gA = gB = 311 (the symmetric steady state), late genes 0; a cell stops when a late gene exceeds 960; GENIE3 with extra-trees, sqrt(p) candidate inputs per split, 1,000 trees, weights normalised per target |
| Supp. 1.3: Wanderlust in low and high dimension, 92% | differs | 0 of 1 fields as printed | Our pseudo times on the data and on four diffusion components correlate at 99.2%, closer than the paper's 92%. The paper does not say how its correlation is computed or which replicates it pairs. |
| Supp. 2.2.3, 2.2.4 and 2.2.7: further robustness runs | not attempted | not attempted | Not attempted. The runs with noise 200 and 300, Nn from 5 to 30, forward and backward start cells, three sampling functions and 200 cells rest on start cells picked by eye (supp. Fig. 22) and on sampling functions shown only as plots (supp. Fig. 26). |
| Fig. 6, gC fit, branch C | inconclusive | 14.98% within 2 px (pass 90.0%, best control 19.9%) | Our gC series is another random draw, drawn on the published axis by rank; the fitted curve rises later than the published one. |
| Fig. 6, gC fit, branch D | inconclusive | 18.28% within 2 px (pass 90.0%, best control 20.4%) | As for the top panel: another draw, and a pulse at another pseudo time. |
| Supp. Table 6, errors under observation noise | differs | 0 of 5 fields as printed | Our errors under observation noise scatter from 6.9 to 37.8% around the paper's 5.1 to 9.1%, with the same weak prior as our main fit. |
| Supp. Table 1, clustering errors | partly | 2 of 6 fields as printed | Low-dimensional clustering beats high-dimensional clustering at both noise levels, as in the paper, but our errors are about twice the paper's. The start and end cells were picked by eye in the paper, and its six regions are defined by plots we cannot read exactly. |
| Supp. Figs 17 and 25, inputs of gC | partly | 3 of 4 fields as printed | GENIE3 on our draw keeps the inputs of supp. Figs 17 and 25 only in part; the weights depend on the draw and on GENIE3's settings. |
| Supp. Table 7, 94 gC models | partly | 1 of 6 fields as printed | and(or(gA+, gB-), gD-) wins on BIC, AIC and the Bayes factor in our run; the paper's BIC and Bayes factor favour and(gA+, gD-). gB does not collapse out of our fit. |
| 597 cells after quality control | exact | 6 of 6 fields as printed |  |
| Fig. 7A (lineage diagram) | not attempted | not attempted | A schematic of the haematopoietic lineages. |
| Supp. Fig. 32A, maximum of <d> | exact | 1 of 1 fields as printed |  |
| Fig. 7B, diffusion map by cell type | inconclusive | 25.59% within 2 px (pass 90.0%, best control 25.7%) | The shape comes back (the four arms and the cell-type order), but the camera of the 3D view is fitted and our component order differs; doubling sigma scores as well, so the comparison cannot pin sigma down. |
| Fig. 7C, GENIE3 network (w > 0.08) | partly | 28 of 31 fields as printed | 28 of the 30 published edges come back and one edge is extra. All three differences lie within 0.002 of the 0.08 threshold: PU.1 to LMO2 0.0799, TEL to LDB1 0.0782, GFI1B to GATA2 0.0807. Which side of the threshold they fall on depends on the random trees. |
| Supp. Fig. 29, six correlations | partly | 5 of 6 fields as printed | Five of the six correlations come back at the printed precision; r(GFI1, GFI1B) is -0.4056 against -0.40. |
| Supp. 2.3.1, branch clustering errors | differs | 0 of 3 fields as printed | The paper picked the start and end cells by eye; ours are the tips of the embedding. Our GMP branch takes in 55 cells of other pathways (54 CLP, 1 PreMegE) of its 176. |
| Supp. Table 8, GATA2 models (CLP) | differs | 0 of 20 fields as printed | Our AIC values scale with our 958 observations (3 replicates of about 360 cells, after outlier removal) against the paper's about 115 points per series. Our best GATA2 model is and(GFI1, NFE2), the paper's new prediction, but SCL alone ranks last. |
| Supp. Table 9, GFI1 models (GMP) | differs | 0 of 6 fields as printed | Our best GFI1 model is GATA2 alone, which the paper ranks worst; our GMP ordering does not give GFI1 the clean low-to-high switch of supp. Fig. 28. |
| Supp. Table 9, GFI1B models (GMP) | differs | 0 of 6 fields as printed | Our best GFI1B model is or(GATA2, GFI1), with only GFI1 effective; the paper finds GATA2 and GFI1 each on their own. |
| Fig. 8, refined subnetwork | partly | 3 of 7 fields as printed | GFI1 inhibiting GATA2, AND(GFI1, NFE2) on GATA2 and GFI1 inhibiting GFI1B come back; the SCL edge, the GFI1B edge on GFI1 and the GATA2 edge on GFI1B do not. |
| Fig. 9, GATA2 with input SCL | inconclusive | 6.89% within 2 px (pass 90.0%, best control 7.8%) | Our series has three times as many cells and a different ordering, so the fitted step sits elsewhere and the curve lies off the published one. |
| Fig. 9, GATA2 with input GFI1 | inconclusive | 13.76% within 2 px (pass 90.0%, best control 14.7%) | Our series has three times as many cells and a different ordering, so the fitted step sits elsewhere and the curve lies off the published one. |
| Fig. 9, GATA2 with AND(GFI1, NFE2) | partly | 14.87% within 2 px (pass 90.0%, best control 14.4%) | Our series has three times as many cells and a different ordering, so the fitted step sits elsewhere and the curve lies off the published one. |
| Fig. 9, GFI1 with input GFI1B | differs | 3.11% within 2 px (pass 90.0%, best control 3.5%) | Our series has three times as many cells and a different ordering, so the fitted step sits elsewhere and the curve lies off the published one. |
| Fig. 9, GFI1B with input GATA2 | differs | 5.94% within 2 px (pass 90.0%, best control 16.6%) | Our series has three times as many cells and a different ordering, so the fitted step sits elsewhere and the curve lies off the published one. |
| Fig. 9, GFI1B with input GFI1 | differs | 5.80% within 2 px (pass 90.0%, best control 21.2%) | Our series has three times as many cells and a different ordering, so the fitted step sits elsewhere and the curve lies off the published one. |
| Fig. 9, points per series | differs | 0 of 3 fields as printed | The published series have 102 to 115 points; ours keep all cells of a pathway except the outliers removed (304 of 360 for GATA2 on CLP). |
| Claims recomputed from the paper's own numbers | agrees | 4 of 4 fields as printed, 3 paper errors | Assumed: Values read off the 600 dpi render of the vector figure |

2 exact, 4 agrees, 16 partly, 12 inconclusive, 15 differs, 6 not attempted; 38 open causes.

### Claims in the text

Each claim is a `text.*` item, compared with our run. `text.arithmetic` first recomputes the claims
from the paper's own numbers. 17% does not come back from Fig. 3's modes (they give 23.1%), a likely
error in the paper. 14.5% comes back from supp. Table 4 as 14.59% (truncated, not rounded) and
6.8% from the peaks of Fig. 1H as 6.6%; both are recorded as small slips. Our own sensitivity runs
(`figure-reproduction/output/sensitivity.json`: a tighter prior, more noise, another time scale) are
tests of causes, never agreement: a ten times tighter prior on lambda gives 7.2% for the toggle
switch, but our run gives 20.3%.

- FFL logic (partly): best model by AIC: paper or(gX+,gY-), ours or(gX+,gY-); second model by AIC: paper or(gX-,gY+), ours or(gX-,gY+); third model by AIC: paper and(gX+,gY-), ours or(gX-,gY-).
- FFL Bayes factors (partly): R(OR/AND) > 100: paper yes, ours yes; R(OR, gX+ gY- / OR, gX- gY+) > 100: paper yes, ours yes; log p(D|M) of OR, gX+ gY-: paper -385, ours -2331.0; log p(D|M) of OR, gX- gY+: paper -400, ours -2338.0.
- Toggle switch logic (partly): best model and(A+,D-) as in Fig. 6.
- Parameter errors (differs, differs, differs): FFL 28.1% (paper 17), with the informative prior 28.0% (paper 14.5); toggle 20.3% (paper 6.8).
- Haematopoietic network (partly): SCL activates GATA2 (CLP): paper yes, ours no; GFI1 inhibits GATA2 (CLP): paper yes, ours yes; AND(GFI1, NFE2) on GATA2 (CLP): paper yes, ours yes; GFI1B inhibits GFI1 (GMP): paper yes, ours no; GATA2 regulates GFI1 (GMP): paper no, ours yes; GFI1 inhibits GFI1B (GMP): paper yes, ours yes; GATA2 activates GFI1B (GMP): paper yes, ours no.

The paper's main claim holds on the simulated data: the OR gate wins for the feed-forward loop, and AND(gA+, gD-) wins for gC among Fig. 6's seven models (among supp. Table 7's 94, a model with gB wins). The parameter errors do not come back, and the refined network of Fig. 8 comes back only in part (3 of 7 edges); the causes are the unstated informative prior, pseudo time scale and noise settings, and the unstated choice of cells and orderings on the GMP and CLP pathways.


Kept local and gitignored: `sources/` (the paper, its supplement and their text), `work/`
(downloads, scratch runs and Slurm logs) and `.venv/` (the Python environment).
