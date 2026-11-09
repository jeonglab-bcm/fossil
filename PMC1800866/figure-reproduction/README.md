# PMC1800866 figure reproduction

Passerini A, Andreini C, Menchetti S, Rosato A, Frasconi P. Predicting zinc binding at the proteome level.
*BMC Bioinformatics* 8:39 (2007). [doi:10.1186/1471-2105-8-39](https://doi.org/10.1186/1471-2105-8-39). CC BY 2.0.

The published figures in `published/` are the paper's (CC BY 2.0, attribution above). Nothing else of the paper,
its supplements or the authors' code is in this folder.

## Results

Every verdict is computed by `pipeline/check_results.py` from the numbers in `../results.json`; the results page
is generated from it. 38 results: 2 exact, 6 agree, 14 partly agree, 5 inconclusive, 6 differ, 5 not attempted.

- **Main claim (exact, 9 of 9 comparisons).** The gated SPCH-SVM beats the local SVM in leave-one-out and in CV,
  on cysteines and on histidines; the AUC differences exceed the sum of the two standard errors.
- **LOO (partly).** AUC 0.893 ± 0.007 and 0.913 ± 0.007 (paper 0.895 ± 0.007, 0.914 ± 0.006); AURPC 0.678 and
  0.709 (paper 0.590 and 0.633).
- **CV (partly).** AUC 0.852 and 0.877 (paper 0.867, 0.890); AURPC 0.494 and 0.552 (paper 0.428, 0.500).
- **SPCHDE-SVM (partly).** D and E AUCs in LOO 0.74 ± 0.03 and 0.70 ± 0.06, as printed; in CV 0.70 and 0.63
  (paper 0.73, 0.65). Zn4 chains are the easiest at protein level and SPCHDE beats SPCH on Zn3 chains (exact).
- **Tables 1 to 3 and Fig. 2 (partly).** 450 sites in 295 chains against 464 in 305. The 11 multiple-site-type
  counts of Table 1 come back exactly; the other counts are short, mostly in Zn4.
- **Fig. 1 (agrees).** 95% and 87% of the published curves lie within 2 px of ours; the best controls reach
  62% and 47%.
- **Figs 3 to 6 (partly, inconclusive or differs).** Our curves are drawn on the published axes; 8% to 39% of the
  published curve lies within 2 px of ours.
- **Human proteome (differs).** About 2,010 (SE 101) zinc proteins from a stratified sample of 300, against 2,833.
- **Figs 8 and 9 (differs).** The same four cysteines of NP_060357.1 rank highest, at lower probabilities.
- **Later structures (agree).** PDB 5ZLQ (2018) binds zinc with exactly the four cysteines of Fig. 8, Cys65
  included; 2HD5 shows the CX2CX43CX2C site predicted for the UBP family (Fig. 9).
- **Not attempted.** Fig. 7 and the 350/100 counts (they need Andreini et al. 2006's paywalled reliability
  levels), the two homology-model renderings, and the authors' code (lost).

The paper's main claim holds: the gated predictor beats the local one in both tests, on cysteines and on
histidines, by more than the error bars. The AURPCs, the proteome count and the single probabilities do not come
back; the causes are our 2010 profiles in place of the lost 2005 ones and the Platt constants tuned on those.

## What the code does against the paper

| Step | Paper | Here |
| --- | --- | --- |
| Zinc chains and labels | 305 chains of the June 2005 PDB, 3 Å cutoff | The 296 chains and every C, H, D, E residue of Additional file 1, mapped to today's SEQRES (`parse_structures.py`, `run_svm.py prepare`). 15 chains need an offset; 28 of 13,837 LOO residues are dropped. |
| Sites (Tables 1 to 3, Figs 1, 2) | Donors within 3 Å | Side-chain donors of C, H, D, E, N, Q within 3 Å of each zinc in today's mmCIF, asymmetric unit (`analyze_sites.py`). |
| Profiles | PSI-BLAST on the 2005 nr, settings not given | PSI-BLAST 2.17.0, 3 iterations, defaults, on UniRef100 release 2010_01, the oldest UniRef archive (`run_psiblast.sh`, `run_profiles.sbatch`). |
| Descriptor | 20 profile values, entropy, relative weight, out-of-chain flag (p = 23) | Weighted observed percentages / 100, information per position, relative weight, flag (`spsvm.descriptors`). |
| Local SVM | Gaussian on a linear window kernel, k = 5 | RBF SVM on the 11 × 23 window, γ 0.1, C 5 (`spsvm.SPSVM`). |
| Semi-pattern SVM | Eq. 1 with a Gaussian on top, k = 6, gaps 0 to 7 | Eq. 1 as an explicit feature map (tested equal), RBF γ 0.05, C 5. |
| Platt, gating | A, B tuned; Eq. 2 | A, B of Additional file 1; Eq. 2 (`spsvm.gate`). |
| LOO and CV | HSSP ≤ 5 subset; SCOP-superfamily folds | The sets and folds of Additional file 1 (`run_svm.py`, `run_loo.sbatch`). |
| AURPC, AUC SE | Not stated; Wilcoxon-Mann-Whitney SE | Average precision of the pooled predictions; Hanley-McNeil SE (`evaluate.py`). |
| Protein level | ≥ 3 residues above a threshold | A chain's third-highest probability; positives per site type, negatives all metal-free chains. |
| Proteome | All 27,960 Build 35.1 proteins | A stratified sample of 300, plus the 65 USP and 26 ADAM-TS proteins (`sample_proteome.py`, `scan_proteome.py`). |

## Details

**Tables 1 to 3 and Figs 1 and 2.** Additional file 1 lists 296 of the 305 zinc chains. Today's 1H79 models its
four-cysteine metal as iron (FE2), so 295 chains have a zinc site. Counting only side-chain donors of the six
residue types of Table 2 brings back all 11 multiple-site-type counts; counting every N, O or S atom brings 29
ligands from other residue types and 3 of the 11 counts off. Fig. 1 matches when X and Y are the C and H of the
zinc chains, the separation is the number of residues between them, and P(X|Y) is taken over pairs. In Fig. 2b a
chain counts as covered when any of its sites holds the semi-pattern; the published 13 covered Zn1 chains need
this, because no Zn1 site can hold it.

**Figs 3 to 6.** The published curves are vector drawings; `extract_published_curves.py` reads them out of the PDF.
The printed AURPCs sit 0.031 to 0.034 below the area under the paper's own curves (LOO 0.624 and 0.666, CV
0.462 and 0.531). On our curves, average precision, the trapezoid and the drawn area differ by 0.002 or less, and
fold-averaging changes nothing. So the gap is not an estimator choice we could find.

