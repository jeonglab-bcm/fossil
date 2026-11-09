# fossil

Independent reproductions of published computational papers. Each folder is one paper, named by its
PubMed Central ID. Each folder holds our code, our data, and our results. We do not redistribute the
papers or their supplements.

| Folder | Paper | Status |
| --- | --- | --- |
| [`PMC1847688`](PMC1847688/) | Mantini D, Petrucci F, Pieragostino D, et al. LIMPIC: a computational method for the separation of protein MALDI-TOF-MS signals from noise. *BMC Bioinformatics* 8:101 (2007). [doi:10.1186/1471-2105-8-101](https://doi.org/10.1186/1471-2105-8-101) | Figs 2, 3, 4c, 5, 6a–d, 7 and 8 reproduced; Figs 9a–b close; Tables 1–3 differ |
| [`PMC4247685`](PMC4247685/) | Curry EWJ. A framework for generalized subspace pattern mining in high-dimensional datasets. *BMC Bioinformatics* 15:355 (2014). [doi:10.1186/s12859-014-0355-5](https://doi.org/10.1186/s12859-014-0355-5) | Fig. 5 reproduced, Fig. 2 rerun, Figs 3 and 4 reconstructed from TCGA; implementation analysis |
| [`PMC2349296`](PMC2349296/) | Pyysalo S, Airola A, Heimonen J, et al. Comparative analysis of five protein-protein interaction corpora. *BMC Bioinformatics* 9(Suppl 3):S6 (2008). [doi:10.1186/1471-2105-9-S3-S6](https://doi.org/10.1186/1471-2105-9-S3-S6) | Co-occurrence and Table 3 identical on HPRD50, IEPA and LLL; RelEx rebuilt (AIMed at the published values); Figs 1 and 2 redrawn; main claim holds; 4 of 8 text claims differ, from BioInfer (later corpus version) and the RelEx rebuild |
| [`PMC4081639`](PMC4081639/) | Yu P, Shaw CA. An efficient algorithm for accurate computation of the Dirichlet-multinomial log-likelihood function. *Bioinformatics* 30(11):1547–1554 (2014). [doi:10.1093/bioinformatics/btu079](https://doi.org/10.1093/bioinformatics/btu079) | Figs 2, 4, 5, 6 and Table 1 reproduced; implementation analysis |
| [`PMC4426843`](PMC4426843/) | Bleazard T, Lamb JA, Griffiths-Jones S. Bias in microRNA functional enrichment analysis. *Bioinformatics* 31(10):1592–1598 (2015). [doi:10.1093/bioinformatics/btv023](https://doi.org/10.1093/bioinformatics/btv023) | miRanda predictions regenerated (99.87% of the published target lists); Fig. 1 and Table 1 reproduced; Table 2 basic algorithm reproduced, multi-hit counts differ; Table 3 (rice) not reproducible |
| [`PMC1800866`](PMC1800866/) | Passerini A, Andreini C, Menchetti S, Rosato A, Frasconi P. Predicting zinc binding at the proteome level. *BMC Bioinformatics* 8:39 (2007). [doi:10.1186/1471-2105-8-39](https://doi.org/10.1186/1471-2105-8-39) | 38 results: 2 exact, 6 agree, 14 partly, 5 inconclusive, 6 differ, 5 not attempted. Main claim holds (gated beats local in LOO and CV); Fig. 1 and the Table 1 multiple-site counts come back; AURPCs and the proteome count differ with today's profiles; `spsvm` package |
| [`PMC4015815`](PMC4015815/) | Liu B, Xu J, Zou Q, Xu R, Wang X, Chen Q. Using distances between Top-n-gram and residue pairs for protein remote homology detection. *BMC Bioinformatics* 15(Suppl 2):S3 (2014). [doi:10.1186/1471-2105-15-S2-S3](https://doi.org/10.1186/1471-2105-15-S2-S3) | 1 exact, 11 agree, 6 partly, 2 inconclusive, 4 differ, 3 not attempted (`results.json`): SVM-DR ROC, Fig. 3 (9 of 10 points) and Figs 4B, 5C–D reproduced; ROC50 not reproduced as defined (explained); SVM-DT re-measured on rebuilt profiles (family 2.5.1.3 back, mean ROC 0.01 high); Gist 2.3 ported |

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

The workflows `.github/workflows/reproduce.yml` (PMC4081639), `.github/workflows/reproduce-pmc4247685.yml` and `.github/workflows/reproduce-pmc1847688.yml` rerun a reproduction with Nextflow when started by hand from the Actions tab, and check the run against its `results.json`. `.github/workflows/reproduce-pmc2349296.yml` reruns its reproduction on changes to its figure-reproduction files or workflow, or when started by hand. `.github/workflows/reproduce-pmc4426843.yml` does the same for PMC4426843 from its committed miRanda predictions, resampling three of its 22 empirical nulls (all of them when started by hand with `rerun = all`). `.github/workflows/reproduce-pmc4015815.yml` reruns PMC4015815 at dMAX 10–200 on changes to its figure-reproduction files or workflow, reading the slow dMAX = 0 points and the PSI-BLAST profiles from the committed outputs (dMAX = 0 too when started by hand with `dmax_zero`). `.github/workflows/reproduce-pmc1800866.yml` reruns PMC1800866 on changes to its folder from its committed PSI-BLAST profiles and leave-one-out predictions, recomputing the five-fold CV, the figures, the proteome sample scan and its `spsvm` package check.

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

Values come from JSON (`"path": "pfs.p"`, or `"fig3.panel=a.published_within_2px"` to pick a list
item by a field), from CSV (`"column"`, `"where"`, `"agg"`), or as a file's SHA-256
(`"digest": "sha256"`). Paths are those of the pipeline's output directory; `"committed_paths"`
maps them to the committed layout where the two differ. A tolerance is `{"abs": …}`, `{"rel": …}` or both. Without one, the value
must be equal. Timings and other values that depend on the machine are left out.
