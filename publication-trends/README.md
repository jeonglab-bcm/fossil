# Publication trends for code and data repositories, 2000–2026

How often PubMed Central articles mention places where code and data are shared. We use it as a
rough proxy for when sharing code and data, and so reproducibility, became common practice.

![Publication trends](publication_trends.png)

| Theme | Group | Query (PMC full text, `[All Fields]`) |
| --- | --- | --- |
| Code hosting | GitHub + GitLab | `"github" OR "gitlab"` |
| Code hosting | SourceForge | `"sourceforge"` |
| Package repositories | CRAN + Bioconductor | `"cran" OR "bioconductor"` |
| Package repositories | PyPI | `"pypi" OR "python package index"` |
| Archives with DOIs | Zenodo + figshare | `"zenodo" OR "figshare"` |
| Data repositories | NCBI GEO | `"gene expression omnibus" OR "ncbi geo"` |
| Data repositories | SRA / ENA | `"sequence read archive" OR "ncbi sra" OR "european nucleotide archive"` |
| Software environments | Docker, Jupyter, Conda, Snakemake, Nextflow | `"docker" OR "jupyter" OR "conda" OR "bioconda" OR "snakemake" OR "nextflow"` |

Each query is ANDed with `<year>[pdat]`. Row B divides by all PMC articles with that publication
year (`<year>[pdat]`), so PMC's growth does not drive the trend. Each column is one theme; the
other groups are drawn in gray for comparison.

Caveats:

- PMC full text includes reference lists, so a citation of a GitHub-hosted tool counts as a mention.
- PMC covers only part of the literature, and its coverage has changed over time (for example,
  journals joining PMC and public access policies).
- 2026 is a partial year (indexed through late October). The raw count for 2026 is therefore low.
  The share is more comparable, but may still change as indexing catches up.
- A mention is not a deposit. An article can name GitHub or GEO without sharing code or data.
- PyPI is rarely named (about 0.1% of articles); papers more often say `pip install` or just "Python".
- Row A omits zero counts, since a log axis cannot show them.
- Early hits for some terms are other uses of the word. For example, the 16 "docker" hits in 2001 are
  medical articles (occupational medicine, primary care), not the container tool.

## Reproduce

```bash
python3 fetch_counts.py counts.csv   # about 250 NCBI E-utilities requests, ~3 min
python3 plot_trends.py counts.csv publication_trends
```

`plot_trends.py` needs matplotlib. `counts.csv` holds the counts we retrieved and the date we
retrieved them.
