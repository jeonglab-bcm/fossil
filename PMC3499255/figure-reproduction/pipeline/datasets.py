"""Load the three analysis datasets of Morelli et al. (2012) into transtree.Data.

* ``test``  : a 20-premise outbreak simulated from the model (Fig. 2, Table 1 row 1).
              Regenerated here because the authors deposited no seed or data.
* ``y2007`` : the 2007 UK outbreak, Datasets S1 (FASTA) + S2 (epi table), 9 premises.
              The duplicate second sample ``IP1b/2`` is dropped (Fig. 3 shows 9 rows).
* ``y2001`` : the 2001 Darlington cluster, Datasets S3 + S4, 12 premises after
              removing A and N (a second source) and B (an independent
              introduction), following Text S1.

The real-data FASTA/epi files are fetched by ``fetch_inputs.sh`` into a sources
directory and are *not* redistributed in the repository.
"""

from __future__ import annotations

import os

import numpy as np

from transtree.core import (
    Data,
    hamming_matrix,
    lonlat_to_km,
    read_epi_table,
    read_fasta,
    simulate_outbreak,
)

# Premises kept for the 2001 analysis (Text S1: drop A, N, B from the 15).
Y2001_KEEP = ["K", "L", "O", "F", "E", "C", "P", "M", "G", "D", "I", "J"]
Y2001_DROP = ["A", "N", "B"]

# Fixed constants (Materials and Methods; Text S1).
REAL_S, REAL_M = 8176.0, 2.076e-5
SIM_S, SIM_M = 8000.0, 1e-4
SIM_ALPHA = (80.0, 10.0)
SIM_BETA = (5.0, 1.0)
SIM_DOMAIN = (22.0, 11.0)   # Results / Text S1 (Methods says 20x10); choice recorded in README


def load_real(sources_dir: str, which: str) -> Data:
    """Load ``y2007`` or ``y2001`` from the fetched Dataset S1-S4 files."""
    if which == "y2007":
        fasta = os.path.join(sources_dir, "pcbi.1002768.s001.fasta")
        epi = os.path.join(sources_dir, "pcbi.1002768.s002.txt")
        drop = {"IP1b/2"}
        keep_order = None
    elif which == "y2001":
        fasta = os.path.join(sources_dir, "pcbi.1002768.s003.fasta")
        epi = os.path.join(sources_dir, "pcbi.1002768.s004.txt")
        drop = set(Y2001_DROP)
        keep_order = Y2001_KEEP
    else:
        raise ValueError(which)

    seqs = read_fasta(fasta)
    names, lonlat, Tobs, Tend, Dobs = read_epi_table(epi)
    idx = {n: i for i, n in enumerate(names)}
    kept = [n for n in names if n not in drop]
    if keep_order is not None:
        kept = [n for n in keep_order if n in kept]
    order = [idx[n] for n in kept]
    X = lonlat_to_km(lonlat[order])
    M = hamming_matrix([seqs[n] for n in kept])
    return Data(names=kept, X=X, Tobs=Tobs[order], Tend=Tend[order], Dobs=Dobs[order],
                M=M, s=REAL_S, m=REAL_M)


def load_test(seed: int = 0, n: int = 20) -> tuple[Data, dict]:
    """Regenerate the simulated test outbreak (Fig. 2) and return (data, truth)."""
    return simulate_outbreak(n, SIM_ALPHA, SIM_BETA, SIM_S, SIM_M,
                             domain=SIM_DOMAIN, seed=seed)
