#!/usr/bin/env python3
"""Write the bundled example network and its expected output.

The example is a synthetic bipartite drug-target network built from two blocks: drugs D01 to D06
bind targets T01 to T04, drugs D07 to D12 bind targets T05 to T08, and the two similarity matrices
are high inside a block and low between blocks. Four interactions are then deleted from the
network: those four pairs are the planted edges a method should rank first.

The expected output is the list of planted pairs and the ranking statistic that follows from the
construction, not from this package: in a network whose blocks are separable, every planted pair
must rank above every pair that crosses the blocks. The test asks for exactly that.

Run from the package folder: python3 scripts/make_example_data.py
"""

import csv
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "src" / "blmdti" / "data"
DRUGS = [f"D{i:02d}" for i in range(1, 13)]
TARGETS = [f"T{i:02d}" for i in range(1, 9)]
BLOCK_DRUGS = [DRUGS[:6], DRUGS[6:]]
BLOCK_TARGETS = [TARGETS[:4], TARGETS[4:]]
#: Interactions removed from the network: the edges the method has to find again.
PLANTED = [("D01", "T01"), ("D04", "T03"), ("D08", "T05"), ("D11", "T08")]
WITHIN, BETWEEN = 0.9, 0.1


def block_of(name, blocks):
    return 0 if name in blocks[0] else 1


def write_matrix(path, rows, columns, value):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow([""] + list(columns))
        for row in rows:
            writer.writerow([row] + [f"{value(row, column):g}" for column in columns])


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    interactions = {
        (drug, target)
        for block in (0, 1)
        for drug in BLOCK_DRUGS[block]
        for target in BLOCK_TARGETS[block]
    } - set(PLANTED)
    # The network file has targets as rows and drugs as columns, as the benchmark files do.
    write_matrix(
        DATA / "example_admat.txt", TARGETS, DRUGS,
        lambda target, drug: int((drug, target) in interactions),
    )
    write_matrix(
        DATA / "example_simmat_dc.txt", DRUGS, DRUGS,
        lambda a, b: 1.0 if a == b else (WITHIN if block_of(a, BLOCK_DRUGS) == block_of(b, BLOCK_DRUGS) else BETWEEN),
    )
    write_matrix(
        DATA / "example_simmat_dg.txt", TARGETS, TARGETS,
        lambda a, b: 1.0 if a == b else (WITHIN if block_of(a, BLOCK_TARGETS) == block_of(b, BLOCK_TARGETS) else BETWEEN),
    )
    expected = {
        "planted_pairs": [list(pair) for pair in PLANTED],
        "rule": (
            "Every planted pair ranks above every pair whose drug and target are in different"
            " blocks. The blocks are separable by construction, so this follows from the data, not"
            " from the package."
        ),
        "blocks": {
            "drugs": [list(b) for b in BLOCK_DRUGS],
            "targets": [list(b) for b in BLOCK_TARGETS],
        },
        "within_block_similarity": WITHIN,
        "between_block_similarity": BETWEEN,
    }
    (DATA / "example_expected.json").write_text(json.dumps(expected, indent=1) + "\n")
    print(f"wrote the example network ({len(interactions)} interactions) and its expected output")


if __name__ == "__main__":
    main()
