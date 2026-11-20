"""Quantitative claims in the text (Spatial connectivity, Discussion).

Computed from our posterior JSONs and the data:
  * mean transmission distance 95% interval, 2007 and 2001 (Figs. 3, 4 / text);
  * the span of pairwise distances in each dataset (~24 km 2007, ~16 km 2001);
  * the mean length of the inferred transmissions in the highest-posterior tree
    (4.3 km 2007, 5.8 km 2001);
  * IP5 is 18.2 km from IP1b;
  * IP5 mean latency over 25 days (2007 Discussion).

Each is written as a field {name, expected, observed}. The arithmetic checks
(distances and tree-edge lengths computed from the data and the committed tree)
are exact; the posterior quantities (intervals, IP5 latency) are MCMC output and
carry a Monte Carlo tolerance recorded in results_notes.json.
"""

from __future__ import annotations

import argparse
import json

import numpy as np


def _dist(X, i, j):
    return float(np.hypot(X[i][0] - X[j][0], X[i][1] - X[j][1]))


def claims(y2007, y2001):
    out = {}

    def tree_edge_mean(post):
        X = post["X"]; bt = post["best_tree"]
        lens = [_dist(X, i, s) for i, s in enumerate(bt) if s is not None and s != -1]
        return float(np.mean(lens))

    def span(post):
        X = np.array(post["X"])
        d = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
        return float(d.max())

    out["dist_ci_2007"] = [round(y2007["mean_distance"]["lo"], 1), round(y2007["mean_distance"]["hi"], 1)]
    out["dist_ci_2001"] = [round(y2001["mean_distance"]["lo"], 1), round(y2001["mean_distance"]["hi"], 1)]
    out["span_2007"] = round(span(y2007), 1)
    out["span_2001"] = round(span(y2001), 1)
    out["mean_edge_2007"] = round(tree_edge_mean(y2007), 1)
    out["mean_edge_2001"] = round(tree_edge_mean(y2001), 1)

    names = y2007["names"]
    i1 = names.index("IP1b"); i5 = names.index("IP5")
    out["ip5_ip1b_km"] = round(_dist(y2007["X"], i1, i5), 1)
    out["ip5_mean_latency"] = round(y2007["latency_median_per_premise"][i5], 1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("y2007"); ap.add_argument("y2001")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    c = claims(json.load(open(args.y2007)), json.load(open(args.y2001)))
    json.dump(c, open(args.out, "w"), indent=1)
    print(json.dumps(c, indent=1))


if __name__ == "__main__":
    main()
