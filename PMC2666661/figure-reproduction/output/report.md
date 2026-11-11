# PMC2666661 reproduction check

## results.json

| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Table 1, K, GRRs and lambda_s of the seven genetic models | exact | 33 of 33 fields as printed, 2 paper errors |  |
| Table 5, the 13 LD models | not attempted | not attempted | A design table: it defines the LD models the simulation uses (rfld.LD_MODELS). |
| Fig. 1, mean IM of the risk SNPs (40 bars) | agrees | 40 of 40 fields as printed | Assumed: Published bar heights, error bars and curve points read off the PMC figure JPEGs (600 px wide) through each axis's tick marks |
| Fig. 2, share of replicates with all risk SNPs above the noise (40 bars) | agrees | 36 of 36 fields as printed, 4 paper errors | Fig. 2 has the bars of RF1:IM0 and RF0:IM1 in the r series swapped: exchanged, they come back 10 of 10; as labelled, 6 of 10. |
| Fig. 3a, top X curves by LD.rSNPs, RF0:IM0 and RF0:IM1 | partly | 49 of 50 fields as printed | One of 50 points misses: the paper's curve at X = 12 (0.44) is read where ours jumps from 0.23 at X = 12 to 0.81 at X = 13; half a step of X, about one pixel, covers it. |
| Fig. 3b, rSNPs with and without their LD.rSNPs, 1 and 4 per rSNP | agrees | 27 of 27 fields as printed | Assumed: Published bar heights, error bars and curve points read off the PMC figure JPEGs (600 px wide) through each axis's tick marks |
| Fig. 3c, the four RF/IM combinations, 1 and 4 LD.rSNPs | partly | 44 of 45 fields as printed | One of 45 points misses: RF0:IM1 with 1 LD.rSNP at X = 5 reads 0.13 where our curve goes 0.00, 0.06, 0.80 at X = 5, 6, 7; at X = 5.5 it is 0.03, within tolerance. |
| Fig. 4, mean IM of risk SNPs, true and predicted risk haplotypes (33 bars) | partly | 30 of 31 fields as printed, 2 paper errors | 30 of 33 bars agree. The paper's PRED.rHAP bars are all the same height (0.654, error bars too): two of them miss ours at r2 = 0 and 0.1, a plotting slip. The rHAP bar at r2 = 0 (0.565 against our 0.736) is the low-r2 gap of Fig. 5. |
| Fig. 5, share of replicates with all risk variables above the noise (33 bars) | partly | 28 of 33 fields as printed | At r2 0-0.4 the paper's true haplotypes beat every noise SNP in 40-45% of replicates, ours in 72-76%; from r2 = 0.5 on they agree. Our risk haplotypes carry the same risk at every r2, as the model says, so ours stay flat. |
| Fig. 6a, top X curves of the risk SNPs (both, and the best of each pair) | partly | 25 of 26 fields as printed | One of 26 points misses: at X = 5 the best-SNP curve for r2 = 1 reads 0.12, but with r2 = 1 the two SNPs are copies and ours is 0; our r2 = 0.9 curve (dark red, next to red in the 87 dpi figure) is 0.21 there. |
| Fig. 6b, top X curves of true and predicted haplotypes | partly | 14 of 27 fields as printed | The paper's true and predicted haplotype curves are low at small r2; ours are high at every r2. At r2 = 0 the published curve also contradicts the paper's own Fig. 5: 40% of replicates have all four risk haplotypes above every noise SNP, so at least 40% have them in the top 5, but the curve reads 12%. |
| Fig. 6c, the four codings at r2 = 0 and 0.9 | partly | 8 of 18 fields as printed | At r2 = 0 the paper's HAP and PRED.HAP curves are low and ours high (the low-r2 gap of Figs 5 and 6b); the SNP and best-SNP curves agree except one best-SNP point. At r2 = 0.9 all four codings agree. |
| Table 2, r2 of three imputed SNPs with rs4420638 (TGen data) | not attempted | not attempted | The TGen Alzheimer GWAS genotypes (Reiman et al. 2007) were only ever released through a request form; no public copy or accession exists. |
| Table 3, IM and rank of rs4420638 (TGen data) | not attempted | not attempted | The TGen Alzheimer GWAS genotypes (Reiman et al. 2007) were only ever released through a request form; no public copy or accession exists. |
| Table 4, top 11 SNPs and single-SNP p-values (TGen data) | not attempted | not attempted | The TGen Alzheimer GWAS genotypes (Reiman et al. 2007) were only ever released through a request form; no public copy or accession exists. |
| Text: the original IM of the risk SNPs falls as LD.rSNPs are added, under all models | exact | 7 of 7 fields as printed |  |
| Text: RF0:IM0 and RF1:IM0 differ very little for a fixed number of LD.rSNPs (Fig. 1) | exact | 1 of 1 fields as printed |  |
| Text: RF0:IM1 is steadier than RF1:IM1 as LD.rSNPs are added, under all models | partly | 6 of 7 fields as printed | Holds for H4M4 and five of the six other models, not for H1M1 (one risk SNP, K1S1): there RF0:IM1 falls from 44.1 to 35.4 with one LD.rSNP and comes back to 41.3, while RF1:IM1 rises steadily from 44.1 to 48.4. The paper shows no numbers for H1M1 (data not shown). |
| Text: RF1:IM1 is inflated as LD.rSNPs are added | exact | 7 of 7 fields as printed |  |
| Main claim: the revised IM with the original RF (RF0:IM1) is the most stable under LD | partly | 6 of 7 fields as printed | Holds for H4M4 and five of the six other models, not for H1M1 (one risk SNP, K1S1): there RF0:IM1 falls from 44.1 to 35.4 with one LD.rSNP and comes back to 41.3, while RF1:IM1 rises steadily from 44.1 to 48.4. The paper shows no numbers for H1M1 (data not shown). |
| Discussion: SNPs in LD with noise SNPs have little effect (data not shown) | exact | 1 of 1 fields as printed |  |
| Text: in Fig. 2, the revised RF with the original IM (RF1:IM0) is the most stable | differs | 0 of 1 fields as printed | The text names RF1:IM0 because of the swapped Fig. 2 series: in our run the steadiest r series is RF0:IM1 (range 0.09), the one the figure labels RF1:IM0. |
| Discussion: in Fig. 2, RF1:IM1 performs best and improves with more LD.rSNPs | exact | 1 of 1 fields as printed |  |
| Text: with LD.rSNPs the top-X share is lower for small X (8) and higher for X >= 20 (30) | exact | 1 of 1 fields as printed |  |
| Text: for a fixed number of LD.rSNPs, RF0 beats RF1 in Fig. 3 | partly | 1 of 2 fields as printed | RF0 and RF1 differ by less than 2 standard errors: the mean share over X = 4-40 is 0.005 lower for RF0 with 1 LD.rSNP (SE 0.004) and 0.007 higher with 4 (SE 0.004); 100 replicates cannot tell them apart, and in the published panels the curves overlap. |
| Text: mean IM rHAP > PRED.rHAP > rSNP in general, the gap closing as r2 rises (Fig. 4) | exact | 1 of 1 fields as printed |  |
| Text: the IM of the risk SNPs rises with LD between them (Fig. 4) | exact | 1 of 1 fields as printed |  |
| Text: the share above the noise rises with LD between the risk SNPs (Fig. 5) | exact | 1 of 1 fields as printed |  |
| Discussion: predicted haplotypes perform between risk SNPs and true haplotypes (Fig. 5) | exact | 1 of 1 fields as printed |  |
| Text: 7 of the 17 top SNPs would be missed by single-SNP tests (TGen data) | not attempted | not attempted | Needs the TGen genotypes (Tables 2-4). The count itself follows from Table 4 (text.arithmetic): 7 of 17. |
| Claims recomputed from the paper's own figures and tables | agrees | 12 of 14 claims about Figs 1-5 follow from the paper's own figure values (not: text.pred_between, text.fig5_fig6b_consistent); the AD application's claims follow from Tables 3 and 4 (7 of 17 top SNPs have p > 0.05 in both tests) |  |
| Port against Breiman and Cutler's Fortran Random Forests 5.1 | agrees | Fortran Random Forests 5.1 against rfld on 20 data sets: IM differs from Fortran 1.01x as much as from itself with another seed (RF0), 1.01x (RF1); risk-SNP IM difference z = 0.08 (RF0), 0.07 (RF1) |  |
| Haplotype EM against haplo.stats (R) | agrees | haplo.stats 1.9.9.1 haplo.em against rfld.haplotype_em on 66 simulated data sets: frequencies within 9.8e-06, phase posteriors within 9.2e-05 |  |
| Python package rfld and its tutorial | agrees | rfld 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |

11 exact, 7 agrees, 10 partly, 1 differs, 5 not attempted; 6 open causes.
OK results.json: {"items": 34, "exact": 11, "agrees": 7, "partly": 10, "inconclusive": 0, "differs": 1, "not_attempted": 5, "open_causes": 6}

## Replicates rerun from scratch

| Study | Replicate | Same as committed |
| --- | --- | --- |
| SNP H4M4 | n0, #0 | yes |
| SNP H4M4 | r4, #0 | yes |
| haplotypes | r2 = 0.5, #0 | yes |
| SNP H8M4 | r2, #0 | yes |

## Package

rfld 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync

## Fresh run against the committed outputs

| File | Fresh vs committed | Detail |
| --- | --- | --- |
| comparison.json | same |  |
| published_values.json | same |  |
| summary.json | same |  |
| table1.json | same |  |
| figures/fig1_ours.png | same |  |
| figures/fig1_overlay.png | same |  |
| figures/fig2_ours.png | same |  |
| figures/fig2_overlay.png | same |  |
| figures/fig3_ours.png | same |  |
| figures/fig3_overlay.png | same |  |
| figures/fig4_ours.png | same |  |
| figures/fig4_overlay.png | same |  |
| figures/fig5_ours.png | same |  |
| figures/fig5_overlay.png | same |  |
| figures/fig6_ours.png | same |  |
| figures/fig6_overlay.png | same |  |

16 of 16 files agree.

**PASS**