**Proteome.** The SPCH-SVM trained on all CV chains calls 81 of the 100 sampled proteins that both methods called,
4 of 50 that only Andreini et al. called, 10 of 50 that only the paper's predictor called, and 0 of 100 others.
With Platt constants refitted to our own CV margins (a sensitivity test, not agreement), the estimate rises to
2,223 (SE 94).

**Paper slip.** Table 2 prints fa = 69.3 for cysteine in Zn4 sites; 663 / 956 = 69.35%, which rounds to 69.4
(every other cell rounds to nearest).

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | The pipeline; `-profile skyriver` runs each process as a Slurm job. |
| `run_skyriver.sbatch` | Runs the pipeline on the Skyriver cluster. |
| `run_profiles.sbatch`, `run_loo.sbatch` | The two slow steps, on the cluster: PSI-BLAST profiles and the leave-one-out. |
| `requirements.txt` | Pinned Python packages (Python 3.12); the method is `../package`. |
| `results_notes.json` | Labels, sources, assumptions, causes and pass marks, written by hand; merged with the run into `../results.json`. |
| `results.json` | The repository's results check (`tools/check_results.py`), generated by `pipeline/make_results_check.py`. |
| `pipeline/` | The steps (below), `check_results.py`, `compare_runs.py` and `check_package.py` from Paper2Repro, `params/` (checksums, the paper's printed tables). |
| `published/` | The paper's figures for comparison. |
| `output/` | The committed run: `struct/` (parsed PDB chains), `profiles/` (PSI-BLAST profiles, `.npz`), `predictions/` (candidates, CV and LOO predictions), `sites/`, `figures12/`, `evaluation/`, `proteome/`, `published_curves.json`, `package.json`. |

## Run

From the repository root, with Python 3.12, `pip install -r PMC1800866/figure-reproduction/requirements.txt ./PMC1800866/package`,
uv, Java 21 and Nextflow 25.04:

```sh
nextflow run PMC1800866/figure-reproduction/main.nf --outdir results          # about 15 min on 2 cores
nextflow run PMC1800866/figure-reproduction/main.nf --outdir results --full   # also refetch and parse the 2,314 PDB entries
sbatch PMC1800866/figure-reproduction/run_skyriver.sbatch                     # the same on the cluster
```

The default run reads the committed profiles and LOO predictions and reruns everything else, the five-fold CV of
both models included; its check step fails if the fresh run differs from `output/`. CI
(`.github/workflows/reproduce-pmc1800866.yml`) runs it on every pull request that touches this folder.

The slow steps run on the cluster and their outputs are committed:

```sh
sbatch PMC1800866/figure-reproduction/run_profiles.sbatch   # PSI-BLAST: database, 2,458 + 392 profiles (about 60 CPU hours)
python PMC1800866/figure-reproduction/pipeline/run_svm.py prepare <S1 dir> PMC1800866/figure-reproduction/output/struct/chains.tsv \
       PMC1800866/figure-reproduction/output/profiles/pdb_profiles.npz PMC1800866/work/svm
sbatch PMC1800866/figure-reproduction/run_loo.sbatch        # 3,840 SVM fits (about 30 CPU hours)
python PMC1800866/figure-reproduction/pipeline/run_svm.py merge CH PMC1800866/work/svm   # and CHDE
```

## Pipeline steps

| Process | Script | Does |
| --- | --- | --- |
| FETCH | `fetch_inputs.sh` | PDF, Additional files 1 and 3 and the figures from PMC's open-access bucket (Europe PMC as fallback), SHA-256 checked; PDB 5ZLQ and 2HD5; with `--full` the 2,314 PDB entries and the human proteome. |
| PUBLISHED | `published.py`, `extract_published_curves.py` | The published figures; the curves of Figs 3 to 6 as numbers from the PDF. |
| STRUCTURES | `parse_structures.py` (`--full`) | SEQRES and zinc contacts of the supplement's chains; otherwise the committed `output/struct`. |
| SITES | `analyze_sites.py`, `text_arithmetic.py` | Tables 1 to 3, Figs 1 and 2 counts; the text's claims from the paper's own tables. |
| FIGURES_1_2 | `figure1.py`, `figure2.py` | Renders, overlays and scores with controls. |
| PREPARE, CV | `run_svm.py` | Candidates on today's SEQRES; five-fold CV of the SPCH- and SPCHDE-SVM. |
| EVALUATE | `evaluate.py` | AURPC, AUC, protein-level curves, the text's comparisons, Figs 3 to 6 renders, overlays and scores. |
| PROTEOME | `scan_proteome.py` | The sample scan, Figs 8 and 9 probabilities, the families, the later structures, the Platt-refit sensitivity. |
| PACKAGE | `check_package.py` | The package built, installed fresh, tested, its tutorial rerun. |
| RESULTS | `build_results.py`, `check_reproduction.py`, `build_page.py` | `results.json` with computed verdicts; the comparison with `output/` (`compare_runs.py`); the results page. |

## Limits

- The 2005 nr is not archived, and the paper gives no PSI-BLAST settings. Our profiles (UniRef100 2010_01) differ
  from the paper's, and the SVM and Platt parameters were tuned on the paper's profiles.
- Nine zinc chains of the paper are not in Additional file 1, and PDB entries changed after 2005 (1H79).
- The proteome count is a sample estimate; a full scan needs about 4,000 CPU hours of PSI-BLAST.
- Fig. 7 needs Andreini et al. 2006's per-protein reliability levels, which are behind a paywall.
- We did not rebuild the homology models of Figs 8 and 9; later crystal structures test their claims instead.
