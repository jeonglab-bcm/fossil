#!/usr/bin/env python3
"""Collect the leave-one-out score matrices the rest of the pipeline reads.

The method fits one local support vector machine for every drug-target pair, in each direction, so
a full run is a few hours of CPU: about 1.5 million fits over the four datasets. The default run
therefore recomputes the nuclear-receptor dataset (a minute, and the dataset the no-positive rule
was calibrated on) and copies the committed score matrices for the other three. `--full`
recomputes all four from the benchmark data.

    run_scores.py --data inputs --out scores --committed ../output/scores --processes 4 [--full]
"""

from __future__ import annotations

import argparse
import shutil
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from compute_scores import DATASETS, METHODS, compute, merge

#: Datasets the default run recomputes; the others are read from the committed outputs.
DEFAULT_RECOMPUTED = ("nr",)
#: Methods that take long enough to be worth splitting across processes.
SHARDED = ("blmd", "blmt", "krmd", "krmt")


def task(arguments: tuple) -> tuple[str, str, int, dict]:
    dataset, method, shard, shards, data = arguments
    return dataset, method, shard, compute(dataset, method, Path(data), shard, shards)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--committed", type=Path, required=True)
    ap.add_argument("--processes", type=int, default=4)
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    recomputed = DATASETS if args.full else DEFAULT_RECOMPUTED
    copied = [d for d in DATASETS if d not in recomputed]

    for dataset in copied:
        for method in METHODS:
            name = f"{dataset}_{method}.npz"
            source = args.committed / name
            if not source.is_file():
                raise SystemExit(f"missing committed score file {source}")
            shutil.copy(source, args.out / name)
    if copied:
        print(f"copied the committed scores for {', '.join(copied)}", flush=True)

    jobs = []
    for dataset in recomputed:
        for method in METHODS:
            shards = args.processes if method in SHARDED else 1
            for shard in range(shards):
                jobs.append((dataset, method, shard, shards, str(args.data)))

    parts: dict[tuple[str, str], list[dict]] = {}
    with ProcessPoolExecutor(max_workers=args.processes) as pool:
        for dataset, method, shard, payload in pool.map(task, jobs):
            parts.setdefault((dataset, method), []).append(payload)

    for (dataset, method), pieces in sorted(parts.items()):
        name = f"{dataset}_{method}.npz"
        if len(pieces) == 1:
            payload = pieces[0]
        else:
            temporary = args.out / "parts"
            temporary.mkdir(exist_ok=True)
            paths = []
            for index, piece in enumerate(pieces):
                path = temporary / f"{dataset}_{method}_{index}.npz"
                np.savez_compressed(path, **piece)
                paths.append(path)
            payload = merge(paths)
            shutil.rmtree(temporary)
        np.savez_compressed(args.out / name, **payload)
        unscored = int(np.isnan(payload["scores"]).sum())
        if unscored:
            raise SystemExit(f"{name}: {unscored} pairs have no score")
        print(f"computed {name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
