# PMC2666661 figure reproduction

Meng YA, Yu Y, Cupples LA, Farrer LA, Lunetta KL. Performance of random forest when SNPs are in linkage
disequilibrium. *BMC Bioinformatics* 10:78 (2009). [doi:10.1186/1471-2105-10-78](https://doi.org/10.1186/1471-2105-10-78).
CC BY 2.0.

The published figures in `published/` are the paper's (CC BY 2.0, attribution above), the JPEGs PMC serves. Nothing
else of the paper is in this folder, and no code of Breiman and Cutler's Random Forests: the pipeline downloads
`prog.f` for the port check and patches a copy in its work folder.

## Results

<!-- summary from results.json (check_results.py); the full table: python3 figure-reproduction/pipeline/check_results.py results.json --markdown -->

34 results: 11 exact, 7 agree, 10 partly agree, 1 differs, 5 not attempted; 6 open causes.

| Result | Verdict | Ours against the paper |
| --- | --- | --- |
| Table 1 | exact | 33 of 35 values recomputed from the model parameters; H2M3's two GRRs print 5.22 for 5.227 (a rounding slip, excepted) |
| Fig. 1, mean IM | agrees | 40 of 40 bars within Monte Carlo error (e.g. RF0:IM0 0.311 against 0.302 with 4 LD.rSNPs; RF1:IM1 1.416 against 1.373) |
| Fig. 2, share above the noise | agrees | 36 of 40; the 4 misses are two series the figure swaps (with the labels exchanged all 10 agree) |
| Fig. 3, top-X curves | agrees or partly | 120 of 122 points; the two misses sit where a curve jumps within one X step |
| Fig. 4, mean IM with haplotypes | partly | 30 of 33; the paper's 11 PRED.rHAP bars are one value repeated (0.654); rHAP at r² = 0 is 0.565 against our 0.736 |
| Fig. 5, share above the noise | partly | 28 of 33; at r² ≤ 0.4 the paper's true haplotypes reach 40-45%, ours 72-76% |
| Fig. 6, top-X curves with haplotypes | partly | 25 of 26 (SNPs), 14 of 27 (true and predicted haplotypes), 8 of 18 (r² = 0 and 0.9) |
| Main claim: RF0:IM1 steadiest under LD | partly | Holds for H4M4 and 5 of the 6 other models; not for H1M1 |
| Other claims of the text | 10 exact, 2 partly, 1 differs | "RF0:IM1 steadier than RF1:IM1" also fails for H1M1; Fig. 2's "RF1:IM0 most stable" follows the swapped labels; "RF0 beats RF1" in Fig. 3 is within Monte Carlo error |
| Claims against the paper's own figures | agrees | 12 of 14 follow from the published values; the Discussion's "predicted haplotypes in between" does not fit Fig. 5, and Fig. 6b at r² = 0 contradicts Fig. 5 |
| Port and phasing | agrees | rfld differs from the Fortran original about as much as from itself with another seed (1.01×); EM matches haplo.stats to 1e-5 (frequencies) and 1e-4 (posteriors) |
| Tables 2-4 (AD data) | not attempted | The TGen genotypes were only released by request; the "7 of 17" count follows from Table 4 |

The main claim holds: with SNPs in LD, the original importance of a risk SNP falls, the revised importance on the
revised forest inflates, and the revised importance on the original forest is the steadiest, in the paper's H4M4
figures and in five of the six other genetic models (not in H1M1, open). Fig. 2's swapped series and Fig. 4's
repeated bars are slips in the paper; why the paper's true haplotypes do worse at low r² than the model gives
is open, with three candidate causes ruled out.

## What the code does, against the paper

| Paper | Here |
| --- | --- |
| Random Forests 5.1 (Fortran, Breiman and Cutler), every SNP categorical, ntree 5000, mtry 35 | `rfld.grow_forest`, a step-by-step port (Numba): bootstrap weights, mtry candidates drawn with replacement, all 2^(L-1) - 1 subset splits by weighted Gini, first best split wins ties, node size 1, breadth-first node order. Checked against the Fortran program on 20 data sets (`output/checks/port_check.json`). |
| RF1: "keeping track of variables selected at each node, and excluding from the selection pool of variables for the remaining nodes in the tree all SNPs with r² > R with any SNP already used" | After each split, the tree's pool loses every other SNP with r² > R with the split SNP (the SNP itself stays). R = 0.5 (not given; see Limits). We also patched `prog.f` the same way and checked one against the other. |
| IM0, Eq. 1: (2/T) Σ_j (1/N_j) Σ_i [...] | 100 × the mean over the T trees of the out-of-bag accuracy drop when the SNP is permuted (what Random Forests 5.1 prints). The factor 2 of Eq. 1 would double every IM and does not fit Fig. 1 (Limits). |
| IM1, Eq. 2: T replaced by T_v, the trees that use the SNP | The same sum divided by T_v. |
| Genetic models (Table 1), heterogeneity-multiplicative, Lunetta et al. 2004 | `rfld.simulate`: penetrance 1 - Π_h [1 - Π_m q_g]; Table 1's K, GRRs and λs recomputed exactly (`table1.py`). |
| 13 LD models (Table 5), r² = 1 proxies; 100 replicates of 250 cases and 250 controls; 92 nSNPs at 0.01-0.99 and 4 at 0.3-0.6 | `rfld.snp_dataset`: LD SNPs are copies; people drawn from the population until 250 affected and 250 unaffected. The LD models of a replicate share its n0 data (incremental); the H4M4 study was also run with each LD model on its own data. |
| Statistics (1)-(3) of "Simulation Analysis for SNPs" | `summarize.py`: mean rSNP IM; share of replicates where every rSNP and LD.rSNP beats every noise SNP; top-X curves (ties count against the risk SNPs). |
| Haplotypes: H4M4 with two-SNP risk haplotypes, G-T at 0.287, r² 0 to 1, K4S4N100, SNP / true / predicted haplo-genotypes, 100 phasings by haplo.stats with 1000 trees each | `rfld.haplotype_dataset`, `rfld.haplotype_em`, `rfld.sample_haplotype_pairs`; the EM matches haplo.stats 1.9.9.1 (`output/checks/haplo_check.json`). The other three haplotype frequencies keep the empirical T-T : G-C ratio; a second rule (T-T = G-C) was run as well. |
| AD application (Tables 2-4) | Not attempted: the TGen genotypes are not available. The claims about Tables 3 and 4 are checked against the tables themselves. |

## Comparing Monte Carlo figures

Every figure is a summary of 100 random replicates with unpublished seeds, so no bar or curve point can come back
exactly. Each published value is read off the figure (`read_published.py`: axes from their tick marks; bars from
their outlines; curves by colour) and compared with ours at a tolerance fixed before the comparison: 3 combined
standard errors of the two 100-replicate estimates, plus one pixel of the published figure. Two runs of the same
design miss it about once in 370 values. Each figure item lists, in `comparison.json`, how many values wrong
inputs get within the same tolerance (another LD model, IM0 and IM1 swapped, RF0 and RF1 swapped, codings rotated,
the neighbouring curve): none gets all of them. A chi-square of the standardized differences is reported as a
diagnostic only, because neighbouring bars and curve points share replicates and are not independent.

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline (profile `skyriver` for the BCM cluster). |
| `run_skyriver.sbatch`, `run_tasks.sbatch` | The Nextflow head as a Slurm job; and the Slurm array runner used for the committed simulation runs. |
| `requirements.txt` | Pinned Python packages. |
| `results_notes.json` | Labels, assumptions and causes, written by hand; merged with the run into `../results.json`. |
| `results.json` | The repository's results check (`tools/check_results.py`): our value for every compared point. |
| `pipeline/` | `fetch_inputs.sh`, `read_published.py`, `table1.py`, `snp_study.py`, `hap_study.py`, `reduce_chunks.py`, `summarize.py`, `sim_check.py`, `compare.py`, `series.py`, `render.py`, `build_results.py`, `check_reproduction.py`, `build_page.py`; the checks `port_check.py`, `patch_prog.py`, `fortran_expected.py`, `haplo_check.py` (+ `.R`), `rf1_variants.py`; copies of the skill's `check_results.py`, `compare_runs.py`, `check_package.py`. |
| `published/` | The paper's six figures (CC BY 2.0). |
| `output/sim/` | Per-replicate statistics of every simulation run (the full runs, about 150 CPU hours). |
| `output/checks/` | The port check, the haplo.stats check, the RF1 variants and the Fortran expected output of the package example. |
| `output/figures/` | `fig*_ours.png` (our values drawn into the published frame) and `fig*_overlay.png` (red: paper, cyan: ours; black where both). |
| `output/` | `published_values.json`, `table1.json`, `summary.json`, `comparison.json`, `report.md`. |

## Run

```bash
pip install -r PMC2666661/figure-reproduction/requirements.txt
nextflow run PMC2666661/figure-reproduction/main.nf --outdir results               # about 10 minutes
nextflow run PMC2666661/figure-reproduction/main.nf --outdir results --port_check  # + Fortran and haplo.stats (gfortran, R)
sbatch PMC2666661/figure-reproduction/run_skyriver.sbatch --full                    # every replicate again, on Slurm
```

The default run rereads the figures, recomputes Table 1, reruns four replicates from scratch (H4M4 n0 and r4, one
haplotype replicate, H8M4 r2) and checks them against `output/sim` bit for bit, recomputes every figure, comparison
and claim from `output/sim`, checks the package, and compares everything with the committed `output/`. The full
simulation (2,600 SNP replicates with three forests each, 2,200 haplotype replicates with 102 forests each)
took about 150 CPU hours on the cluster; it ran as Slurm arrays of the same scripts (`run_tasks.sbatch`), and
`--full` runs it through Nextflow.

## Pipeline steps

1. `FETCH`: the six figure JPEGs from PMC's open-access bucket (SHA-256 checked); with `--port_check` also `prog.f`.
2. `READ_PUBLISHED`: bar heights, error bars and curve points of Figs 1-6.
3. `TABLE1`: K, GRRs and λs of the seven models from their allele frequencies and penetrance factors.
4. `SIM_COMMITTED` or (`--full`) `SNP_CHUNK`, `HAP_CHUNK`, `REDUCE`: the per-replicate statistics.
5. `SIM_CHECK`: four replicates rerun from scratch against the committed statistics.
6. `SUMMARY`: aggregate, compare with the published values, render ours on the published frames.
7. `CHECKS`: the committed checks, or (`--port_check`) the Fortran and haplo.stats checks run again.
8. `PACKAGE`: `check_package.py` on `../package`.
9. `RESULTS`: `results.json`, the check step (`report.md`) and the results page.

## Limits

- **Monte Carlo figures.** No published bar or curve point can come back exactly: the seeds are not given, and
  two runs of 100 replicates differ by about 1.4 standard errors. Values are compared at 3 combined standard errors
  plus a pixel; a wrong input (another LD model, IM0 and IM1 swapped, the neighbouring curve) gets fewer values
  within than ours in every figure (`output/comparison.json`, `controls`).
- **Unstated settings.** R (no chance r² among the independent SNPs reached 0.1 in any replicate, maximum 0.090, so any value from 0.1 to just below 1 gives identical forests here; R = 0.02 is in
  `summary.json`); whether H4M4's LD models share their data (we build them incrementally; the independent run,
  `snp_independent`, also gives Fig. 1 40 of 40); how the cases and controls were drawn; the three free haplotype
  frequencies (two rules run, T-T = G-C being the "equal SNP frequencies" rule; nearly the same results: Fig. 5 27 of 33 against 28).
- **The paper's RF1 bars at no LD** are about 10% above RF0 in Fig. 1 and 3-4% in Fig. 2. RF1 cannot change a forest with no SNPs
  in LD, so ours equal RF0 there; a low R lowers IM0 (0.92 of RF0) and leaves IM1 unchanged, and a once-per-tree rule lowers both (0.94 and 0.80)
  (`output/checks/rf1_variants.json`). A separate set of simulated replicates for RF1 would explain it; the bars are
  within tolerance either way.
- **Error bars.** The paper does not say what they show; they are 2.4 (Fig. 1) and 2.2 (Fig. 4) times our standard
  errors (`comparison.json`, `error_bars`). Ours are drawn at 1.96 standard errors.
- **Eq. 1** has a factor 2/T; the figures fit the importance Random Forests 5.1 prints, 100 times the mean over T.
- **Reading the figures.** Fig. 6 is an 87 dpi JPEG with 11 curve colours; only r² = 0, 0.2, 0.4, 0.7 and 1 are
  read in its top and middle panels, and points hidden under other curves are skipped.
- **Port check.** RF0 is checked against Breiman and Cutler's own program; RF1 only against our own patch of it,
  because the authors' program is lost.
- **Tables 2-4** need the TGen genotypes, which were never public.
