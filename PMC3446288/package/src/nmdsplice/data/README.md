# Example data

| File | What it is | Source and licence |
| --- | --- | --- |
| `example_junctions.tsv` | 12 exon-exon junctions (chromosome, strand, donor, acceptor; mm9, UCSC coordinates: donor = end of the upstream exon, acceptor = start of the downstream exon). Three are inclusion junctions of PTC-upon-inclusion events (Additional file 8), nine are skipping junctions of PTC-upon-exclusion events (Additional file 9). | Coordinates as printed in Weischenfeldt et al. 2012, Additional files 8 and 9 (CC BY 2.0, © 2012 Weischenfeldt et al.; licensee BioMed Central). |
| `example_expected.tsv` | The expected output: the "PTC distance" the paper prints for each event. | The same files. The paper's own pipeline (RAINMAN) computed these values; this package did not. |
| `example_annotation/` | The rows of the UCSC mm9 tables `refGene`, `ensGene`, `knownGene`, `genscan` and `exoniphy` that lie inside each junction's region (every RefSeq and Ensembl model that overlaps the junction, plus 2 kb). | UCSC Genome Browser mm9 database dumps (hgdownload.soe.ucsc.edu/goldenPath/mm9/database/), free for all uses. |
| `example_genome.fa` | mm9 sequence of each region; records are named `chrom:start-end` (0-based start). | UCSC mm9 `chromFa.tar.gz`, free for all uses. |

`scripts/make_example_data.py` makes these files from the reproduction's downloaded inputs.

The 12 events are ones whose distance our full run reproduces: on the full mm9 annotation, the
package gives the printed distance for 42 of the 45 PTC-upon-exclusion events and 16 of the 19
PTC-upon-inclusion junction pairs it calls PTC+ (see the reproduction's `results.json`, item
`port.ptc_distance`). The example is a check that an installed package still computes them; it is
not the evaluation of the method. Compare at exact equality: distances are whole nucleotides.
