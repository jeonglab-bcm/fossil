# PMC2666661: Performance of random forest when SNPs are in linkage disequilibrium (Meng et al. 2009)

Meng YA, Yu Y, Cupples LA, Farrer LA, Lunetta KL. Performance of random forest when SNPs are in linkage
disequilibrium. *BMC Bioinformatics* 10:78 (2009).
[doi:10.1186/1471-2105-10-78](https://doi.org/10.1186/1471-2105-10-78) ·
[PMC2666661](https://pmc.ncbi.nlm.nih.gov/articles/PMC2666661/) · issue #41

The paper is © 2009 Meng et al., licensee BioMed Central, under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). This folder does not contain the paper or its full
text; `figure-reproduction/published/` holds its six figures (the JPEGs PMC serves) for comparison,
redistributed under CC BY 2.0 with the attribution above.

The authors' program, a revised Breiman and Cutler Random Forests 5.1 in Fortran 77 ("Random Forests Linkage
Disequilibrium project"), was only on a Broad Institute personal page that is gone and was never archived. We
rebuilt it from the paper as the Python package [`package/`](package/) (`rfld`): a step-by-step port of Random
Forests 5.1 with the revised tree builder (RF1) and importance (IM1), checked against Breiman and Cutler's
Fortran program, which is still online. With it we reran the paper's simulations: the H4M4 SNP study of Figs 1-3
(13 LD models, 100 replicates each), the same for the other six genetic models of Table 1, and the haplotype
study of Figs 4-6.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | Table 1 recomputed; Figs 1-6 read off the published JPEGs and compared with our simulations; the Nextflow pipeline, the cluster scripts, the port and haplo.stats checks. |
| [`package/`](package/) | `rfld`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC2666661/>

## Results

<!-- summary from results.json (check_results.py); the full table: python3 figure-reproduction/pipeline/check_results.py results.json --markdown -->

34 results: 11 exact, 7 agree, 10 partly agree, 1 differs, 5 not attempted; 6 open causes.

| Result | Verdict | Ours against the paper |
| --- | --- | --- |
| Table 1 | exact | 33 of 33 values recomputed from the model parameters; H2M3's GRR prints 5.22 for 5.227 (a rounding slip) |
| Fig. 1, mean IM | agrees | 40 of 40 bars within Monte Carlo error (e.g. RF0:IM0 0.306 against 0.302 with 4 LD.rSNPs; RF1:IM1 1.355 against 1.373) |
| Fig. 2, share above the noise | agrees | 36 of 36; the other 4 bars are two series the figure swaps (with the labels exchanged all 10 agree) |
| Fig. 3, top-X curves | agrees or partly | 120 of 122 points; the two misses sit where a curve jumps within one X step |
| Fig. 4, mean IM with haplotypes | partly | 30 of 33; the paper's 11 PRED.rHAP bars are one value repeated (0.654); rHAP at r² = 0 is 0.565 against our 0.736 |
| Fig. 5, share above the noise | partly | 28 of 33; at r² ≤ 0.4 the paper's true haplotypes reach 40-45%, ours 72-76% |
| Fig. 6, top-X curves with haplotypes | partly | 25 of 26 (SNPs), 14 of 27 (true and predicted haplotypes), 8 of 18 (r² = 0 and 0.9) |
| Main claim: RF0:IM1 steadiest under LD | partly | Holds for H4M4 and 5 of the 6 other models; not for H1M1 |
| Other claims of the text | 10 exact, 2 partly, 1 differs | "RF0:IM1 steadier than RF1:IM1" also fails for H1M1; Fig. 2's "RF1:IM0 most stable" follows the swapped labels; "RF0 beats RF1" in Fig. 3 is within Monte Carlo error |
| Claims against the paper's own figures | agrees | 12 of 14 follow from the published values; the Discussion's "predicted haplotypes in between" does not fit Fig. 5, and Fig. 6b at r² = 0 contradicts Fig. 5 |
| Port and phasing | agrees | rfld differs from the Fortran original no more than from itself (1.01×); EM matches haplo.stats to 1e-5 |
| Tables 2-4 (AD data) | not attempted | The TGen genotypes were only released by request; the "7 of 17" count follows from Table 4 |

The main claim holds: with SNPs in LD, the original importance of a risk SNP falls, the revised importance on the
revised forest inflates, and the revised importance on the original forest is the steadiest, in the paper's H4M4
figures and in five of the six other genetic models (not in H1M1, open). Fig. 2's swapped series and Fig. 4's
repeated bars are slips in the paper; why the paper's true haplotypes do worse at low r² than the model gives
is open, with three candidate causes ruled out.

Kept local and gitignored: `sources/` (the paper, its figures, Breiman and Cutler's `prog.f`, Lunetta et al.
2004), `work/` (the per-replicate forests, Slurm logs, the R library, scratch runs), `scratch/` and `.venv/`.
