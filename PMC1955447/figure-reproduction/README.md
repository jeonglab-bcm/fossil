# PMC1955447 figure reproduction

Moineddin R, Matheson FI, Glazier RH. A simulation study of sample size for multilevel logistic regression models.
*BMC Medical Research Methodology* 7:34 (2007). [doi:10.1186/1471-2288-7-34](https://doi.org/10.1186/1471-2288-7-34). CC BY 2.0.

The paper has no figures; its results are Tables 1-5 (the simulation study) and the claims of its text. Nothing of
the paper is in this folder: `output/published_values.json` holds the printed numbers of Tables 1-5, read from the
article XML by `pipeline/extract_published.py` (rerun with `--extract`, which downloads the XML and checks its
SHA-256).

## Results

<!-- full table from results.json (check_results.py --markdown); regenerate with pipeline/update_readmes.py -->

<!--RESULTS-TABLE-->
<!--/RESULTS-TABLE-->

<!--CLAIMS-LINE-->
<!--/CLAIMS-LINE-->

<!--DETAILS-->
<!--/DETAILS-->

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| logit p_ij = γ00 + γ10 x_ij + γ01 z_j + γ11 x_ij z_j + u0j + u1j x_ij (equation 2) | `mlagq.simulation.generate`: as printed; fixed effects 1, z, x, x z; random intercept and slope on x. |
| x_ij, z_j standard normal; u0j, u1j independent normal; σ1 = 1; random-intercept variance 0.13, 0.67, 2.0 (ICC 0.04, 0.17, 0.38); γ = (-1.0, 0.3, 0.3, 0.3); 30, 50, 100 groups of 5, 30, 50; 1,000 data sets per cell | As printed. The variances are used as given (σ0 = 0.361, 0.819, 1.414; the paper prints 0.36, 0.82 and 1.42). |
| SAS 9.1 PROC NLMIXED, default options: full maximum likelihood, normal random effects, adaptive Gaussian quadrature with the points selected automatically | `mlagq.fit`: the marginal likelihood by adaptive Gauss-Hermite quadrature centred and scaled at each group's posterior mode, re-adapted at every iteration; the number of points per dimension chosen at the starting values by NLMIXED's rule (1, 3, 5, 7, 9, 11, 21, 31 until two successive log-likelihoods differ by less than 1e-4, the larger kept). Checked against a dense-grid integral (`CROSSCHECK`). |
| Dual quasi-Newton; starting values at the true values; "absolute value for parameter convergence criterion" 1e-8; at most 200 iterations | BFGS with a backtracking line search from the true values (σ01 started at 0); converged on NLMIXED's default gradient criteria (ABSGCONV 1e-5, GCONV 1e-8) or when no parameter moves by more than 1e-8 in an iteration (ABSXCONV, our reading of the paper's criterion); at most 200 iterations and 500 function calls (NLMIXED's MAXFUNC). |
| The model with σ01 (equation 1); data drawn with σ01 = 0 | σ01 estimated; the variances and the covariance unconstrained, so a trial point with a covariance matrix that is not positive definite has no likelihood. |
| "If convergence was not achieved the estimated parameters were not included" | Summaries over converged fits only. |
| % relative bias of σ0 and σ1; non-coverage of the 95% Wald interval "from the asymptotic standard normal distribution" | On the variance scale, the parameters as fitted (the SD scale is a tested hypothesis); Wald intervals from the observed information. |
| Table 2: non-coverage by factor, with p-values from logistic regression | All converged fits of a level pooled; p from a likelihood-ratio test of the 3-level factor; compared as significant or not at 0.05. |
| Table 4: prevalence 0.10, 0.34, 0.45 with γ = (-3, .3, .3, .3), (-1, .3, .3, .3), (-.3, -.3, -.3, -.3), both variances 1 | The nine groups x size cells of the main grid, 1,000 data sets each, pooled per prevalence (the cells and the pooling are not stated). |
| Table 5: eight models for the distributions of (z, u0, u1, x), 100 replications | All 72 cells x 100; the true variance of a random effect is its distribution's variance (t3: 3, t5: 5/3, U(-2, 2): 4/3). |
| SAS's random-number generator, seeds not given | NumPy 2.2.6 PCG64, one stream per data set (seed [19554471, study, cell, replicate]); a second run of the main grid uses base 19554472. |
