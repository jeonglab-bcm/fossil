"""Generate the bundled example dataset for the transtree package.

A small 6-premise outbreak simulated from the model with a fixed seed. The
example exists only to show the method runs end to end; it is not the paper's
data. The *expected output* committed next to it is produced independently of the
package's inference: it is the simulation's own ground-truth transmission tree
and parameters (``simulate_outbreak`` returns the truth), so the tutorial's
check compares the package's inference against data it did not itself produce.

Run from the package root:
    python scripts/make_example_data.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from transtree.core import simulate_outbreak

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "src" / "transtree" / "data"

SEED = 7
N = 6
ALPHA = (60.0, 6.0)
BETA = (6.0, 2.0)
S = 4000.0
M = 1e-4
DOMAIN = (10.0, 8.0)


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    data, truth = simulate_outbreak(N, ALPHA, BETA, S, M, domain=DOMAIN, seed=SEED)

    # observable input: one row per premise (location in km, Tobs, Tend, Dobs) and
    # the pairwise Hamming distance matrix.
    with open(DATA / "example_epi.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["premise", "x_km", "y_km", "Tobs", "Tend", "Dobs"])
        for i, nm in enumerate(data.names):
            w.writerow([nm, f"{data.X[i,0]:.4f}", f"{data.X[i,1]:.4f}",
                        f"{data.Tobs[i]:.4f}", f"{data.Tend[i]:.4f}", f"{data.Dobs[i]:.4f}"])
    np.savetxt(DATA / "example_hamming.csv", data.M.astype(int), fmt="%d", delimiter=",")

    # independent expected output: the true tree and parameters from the simulator.
    expected = dict(
        s=S, m=M,
        true_tree=[int(x) for x in truth["J"]],      # -1 = external source
        true_mean_latency=float(truth["beta"][0]),
        true_mean_distance=float(2.0 * truth["alpha"][1]),
        names=list(data.names),
        note=("Ground truth from the simulation that generated example_epi.csv / "
              "example_hamming.csv; produced by the simulator, not by transtree's "
              "inference. The tutorial infers the tree and checks it against this."),
    )
    with open(DATA / "example_expected.json", "w") as fh:
        json.dump(expected, fh, indent=2)
    print("wrote", DATA / "example_epi.csv", DATA / "example_hamming.csv",
          DATA / "example_expected.json")


if __name__ == "__main__":
    main()
