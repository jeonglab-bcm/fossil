#!/usr/bin/env python3
"""Leave-one-out scores of one method on one benchmark dataset.

Every score comes from the installed `blmdti` package, so the pipeline and the package hold one
copy of the method. The work splits over shards: BLMd and KRMt over the target columns, BLMt and
KRMd over the drug rows, so that a cluster can run the four big datasets as a job array.

    compute_scores.py --data DIR --dataset nr --method blmd --out scores/nr_blmd.npz
    compute_scores.py --data DIR --dataset e --method blmt --shard 3 --shards 48 --out part.npz
    compute_scores.py --merge part0.npz part1.npz ... --out scores/e_blmt.npz
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

import blmdti as B

DATASETS = ("e", "ic", "gpcr", "nr")
METHODS = ("blmd", "blmt", "krmd", "krmt", "nnd", "nnt")
#: Rule for a local model whose only positive example is the pair being scored. Calibrated on the
#: nuclear-receptor dataset and then used unchanged everywhere (see results.json).
NO_POSITIVE = "minus_one"
H = 2.0  # KRM width parameter: the value Yamanishi et al. (2008) report using


def load(data: Path, dataset: str):
    drugs, targets, adjacency = B.read_network(data / f"{dataset}_admat_dgc.txt")
    drug_rows, drug_cols, chemical = B.read_matrix(data / f"{dataset}_simmat_dc.txt")
    target_rows, target_cols, genomic = B.read_matrix(data / f"{dataset}_simmat_dg.txt")
    if drug_rows != drugs or drug_cols != drugs:
        raise SystemExit(f"{dataset}: the chemical matrix is not in the adjacency's drug order")
    if target_rows != targets or target_cols != targets:
        raise SystemExit(f"{dataset}: the genomic matrix is not in the adjacency's target order")
    return drugs, targets, adjacency, chemical, genomic


def shard_of(count: int, shard: int, shards: int) -> range:
    """The indices this shard owns, as an even split of range(count)."""
    if not 0 <= shard < shards:
        raise SystemExit(f"shard {shard} is outside 0..{shards - 1}")
    start = count * shard // shards
    stop = count * (shard + 1) // shards
    return range(start, stop)


def compute(dataset: str, method: str, data: Path, shard: int, shards: int) -> dict:
    drugs, targets, adjacency, chemical, genomic = load(data, dataset)
    drug_kernel, drug_shift = B.make_psd(chemical)
    target_kernel, target_shift = B.make_psd(genomic)
    started = time.time()
    if method == "blmd":
        scores = B.blm_drug_scores(
            adjacency, drug_kernel, no_positive=NO_POSITIVE,
            targets=shard_of(len(targets), shard, shards),
        )
    elif method == "blmt":
        scores = B.blm_target_scores(
            adjacency, target_kernel, no_positive=NO_POSITIVE,
            drugs=shard_of(len(drugs), shard, shards),
        )
    elif method == "krmd":
        scores = B.krm_drug_scores(
            adjacency, chemical, h=H, drugs=shard_of(len(drugs), shard, shards)
        )
    elif method == "krmt":
        scores = B.krm_target_scores(
            adjacency, genomic, h=H, targets=shard_of(len(targets), shard, shards)
        )
    elif method == "nnd":
        scores = B.nn_drug_scores(adjacency, chemical)
    elif method == "nnt":
        scores = B.nn_target_scores(adjacency, genomic)
    else:
        raise SystemExit(f"unknown method {method!r}")
    return {
        "scores": scores,
        "drugs": np.array(drugs),
        "targets": np.array(targets),
        "adjacency": adjacency.astype(np.int8),
        "meta": np.array(
            json.dumps(
                {
                    "dataset": dataset,
                    "method": method,
                    "shard": shard,
                    "shards": shards,
                    "no_positive": NO_POSITIVE if method.startswith("blm") else None,
                    "h": H if method.startswith("krm") else None,
                    "psd_shift_chemical": drug_shift,
                    "psd_shift_genomic": target_shift,
                    "seconds": round(time.time() - started, 1),
                    "blmdti_version": B.__version__,
                }
            )
        ),
    }


def merge(parts: list[Path]) -> dict:
    """Put sharded score matrices back together; every cell must be filled exactly once."""
    out = None
    metas = []
    for path in parts:
        with np.load(path, allow_pickle=False) as f:
            scores = f["scores"]
            metas.append(json.loads(str(f["meta"])))
            if out is None:
                out = {k: f[k] for k in ("drugs", "targets", "adjacency")}
                out["scores"] = np.full(scores.shape, np.nan)
            filled = ~np.isnan(scores)
            clash = filled & ~np.isnan(out["scores"])
            if clash.any():
                raise SystemExit(f"{path}: {int(clash.sum())} cells are in two shards")
            out["scores"][filled] = scores[filled]
    if out is None:
        raise SystemExit("merge needs at least one part")
    meta = dict(metas[0])
    meta["shard"] = None
    meta["seconds"] = round(sum(m["seconds"] for m in metas), 1)
    meta["shards_merged"] = len(metas)
    out["meta"] = np.array(json.dumps(meta))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, help="folder with the benchmark files")
    ap.add_argument("--dataset", choices=DATASETS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--merge", nargs="+", type=Path, help="shard files to merge instead")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    if args.merge:
        payload = merge(args.merge)
    else:
        if not (args.data and args.dataset and args.method):
            ap.error("--data, --dataset and --method are required unless --merge is given")
        payload = compute(args.dataset, args.method, args.data, args.shard, args.shards)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out, **payload)
    meta = json.loads(str(payload["meta"]))
    nan = int(np.isnan(payload["scores"]).sum())
    print(f"{args.out}: {payload['scores'].shape} {nan} unscored, {meta['seconds']}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
