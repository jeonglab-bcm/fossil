# Reproduction plans for ten papers whose software is lost

These ten papers were picked as follows:
- well cited (iCite RCR at least 1.9);
- software not found anywhere (see `../software_new_homes.csv`);
- input data still obtainable and small, rated high readiness in `../lost_software_data.csv`.

For each paper we read the full text and listed every figure and table. For each item we checked whether its inputs
exist today and whether the method and its parameters are written down, then rated it:
- **exact:** deterministic, with all inputs and parameters given;
- **approximate:** stochastic steps, unspecified seeds, newer database or tool versions, or parameters only partly given;
- **no:** an input or a step is missing;
- **not-a-result:** a schematic, diagram, pseudocode or worked example.

Each `PMC*.md` file has the inventory, a check of which method details are given, an ordered plan, the reported
numbers to compare against, and the risks. `items.csv` has one row per figure or table. Supplementary items for
PMC2711306 are included there, flagged `supplementary=True`. These are plans: nothing was reimplemented or run.

No item is regenerable exactly. Every paper depends on at least one of these:
- a database that has changed since (NCBI nr, PDB, GO);
- an unpublished random split or seed;
- a parameter the paper does not state.

Of the 66 main-text result items, 60 are regenerable approximately and 6 are not.

## Ranking

Ordered by how much can be regenerated, how close it should come, and how much work it takes.

| | Paper | RCR | Result items regenerable | Effort | Why this position |
| --- | --- | --- | --- | --- | --- |
| 1 | [PMC2735674](PMC2735674.md) Bipartite local models for drug–target prediction (2009) | 10.4 | 7 of 7 | ~4 days | Benchmark files online match the paper exactly (16 files, every count); LIBSVM 2.88 still downloadable. One unstated rule (scoring a held-out edge that is a local model's only positive) needs calibrating on one dataset, then testing unchanged on the other three |
| 2 | [PMC4015815](PMC4015815.md) Top-n-gram and residue-pair distances for remote homology (2014) | 2.6 | 4 of 4 | 2–3 days for SVM-DR | SCOP 1.53 benchmark intact (4,352 sequences, 54 families) and the Gist SVM source online, so the SVM-DR results should come out nearly exact. SVM-DT is approximate: its original nrdb90 is gone, but the lab's Pse-in-One 2.0 ships a 2016 nrdb90 and the PSI-BLAST settings |
| 3 | [PMC2711306](PMC2711306.md) Geometric de-noising of PPI networks (2009) | 2.5 | 5 of 5 | 3–4 days | BioGRID 2.0.35 rebuilt to 23,606 edges (paper: 23,543). Figures 2–4 need the Collins 2007 list, downloaded by hand from the journal. Three parameters are missing: the edge prior, coordinate scaling and path-length cap |
| 4 | [PMC2850872](PMC2850872.md) SVM for diabetes on NHANES (2010) | 6.2 | 4 of 4 | ~3 days | All 33 NHANES files still served (96 MB). Random splits unpublished, a few variable choices unstated, and glucose files re-released in 2016. Expect agreement in distribution, not to four decimals |
| 5 | [PMC1800866](PMC1800866.md) Zinc binding at the proteome level (2007) | 1.9 | 11 of 12 | ~2 days for Tables 1–3, Figs 1–2; +1 week for profile-based figures | Supplement gives every evaluation residue, the folds and the tuned SVM and Platt parameters. The human proteome (RefSeq 35.1) is archived. Figure 7 needs a paywalled supplement |
| 6 | [PMC4426843](PMC4426843.md) Bias in miRNA functional enrichment (2015) | 3.0 | 4 of 4 | 4–5 days, mostly compute | miRBase 20 and Ensembl 75 GO dumps archived; Supplementary Tables S1 and S3 give exact intermediate checks. miRanda 3.3a only as bioconda binaries. The rice table depends on plant tools that could not be reached |
| 7 | [PMC2349296](PMC2349296.md) Five protein–protein interaction corpora (2008) | 2.6 | 6 of 8 | ~1 day for co-occurrence; 1–2 weeks for RelEx | Only a third-party copy of the corpora survives: three match the paper, AIMed is close, BioInfer is a later conversion. The manual-annotation results (Figure 3, Table 5) were never released |
| 8 | [PMC4331676](PMC4331676.md) DNA-binding proteins with PSSM distance transformation (2015) | 2.4 | 9 of 9 | 4–5 days after profiles | PSI-BLAST profiles must be rebuilt against today's NCBI nr (about 400 GB), and feature scaling is unstated. The paper's own accuracy and MCC do not follow from its sensitivity and specificity: a finding in itself |
| 9 | [PMC4765871](PMC4765871.md) Gene-regulatory dynamics from single-cell snapshots (2015) | 2.4 | 8 of 8 | ~2 weeks | The Moignard 2013 data rebuild exactly (597 cells), and the model equations and kinetic parameters are given. Missing: simulation noise and time step, the MCMC and thermodynamic-integration schedule, GENIE3 settings, and start and end cells picked by eye |
| 10 | [PMC3322362](PMC3322362.md) RPISeq: RNA–protein interactions from sequence (2011) | 10.1 | 2 of 5 | ~1 week | Negative pairs were never published. Another group using the same positives and its own negatives got accuracy 0.65 against the paper's 0.90. 181 of 563 PDB entries are now obsolete (still served). The NPInter evaluation set was never released |

## What this suggests

- **Best first targets:** PMC2735674 and PMC4015815. Both have intact data, small compute needs and published numbers
  to check against, and the most uncertain step in each is a single named gap.
- **The fossil question:** PMC3322362 is the most cited of the ten, and it shows how a result can rest on data that
  were never released. A reproduction would measure how much the reported accuracy depended on the unpublished
  negative set.
- **Self-consistency:** PMC4331676's own figures do not agree with each other, so a reproduction can say which of
  its numbers hold.
