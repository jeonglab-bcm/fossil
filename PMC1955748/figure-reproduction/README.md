# Figure reproduction (PMC1955748)

Every figure and table in the paper comes out of ASH runs: Fig. 1 from LASH on all 2930 × 2930
pairs of the test set (891 CPU hours in 2007) and on the training set, Fig. 2 and
Table 2 from six alignment programs on 2,071 pairs, Table 1 from a Monte Carlo fit over the
training-set alignments, and Additional Files 2 to 4 from the same alignments. ASH is no longer
available. Its home page, `http://www.pdbj.org/ASH/`, now answers 404, and so does the address
PDBj's help page gives for it today, `https://sysimm.org/ash_service/`. The test set of Kolodny et al. (2,930 CATH 2.4 domains) was on a Stanford page that no
longer resolves and a Haifa page that answers 404. So no figure or table can be redrawn the way
the paper made it.

What the published files still allow is checked here: the training set against CATH 3.0.0 and
SCOP 1.69, Additional File 3 against both, the substitution matrix of Additional File 2 against
BLOSUM62, AAindex and Additional File 4, and the numbers in the text that follow from other
numbers in the paper.

## Results

| Item | Paper | Ours |
| --- | --- | --- |
| Additional File 2 | an image of 210 values | Transcribed to `af2_matrix.txt`. All 884 glyphs sit nearest their own character's template (`pipeline/check_af2.py`); a deliberately changed digit is caught. |
| Training set | 2,911 sequence-unique domains | Additional File 1 lists 2,911 IDs, all different, all in CATH 3.0.0. |
| CATH and SCOP domains compared, equivalent | 63,010 and 43,773 | 71,578 CATH 3.0.0 domains in the 23,344 PDB entries SCOP 1.69 also covers (62,816 SCOP domains); 51,173 have a SCOP domain sharing 75% of the larger one. |
| Queries with a template of the same CATH topology and SCOP fold | 1,641 | 2,325 |
| Queries whose top template is false (Additional File 3) | 69 | 69 rows. All 207 domain lengths equal CATH 3.0.0's. All 69 "true negatives" share topology and fold with the query. |
| ASH matrix against BLOSUM62: slope, correlation | .52, .94 | 0.29 and 0.93 for Additional File 2 on Additional File 4's axis (BLOSUM62 in 1/3 bit units); 0.42 and 0.92 in 1/2 bit units. |
| AAindex | 98 entries; Gonnet closest by dot product (.89), SDM by RMSD (.13) | AAindex2 holds 94 today. Centred and scaled to unit length, Gonnet's matrix comes 6th (0.933); first is CROG050101 (0.953). |
| Table 2, CPU/Align and Rel. to FAST | | CPU (s) / 2,071 gives the printed CPU/Align. Rel. to FAST is CPU over FAST's 645 s, rounded, except STRUCTAL's 5.74, printed as 5. |
| Test-set pairs | 4,298,905 | 2930 × 2929 / 2 = 4,290,985. |
| LASH CPU | 891 h, .37 s per alignment | 891 h over 2930 × 2930 pairs is 0.374 s. |
| Reduced training set | 2,911 less 2,514 removed is 1,397 | 2,911 − 2,514 = 397. |

The full list is in `output/report.md`.

## What the files say, against the paper

- **Additional Files 2 and 4 hold different matrices.** The paper calls Additional File 2 "the
  final amino acid substitution matrix", and Additional File 4 plots "the ASH amino acid
  substitution matrix" against BLOSUM62. Drawn on Additional File 4's axes
  (`output/af4_overlay.png`, Additional File 2 in orange), Additional File 2's off-diagonal
  values sit about 2 above the black points and its diagonal mostly below. Where one residue
  owns an x value the published points read W-W 8.49, C-C 9.24 and Y-Y 5.83; Additional File 2
  has 7.12, 9.27 and 4.27. The slope of .52 belongs to the plotted matrix, which is not published.
- **The equivalence rule.** "Equivalent if 75% or more of the residues of the larger domain were
  shared" leaves 12 of the 2,911 training domains without a SCOP 1.69 partner. 1b9yC01 covers
  129 of the 217 residues of the whole-chain SCOP domain d1b9yc_; 1wf4g03 is on chain g, which
  SCOP 1.69 does not classify (it has 1wf4 chains A to U). With 75% of the smaller domain, only
  1wf4g03 is left. Neither reading gives 63,010 or 43,773.
