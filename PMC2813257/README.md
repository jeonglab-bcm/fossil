# PMC2813257: Recombination rate and selection strength in HIV intra-patient evolution (Neher and Leitner 2010)

Neher RA, Leitner T. Recombination rate and selection strength in HIV intra-patient evolution.
*PLoS Computational Biology* 6(1):e1000660 (2010).
[doi:10.1371/journal.pcbi.1000660](https://doi.org/10.1371/journal.pcbi.1000660) ·
[PMC2813257](https://pmc.ncbi.nlm.nih.gov/articles/PMC2813257/) · issue #51

The paper is in the public domain under the
[Creative Commons Public Domain declaration (CC0 1.0)](https://creativecommons.org/publicdomain/zero/1.0/).
This folder does not hold the paper or its full text; `figure-reproduction/published/` holds its four
figures at the publisher's resolution, for comparison.

The authors' analysis was written in Python with NumPy, SciPy and Matplotlib and was never released: the
paper gives no code link, has no supplement, and neither the arXiv preprint, the group's page of the time
nor any later repository of the group holds the scripts. We wrote the method from the paper's text as the
Python package [`package/`](package/) (`hivrecomb`), fetched the 1,753 HIV-1 *env* C2-V5 clones of 11
patients from the paper's four GenBank accession ranges, aligned each patient with MUSCLE 3.6 built from
its own source, and ran both analyses again: the missing-haplotype estimate of the recombination rate
(Figs 2 and 3) and the distribution of allele frequency changes (Fig. 4).

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: the downloads, the alignment, both analyses, the four panels drawn on the published pixel grid with their controls, the published points read back in data units, and the hypothesis tests behind the causes. |
| [`package/`](package/) | `hivrecomb`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, number and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC2813257/>

## Results

<!-- summary from results.json (check_results.py); the full table:
     python3 figure-reproduction/pipeline/check_results.py results.json --markdown -->

18 results: 4 agree, 8 partly agree, 4 differ, 2 not attempted; 9 open causes.

| Result | Verdict | Ours against the paper |
| --- | --- | --- |
| Fig. 2A, missing haplotype against distance | partly | 8 of 14 points inside the published error bars plus ours; the recombinant curve follows the published one to 300 bp and then runs 0.03 to 0.06 low |
| Fig. 2B, with the fit of Eq. 5 | partly | 7 of 9 points |
| Fig. 2B legend: c0, c1 and c2 | agrees | 0.106, 0.261 and 4.06e-05 against 0.10, 0.26 and 4.39e-05, each inside the spread of the same fit over the 500 resamples |
| Methods: `<M pA pB>` | differs | 1.19 against 0.93; this is the divisor that sets the rate |
| Eq. 3: rho = 1.4 +- 0.6 x 10^-5 | agrees | 9.8e-06, inside the standard deviation the paper prints |
| Fig. 3, printed mean, median, standard deviation | differs | 0.92, 0.83 and 0.39 x 10^-5 against 1.51, 1.38 and 0.55 |
| Fig. 3, the bootstrap histogram | differs | On the published axes our peak sits at 9 to 10 x 10^-6 against 13 to 15; a wrong-input control scores better than ours |
| Fig. 4, the three cumulative distributions | partly | 15 of 18 readable points within two standard errors |
| Fig. 4 inset, the observation counts | partly | 15 of 32; non-synonymous 9 of 15 bins, synonymous 4 of 10, synonymous without hitch-hiking 0 of 6 |
| Results: 15% faster than 0.002 per generation | partly | 4 of 5 counted fields; two of our 195 filtered synonymous observations lie beyond 0.003 per generation, where the paper reports none. The paper's own Fig. 4 puts its share at 17.2% where its text says about 15; ours is 15.9, between the two |
| Results: the two Kolmogorov-Smirnov p values | partly | 7.6e-14, below the paper's 1e-13; 3.6e-21 against its 1e-25 on 195 observations |
| Results: no distance dependence for other haplotypes | partly | Far flatter than the recombinant curve, but rising 0.054 +- 0.017 over 500 bp where the published one falls 0.041 |
| Discussion numbers from the paper's own rho | agrees | All four come back: factor 21.4 (20), coinfection 0.093 (0.1), sweep region 155 bp (200), spacing 444 bp (400) |
| Discussion numbers from our rho | partly | 3 of 4; the factor below template switching is 31 rather than 20 |
| Methods: the cutoff at 2 or 4 alleles gives similar results | differs | At two alleles rho is 1.3e-05, but at four the fit runs into its bound and gives 4.1e-06 |
| Fig. 1 | not attempted | A schematic of two sites and four haplotypes |
| The authors' scripts | not attempted | Never released |
| The package | agrees | `hivrecomb` installs in a fresh environment, 7 tests pass, the tutorial runs |

Both findings of the paper come back. The probability that a missing two-site haplotype appears at the next
sample rises with the distance between the sites and with the time between the samples, while the haplotypes
recombination cannot build stay flat; the fit of Figure 2B comes back with every constant inside its own
uncertainty, and the rate, 9.8e-06 per site and generation, lies inside the 1.4 +- 0.6 x 10^-5 the paper
prints. About a sixth of the non-synonymous polymorphisms change faster than 0.002 per generation, where the
synonymous ones do not.

Four things differ. The measured average `<M pA pB>` is 1.19 against the paper's 0.93, and since it divides
`c1 c2` it is what holds our rate below the paper's: with the paper's 0.93 our own fit gives 1.3e-05. The
bootstrap distribution of Figure 3 and its three printed statistics move with it, about 40 percent low. The
inset of Figure 4 shows a second, separate gap: the counts behind the curves. Ours are about half the paper's
for synonymous polymorphisms and a ninth of them for synonymous polymorphisms away from hitch-hiking (195
against about 1,850), which is also why our second Kolmogorov-Smirnov p value stops at 3.6e-21 rather than
below 1e-25. And the paper's claim that a cutoff at two or four alleles gives similar results does not hold at
four on our run, where the fit runs into its bound on 3,570 pairs.

Building MUSCLE 3.6 from its own source instead of running its 2005 binary moves the rate from 1.25e-05 to
9.8e-06, so the alignment carries part of the first gap; adding the 212 Shriner 2004 clones that LANL's set 1
holds beyond the paper's accession list moves it further away, so they were left out.

Kept local and gitignored: `sources/` (the paper, the GenBank records, LANL's files, MUSCLE), `work/` (the
alignments, Slurm logs, scratch runs) and `.venv/`.

## Run it

```bash
nextflow run PMC2813257/figure-reproduction/main.nf --outdir results
```

About 5 minutes on one node (4 cores), most of it the GenBank download and the MUSCLE build. On the
Skyriver cluster, `sbatch PMC2813257/figure-reproduction/run_skyriver.sbatch` runs the head and every step as
Slurm jobs. The hypothesis tests behind the causes run with `--studies` (about 15 minutes more).
