# fossil

Independent reproductions of published computational papers. Each folder is one paper, named by its
PubMed Central ID. Each folder holds our code, our data, and our results. We do not redistribute the
papers or their supplements.

| Folder | Paper | Status |
| --- | --- | --- |
| [`PMC4247685`](PMC4247685/) | Curry EWJ. A framework for generalized subspace pattern mining in high-dimensional datasets. *BMC Bioinformatics* 15:355 (2014). [doi:10.1186/s12859-014-0355-5](https://doi.org/10.1186/s12859-014-0355-5) | Figs 2 and 5 reproduced, Figs 3 and 4 running; implementation analysis |
| [`PMC4081639`](PMC4081639/) | Yu P, Shaw CA. An efficient algorithm for accurate computation of the Dirichlet-multinomial log-likelihood function. *Bioinformatics* 30(11):1547–1554 (2014). [doi:10.1093/bioinformatics/btu079](https://doi.org/10.1093/bioinformatics/btu079) | Figs 2, 4, 5, 6 and Table 1 reproduced; implementation analysis |

Other analyses:

- [`publication-trends`](publication-trends/): PMC articles per year (2000–2026) mentioning
  code hosts, R and Python ecosystems, DOI archives, data repositories, and software environment tools,
  as a proxy for when code and data sharing took hold.

Figures for the papers are in [`figures/`](figures/).

Site: <https://jeonglab-bcm.github.io/fossil/>

The workflows `.github/workflows/reproduce.yml` (PMC4081639) and `.github/workflows/reproduce-pmc4247685.yml` rerun each reproduction with Nextflow on every change.