- **Additional File 3.** The text says the 69 mistakes were false "according to both CATH and
  SCOP classifications". Six of the 69 top false positives share the query's SCOP 1.69 fold:
  1hz4A00 and 1o9eA00 (a.118), 1ksgB00 and 1px3A04 (b.1), 1fipB00 and 1iw7P03 (a.4), 1nji100
  and 1pg5B02 (g.41), 1jwqA00 and 1cfzB00 (c.56), 1lvfA00 and 1bf5A01 (a.47). In seven rows the
  false positive does not outscore the true template listed beside it: 1liuD03 (38 against 43),
  1vklA01 (23 and 23), 1glaG01 (7, 17), 1otkA00 (31, 32), 1sur000 (11, 17), 1nhlA00 (62, 63)
  and 1f4oB00 (−16, −13).
- **Counts.** 4,298,905 is 4,290,985 with two digits swapped. The geometric test set has 2,070
  pairs in the Methods and 2,071 in Table 2 and Fig. 2.

## Not reproduced

| Item | Needs | Why not |
| --- | --- | --- |
| Fig. 1 | LASH on the 2,930-domain test set and on the training set | ASH and the test-set list are gone. |
| Fig. 2 | GASH, RASH, DaliLite, FAST, SSM and STRUCTAL on the 2,071 "challenging" pairs | GASH and RASH are ASH; the pair list is gone with the test set. |
| Table 1 | The Monte Carlo fit over ASH training-set scores | Needs ASH. |
| Table 2 | CPU times on a 2007 Pentium 4 | Needs the programs and the machine. Only the derived columns are checked. |
| Additional File 2 | Substitution statistics over ASH superpositions | Needs ASH. Checked as published. |
| Additional File 3 | ASH scores of every training pair | Needs ASH. The classifications and lengths are checked. |
| Additional File 4 | The true-pair and false-pair matrices | Neither is published. Additional File 2 is drawn on its axes instead. |
| Reduced training set (1,397 or 397) | BLAST of the training set against the test set | Needs the test-set list. |

## Layout

| Path | Content |
| --- | --- |
| `main.nf`, `nextflow.config` | Nextflow pipeline that runs every step below. |
| `af2_matrix.txt` | Our transcription of Additional File 2, in its layout (© 2007 Standley et al., licensee BioMed Central, CC BY 2.0). |
| `pipeline/` | The scripts (Python, shell). |
| `output/` | `report.md`, `cath_scop.json`, `matrices.json`, `arithmetic.json`, `af2_check.txt`, and `af4_overlay.png` (Additional File 4, © 2007 Standley et al., CC BY 2.0, with Additional File 2 drawn on it in orange). |

## Run

Requirements: Python 3 with numpy, scipy, pillow and xlrd; Nextflow with Java 17 or later.

```sh
nextflow run PMC1955748/figure-reproduction/main.nf --outdir results
```

The run downloads Additional Files 1 to 4 from PMC's open-access copy, CATH 3.0.0's domain list
and boundaries, SCOP 1.69's classification, AAindex2 and BLOSUM62 (1/2 and 1/3 bit), and checks
each file's SHA-256 (`--sources DIR` reuses local copies). It takes under a minute and writes
`results/report.md`; it fails if any result above moves. The GitHub workflow
`.github/workflows/reproduce-pmc1955748.yml` does the same run on Ubuntu.

## Pipeline steps

| Step | Script | Output |
| --- | --- | --- |
| Fetch and check inputs | `fetch_inputs.sh` | the ten input files |
| Check the transcription | `check_af2.py` | `af2_check.txt` |
| Additional File 3 as CSV | `export_af3.py` | `data/additional-file-3.csv` |
| Training set against CATH and SCOP | `cath_scop.py` | `cath_scop.json` |
| Matrix comparisons, Additional File 4 | `matrices.py` | `matrices.json`, `af4_overlay.png` |
| Numbers from numbers | `arithmetic.py` | `arithmetic.json` |
| Check | `check_reproduction.py` | `report.md` |

## Limits

- Residues are counted from the PDB residue numbers in the CATH and SCOP boundary files, without
  insertion codes. A SCOP domain given as a whole chain or entry takes CATH's extent for that
  chain. The paper does not say how residues were counted.
- "Same CATH and SCOP classification" is read as the same CATH topology (C.A.T) and the same
  SCOP fold. The other pairings of CATH architecture, topology or superfamily with SCOP fold,
  superfamily or family give 1,296 to 2,440 queries (`cath_scop.json`), none 1,641.
- AAindex2 has changed since 2007 (94 entries now, 98 in the paper), and the paper does not say
  how the matrices were centred and normalized. `matrices.json` lists 24 readings; none puts
  Gonnet first by dot product and SDM first by RMSD.
- Additional File 4's values are read from the image: its axes come from the frame and the
  printed limits, and only markers standing alone are read. Marker centres fall within 0.08 of
  whole BLOSUM62 values.
