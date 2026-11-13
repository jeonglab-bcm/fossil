# PMC407845: Defining transcriptional networks through integrative modeling of mRNA expression and transcription factor binding data (Gao et al. 2004)

Gao F, Foat BC, Bussemaker HJ. Defining transcriptional networks through integrative modeling of mRNA
expression and transcription factor binding data. *BMC Bioinformatics* 5:31 (2004).
[doi:10.1186/1471-2105-5-31](https://doi.org/10.1186/1471-2105-5-31),
[PMC407845](https://pmc.ncbi.nlm.nih.gov/articles/PMC407845/), issue
[jeonglab-bcm/fossil#48](https://github.com/jeonglab-bcm/fossil/issues/48).

The paper is © 2004 Gao et al; licensee BioMed Central Ltd: "This is an Open Access article: verbatim
copying and redistribution of this article are permitted in all media for any purpose, provided this
notice is preserved along with the article's original URL"
(<https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-5-31>). This folder does not
contain the paper or its full text; `figure-reproduction/published/` holds its three figures for
comparison, unchanged, with that notice.

MA-Networker infers each transcription factor's (TF's) activity in each microarray experiment by
regressing the experiment's expression log ratios on the TFs' ChIP binding log ratios, and calls a
bound gene a functional target when its expression correlates with the TF's activity across
experiments. The authors released neither MA-Networker nor their online regression tool, and their
site is gone. We rebuilt the method from the paper as the Python package [`package/`](package/)
(`manetworker`) and ran it on the paper's ChIP data (Lee et al. 2002, 113 TFs) and an expression
library rebuilt from the SGD expression archive: 677 arrays from 15 of the paper's 19 sources, against
the paper's 751.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The Nextflow pipeline: inputs, MA-Networker on the paper's data, Tables 1 and 3, Figs 1 to 3, the text's claims, and the check against the committed outputs. |
| [`package/`](package/) | `manetworker`, the method as an installable Python package, with example data, tests and an [executed tutorial](package/tutorial/TUTORIAL.md). |
| [`results.json`](results.json) | Every figure, table and claim of the paper, with our values and computed verdicts. |
| [`session/`](session/) | The ledger of the session that made this reproduction. |

Results page: <https://jeonglab-bcm.github.io/fossil/PMC407845/>

## Results

<!-- summary and table from results.json (check_results.py --markdown); do not edit by hand -->
<!--RESULTS-SUMMARY-->
1 exact, 4 agrees, 7 partly, 1 inconclusive, 5 differs, 3 not attempted; 11 open causes.

| Item | Verdict | Measure |
| --- | --- | --- |
| Fig. 1a | not attempted | not attempted |
| Text: 751 arrays and 113 TFs | partly | 1 of 2 fields as printed |
| Fig. 1b, activity profiles of Hap4, Ndd1 and Ste12 | agrees | 3 of 3 fields as printed |
| Fig. 1c, Hap4 binding against coupling | partly | 52.54% within 2 px (pass 90.0%, best control 49.3%) |
| Fig. 1c, Ndd1 binding against coupling | inconclusive | 58.95% within 2 px (pass 90.0%, best control 64.1%) |
| Fig. 1c, Ste12 binding against coupling | differs | 27.53% within 2 px (pass 90.0%, best control 34.3%) |
| Text: 37 of 113 TFs kept by backward selection | differs | 0 of 2 fields as printed |
| Table 1 | partly | 12 of 148 fields as printed |
| Text: on average 58% of bound genes couple | differs | 0 of 1 fields as printed |
| Claims recomputed from the paper's own tables | agrees | 6 of 6 claims come back from the paper's own tables and Fig. 2 values (58% is 58.4% per TF, 58.3% pooled; B+/C- insignificant for 5 of 7 in Table 2; 26 of 37 B+/C- bars are 0). Table 4 rows sum to [6027, 6067] genes (Dig1 6027), not to Table 1's 6382. |
| Fig. 2, GO categories per TF | partly | 29 of 73 fields as printed |
| Text: no GO enrichment in most B+/C- groups | agrees | 2 of 2 fields as printed |
| Table 2, deletion response | not attempted | not attempted |
| Text: B+/C+ genes respond to TF deletion, B+/C- mostly not | partly | 1 of 2 fields as printed |
| Table 3, cell cycle motifs | partly | 1 of 20 fields as printed |
| Text: motif enrichment in B+/C- always far below B+/C+ | differs | 0 of 1 fields as printed |
| Text: 85% overlap with B+/C+ groups from Simon et al. | differs | 0 of 1 fields as printed |
| Text: 1592 of 4532 probes shared by divergent genes | exact | 2 of 2 fields as printed |
| Fig. 3, coupling scores at divergent promoters | partly | 2 of 6 fields as printed, 2 paper errors |
| Table 4, deletion in place of coupling | not attempted | not attempted |
| Python package manetworker and its tutorial | agrees | manetworker 0.1.0: wheel installed in a fresh environment and imported from it; tests 6 passed; tutorial 5 cells compared, 0 skipped (nondeterministic); TUTORIAL.md in sync |
<!--/RESULTS-SUMMARY-->

The main claim nearly comes back: on average 59% of the genes a TF binds couple to its activity in
our run, against the paper's 58%, and the validations point the same way as the paper's (most
non-coupling groups have no enriched GO category; coupling genes respond to TF deletion in 6 of 7
TFs and non-coupling genes in none; cell cycle motifs are enriched in coupling genes far more than in
non-coupling ones in 9 of 10 cases). The individual counts differ: the expression library was
rebuilt (677 of 751 arrays, reprocessed in 2010), the GO release, motif counting and several
thresholds are not stated, and Hughes et al.'s per-gene P-values, behind Tables 2 and 4, are not public.

Slips in the paper, reported and not fixed: Table 2's numbers are not the log ratios
its text names (genome-wide means of 0.52 to 0.83 cannot be mean log ratios) and look like Hughes et
al.'s P-values; Table 4's rows sum to 6027 and 6067 genes, Table 1's to 6382; Fig. 3 shows Hap6,
which is not among the ChIP data's 113 TFs. Fig. 2's Hap4 bar is 62 in the vector original, drawn
clipped at 60.

## Kept local

Git-ignored: `sources/` (the paper, its figure files and every downloaded input), `.venv/`. The
pipeline downloads its inputs itself (`figure-reproduction/pipeline/fetch_inputs.sh`).

The authors' released result files (`sig_t_result`, `sig_p_result`, `coupling_result`) on
bussemakerlab.org would allow a gene-level check of Steps 1 and 2. They could not be fetched from the
environment of this session: the site refuses scripted requests (HTTP 406) and web.archive.org,
which holds copies from 2004 to 2008, was blocked by the session's network policy. This
reproduction compares with the paper only.

Made with Paper2Repro v0.5.0 (installed from Paper2Repro commit 7847463; the copy had no git
metadata, so `results.json` records `commit: null`).
