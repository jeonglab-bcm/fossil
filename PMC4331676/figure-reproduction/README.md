# PMC4331676 figure reproduction

Xu et al. 2015 built SVM-PSSM-DT: a PSI-BLAST profile of each protein, turned into 2,000 numbers by
PSSM distance transformation, classified by an RBF support vector machine. This folder rebuilds
every step from the paper, reruns the paper's experiments on its own data, and compares each table,
figure and claim with the published one. The verdicts are in [`../results.json`](../results.json)
and in the [README one level up](../README.md#results); the results page is
<https://jeonglab-bcm.github.io/fossil/PMC4331676/>.

## Run

```bash
# From the repository root. Starts from the committed PSSMs and reruns everything after them:
# grid searches, jackknife and cross validation, the independent test, weights, sensitivity
# variants, figures, scores, the package check and results.json (about 15 CPU minutes).
# This is what CI runs.
nextflow run PMC4331676/figure-reproduction/main.nf --outdir results

# On the Skyriver cluster (every process a Slurm job, never on the login node):
sbatch PMC4331676/figure-reproduction/run_skyriver.sbatch

# Everything, the PSSMs included: PSI-BLAST for 1,261 chains against UniRef100 2014_01
# (about 200 CPU hours). Build the database first, as below.
sbatch PMC4331676/figure-reproduction/run_skyriver.sbatch --blastdb /path/to/uniref100 --blast /path/to/ncbi-blast-2.16.0+/bin
```

The database: download `uniref2014_01.tar.gz` (22 GB, sha256 in `results.json`) from
<https://ftp.uniprot.org/pub/databases/uniprot/previous_releases/release-2014_01/uniref/>, unpack
`uniref100.tar`, convert `uniref100.xml.gz` to FASTA (one record per cluster, the representative
sequence) and run `makeblastdb -dbtype prot` on it (33,613,081 sequences). The same for UniRef90
(20,200,107) gives the profiles of the sensitivity variant. BLAST+ 2.16.0 is the NCBI build
`ncbi-blast-2.16.0+-x64-linux.tar.gz`.

Python 3.12 with `requirements.txt` and the package (`pip install -r requirements.txt ../package`);
Nextflow 25.04.6 with Java 21; `uv` for the package check.

## Pipeline steps

| Process | Does |
| --- | --- |
| `FETCH` | `fetch_inputs.sh`: the supplement (benchmark), PDB186 and the six predictors' outputs (Lou et al. 2014), the published figures and 1AKH, each checked against its SHA-256. |
| `PREPARE` | `parse_datasets.py` (1,075 benchmark chains from the supplement PDF, 186 PDB186 chains, every defect of the supplement), `read_published.py` (Fig. 1 values and figure frames), `lou_comparators.py` (Table 4 rows and Fig. 5 curves of the earlier predictors), `akh_occurrences.py` (Fig. 2C), `paper_arithmetic.py` (claims recomputed from the paper's own tables). |
| `PSIBLAST`, `PACK` | Only with `--blastdb`: `run_psiblast.sh` (3 iterations, E-value 0.001) and `pack_pssms.py`. Otherwise `output/pssm/pssm_uniref100_2014_01.npz` is used. |
| `HOMOLOGY` | `homology_filter.py`: benchmark chains above 25% identity to a same-class PDB186 chain (from blastp, rerun with `--blast`). |
| `BENCHMARK` | `experiments.py benchmark`: grid search and jackknife for PSSM-DT, its two halves and the four comparator encodings (Tables 1 to 3, Figs 3 and 4). |
| `LG_SWEEP` | `experiments.py lg`: 5-fold cross validation for LG = 1 to 14 on five splits (Fig. 1). |
| `INDEPENDENT` | `experiments.py independent`: PSSM-DT trained on the filtered benchmark, tested on PDB186 (Table 4, Fig. 5). |
| `WEIGHTS` | `experiments.py weights`: discriminant weights (Eq. 12) of the model trained on the whole benchmark (Fig. 2A, 2B). |
| `DEFINITION` | `bioseq_definition.py`: the package's PSSM-DT against the transliterated loops of BioSeq-Analysis2.0. |
| `SENSITIVITY` | `sensitivity.py`: the settings the paper does not state, one at a time (hypothesis tests for the causes). |
| `FIGURES` | `figures.py`: our curves, bars and heatmap drawn on the published pixel grids, overlays and two-way scores with controls. |
| `PACKAGE` | `check_package.py ../package`: wheel, fresh install, tests, tutorial rerun. |
| `RESULTS` | `build_results.py` (numbers plus `results_notes.json` into `results.json`, verdicts by `check_results.py`), `check_reproduction.py` (fails on a broken rule or any difference from `output/`), `build_page.py` (the results page). |

## What the code does against the paper

| Paper | Ours |
| --- | --- |
| PSI-BLAST against NCBI nr, 3 iterations, E-value 0.001 (nr of about 2014). | BLAST+ 2.16.0 `psiblast -num_iterations 3 -evalue 0.001` against UniRef100 release 2014_01 (33.6 million clusters, January 2014), the closest archived non-redundant set. UniRef90 2014_01 as a variant. The 2014 nr is not archived. |
| PSSM: L x 20 scores (Eq. 2); called "occurrence probabilities" but described as integer log-odds. | The raw integer log-odds scores of the ASCII PSSM, as BioSeq-Analysis2.0 uses them. The logistic transform is a variant. |
| PSSM-SDT and PSSM-DDT (Eqs. 3, 4), 400 x LG features. | `pssmdt.pssm_dt`; Eq. 3's indices are swapped against Eq. 2, we follow Eq. 4 and BioSeq-Analysis2.0 (identical on 127 profiles). |
| Sequences with no profile: not mentioned. | The 7 DNA strands among the positives get no PSI-BLAST hits; they are encoded from BLOSUM62 rows, as BioSeq-Analysis2.0 does. |
| LIBSVM, RBF; C and gamma by grid search with 5-fold cross validation; range not given. | scikit-learn `SVC` (LIBSVM) on features scaled to [-1, 1]; LIBSVM's default grid (log2 C -5..15, log2 gamma 3..-15); split seed 0; the pair is then fixed for the jackknife. Solver tolerance 1e-6, not LIBSVM's 1e-3: with 1e-3 the solver stops early enough that last-bit differences between CPUs (our cluster, GitHub's runners) moved decision values in the 4th digit and failed the rerun check; no printed value or verdict changed. |
| Jackknife (Tables 1 to 3), 5-fold cross validation (Fig. 1). | Leave-one-out on the precomputed kernel; stratified 5-fold, five splits per LG. |
| AvePscore-20, AvePscore-400, Pscore-100 [Lou 2014], ACC [Dong 2009], "in-house implementations". | As Lou et al. define them on the logistic PSSM (percentiles 0, 25, 50, 75, 100); ACC as auto-cross covariance of the logistic PSSM with LG = 5. Each gets its own grid search. |
| DNA-Prot and iDNA-Prot rebuilt in house (Table 3, Figs 4, 5). | Not rebuilt. |
| PDB186: benchmark chains with more than 25% identity to PDB186 removed with CD-HIT. | cd-hit cannot go below 40%; blastp alignments with cd-hit-2d's identity (identical residues over the shorter chain), same class only: 120 chains removed. Thresholds up to 99% and no filter as variants. |
| Comparator rows of Table 4 from Lou et al. | Recomputed from Lou et al.'s Information S1. |
| Discriminant weights W = A M (Eq. 12); a pair's weight is the "quadratic sum" of its positive descriptor weights. | `dual_coef_` times the scaled features of the support vectors; the root of the sum of squares over lg. Unscaled features, the other sign and plain class-mean differences as variants. |
| Fig. 2C: occurrences of the top four pairs on 1AKH chain A, in and out of the DNA-binding region (not defined). | Pairs at lag 1 to 5 on the chain's sequence; a residue is DNA-binding when a heavy atom lies within 4.5 Å of the DNA in 1AKH. |

## Figures and scores

Each figure is the PMC JPEG, 600 px wide. Our version is drawn on the same pixel grid: the axes are
fitted to the tick marks (`figures.py`, `GRID`, `F2A`, `F2B`), the published curves are picked out
by colour, and each curve is scored both ways at 2 px. Controls: another method's curve from our run
(wrong input) and our curve moved by 3 points of true positive rate (near misses). The pass mark is
75% or 5 points above the best control. It is set by the three curves of Fig. 5 drawn from Lou et
al.'s published outputs, which are the same data as the paper's and score 78 to 97%; dashed and
dotted lines lose pixels in their gaps. Fig. 1 and Fig. 2 are compared as values; their renders are
for the eye. In Fig. 2 our weights are in arbitrary units, scaled so that our largest pair weight is
the colour bar's 150 and our tallest bar is the tallest published bar.

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config`, `run_skyriver.sbatch` | The pipeline and the cluster profile. |
| `requirements.txt` | Pinned Python packages. |
| `results_notes.json` | What a person writes: labels, the paper's values, assumptions, causes, page prose. |
| `pipeline/` | The scripts above, plus `check_results.py`, `compare_runs.py` and `check_package.py` (from the paper2repro skill), `readme_tables.py`, `page_template.html`. |
| `published/` | The paper's figures (CC BY 4.0). |
| `output/pssm/` | The PSSMs of the 1,261 chains, packed (int8 scores), for UniRef100 and UniRef90 2014_01. |
| `output/run/` | Every number of the run (JSON). |
| `output/figures/` | Renders, overlays and `scores.json`. |
| `output/sensitivity.json`, `homology_removed.tsv`, `blastp_bench_vs_pdb186.tsv`, `report.md` | Variants, the filter and the check report. |

## Limits

- The 2014 nr is gone, so no profile is the paper's. UniRef100 and UniRef90 of January 2014 move the
  PSSM-DT jackknife by half a point; how far the paper's nr would move it is unknown.
- The comparator encodings and the two rebuilt predictors are "in-house implementations" known only
  by citation. Ours follow the definitions of Lou et al. 2014 and mostly score higher than the paper's,
  which shrinks the paper's main margin.
- The homology filter of the independent test cannot run as written and the paper does not say how
  many chains it removed; PDB186 does not come back with any filter we tried.
- PMC's figures are 600 px JPEGs; a 2 px tolerance is about half a percentage point on the ROC axes.
- Fig. 2D (a structure drawing) and Fig. 6 (a screenshot) are not results.
