# Example data

| File | What it is |
| --- | --- |
| `pssm/<id>.pssm` | ASCII PSSMs of eight chains of the paper's benchmark (Additional file 1): four DNA-binding (label 1) and four not (label 0), listed in `labels.csv`. |
| `labels.csv` | `id,label` for the eight chains. |
| `expected_pssm_dt.csv` | The PSSM-DT vector (LG = 5, 2,000 values) of each example PSSM. |

**Input.** The profiles were made in the reproduction with NCBI BLAST+ 2.16.0,
`psiblast -num_iterations 3 -evalue 0.001 -out_ascii_pssm`, against UniRef100 release 2014_01
(UniProt Consortium; CC BY-ND 3.0 at release, the database itself is not included). A PSSM is a
statistic computed from the alignments, not a copy of database entries. The sequences are PDB chains
(public domain) listed in the paper's Additional file 1 (Xu et al. 2015, CC BY 4.0).

**Expected output.** `expected_pssm_dt.csv` does not come from this package. `scripts/make_expected.py`
reads each PSSM with its own parser and computes PSSM-DT with plain loops transliterated from the
authors' later toolkit, BioSeq-Analysis2.0 (mode PSSM-DT, functions `preHandleColumns`,
`generate_ksb_pssm` and `aver`, read from its compiled Python). The package must reproduce it to a
relative tolerance of 1e-12; the numbers are written with full precision (`repr`).
