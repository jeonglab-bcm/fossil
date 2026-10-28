# fossil

Independent reproductions of published computational papers. Each folder is one paper, named by its
PubMed Central ID. Each folder holds our code, our data, and our results. We do not redistribute the
papers or their supplements.

| Folder | Paper | Status |
| --- | --- | --- |
| [`PMC1847688`](PMC1847688/) | Mantini D, Petrucci F, Pieragostino D, et al. LIMPIC: a computational method for the separation of protein MALDI-TOF-MS signals from noise. *BMC Bioinformatics* 8:101 (2007). [doi:10.1186/1471-2105-8-101](https://doi.org/10.1186/1471-2105-8-101) | Figs 2, 3, 4c, 6a–d, 7 and 8 reproduced; Figs 5 and 9a–b close; Tables 1–3 differ |
| [`PMC4247685`](PMC4247685/) | Curry EWJ. A framework for generalized subspace pattern mining in high-dimensional datasets. *BMC Bioinformatics* 15:355 (2014). [doi:10.1186/s12859-014-0355-5](https://doi.org/10.1186/s12859-014-0355-5) | Fig. 5 reproduced, Fig. 2 rerun, Figs 3 and 4 reconstructed from TCGA; implementation analysis |
| [`PMC4081639`](PMC4081639/) | Yu P, Shaw CA. An efficient algorithm for accurate computation of the Dirichlet-multinomial log-likelihood function. *Bioinformatics* 30(11):1547–1554 (2014). [doi:10.1093/bioinformatics/btu079](https://doi.org/10.1093/bioinformatics/btu079) | Figs 2, 4, 5, 6 and Table 1 reproduced; implementation analysis |

Site: <https://jeonglab-bcm.github.io/fossil/>

The workflows `.github/workflows/reproduce.yml` (PMC4081639), `.github/workflows/reproduce-pmc4247685.yml` and `.github/workflows/reproduce-pmc1847688.yml` rerun each reproduction with Nextflow on every change.
