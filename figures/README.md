# Figures

Figures for the papers. Each comes as PNG (200 dpi), SVG and PDF (fonts embedded). Do not edit
them by hand: rerun the script that makes them.

| Figure | Files | Made by | Data |
| --- | --- | --- | --- |
| Three eras of code and data sharing | `publication_eras.{png,svg,pdf}` | [`publication-trends/plot_eras.py`](../publication-trends/plot_eras.py) | [`publication-trends/counts.csv`](../publication-trends/counts.csv) |
| Publication trends by theme | `publication_trends.{png,svg,pdf}` | [`publication-trends/plot_trends.py`](../publication-trends/plot_trends.py) | [`publication-trends/counts.csv`](../publication-trends/counts.csv) |

## Draft captions

**Three eras of code and data sharing.** Share of PubMed Central articles, by publication year,
whose full text mentions each resource (log scale), 2000–2026. The strip above marks three eras:
data first (2004–2014), code moves to GitHub (2015–2017), and archived copies and software
environments (2016 onward). The shaded band is our period of interest, 2004–2015. Circles mark the
milestones that date each era. Environment tools (Docker, Jupyter, Conda/Bioconda, Snakemake,
Nextflow) are counted from 2012. 2026 is a partial year.

**Publication trends by theme.** PubMed Central articles per year mentioning each resource (A, log
scale) and their share of all PubMed Central articles that year (B), 2000–2026, grouped by theme:
code hosting, R and Python ecosystems, archives with DOIs, data repositories, and software
environments. Gray lines repeat the other groups for comparison. 2026 is a partial year.

Queries, caveats and how to regenerate the data are in
[`publication-trends/README.md`](../publication-trends/README.md).
