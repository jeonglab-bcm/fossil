# PMC4081021 — ODE constrained mixture modelling (Hasenauer et al. 2014)

Hasenauer J, Hasenauer C, Hucho T, Theis FJ. ODE constrained mixture modelling: a method for
unraveling subpopulation structures and dynamics. *PLoS Comput Biol* 10(7):e1003686 (2014).
[doi:10.1371/journal.pcbi.1003686](https://doi.org/10.1371/journal.pcbi.1003686) ·
[PMC4081021](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4081021/)

The paper is © 2014 Hasenauer et al., published under CC BY 4.0. In keeping with the rest of
this repository, this folder does not contain the paper, Supporting Information S1 or Code S1
(the authors' MATLAB code, data and saved results). `figure-reproduction/published/` holds
Figs 1 to 6 of the paper and the paper's Tables 1, 2 and Supporting Information S1 Table 1
as CSV, for comparison, under CC BY 4.0 with the attribution above.

| Folder | Content |
| --- | --- |
| [`figure-reproduction/`](figure-reproduction/) | The ODE-MM likelihood and the four pathway models ported to Python and checked against the authors' 51 saved fits. Figs 2B–G, 3B–D, 4B–D, 5B and 6 rebuilt the way the authors' plotting scripts draw them and compared with the published figures pixel by pixel; Tables 1, 2 and S1 Table 1 recomputed; the 24 conversion-reaction models of Table 1 refitted from scratch. Nextflow pipeline. |

Kept local and gitignored: `sources/` (the paper, Supporting Information S1, Code S1, the
original-size figure TIFFs), `odemm-paper/` (an agent-readable copy of the paper and S1 built
with the paper2agent skill), `paper-review/` (its review, adjudication and verification
records) and `staging/` (its draft builds). Code S1 is MATLAB, which the paper2agent skill's
MCP route (Python, R and command-line code) does not cover, so no MCP server was built for it.
