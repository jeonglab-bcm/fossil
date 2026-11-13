# Example data

| File | What it is |
| --- | --- |
| `fig7_profile.tsv` | The worked example of the paper's Figure 7: one gene with three values, 343, 314 and 409. |
| `fig7_expected.tsv` | Its expected edge angles (as printed, whole degrees) and regulation: 138 and -1, then 52 and +1. |
| `gds3702_mrps26_pfn2.tsv` | The two genes of the paper's Figure 2: GEO GDS3702 (rat pineal gland), probes 1367526_at (Mrps26) and 1367970_at (Pfn2), the 12 samples in GEO's order, values as GEO gives them (count). |
| `gds3702_expected.tsv` | The expected network for that pair: one edge, sign -1 (negative regulation). |

## Where it comes from

- `fig7_*`: printed in the paper (Roy et al. 2014, Figure 7 and the Methods text), © the authors, CC BY 2.0.
- `gds3702_mrps26_pfn2.tsv`: NCBI GEO, GDS3702 (GSE12343), downloaded from
  `https://ftp.ncbi.nlm.nih.gov/geo/datasets/GDS3nnn/GDS3702/soft/GDS3702.soft.gz`. GEO places no
  restrictions on the use of its data; cite Bailey et al. 2009 (GSE12343) and GEO.
- Expected outputs come from the paper's text, not from this package: Figure 7 prints the angles and
  regulation, and the Background section says the two Figure 2 genes "clearly show negative behaviour".
  Compare the angles at the printed precision (whole degrees) and the sign exactly, with the default
  settings (theta 0.5, tau 20).
