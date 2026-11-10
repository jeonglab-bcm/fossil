# Example data

| File | What it is |
| --- | --- |
| `example_train_profiles.npz` | PSI-BLAST profiles (`spsvm.write_profiles` format) of 150 PDB chains of the paper's data set: 50 zinc-binding chains and 100 chains without metal, drawn at random (seed 1) from the five CV folds of Additional file 1. |
| `example_train_labels.txt` | Their C and H residues with zinc labels, in the format of Additional file 1 (`class chain position residue cofactor`, positions 0-based on today's SEQRES). |
| `czib_NP_060357.1.pssm` | The PSI-BLAST ASCII PSSM of the human protein NP_060357.1 (CZIB, formerly "hypothetical protein FLJ20580"), the protein of the paper's Fig. 8. |
| `czib_5zlq_zinc_ligands.csv` | Expected output: the residues of CZIB whose side-chain donor atoms lie within 3 Å of the zinc ion in PDB entry 5ZLQ (columns `position` (1-based, NP_060357.1 numbering), `residue`, `atom`, `distance_A`). |

## Where it comes from

- Labels: the paper's Additional file 1 (Passerini et al. 2007, BMC Bioinformatics 8:39, CC BY 2.0), positions mapped to today's SEQRES by the reproduction (`PMC1800866/figure-reproduction/output/predictions/candidates.tsv`).
- Profiles: computed by the reproduction with PSI-BLAST (BLAST+ 2.17.0, 3 iterations, other settings default) against UniRef100 release 2010_01. The profile values are statistics computed from the database search, not database records. UniProt data are distributed under CC BY 4.0 (the 2010 release under CC BY-ND); see https://www.uniprot.org/help/license.
- Expected output: from the crystal structure 5ZLQ (RCSB PDB, released 2018; PDB data are CC0), read with gemmi at the paper's 3 Å cutoff. It does not come from this package. The four cysteines it lists are those the paper predicted (its Cys31, Cys34 and Cys68 above 0.7, and Cys65 at 0.67, in the numbering of its homology model, two lower than NP_060357.1).

Compare positions exactly. The tutorial and tests check that the four highest gated probabilities fall on these four residues.
