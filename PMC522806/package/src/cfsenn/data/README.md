# Example data

| File | What it is |
| --- | --- |
| `example_train.csv` | Example training table: 40 samples (20 "normal", 20 "tumor") x 500 genes. Column `class`, then `g1` to `g500`. |
| `example_test.csv` | Example test table: 20 samples (10 of each class), same columns. |
| `example_test_expected.csv` | Expected output: the class each test sample was drawn from. Columns `sample` (1-based row of the test table) and `class`. |

## Where it comes from

- Input: synthetic, written by `scripts/make_example_data.py` (NumPy seed 522806). Genes 1 to 30 are informative, in three co-expressed blocks of 10 genes (a shared block factor plus noise); in class "tumor" their log-scale mean is shifted by +1.5, -1.5 and +1.0 standard deviations. Genes 31 to 500 are noise. Values are exp(0.5 z + 5), rounded to 2 decimals, so they look like array intensities.
- Expected output: the generator's class labels, not output of this package. With the paper's settings every test sample should be classified correctly (20 of 20).
- Licence: synthetic data, released with the package under its licence (MIT).

The Kent Ridge datasets of the paper are not bundled: the repository that held them gave no licence for redistribution. The reproduction downloads them.
