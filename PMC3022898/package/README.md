# esrisk

Exposure-specific risk (ESR) from two independent samples: the overall risk of a disease from one
sample, the relative risk of an exposure and the exposure probability from another. `esrisk` gives the
two point estimators and three 95% confidence intervals of

> Reichmann WM, Gagnon D, Horsburgh CR, Losina E. Evaluation of exposure-specific risks from two
> independent samples: a simulation study. *BMC Medical Research Methodology* 11:1 (2011).
> [doi:10.1186/1471-2288-11-1](https://doi.org/10.1186/1471-2288-11-1)

and the simulation study that compares them.

| Estimator | Formula (equation of the paper) |
| --- | --- |
| Simple product-based, ESR_S | P1(D) x RR2 (eq. 2); log CI (eqs 5-6) |
| Revised product-based, ESR_R | P1(D) / ((RR2 - 1) P2(E) + 1) x RR2 (eq. 9); log CI (eq. 10) and binomial CI (eqs 11-12) |

ESR_S is biased upward whenever the exposure is common or the RR large (93.9% in the paper's worst
setting); ESR_R removes that bias by estimating the risk in the unexposed first.

## Install

```bash
pip install "git+https://github.com/jeonglab-bcm/fossil#subdirectory=PMC3022898/package"
```

Python 3.10 or later; depends on NumPy.

## Quick start

```python
import esrisk

# From counts: 31 cases among 1,000 people in sample 1; in sample 2, 19 of 184 exposed
# and 14 of 816 unexposed people have the disease.
e = esrisk.estimate(31, 1000, 19, 184, 14, 816)
print(float(e.esr_s), float(e.esr_r), e.ci_r_log, e.ci_r_binomial)

# From published summaries: an overall risk from a sample of n1, a relative risk with its 95% CI,
# and the exposure probability of the second study.
esrisk.esr_from_summaries(p1_d=0.0147, n1=11817, rr2=1.91, rr2_ci=(1.46, 2.50), p2_e=0.371)

# One setting of the simulation study.
est, *_ = esrisk.simulate(0.20, 0.02, 5.0, n1=1000, n2=1000, reps=1000, rng=1)
esrisk.evaluate(est, true_esr=0.10)["esr_s"]["relative_bias"]
```

Command line:

```bash
esrisk estimate "$(esrisk --example-path)" -o estimates.csv
esrisk simulate --p-exposed 0.2 --p-unexposed 0.02 --rr 5 --n1 1000 --n2 1000 --seed 1
```

Tutorial: [tutorial/TUTORIAL.md](tutorial/TUTORIAL.md).

## Choices the paper does not state

- **Zero cells.** With no cases among the exposed (or the unexposed) of sample 2, the log-based
  variances are undefined. The default, `zero_cells="unbounded"`, returns the log interval (0, inf);
  `"missing"`, `"not_covered"` and `"half"` (0.5 added to the cells) are the alternatives. The
  default is the one that fits the paper's coverage tables best.
- **z.** 1.959964 (the paper prints 1.96).

## Language and checks

Python, by the default rule: the paper's SAS 9.2 programs were never released, and the method needs
no R or Bioconductor package. It is implemented from the paper's text (equations 2-12) and checked
against the paper's tables and figures only, not against the original code, which is lost. The
reproduction ([PMC3022898](https://github.com/jeonglab-bcm/fossil/tree/main/PMC3022898)) runs the
paper's whole simulation through this package and compares every table cell and figure bar; its
README gives the results. One finding matters to users: eq. 10 as printed gives
log intervals for ESR_R that cover more often than the paper's simulation shows; the paper's
simulation behaves as if eq. 10's first term were left out, while its case study uses eq. 10 as
printed. This package implements eq. 10 as printed.

## Licence

MIT. Implemented from the paper's text (CC BY 2.0); no code of the authors is included.
