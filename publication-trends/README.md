# Publication trends for code and data repositories, 2010–2026

How often PubMed Central articles mention places where code and data are shared. We use it as a
rough proxy for when sharing code and data, and so reproducibility, became common practice.

![Publication trends](publication_trends.png)

| Group | Query (PMC full text, `[All Fields]`) |
| --- | --- |
| GitHub + GitLab | `"github" OR "gitlab"` |
| SourceForge | `"sourceforge"` |
| NCBI GEO | `"gene expression omnibus" OR "ncbi geo"` |
| Python | `"python" NOT ("snake" OR "snakes" OR "boidae")` |
| CRAN + Bioconductor | `"cran" OR "bioconductor"` |

Each query is ANDed with `<year>[pdat]`. Panel B divides by all PMC articles with that publication
year (`<year>[pdat]`), so PMC's growth does not drive the trend.

Caveats:

- PMC full text includes reference lists, so a citation of a GitHub-hosted tool counts as a mention.
- PMC covers only part of the literature, and its coverage has changed over time (for example,
  journals joining PMC and public access policies).
- 2026 is a partial year (indexed through late October). The raw count for 2026 is therefore low.
  The share is more comparable, but may still change as indexing catches up.
- A mention is not a deposit. An article can name Python or GEO without sharing code or data.

## Reproduce

```bash
python3 fetch_counts.py counts.csv   # about 100 NCBI E-utilities requests, ~1 min
python3 plot_trends.py counts.csv publication_trends
```

`plot_trends.py` needs matplotlib. `counts.csv` holds the counts we retrieved and the date we
retrieved them.
