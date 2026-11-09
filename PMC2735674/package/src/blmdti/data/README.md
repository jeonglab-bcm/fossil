# Example data

| File | What it is |
| --- | --- |
| `example_admat.txt` | Example network: 12 drugs (D01 to D12), 8 target proteins (T01 to T08), 44 known interactions. Targets are rows and drugs are columns, as in the benchmark files the paper uses. |
| `example_simmat_dc.txt` | Chemical similarity between the 12 drugs. |
| `example_simmat_dg.txt` | Sequence similarity between the 8 targets. |
| `example_expected.json` | The expected output: the four interactions deleted from the network, and the rule they must satisfy. |

## Where it comes from

- Input: synthetic, written by `scripts/make_example_data.py`. The network has two blocks: drugs
  D01 to D06 bind targets T01 to T04 and drugs D07 to D12 bind targets T05 to T08. Similarity is
  0.9 inside a block and 0.1 between blocks. Four interactions were then deleted:
  D01-T01, D04-T03, D08-T05 and D11-T08.
- Expected output: the four deleted pairs, and the rule that each of them ranks above every pair
  whose drug and target lie in different blocks. That follows from the construction of the data,
  not from this package: inside a block every drug and target are near neighbours of a known
  interaction, while across blocks none are. The test checks that the four deleted pairs are the
  four highest scoring pairs that the network does not already contain.
- Licence: synthetic data, released with the package under its licence. The paper's own benchmark
  files are not redistributed here; `fetch_inputs.sh` in the reproduction downloads them from the
  Yamanishi et al. (2008) supplement page.

The example is there to show the input format and to check the method end to end, not to
reproduce the paper. The reproduction does that, on the paper's four networks.
