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

16 results: 2 agree, 11 partly agree, 1 differs, 2 not attempted; 8 open causes.

| Result | Verdict | Ours against the paper |
| --- | --- | --- |
| Fig. 2A, missing haplotype against distance | partly | 8 of 14 points inside the published error bars plus ours; the recombinant curve follows the published one to 300 bp and then runs 0.03 to 0.06 low |
| Fig. 2B, with the fit of Eq. 5 | partly | 7 of 9 points; the fit is 0.106 + 0.261 (1 - exp(-4.06e-05 x)) against the published 0.10 + 0.26 (1 - exp(-4.39e-05 x)) |
| Fig. 2B legend and Methods: c0, c1, c2, <M pA pB> | partly | c1 0.261 against 0.26; c0 0.106 against 0.10; c2 4.06e-05 against 4.39e-05; <M pA pB> 1.19 against 0.93 |
| Eq. 3: rho = 1.4 +- 0.6 x 10^-5 | partly | 9.8e-06, inside the paper's own standard deviation; our bootstrap deviation is 0.39e-05 against 0.55e-05 |
| Fig. 3, printed mean, median, standard deviation | differs | 0.92, 0.83 and 0.39 x 10^-5 against 1.51, 1.38 and 0.55 |
| Fig. 3, the bootstrap histogram | partly | 27.2% of the published ink within 2 px (best control 26.1%): the shape is the paper's, the peak sits 0.6e-05 left |
| Fig. 4, the three cumulative distributions | partly | 15 of 18 readable points within two standard errors |
| Results: 15% faster than 0.002 per generation | partly | 16%; fastest non-synonymous change 0.011 against 0.01; s of the top sixth 0.0083 against 0.008; the synonymous tail without hitch-hiking reaches 0.0041 against 0.003 |
| Results: the two Kolmogorov-Smirnov p values | partly | 7.6e-14, below the paper's 1e-13; 3.6e-21 against its 1e-25 |
| Results: no distance dependence for other haplotypes | partly | Flat against the recombinant curve, but rising 0.054 over 500 bp where the published one falls 0.041 |
| Discussion numbers from the paper's own rho | agrees | All four come back: factor 21.4 (20), coinfection 0.093 (0.1), sweep region 155 bp (200), spacing 444 bp (400) |
| Discussion numbers from our rho | partly | 3 of 4; the factor below template switching is 31 rather than 20 |
| Methods: the cutoff at 2 or 4 alleles gives similar results | partly | At 2 alleles rho is 1.3e-05; at 4 the fit runs into its bound and gives 4.1e-06 on 3,570 pairs |
| Fig. 1 | not attempted | A schematic of two sites and four haplotypes |
| The authors' scripts | not attempted | Never released |
| The package | agrees | `hivrecomb` installs in a fresh environment, 7 tests pass, the tutorial runs |

Both findings of the paper come back. The probability that a missing two-site haplotype appears at the next
sample rises with the distance between the sites and with the time between the samples, while the haplotypes
recombination cannot build stay flat, and about a sixth of the non-synonymous polymorphisms change faster
than 0.002 per generation, where the synonymous ones do not. The rate itself is 9.8e-06 per site and
generation against the paper's 1.4e-05, inside its own standard deviation, and its three bootstrap statistics
sit about 40 percent low. That gap is open: the fit parameters c0, c1 and c2 come back, so the rate differs
through the divisor `<M pA pB> - c0`, and no averaging convention we tried gives the paper's 0.93 (five tried,
1.04 to 1.60). Building MUSCLE 3.6 from its own source instead of running its 2005 binary moves the rate from
1.25e-05 to 9.8e-06, so the alignment carries part of it; adding the 212 Shriner 2004 clones that LANL's set 1
holds beyond the paper's accession list moves it further away, so they were left out.

Kept local and gitignored: `sources/` (the paper, the GenBank records, LANL's files, MUSCLE), `work/` (the
alignments, Slurm logs, scratch runs) and `.venv/`.

## Run it

```bash
nextflow run PMC2813257/figure-reproduction/main.nf --outdir results
```

About 4 minutes on one node (4 cores), most of it the GenBank download and the MUSCLE build. On the
Skyriver cluster, `sbatch PMC2813257/figure-reproduction/run_skyriver.sbatch` runs the head and every step as
Slurm jobs. The hypothesis tests behind the causes run with `--studies` (about 15 minutes more).
