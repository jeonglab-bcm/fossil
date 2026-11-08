# Paper2Repro checkers

Copies of three scripts of the Paper2Repro skill
([jeonglab-bcm/Paper2Repro](https://github.com/jeonglab-bcm/Paper2Repro), `skills/paper2agent/paper2repro/scripts/`,
commit 727d35e, MIT licence, © 2025 Jiacheng Miao), so a reproduction's pipeline and CI can run them from this
repository:

| Script | Use |
| --- | --- |
| `check_results.py` | Validate a paper's `<PMCID>/results.json` (schema `paper2repro/results/v1`), compute each verdict and the summary (`--write`), print the Markdown table (`--markdown`). Not to be confused with `tools/check_results.py`, which checks `figure-reproduction/results.json` against outputs. |
| `compare_runs.py` | Compare a fresh pipeline run with the committed outputs (numbers within tolerance, images by decoded pixels). |
| `check_package.py` | Build a paper's Python package, install it in a fresh environment, run its tests and its tutorial. |
