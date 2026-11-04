# PMC2349296 — Comparative analysis of five protein-protein interaction corpora (Pyysalo et al. 2008)

Pyysalo S, Airola A, Heimonen J, Björne J, Ginter F, Salakoski T. Comparative analysis of five
protein-protein interaction corpora. *BMC Bioinformatics* 9(Suppl 3):S6 (2008).
[doi:10.1186/1471-2105-9-S3-S6](https://doi.org/10.1186/1471-2105-9-S3-S6) ·
[PMC2349296](https://pmc.ncbi.nlm.nih.gov/articles/PMC2349296/)

The paper is © 2008 Pyysalo et al., licensee BioMed Central Ltd., published under
[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). In keeping with the rest of this
repository, this folder does not contain the paper or its full text.
`figure-reproduction/published/` holds Figs 1 and 2 of the paper for comparison, under CC BY 2.0
with the attribution above.

The corpora, MedPost and Stanford Parser 1.5.1 are downloaded by the pipeline and checked
against SHA-256 sums; they are not redistributed here. The unified corpora survive only in a
third-party copy that states no license (`github.com/metalrt/ppi-dataset`), and the original
corpora have their own terms.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | Tables 2 to 4, Figs 1 and 2 and the summary claims, rerun on the surviving unified corpora with the paper's own tagger (MedPost) and parser (Stanford Parser 1.5.1) and a reimplementation of RelEx. Figures drawn with base R on the published pixel grid. Nextflow pipeline. |

## Results

| Item | Status | Evidence |
| --- | --- | --- |
| Table 2, co-occurrence | Identical data on HPRD50, IEPA, LLL; same setup on AIMed; different corpus version for BioInfer | 9 of 9 values on HPRD50, IEPA, LLL. AIMed P and F equal; R 1.00 against 0.95, because the surviving AIMed lacks its self-interactions. BioInfer P 0.26 against 0.13. |
| Table 2, RelEx | Same setup, reimplemented method | RelEx was never released; ours follows both papers' descriptions. AIMed 0.40 / 0.50 / 0.44, the published values. F within 3 points on HPRD50, 7 on IEPA, 1 on LLL; none of the 9 RelEx cells on HPRD50, IEPA and LLL matches at the printed precision. The parser's relation-order noise moves each value by 0.01 at most. |
| Table 3 | Identical data on AIMed, HPRD50, IEPA, LLL except AIMed's no-interaction share | MedPost token counts equal the paper on all five corpora. BioInfer differs (later conversion). |
| Table 4 | Identical data for co-occurrence on HPRD50, IEPA, LLL; RelEx same setup | See `figure-reproduction/output/report.md`. |
| Figs 1, 2 | Same setup | Base R on the published pixel grid. With the paper's values the drawing is within 0.2 to 0.4 px (chamfer); with ours, the points move by the data differences above. |
| Claims in the text, our run | 3 of 8 hold, 1 close, 4 differ | Holds: the main claim (RelEx varies 19.5 points between corpora, more than the 8.2-point gap between the methods), co-occurrence beating RelEx on every filtered corpus except LLL, and the non-significant Kendall test. Close: the largest error cut (35.0% against 32%). Differ: the method gap (8.2 against 13 points), the filtered difference (15.7 against 11), the smallest error cut (−2.3% against 21%) and the Kendall p (0.233 against about 0.08). |
| Causes of the differences | BioInfer and our RelEx rebuild | BioInfer's surviving copy is a later conversion and sets the −2.3%. Our RelEx is 7 F points low on IEPA, a corpus that matches the paper's, so with the paper's BioInfer row (a sensitivity check that moves toward the paper by construction) the smallest cut is still 4.1% and the method gap 11.5 points. See `figure-reproduction/README.md`. |
| Table 1 | Not reproduced | Descriptive; the size row equals the surviving corpora except AIMed (1,943 of 1,955 sentences). |
| Fig. 3, Table 5 | Not reproduced | Need the authors' 250 sampled interactions and their manual labels, which were never released. |
| Fig. 4 | Not applicable | An illustration of the RelEx rules. |

Kept local and gitignored: `sources/` (the paper's full text, figures and the downloads),
`work/` (scratch runs and Slurm logs) and `.env/` (the conda environment with R and Python).
