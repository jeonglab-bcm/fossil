# Paper navigation

Use exact headings to locate current line numbers. Read relevant passages, not both complete documents. This index locates evidence; it does not summarize findings.

## Main paper — [paper.md](paper.md)

| Exact heading | Look here for |
| --- | --- |
| Abstract | Summary of method, simulation study and NGF/Erk1/2 application |
| Introduction | Population snapshot data, existing mixture and population models, motivation |
| Mixture models | Mixture likelihood, Eq. 1-2, normal and log-normal components |
| Pathway models | Reaction rate equations used as ODE constraints |
| General class of ODE constrained mixture models | Definition of ODE-MMs: subpopulation parameters, mean/median constraints |
| Parameter estimation and model selection | Multi-start optimisation, profile likelihoods, BIC |
| Acquisition of snapshot data for NFG-induced Erk1/2 phosphorylation | Experimental protocol for the DRG neuron data (heading typo NFG as printed) |
| Simulation example: Conversion process | Conversion reaction scenarios 1-2, Figure 2, Table 1 (hypotheses H1-H4) |
| Application example: NGF-induced Erk1/2 signalling | Pathway model A, hypotheses H1-H3, Figures 3-6, Table 2 |
| Comparison of pathway models | Pathway models A-C, BIC comparison and subpopulation sizes (Figure 5) |
| Validation of subpopulation structure | pErk/total Erk co-labelling and correlation analysis (Figure 6) |
| Discussion | Limitations, extensions and relation to other methods |
| Supporting Information | Code S1 and Supporting Information S1 descriptions |
| References | Numbered reference list 1-85 |

For long sections, search a narrower subsection or prompt. Headings inside fenced quotations are source content, not document section boundaries.

## Supplementary information — [supplement.md](supplement.md)

| Exact heading | Look here for |
| --- | --- |
| 1 Material and Methods | Chemicals, antibodies, animals, cell culture, QuAM imaging, data preprocessing and scaling |
| 2 Parameter estimation, uncertainty analysis and model selection | Optimiser settings and model selection details |
| 3.1 Pathway model A | Reactions, RRE, parametrisation, bounds and multi-starts for model A |
| 3.2 Pathway model B | Ras/Raf/Mek cascade model, parametrisation and estimation settings |
| 3.3 Pathway model C | Cascade with pErk feedback, parametrisation, oscillation filter |
| 4 Implementation | Software (MATLAB, CVODES) and code availability |
| References | Supplement references, followed by Supplement Table 1 (BIC of all models), Figures 1-2 (profile likelihoods) and Tables 2-4 (estimates), printed after the references |

For long sections, search a narrower subsection or prompt. Headings inside fenced quotations are source content, not document section boundaries.

## Assets

Figure and table captions in the documents link to the files below. Open only the needed image; for a table, read its header and relevant rows first.

- `assets/figure/`: main figures (JPEG).
- `assets/supp_figs/`: supplementary and extended-data figures (JPEG).
- `assets/table/`: main tables (CSV, or JPEG when transcription is unreliable).
- `assets/supp_table/`: supplementary tables (CSV, or JPEG fallback).

Asset paths are relative to the skill root. CSVs retain internal blank rows; captions and merged headers may also occupy rows. Consult the document notes before treating every row as data.
