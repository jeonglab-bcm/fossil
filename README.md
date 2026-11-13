# fossil

Independent reproductions of published computational papers. Each folder is one paper, named by its
PubMed Central ID. Each folder holds our code, our data, and our results. We do not redistribute the
papers or their supplements.

| Folder | Paper | Status |
| --- | --- | --- |
| [`PMC1847688`](PMC1847688/) | Mantini D, Petrucci F, Pieragostino D, et al. LIMPIC: a computational method for the separation of protein MALDI-TOF-MS signals from noise. *BMC Bioinformatics* 8:101 (2007). [doi:10.1186/1471-2105-8-101](https://doi.org/10.1186/1471-2105-8-101) | Figs 2, 3, 4c, 5, 6a–d, 7 and 8 reproduced; Figs 9a–b close; Tables 1–3 differ |
| [`PMC2850872`](PMC2850872/) | Yu W, Liu T, Valdez R, Gwinn M, Khoury MJ. Application of support vector machine modeling for prediction of common diseases: the case of diabetes and pre-diabetes. *BMC Medical Informatics and Decision Making* 10:16 (2010). [doi:10.1186/1472-6947-10-16](https://doi.org/10.1186/1472-6947-10-16) | Table 1 1 of 8 counts exact (diagnosed 1,266 as published, the rest within 10); Table 2 6 of 8 AUCs within the split spread (polynomial kernels differ); Table 3 9 of 15 and 14 of 14; Fig. 2 30 of 35 curve points; main claim holds; package `diabclass`; 7 verdicts set to agrees in review |
| [`PMC4247685`](PMC4247685/) | Curry EWJ. A framework for generalized subspace pattern mining in high-dimensional datasets. *BMC Bioinformatics* 15:355 (2014). [doi:10.1186/s12859-014-0355-5](https://doi.org/10.1186/s12859-014-0355-5) | Fig. 5 reproduced, Fig. 2 rerun, Figs 3 and 4 reconstructed from TCGA; implementation analysis |
| [`PMC2349296`](PMC2349296/) | Pyysalo S, Airola A, Heimonen J, et al. Comparative analysis of five protein-protein interaction corpora. *BMC Bioinformatics* 9(Suppl 3):S6 (2008). [doi:10.1186/1471-2105-9-S3-S6](https://doi.org/10.1186/1471-2105-9-S3-S6) | Co-occurrence and Table 3 identical on HPRD50, IEPA and LLL; RelEx rebuilt (AIMed at the published values); Figs 1 and 2 redrawn; main claim holds; 4 of 8 text claims differ, from BioInfer (later corpus version) and the RelEx rebuild |
| [`PMC4081639`](PMC4081639/) | Yu P, Shaw CA. An efficient algorithm for accurate computation of the Dirichlet-multinomial log-likelihood function. *Bioinformatics* 30(11):1547–1554 (2014). [doi:10.1093/bioinformatics/btu079](https://doi.org/10.1093/bioinformatics/btu079) | Figs 2, 4, 5, 6 and Table 1 reproduced; implementation analysis |
| [`PMC4426843`](PMC4426843/) | Bleazard T, Lamb JA, Griffiths-Jones S. Bias in microRNA functional enrichment analysis. *Bioinformatics* 31(10):1592–1598 (2015). [doi:10.1093/bioinformatics/btv023](https://doi.org/10.1093/bioinformatics/btv023) | miRanda predictions regenerated (99.87% of the published target lists); Fig. 1 and Table 1 reproduced; Table 2 basic algorithm reproduced, multi-hit counts differ; Table 3 (rice) not reproducible |
| [`PMC4015815`](PMC4015815/) | Liu B, Xu J, Zou Q, Xu R, Wang X, Chen Q. Using distances between Top-n-gram and residue pairs for protein remote homology detection. *BMC Bioinformatics* 15(Suppl 2):S3 (2014). [doi:10.1186/1471-2105-15-S2-S3](https://doi.org/10.1186/1471-2105-15-S2-S3) | 1 exact, 11 agree, 6 partly, 2 inconclusive, 4 differ, 3 not attempted (`results.json`): SVM-DR ROC, Fig. 3 (9 of 10 points) and Figs 4B, 5C–D reproduced; ROC50 not reproduced as defined (explained); SVM-DT re-measured on rebuilt profiles (family 2.5.1.3 back, mean ROC 0.01 high); Gist 2.3 ported |
| [`PMC2666661`](PMC2666661/) | Meng YA, Yu Y, Cupples LA, Farrer LA, Lunetta KL. Performance of random forest when SNPs are in linkage disequilibrium. *BMC Bioinformatics* 10:78 (2009). [doi:10.1186/1471-2105-10-78](https://doi.org/10.1186/1471-2105-10-78) | 11 exact, 7 agree, 10 partly, 1 differs, 5 not attempted (`results.json`): revised Random Forests rebuilt (`rfld`, checked against the Fortran original); Table 1 and Figs 1-3 reproduced (Fig. 2 with two series the paper swaps); main claim holds except for H1M1; haplotype Figs 4-6 low-r² gap open; Tables 2-4 need unavailable TGen data |
| [`PMC2563693`](PMC2563693/) | Lee E, Chuang HY, Kim JW, Ideker T, Lee D. Inferring pathway activity toward precise disease classification. *PLoS Computational Biology* 4(11):e1000217 (2008). [doi:10.1371/journal.pcbi.1000217](https://doi.org/10.1371/journal.pcbi.1000217) | 4 exact, 7 agree, 33 partly, 5 differ, 3 not attempted (`results.json`): PAC method rebuilt from the paper (`pacorg`); all 18 CORG lists of Table 1 exact from the GSEA lung files; Fig. 2 Michigan panels (E, F) and Fig. 4 back; PAC beats Gene in 4 of 7 datasets and 2 of 4 transfers as in the paper; breast data, Boston pathway pre-selection and NF-kB sample choice differ (open) |

Other analyses:

- [`availability-audit`](availability-audit/): what still works in 7,080 open-access bioinformatics and
  biomedical-informatics methodology papers from 2004–2015 (links, Wayback captures, repository
  accessions, supplementary files, and the software of a 150-paper sample), with a per-paper
  readiness tier for choosing reproduction targets.
- [`publication-trends`](publication-trends/): PMC articles per year (2000–2026) mentioning
  code hosts, R and Python ecosystems, DOI archives, data repositories, and software environment tools,
  as a proxy for when code and data sharing took hold.

Figures for the papers are in [`figures/`](figures/).

Site: <https://jeonglab-bcm.github.io/fossil/>

The workflows `.github/workflows/reproduce.yml` (PMC4081639), `.github/workflows/reproduce-pmc4247685.yml` and `.github/workflows/reproduce-pmc1847688.yml` rerun a reproduction with Nextflow when started by hand from the Actions tab, and check the run against its `results.json`. `.github/workflows/reproduce-pmc2349296.yml` reruns its reproduction on changes to its figure-reproduction files or workflow, or when started by hand. `.github/workflows/reproduce-pmc2850872.yml` reruns PMC2850872 on changes to its folder, refitting every model from the committed grid search (the search itself, about 80 minutes, only when started by hand with `search = true`). `.github/workflows/reproduce-pmc4426843.yml` does the same for PMC4426843 from its committed miRanda predictions, resampling three of its 22 empirical nulls (all of them when started by hand with `rerun = all`). `.github/workflows/reproduce-pmc4015815.yml` reruns PMC4015815 at dMAX 10–200 on changes to its figure-reproduction files or workflow, reading the slow dMAX = 0 points and the PSI-BLAST profiles from the committed outputs (dMAX = 0 too when started by hand with `dmax_zero`). `.github/workflows/reproduce-pmc2666661.yml` reruns PMC2666661 on changes to its figure-reproduction or package files, rerunning four simulation replicates from scratch and the rest from the committed per-replicate statistics (the port check against the Fortran program too when started by hand with `port_check`). `.github/workflows/reproduce-pmc2563693.yml` reruns PMC2563693 on changes to its figure-reproduction or package files, rebuilding the seven datasets and every deterministic result from scratch and rerunning two cross-validation repeats per experiment against the committed full run.

## Results check

Each reproduction lists the results it stands on in `PMC…/figure-reproduction/results.json`. Each
entry gives:

- where the pipeline writes the value (a file under its output directory and a path into it);
- the value expected;
- how far a rerun may stray from it.

When a pull request creates or changes a reproduction's `results.json`, `.github/workflows/results-check.yml`
compares it with the outputs committed in the same pull request. Nothing is rerun, so it takes seconds.
It keeps one comment per reproduction on the pull request, with:

- what the pull request changes in `results.json` (a diff of expected values);
- any result that does not agree with the committed outputs (expected against committed);
- the full table;
- an overlay of each published figure with the committed render. Grey is where they agree within
  2 px, dark is only in the paper, and green is only in the render. Only renders the pull request
  changes are shown, or all of them when it adds `results.json`. The images live on the `ci-assets`
  branch.

The job fails if a value is missing or outside its tolerance. A full rerun, started by hand, is
checked against `results.json` in the same way.

```sh
python3 tools/check_results.py PMC4247685/figure-reproduction/results.json --committed               # against the committed outputs
python3 tools/check_results.py PMC4247685/figure-reproduction/results.json results --report results-check   # against a run
python3 tools/check_results.py PMC4247685/figure-reproduction/results.json results --update            # after an intended change
```

Each reproduction also names the [Paper2Repro](https://github.com/jeonglab-bcm/Paper2Repro) release
it was made with, in a `skill` block in `PMC…/results.json`. Papers made before that file existed keep
it in `PMC…/figure-reproduction/results.json`. Sessions write it with the skill's
`scripts/skill_version.py`. Blocks added afterwards say how the version was found (`source`:
`transcript`, `inferred`, `none` or `unknown`, with a `note`). The `skill` job in the same workflow
fails when a pull request adds a paper, or changes a paper's `results.json`, without a block whose
version is a `paper2repro-v…` tag of Paper2Repro.

The same job checks that the front page's Paper2Repro column matches each paper's block. The
column is written by `tools/site_versions.py --write`, never by hand.

```sh
python3 tools/check_skill.py --all                 # every paper
python3 tools/check_skill.py --base origin/main    # what this branch adds or changes
```

Values come from JSON (`"path": "pfs.p"`, or `"fig3.panel=a.published_within_2px"` to pick a list
item by a field), from CSV (`"column"`, `"where"`, `"agg"`), or as a file's SHA-256
(`"digest": "sha256"`). Paths are those of the pipeline's output directory; `"committed_paths"`
maps them to the committed layout where the two differ. A tolerance is `{"abs": …}`, `{"rel": …}` or both. Without one, the value
must be equal. Timings and other values that depend on the machine are left out.
