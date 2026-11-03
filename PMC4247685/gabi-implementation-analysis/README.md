# GABi implementation analysis (Curry 2014, BMC Bioinformatics 15:355)

The paper describes GABi, a genetic algorithm (GA) that searches over column subsets J and scores each J
with a model-specific fitness function. The fitness function picks the rows I by rule. The code is the
CRAN package `GABi` 0.1, which holds the GA, plus Additional file 1 (S1), which holds the R code for the
paper's four bicluster models. This folder records what that code computes and where it departs from
the paper. Every claimed difference has a small executable check.

## Sources

| File | What | sha256 | Get it from |
| --- | --- | --- | --- |
| `12859_2014_Article_355.pdf` | the paper, 14 pp, CC BY 4.0 | `01d30067314aa50da8111c7e2295d86340e0cae5127ad21d5f201824e3a1d96a` | [doi:10.1186/s12859-014-0355-5](https://doi.org/10.1186/s12859-014-0355-5) |
| `GABi_0.1.tar.gz` | GABi 0.1 (Packaged 2013-09-17), the only CRAN release, archived 2022. GPL (>= 2). Pure R, depends on `hash`. | `ae9655fc16e48a5e7da46d4e09bdef835ef65e46da8409d38f37cbd01656b1fe` | <https://cran.r-project.org/src/contrib/Archive/GABi/GABi_0.1.tar.gz> |
| `12859_2014_355_MOESM1_ESM.txt` | Additional file 1 (S1): `block.*`, `cor.*`, `highvar.*`, `getFitnesses`, `featureSelection.dysregSurv`. CRLF line endings. | `f91e4234ae7c76ca7ebf4a852b95373012f82cc0206ceb07d4bf94552d73e1f7` | <https://static-content.springer.com/esm/art%3A10.1186%2Fs12859-014-0355-5/MediaObjects/12859_2014_355_MOESM1_ESM.txt> |

These files are kept in `PMC4247685/sources/`. That folder is gitignored and not redistributed. To get them:

```
mkdir -p PMC4247685/sources && cd PMC4247685/sources
curl -LO https://cran.r-project.org/src/contrib/Archive/GABi/GABi_0.1.tar.gz
curl -L -o 12859_2014_355_MOESM1_ESM.txt \
  'https://static-content.springer.com/esm/art%3A10.1186%2Fs12859-014-0355-5/MediaObjects/12859_2014_355_MOESM1_ESM.txt'
R CMD INSTALL GABi_0.1.tar.gz      # needs the hash package; the checks also use survival
```

Line references: `GABi.R:n` and the other `.R` names are files in `GABi/R/` of the tarball. `S1:n` is a
line of Additional file 1 (the line numbers are the same with or without the CRs).

## Method

- Read `R/*.R` and `man/*.Rd` of GABi 0.1, the S1 code, and the paper: Algorithm 1 and "Parameter setting"
  (pp 5-6), Eqs 14-44 (pp 7-8), Eq 45 and Algorithm 2 (p 9), and the synthetic offsets (p 10).
- Ran the authors' code: GABi from the installed library, with S1 `sys.source`d from `sources/`. Check
  01 confirms that the installed functions are the tarball's. To read intermediate values without copying
  code, `checks/common.R` has three helpers. `instrument()` returns an S1 function's local variables in
  place of its result. `patch()` swaps exactly one source fragment, to test a proposed fix. `trace()` is
  used on GABi namespace functions.
- `reference/paper_models.R` implements Eqs 14-16, 17-23, 24-29, 31-35, 45 and Algorithm 2 from the paper
  alone. Where a formula is inconsistent with its text, the function has a switch for the printed form
  and the evident intent. Check 12 compares it with S1 on random Algorithm 2 inputs.
- R 4.6.1, survival 3.8.6, hash 2.2.6.4. The Fig 2 benchmark and the TCGA analysis were not run here.
  They are in `../figure-reproduction/`.
- Status column below: **exec** means shown by running the code (check id given). **read** means from
  reading the code only.

## Recovered algorithm (`GABi()` with defaults)

```
x: features x samples. A solution is a 0/1 vector over the columns (samples).
fitnessArgs$tabu <- list(features = 0, samples = 0)                     # GABi.R:5, overwrites any user tabu
diffRows <- rows that are not constant and whose min-max scaled row mean is
            in [1 - diffThreshold, diffThreshold] = [0.1, 0.9]           # GABi.R:7-18; not in the paper
fitnessFun and featureSelFun get GABi's frame as enclosure, so they read x, diffRows,
row.mins, row.maxes, fitnessArgs from there                             # GABi.R:29-32
repeat while length(allSols) <= nSols (0) and loop < maxLoop (1):       # GABi.R:37
  4 demes x ceiling(256/4) = 64 solutions, each with exactly 2 random columns set   # GABi.R:40-45
  cache: chromosome string -> fitness (one hash per loop)               # GABi.R:58
  for gen in 1..maxNgens (200), until converged:
    for each deme j:
      fitness of uncached rows; Inf and NA -> 0                         # GABi.R:69-91
      best_j <- first row with maximal fitness
      stagnant_j <- best_j identical to any current best_k (k = 1..4); otherwise counter <- 0
      if counter >= convergenceGens (40): converged; skip this deme     # GABi.R:108, 187-190
      while all fitnesses == 0:                                         # GABi.R:110-158
        "re-initialise": rows[i, 2 random cols] == 1  (comparison; the deme stays all 0)
        after 100 tries: diffThreshold += 0.1; if > 1: warning, return(list())
      selection: row 1 <- argmax (elite); rows 2..64 <- roulette over rows with fitness > 0  # fps.R
      crossover: each non-elite row independently with prob xfreq (0.5); shuffle the picked rows
        and pair them; one-point cut k ~ round(U(1, n)) (k = n acts as n - 1); an odd row is kept  # reproduction.R, crossover.R
      mutation: each bit of rows 2..64 flips with prob mfreq/ncol = 1/n  # mutation.R
    if all 4 demes stagnant: counter += 1                               # GABi.R:192-194
    every experiod (10) gens: exchangeSols(new demes, fitnesses of the previous population)  # GABi.R:195-198
      k_i <- argmax of old fitness in deme i; migrant_i <- new deme i row k_i
      deme i row k_i <- migrant_{pi(i)}, pi a random permutation        # exchange_sols.R:9-11, 33-38
  final: pool all demes, recompute fitness (Inf/NA -> 0), keep rows with fitness > 0  # GABi.R:201-211
  dedup in population order: a new solution evicts every kept solution with
    |A n B| / min(|A|, |B|) > identityThreshold (0.75) over sample sets; the best of that group stays  # GABi.R:212-230
  each kept solution -> list(samples, features = featureSelFun(samples), score = fitnessFun(chr))  # GABi.R:232
  tabu <- union(tabu, returned features and samples)                    # GABi.R:237-244
return allSols
```

`keepBest = TRUE` keeps a de-duplicated archive of every positive-fitness solution seen during the run,
and the final population is merged into it (GABi.R:165-181, 213-216). The Rd file describes `keepBest`
as elitism. Elitism is in fact always on (GABi.R:183, 185).

## Differences: GA framework (`GABi` 0.1)

| # | Item | Paper | Code | Effect | Check | Status |
| --- | --- | --- | --- | --- | --- | --- |
| G1 | Re-initialisation of an all-zero deme | Not described | `demes[[j]][i,sample(ncol(x),2)]==1` (GABi.R:115) compares and discards, so the deme stays all 0. After about 200 tries GABi warns "cannot find biclusters" and returns `list()`. | GABi returns nothing whenever the 64 random initial solutions of a deme all score 0. With `<-` the deme is re-drawn, but always with 2 columns again (G2). | 04.1-04.3 | exec |
| G2 | Initial solutions | q0 columns, an input of Algorithm 1 | Always 2 (GABi.R:43), no argument | For the S1 cor model a 2-column J gets Spearman p = 1, so the score comes only from the all-high fallback (C4). With `consistency >= 1` every initial solution scores 0 and G1 ends the run: on an Algorithm 2 'cor' dataset GABi returns nothing, with or without the G1 fix. | 02.7, 04.4-04.6 | exec |
| G3 | `return(list())` inside the retry loop | - | GABi.R:146 returns an empty list, not `allSols` | With `maxLoop > 1`, a later loop that scores 0 everywhere (for example once the tabu list covers the samples) throws away the earlier loops' biclusters | 07.2 | exec |
| G4 | MaxLoop / tabu | MaxLoop > 1 reruns the GA, and found biclusters get zero fitness (p 6) | The loop condition `!length(allSols)>nSols & loopCount<maxLoop` (GABi.R:37) needs `nSols` too: with the default `nSols = 0`, a second loop never runs once anything is found. No S1 function reads `fitnessArgs$tabu`. GABi's own `getFitnesses.basic` does read it, but it only shrinks counts. | With S1 models, a second loop re-finds the same bicluster | 07.1, 07.3-07.6 | exec |
| G5 | Row pre-filter | Not described | Drops rows whose scaled mean is < 0.1 or > 0.9 before any fitness evaluation (GABi.R:7-18) | No rows are dropped on Algorithm 2 data (300 datasets), so no effect on Fig 2. It does apply to the TCGA β-values: not quantified here. | 03.1-03.5 | exec |
| G6 | Inf / NA fitness | - | Set to 0 (GABi.R:79-80, 88-89, 209-210) | A solution whose score overflows is never selected or returned. This hits S1 `getFitnesses` (D1, D6). | 08.1 | exec |
| G7 | Default population | 128 "is sufficient"; up to 4 subpopulations of at least 32 | `popsize = 256`, 4 demes of 64 | More search than the text suggests. Effect not measured. | 02.1-02.2 | exec |
| G8 | Elitism | Not in Algorithm 1 | Always on (fps.R:8-13, reproduction.R:6-10). The Rd says `keepBest` controls it, but it does not. | Best solution per deme is kept | 02.8-02.9 | exec |
| G9 | Elitism hole | - | reproduction.R:17 `sample(setdiff(1:popsize, xindex))`: when exactly one row k is picked for crossover, `sample(k)` permutes 1..k and rows 1..k, the elite among them, are crossed | Only in small demes: 135/3000 generations with demes of 8, 0/3000 with the default 64 | 02.13 | exec |
| G10 | Crossover | "swap randomly-sampled subset of this row's values" (Alg 1 l.15) | One-point crossover between shuffled pairs of rows. Each row is picked independently with prob `xfreq` (the Rd says "each pair"). | Positional linkage. Algorithm 2 places J at random, so this probably matters little. Not measured. | 02.10 | exec |
| G11 | Migration | Subpopulations described as "isolated"; no migration in Algorithm 1 | Every 10 generations, after reproduction, with the previous generation's fitnesses (GABi.R:196). The migrant is the new row at the old argmax index, and it overwrites the receiver's row at its own old argmax index, usually row 1 (the elite). | 4/96 migrants were not their deme's best. In 38/96 cases the receiver's elite was replaced: elites get permuted among demes, not copied. | 06.1-06.4 | exec |
| G12 | Convergence | Stop when the best fitness has not improved for a set number of generations (p 4) | Counts consecutive generations in which every deme's best chromosome is identical to one of the current best chromosomes (GABi.R:94-108, 192-194). A migration that moves different elites between demes resets the count. | In practice it stops only once the demes share their best, otherwise it runs to 200 generations. S1 block runs on Algorithm 2 data stopped at generations 45-85. | 02.12, 02.14 | exec |
| G13 | Final dedup | Rank by fitness, then drop highly overlapping solutions (Alg 1 l.27-30) | Greedy in population order. A solution that overlaps two disjoint kept solutions evicts both, and only the best of the three stays. | The output can lose distinct biclusters: order B,C,A keeps {B}; rank-then-filter keeps {B,C} | 05.3-05.4 | exec |
| G14 | `fitness=fitnesses[1]` (GABi.R:215) | - | Wrong index in the seed entry of `keptSols` | **None.** The first pass of the loop replaces that entry (the stored fitness is ≤ the correct one), and the stored fitness is never output. Output identical with the fix (5 seeds). | 05.1-05.2 | exec |
| G15 | Other defaults | Mutation ≈ 1/n; crossover 0.5-1; 100-200 generations | Mutation 1/n per bit (`mfreq/ncol`), `xfreq = 0.5`, `maxNgens = 200`. No values in the paper for `convergenceGens` 40, `experiod` 10, `identityThreshold` 0.75, `diffThreshold` 0.9. | Matches where the paper gives values | 02.3-02.5, 02.11 | exec |

## Differences: bicluster models (S1)

The paper does not state θ (`consistency`), α or ρ for Fig 2 or for the TCGA run. ρ is not in the paper.

| # | Item | Paper | S1 code | Effect | Check | Status |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | Block model | Eqs 14-16, mean ≥ θ | Same, with `>` (S1:3-18) | None on continuous data | 12.1 | exec |
| C1 | Seed row | Eq 20: argmax \|cor(row, PC1 rotation of A_XJ)\| | `which.max(rowMeans(cor.mat))`: the largest mean Pearson correlation with the candidate rows (S1:33) | Agrees with Eq 20 in 6% of random J | 09.1, 12.3 | exec |
| C2 | Seed index bug | - | `cor.test(y, y=x[cor.seed, chr==1])` (S1:36, also S1:59): `cor.seed` is a position in `cor.features`, not a row of x. Wrong whenever all-high rows were removed (C4) or GABi dropped rows. | p-values are computed against an arbitrary row: score 136 vs 285 when fixed. Active in 9% of evaluations on Algorithm 2 'cor' data at consistency 0.8. If that row is constant on J, the fitness is NA (scored 0) and `cor.selection` stops with an error, which would abort GABi's last step. | 09.2, 09.6 | exec |
| C3 | Row gate and α | δ = 1 if p < α (Eq 22) | Rows pass if \|Pearson r with seed\| > ρ (S1:34). α is not used by `cor.fitness`, only by `cor.selection` (S1:62). | The fitness sums -log p over rows the selection may drop: 6 vs 42 vs 47 rows for α = 1e-12, 0.05, 1, with the same fitness | 09.3-09.4 | exec |
| C4 | All-high fallback | Not in Eqs 19-23 | Rows with raw mean over J > θ are removed from the correlation candidates. Score = max(cor score, \|J\|·n_high) (S1:27-31, 39). | At q0 = 2 this is the only non-zero term (G2) | 09.5 | exec |
| C5 | `cor.selection` row indices | - | If the fallback wins, it returns positions within `diffRows`, not rows of x (S1:50, 62) | Wrong rows are returned whenever GABi's filter dropped a row above them | 09.7 | exec |
| C6 | p-values | Fisher z on Pearson r, sqrt((\|J\|-3)/1.06)·atanh(r) (Eq 19) | `cor.test(method="spearman")`, floored at 2e-16 (S1:36). For 10 ≤ n < 1290, R uses the AS 89 Edgeworth series clamped at 0, which is not monotone in ρ. | At n = 16, -log p is 36.1 for a row with ρ = 0.944 and 11.9 for a row with ρ = 1. The seed is always in its own row set, so every J gets \|J\|·(-log p_self): 109 at \|J\| = 9, 361 at 10, 542 at 15, 190 at 16. This is a size preference that has nothing to do with the data. | 09.9 | exec |
| C7 | Eq 19 as printed | 2Φ(z) | - | 2Φ(z) > 1 for every positive r, so as printed only negatively correlated rows count. Two-sided 2Φ(-\|z\|) is evidently intended. The seed row (r = 1) then makes Eq 23 infinite for every J. | 09.8 | exec |
| V1 | High-variance tail | p = F_χ²(σ²_J/σ²_J′; \|J\|-1), the CDF (Eq 25) | `1 - pchisq(...)`, the upper tail, floored at 2e-16 (S1:74) | Code follows the text, not the printed formula. It equals the reference to 8e-16. | 10.1-10.2, 12.2 | exec |
| V2 | High-variance statistic (paper and code) | Bare variance ratio against χ²(\|J\|-1) | Same | Not a valid test: under H0 the ratio is F(\|J\|-1, \|J′\|-1). Type I error at α = 0.05 (m = 20): 0.065, 0.013, 0.001, 0.000, 0.14 for \|J\| = 2, 3, 5, 10, 18. On Algorithm 2 'highvar' data, along nested subsets of the true J, the S1 fitness peaks below 0.75·q in 47% of datasets (F test: 2%). This lowers sample recall in Fig 2's highvar panel. | 10.3-10.4 | exec |
| D1 | Seed in its own feature set, unfloored p | - | `rowsForCor` keeps the seed (S1:112). `getFitnesses` uses raw `-log(p)` (S1:116), while the selection floors at 2e-16 (S1:163). R gives p = 0 for the self-test at n = 10-15 and n ≥ 27, and at every n if the seed row has ties. At n = 16-21 it also gives p = 0 for a band of \|ρ\| < 1 (n = 21: 0.836-0.865). | Fitness Inf → 0 (G6). The correlation branch can score only \|J\| in 3-9 and 22-26 (if the seed row has no ties), or 16-21 if no candidate row also falls in the band. On tied data (e.g. rounded β-values) no \|J\| can score. The paper's bicluster has \|J\| = 21. | 11.5-11.10 | exec |
| D2 | "All-low" rows | Block branch δ^block (Eq 41), high rows only | `alllow.rows <- which(1-pmatMeans<(1-consistency))` (S1:98, 146) is the all-high condition again. The block score is (Σm + Σ(1-m))·\|J\| = n_high·\|J\|. | The score is not doubled: it equals Eq 16 with scaled means. But rows low on J are in neither branch, and the selection returns each high row twice. | 11.1-11.4 | exec |
| D3 | Rows for J′ in the fitness | I″ (Eq 44) | `survFeatures <- cor.features` (S1:123) holds positions within `rowsForCor`, but S1:126 uses them as positions in `diffRows`. The selection function maps them (S1:166). | In the correlation branch, the comparison group J′, and so h, comes from the wrong rows: fitness 126 vs 595 when fixed. The GA optimises a different h from the one reported. | 11.11 | exec |
| D4 | Multiple testing | - | BH in `featureSelection.dysregSurv` only (S1:163). The fitness uses raw p (S1:115). | The GA's I″ is larger than the reported one: 14 vs 3 rows | 11.12 | exec |
| D5 | Correlation candidates | I″ from all rows X | Only rows with scaled mean in (1-θ, θ) on J (S1:101). PCA input is centred with scaled means, and `na.action` is ignored by `prcomp` (S1:106). The seed is argmax \|Spearman r with PC1\| (S1:107-108). | Correlated rows that are high or low on J are not candidates. The centring shifts PC1 slightly. | 11.3 | exec (rows), read (PCA) |
| D6 | h(I, J) | -log(2Φ(z)) (Eq 31) | `-log(1-pchisq(survdiff()$chisq, 1))` (S1:128) = -log(2Φ(-\|z\|)) | Equal to the two-sided form of Eqs 31-35. Eq 31 as printed has a sign error (h < 0 for z > 0). `1-pchisq` underflows for χ² > 70.13 (p < 5.6e-17), giving Inf → 0. Unlikely at 21 vs 21 (published p = 1e-5). | 08.2-08.3, 11.14 | exec |
| D7 | J′, l, reference column | l = min(\|J\|, \|Y\|-\|J\|) least-correlated columns, against j₁, the first column of J (Eqs 36-40; p 9 text) | Same, ranked within Y \\ J (S1:126-127) | **Matches.** The suspected "first column only" difference is in the paper too. | 11.13 | exec |
| D8 | ρ gate | Not in Eqs 41-44 | \|Spearman ρ\| > ρ as well as p < α (S1:115, 164) | Same as C3 | - | read |
| T1 | Tabu | Zero fitness for found biclusters | Not read by any S1 function | See G4 | 07.3, 07.5 | exec |

### Differential test, cor model (check 12)

25 Algorithm 2 'cor' datasets, each scored at the true J and at 20 random J of the same size. S1 uses
ρ = 0.5 and α = 0.05. The reference is Eqs 17-23, two-sided, with the same 2e-16 floor.

| | consistency 1 | consistency 0.8 |
| --- | --- | --- |
| Seed row identical | 6% | 6% |
| S1 score from the block fallback | 0% | 4% |
| Jaccard, selected rows | 0.33 | 0.33 |
| Spearman correlation of the two fitnesses across J (median) | 0.74 | 0.71 |
| True J scores highest: S1 / paper | 68% / 32% | 64% / 32% |
| Recall of implanted rows at the true J: S1 / paper | 0.54 / 0.67 | 0.54 / 0.67 |
| S1 / paper score at the true J (median) | 1.00 | 0.98 |

The two models rank solutions differently, so a GA run with Eqs 17-23 would not reproduce a run with S1.
On these data, S1 ranks the true J first more often than the reference does.

## What could change the published results

Fig 2 (block, cor and highvar models on Algorithm 2 data, n = 100, m = 20), most to least:

1. Cor model: C2, C6 and C1/C3. Wrong-row p-values, a size preference from R's Spearman p-values, and a
   different seed and row gate from Eqs 17-23. Combined with G2, the cor GA starts only through the
   block fallback, and with θ ≥ 1 GABi returns nothing. Which of these bite depends on θ and ρ, which the
   paper does not give.
2. Highvar model: V2 favours J smaller than the implanted one. The paper's formula has the same flaw, so
   the published panel already reflects it.
3. GA framework (G7, G10-G13): affects search quality, not the objective. Not quantified.
4. G5 does not apply (no rows dropped). The block model matches the paper (B1).

TCGA bicluster (dysregulation-vs-outcome model, |J| = 21), most to least:

1. D1: under R 4.6.1, a 21-sample J scores 0 if any candidate CpG has |ρ| with the seed in
   0.836-0.865 (and the ρ gate is below 0.836), or if the seed row has a tie. Not tested on 2013-era R.
2. D3 and D4: during the search, h and I″ are computed on different rows from the ones the reported
   bicluster uses.
3. G5 and D5: rows are removed before the model sees them (scaled mean outside [0.1, 0.9]), and rows
   high or low on J are never correlation candidates. Not quantified without the TCGA data.
4. D2: no effect on a correlation-branch bicluster. It only changes the branch choice through the
   missing low rows.

## Reproduce

```
Rscript PMC4247685/gabi-implementation-analysis/run_checks.R      # about 75 s
GABI_SOURCES=/path/to/sources Rscript .../run_checks.R            # if the sources live elsewhere
Rscript PMC4247685/gabi-implementation-analysis/checks/09_cor_model.R   # one check
```

Output summary (R 4.6.1, GABi 0.1, survival 3.8.6; two runs gave identical output):

```
SUMMARY 01_provenance.R: 4 pass, 0 fail
SUMMARY 02_ga_settings.R: 14 pass, 0 fail
SUMMARY 03_row_filter.R: 5 pass, 0 fail
SUMMARY 04_reinit.R: 6 pass, 0 fail
SUMMARY 05_final_dedup.R: 4 pass, 0 fail
SUMMARY 06_migration.R: 4 pass, 0 fail
SUMMARY 07_maxloop_tabu.R: 6 pass, 0 fail
SUMMARY 08_inf_to_zero.R: 3 pass, 0 fail
SUMMARY 09_cor_model.R: 9 pass, 0 fail
SUMMARY 10_highvar_model.R: 4 pass, 0 fail
SUMMARY 11_dysreg_model.R: 14 pass, 0 fail
SUMMARY 12_difftest.R: 4 pass, 0 fail
TOTAL: 77 pass, 0 fail in 12 scripts
```

A PASS means the stated behaviour of the authors' code was observed. It does not mean the code is
correct.
