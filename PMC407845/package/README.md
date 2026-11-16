# manetworker

Transcription factor (TF) activity profiles and regulatory coupling from mRNA expression and ChIP
binding data: MA-Networker, from

> Gao F, Foat BC, Bussemaker HJ. Defining transcriptional networks through integrative modeling of
> mRNA expression and transcription factor binding data. *BMC Bioinformatics* 5:31 (2004).
> [doi:10.1186/1471-2105-5-31](https://doi.org/10.1186/1471-2105-5-31)

Step 1 regresses each experiment's expression log ratios on the TFs' ChIP log ratios; the
coefficients over all experiments are each TF's activity profile, and backward selection keeps the
TFs that predict expression. Step 2 correlates each gene's expression profile with each activity
profile; a bound gene (ChIP P < 1e-3) whose correlation passes a 5% false discovery rate is a
functional target (B+/C+), and the other bound genes are B+/C-.

The authors' code was never released. This package implements the method from the paper's
Methods, in Python because the method needs only linear regression and correlation (NumPy, SciPy)
and the paper used no R or Bioconductor package. It was checked against the paper, not against
the original program: see the reproduction in [`PMC407845`](..) and its
[results page](https://jeonglab-bcm.github.io/fossil/PMC407845/).

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC407845/package"
```

Python 3.10 or later, with NumPy and SciPy.

## Use

```python
import manetworker as mn

genes, experiments, E = mn.read_matrix("expression.tsv")      # genes x experiments, log2 ratios
_, tfs, ratio = mn.read_matrix("binding_ratio.tsv")            # genes x TFs, ChIP ratios
_, _, chip_p = mn.read_matrix("binding_p.tsv")                 # genes x TFs, ChIP P-values
res = mn.run(E, mn.log_ratio(ratio), chip_p, tfs)
res["tfs"], res["counts"]          # kept TFs; B-, B+/C+, B+/C-, unclassified per TF
```

Command line:

```bash
manetworker expression.tsv binding_ratio.tsv binding_p.tsv -o out
manetworker --example -o out       # the bundled example data
```

The building blocks are public too: `regress_activities`, `backward_select`, `coupling`,
`bh_reject`, `coupled`, `classify`.

## Tutorial

[`tutorial/TUTORIAL.md`](tutorial/TUTORIAL.md): install, the example input, a run through the API
and the command line, and the comparison with the expected output of the synthetic example
(`src/manetworker/data/README.md`).

## Choices where the paper is silent

`run()` follows the paper's text: activity profiles from the regression, coupling P-values
two-sided, Benjamini-Hochberg per TF. The reproduction of the paper found that its figures fit
t-value activity profiles and a one-sided test for positive coupling better: pass
`profile="t", sided="one"` to `run()`.

## Licence

MIT (the fossil repository's licence). The method is implemented from the paper's text.
