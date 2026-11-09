# PMC4331676: Identifying DNA-binding proteins by combining support vector machine and PSSM distance transformation (Xu et al. 2015)

Xu R, Zhou J, Wang H, He Y, Wang X, Liu B. Identifying DNA-binding proteins by combining support
vector machine and PSSM distance transformation. *BMC Systems Biology* 9(Suppl 1):S10 (2015).
[doi:10.1186/1752-0509-9-S1-S10](https://doi.org/10.1186/1752-0509-9-S1-S10) ·
[PMC4331676](https://pmc.ncbi.nlm.nih.gov/articles/PMC4331676/)

The paper is © 2015 Xu et al.; licensee BioMed Central, published under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). In keeping with the rest of this
repository, this folder does not contain the paper, its supplement or their full text.
`figure-reproduction/published/fig*.png` are the paper's Figures 1 to 6 as PMC serves them
(600 px wide), kept for comparison under CC BY 4.0 with the attribution above.

The independent test set PDB186 and the outputs of six earlier predictors on it come from Lou W,
Wang X, Chen F, Chen Y, Jiang B, Zhang H. Sequence based prediction of DNA-binding proteins based on
hybrid feature selection using random forest and Gaussian naïve Bayes. *PLoS One* 9(1):e86703
(2014), [doi:10.1371/journal.pone.0086703](https://doi.org/10.1371/journal.pone.0086703) (CC BY 4.0,
Dataset S2 and Information S1). The pipeline downloads them and checks their SHA-256.

No code was released and the web server (bioinformatics.hitsz.edu.cn/PSSM-DT) answers 503. The
method is rebuilt from the paper as the Python package [`pssmdt`](package/). Its feature definition
matches the PSSM-DT mode of BioSeq-Analysis2.0, a later toolkit from the senior author's lab, which
we read from its compiled code and do not redistribute.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The pipeline: datasets, PSI-BLAST profiles (committed, packed), jackknife and cross-validation experiments, the independent test, discriminant weights, every figure redrawn on the published pixel grid and scored, and the checks. |
| [`package/`](package/) | `pssmdt`, the method as an installable Python package, with example data, tests and an executed [tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure panel, table and claim of the paper, with our numbers, the verdicts computed from them and the cause of each mismatch. |
| [`session/`](session/) | The record of the session that made this reproduction. |

Kept local and git-ignored: `sources/` (the paper, its supplement, the PDB186 files, BioSeq-Analysis2.0
and its disassembly), `work/` (the UniRef 2014_01 BLAST databases, raw PSSMs, scratch runs) and
`.env/`.

## Results

Every verdict below is computed by `figure-reproduction/pipeline/check_results.py` from the numbers
in [`results.json`](results.json); nothing is typed by hand. "Measure" counts the values that match
at the printed precision, or gives the share of the published curve within 2 px of ours. Values the
paper's own tables contradict are kept in `results.json` as paper errors and not counted.

<!-- RESULTS TABLE -->
| Item | Verdict | Measure | Why |
| --- | --- | --- | --- |
| Benchmark and PDB186 sizes | exact | 4 of 4 fields as printed |  |
| Fig. 1, ACC and MCC against LG | partly | 12 of 28 fields as printed | Our curve has the published level (ACC 0.76 to 0.79, MCC 0.53 to 0.59) and is as flat, but between 5-fold splits single ACC values move by up to 0.02 and MCC values by up to 0.04, more than most gaps to the paper. |
| Best LG is 5 (text and Fig. 1) | differs | 0 of 2 fields as printed | No split of ours puts the optimum at LG 5: the best LG is 7, 6, 8, 6 and 7 on five splits, and LG 5 is within 0.02 ACC of the best on every split. The paper's peak at LG 5 is a 0.016 rise over LG 4 that our runs do not show. |
| Table 1, PSSM-DT, PSSM-DDT and PSSM-SDT (jackknife) | differs | 0 of 7 fields as printed, 5 paper errors | PSSM-DT comes back within about 2 points: ACC 78.88 against 79.96, SN 82.10 against 81.91 (one chain more), SP 75.82 against 78.00 (12 chains fewer), AUC 86.34 against 86.50. No value matches at the printed precision. Five printed ACC and MCC values do not follow from the printed SN and SP and are left out of the count. The PSSMs of the 2014 nr cannot be rebuilt; each other unstated setting moves ACC by at most 1.3 points and none closes the gap in all four metrics. |
| Table 2, five PSSM encodings (jackknife) | differs | 0 of 21 fields as printed, 4 paper errors | Our comparator encodings, built as Lou et al. 2014 define them, score far above the paper's in-house versions: AvePscore-20 78.33 ACC and 85.68 AUC against 73.95 and 81.40, Pscore-100 77.40 and 84.53 against 73.12 and 80.50. ACC (73.49 and 81.02 against 73.77 and 81.90) and AvePscore-400 come closer. The paper's implementations are not given beyond citations, so its lead of 6 ACC points shrinks to 0.56 in our run. |
| Table 3, DNAbinder rows (jackknife) | differs | 0 of 9 fields as printed, 1 paper errors | Our comparator encodings, built as Lou et al. 2014 define them, score far above the paper's in-house versions: AvePscore-20 78.33 ACC and 85.68 AUC against 73.95 and 81.40, Pscore-100 77.40 and 84.53 against 73.12 and 80.50. ACC (73.49 and 81.02 against 73.77 and 81.90) and AvePscore-400 come closer. The paper's implementations are not given beyond citations, so its lead of 6 ACC points shrinks to 0.56 in our run. |
| Table 3, DNA-Prot and iDNA-Prot rows | not attempted | not attempted | The paper's in-house DNA-Prot and iDNA-Prot are given only as citations (random forests on composition, predicted secondary structure and physicochemical or grey-model features, settings not stated). A rebuild would test our reading of two other papers, not this one. Their printed ACC does not follow from their own SN and SP (72.55 against 70.98, 75.40 against 74.05). |
| Table 4, the six earlier predictors on PDB186 | exact | 25 of 25 fields as printed, 2 paper errors |  |
| Table 4, PSSM-DT on PDB186 | differs | 0 of 3 fields as printed, 2 paper errors | On PDB186 our model gets ACC 66.13 and AUC 74.44 against the paper's 80.00 and 87.40, below DBPPred (76.88, 79.29). No identity threshold for the homology filter brings it back: AUC stays between 74.4 and 76.0 for thresholds of 25 to 99%, and only training on the unfiltered benchmark, which shares 42 chains with PDB186, reaches 81.49 (87.46 with UniRef90 PSSMs). The paper does not report how many chains its filter removed. |
| Table 4, AUC of iDNA-Prot and DNA-Prot | not attempted | not attempted | Table 4 says its comparator rows come from Lou et al. 2014, but Lou et al. print N/A for the AUC of iDNA-Prot and DNA-Prot and publish no real-valued outputs for them; the 83.30 and 79.60 come from the authors' in-house versions, which are not available. |
| Fig. 2A, discriminant weights of the 400 pairs | differs | 0 of 4 fields as printed | Our largest pair weights are (G,G), (G,D), (G,P) and (N,P). (R,R) and (R,P) have no positive descriptor weight at all (pair weight 0, tied last), and (P,R) and (A,R) rank 133 and 176 of 400. Products of raw log-odds scores do not grow with arginine content (two negative R scores multiply to a large positive), and no variant of Eq. 12 we tried brings the four pairs to the top. Read as a linear grey scale, the published Fig. 2A itself puts (R,R), (P,R) and (R,P) on top and (A,R) eighth (published_values.json, fig2). |
| Fig. 2B, weights of the top four pairs by lg | differs | 0 of 2 fields as printed | Our (R,R) descriptor weights are negative at every lg, so (R,R) has no positive weight to peak; (A,R) peaks at lg 4, not 5. (R,R) and (R,P) have no positive descriptor weight at all (pair weight 0, tied last), and (P,R) and (A,R) rank 133 and 176 of 400. Products of raw log-odds scores do not grow with arginine content (two negative R scores multiply to a large positive), and no variant of Eq. 12 we tried brings the four pairs to the top. Read as a linear grey scale, the published Fig. 2A itself puts (R,R), (P,R) and (R,P) on top and (A,R) eighth (published_values.json, fig2). |
| Fig. 2C and text, descriptor occurrences on 1AKH chain A | partly | 1 of 3 fields as printed, 1 paper errors | The five occurrences come back; the text gives three of their lags off by one ((R,R) lg 3 for lg 2, (P,R) lg 2 and 3 for lg 3 and 4). Whether all five lie in the DNA-binding region depends on how the region is drawn, which the paper does not say: by contact with the DNA in the crystal structure, (R,R) lg 1 (R25, R26), which the text calls very close to the DNA, is 13.2 A away, so four are in and one is out; by the span of contacts, all five are in. |
| Fig. 2D, the occurrences drawn on the 1AKH structure | not attempted | not attempted | A drawing of panel C's occurrences on the 1AKH structure; the distances it illustrates are checked in Fig. 2C. |
| Fig. 3, PSSM-DT ROC curve | partly | 59.81% within 2.0 px (pass 75.0%, best control 54.6%) | Our PSSM-DT curve stays within about 2 points of true positive rate of the published one (AUC 86.34 against 86.50), lowest between 15 and 30% false positives, where our specificity is lower (scores.json, tpr_gap). At 2 px that clears the wrong-input control by only a little. Same causes as Table 1. |
| Fig. 3, ACC ROC curve | partly | 63.66% within 2.0 px (pass 75.0%, best control 28.6%) | Our ACC encoding is the one comparator that comes close: AUC 81.02 against 81.90, ACC 73.49 against 73.77, and its curve runs near the published one. The other comparators lie above theirs. The paper's implementations are known only by citation. |
| Fig. 3, AvePscore-20 ROC curve | differs | 9.91% within 2.0 px (pass 75.0%, best control 35.5%) | Our AvePscore and Pscore curves lie above the published ones, as their AUCs in Table 2 do (AvePscore-20 85.68 against 81.40, AvePscore-400 82.09 against 81.50, Pscore-100 84.53 against 80.50). The paper's implementations are known only by citation. |
| Fig. 3, AvePscore-400 ROC curve | inconclusive | 13.70% within 2.0 px (pass 75.0%, best control 27.4%) | Our AvePscore and Pscore curves lie above the published ones, as their AUCs in Table 2 do (AvePscore-20 85.68 against 81.40, AvePscore-400 82.09 against 81.50, Pscore-100 84.53 against 80.50). The paper's implementations are known only by citation. |
| Fig. 3, Pscore-100 ROC curve | inconclusive | 4.46% within 2.0 px (pass 75.0%, best control 7.6%) | Our AvePscore and Pscore curves lie above the published ones, as their AUCs in Table 2 do (AvePscore-20 85.68 against 81.40, AvePscore-400 82.09 against 81.50, Pscore-100 84.53 against 80.50). The paper's implementations are known only by citation. |
| Fig. 4, PSSM-DT ROC curve | partly | 61.62% within 2.0 px (pass 75.0%, best control 55.5%) | Our PSSM-DT curve stays within about 2 points of true positive rate of the published one (AUC 86.34 against 86.50), lowest between 15 and 30% false positives, where our specificity is lower (scores.json, tpr_gap). At 2 px that clears the wrong-input control by only a little. Same causes as Table 1. |
| Fig. 4, DNAbinder(dimension 21) ROC curve | differs | 3.31% within 2.0 px (pass 75.0%, best control 22.2%) | Our AvePscore and Pscore curves lie above the published ones, as their AUCs in Table 2 do (AvePscore-20 85.68 against 81.40, AvePscore-400 82.09 against 81.50, Pscore-100 84.53 against 80.50). The paper's implementations are known only by citation. |
| Fig. 4, DNAbinder(dimension 400) ROC curve | inconclusive | 13.78% within 2.0 px (pass 75.0%, best control 25.2%) | Our AvePscore and Pscore curves lie above the published ones, as their AUCs in Table 2 do (AvePscore-20 85.68 against 81.40, AvePscore-400 82.09 against 81.50, Pscore-100 84.53 against 80.50). The paper's implementations are known only by citation. |
| Fig. 5, PSSM-DT ROC curve | differs | 13.32% within 2.0 px (pass 75.0%, best control 20.0%) | On PDB186 our model gets ACC 66.13 and AUC 74.44 against the paper's 80.00 and 87.40, below DBPPred (76.88, 79.29). No identity threshold for the homology filter brings it back: AUC stays between 74.4 and 76.0 for thresholds of 25 to 99%, and only training on the unfiltered benchmark, which shares 42 chains with PDB186, reaches 81.49 (87.46 with UniRef90 PSSMs). The paper does not report how many chains its filter removed. |
| Fig. 5, DBPPred ROC curve | agrees | 97.44% within 2.0 px (pass 75.0%, best control 38.4%) |  |
| Fig. 5, DNABIND ROC curve | agrees | 78.09% within 2.0 px (pass 75.0%, best control 22.7%) |  |
| Fig. 5, DNAbinder ROC curve | agrees | 82.22% within 2.0 px (pass 75.0%, best control 16.3%) |  |
| Fig. 4, DNA-Prot and iDNA-Prot ROC curves | not attempted | not attempted | The DNA-Prot and iDNA-Prot curves come from the authors' in-house versions of those predictors, which were not rebuilt (Table 3). |
| Fig. 5, DNA-Prot and iDNA-Prot ROC curves | not attempted | not attempted | The DNA-Prot and iDNA-Prot curves come from the authors' in-house versions of those predictors, which were not rebuilt (Table 3). |
| Fig. 6, the web server's home page | not attempted | not attempted | A screenshot of the web server, which no longer answers. |
| PSSM-DT beats the four other encodings and its two halves (text, Tables 1 to 3) | partly | 4 of 6 fields as printed | Our comparator encodings, built as Lou et al. 2014 define them, score far above the paper's in-house versions: AvePscore-20 78.33 ACC and 85.68 AUC against 73.95 and 81.40, Pscore-100 77.40 and 84.53 against 73.12 and 80.50. ACC (73.49 and 81.02 against 73.77 and 81.90) and AvePscore-400 come closer. The paper's implementations are not given beyond citations, so its lead of 6 ACC points shrinks to 0.56 in our run. |
| PSSM-DT is best on PDB186 (text, Table 4) | differs | 0 of 4 fields as printed, 2 paper errors | On PDB186 our model gets ACC 66.13 and AUC 74.44 against the paper's 80.00 and 87.40, below DBPPred (76.88, 79.29). No identity threshold for the homology filter brings it back: AUC stays between 74.4 and 76.0 for thresholds of 25 to 99%, and only training on the unfiltered benchmark, which shares 42 chains with PDB186, reaches 81.49 (87.46 with UniRef90 PSSMs). The paper does not report how many chains its filter removed. |
| Claims recomputed from the paper's own tables | agrees | 20 of 38 claims recomputed from the paper's own tables come back; the other 18 do not follow from the printed numbers (run/arithmetic.json) |  |
| PSSM-DT as in the authors' later toolkit (BioSeq-Analysis2.0) | agrees | pssmdt.pssm_dt equals the transliterated BioSeq-Analysis2.0 loops on 127 PSSMs (largest relative difference 0.0e+00) |  |
| Python package pssmdt and its tutorial | agrees | pssmdt 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 7 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |  |

2 exact, 6 agrees, 6 partly, 3 inconclusive, 11 differs, 6 not attempted; 18 open causes.

## Claims

| Claim | Paper | Ours | Kind |
| --- | --- | --- | --- |
<!-- CLAIMS TABLE -->
| LG with the highest ACC | 5 | 7 | ours |
| LG with the highest MCC | 5 | 7 | ours |
| PSSM-DT ACC above all four other encodings | yes | yes | ours |
| PSSM-DT MCC above all four other encodings | yes | yes | ours |
| PSSM-DT AUC above all four other encodings | yes | yes | ours |
| ACC gain over the best other encoding (points) | 6.01 | 0.56 | ours |
| AUC gain over the best other encoding (points) | 4.60 | 0.66 | ours |
| PSSM-DT ACC above PSSM-DDT and PSSM-SDT | yes | yes | ours |
| PSSM-DT ACC above the six other predictors | yes | no | ours |
| PSSM-DT MCC above the six other predictors | yes | no | ours |
| PSSM-DT AUC above DBPPred, DNAbinder and DNABIND | yes | no | ours |
| ACC gain over DBPPred (points) | 3.105 (paper error: does not follow from its own Table 4) | -10.753 | ours |
| MCC gain over DBPPred | 0.136 (paper error: does not follow from its own Table 4) | -0.215 | ours |
| AUC gain over DBPPred (points) | 8.30 | -4.86 | ours |
| Claims recomputed from the paper's own tables | | 20 of 38 claims recomputed from the paper's own tables come back; the other 18 do not follow from the printed numbers (run/arithmetic.json) | arithmetic check |

The arithmetic check recomputes each claim from the paper's own tables; "ours" is our run. No
number from a sensitivity variant (`figure-reproduction/output/sensitivity.json`) is shown as ours.

<!-- CLAIMS LINE -->
PSSM-DT still beats the four earlier encodings in our run, but by half a point, not six. The PDB186 result does not come back. Causes: the comparators the authors built in house, and a homology filter that cannot run as written.

## Install the method

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC4331676/package"
```

See [`package/README.md`](package/README.md) and the [tutorial](package/tutorial/TUTORIAL.md).
