"""Command line.

  oisim cumulative TRIALS.csv [-o OUT.csv]       cumulative DerSimonian-Laird meta-analysis of your trials
  oisim ois --pc 0.10 --rrr 0.20 [--i2 0.25] [--beta 0.10] [--alpha 0.05]
                                                 optimal information size (patients and events)
  oisim simulate --sizes cochrane --pc 5-15 --tau2 0.15 --rrr 0 [--n-meta 2000] [--seed 1]
                                                 [--width-patients 500] [--width-events 50] [-o OUT.json]
                                                 probability of overestimation and the numbers required
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__, example_path
from .core import PC_RANGES, SIZE_DISTRIBUTIONS, Scenario, format_required, ois, overestimation_curve, required_table, round_ois, simulate
from .io import cumulative, read_trials, write_cumulative


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="oisim", description="Risk of overestimation in cumulative meta-analysis, "
                                 "and the optimal information size (Thorlund et al. 2011).")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--example-path", action="store_true", help="print the path of the bundled example input and exit")
    sub = ap.add_subparsers(dest="command")

    c = sub.add_parser("cumulative", help="cumulative random-effects meta-analysis of a CSV of trials")
    c.add_argument("input", help="CSV: trial, events_treatment, n_treatment, events_control, n_control")
    c.add_argument("-o", "--output", help="output CSV (default: standard output)")
    c.add_argument("--zero", default="exclude_double", choices=("exclude_double", "correct_all"))

    o = sub.add_parser("ois", help="optimal information size")
    o.add_argument("--pc", type=float, required=True, help="control-group risk (proportion)")
    o.add_argument("--rrr", type=float, required=True, help="relative risk reduction to detect (proportion)")
    o.add_argument("--i2", type=float, default=0.0, help="heterogeneity correction I^2 (proportion)")
    o.add_argument("--alpha", type=float, default=0.05)
    o.add_argument("--beta", type=float, default=0.20)

    s = sub.add_parser("simulate", help="simulate a scenario and read off the numbers required")
    s.add_argument("--sizes", default="cochrane", choices=sorted(SIZE_DISTRIBUTIONS))
    s.add_argument("--pc", default="5-15", choices=sorted(PC_RANGES))
    s.add_argument("--tau2", type=float, default=0.15)
    s.add_argument("--rrr", type=float, default=0.0, help="true relative risk reduction (proportion)")
    s.add_argument("--n-meta", type=int, default=2000)
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--width-patients", type=int, default=500)
    s.add_argument("--width-events", type=int, default=50)
    s.add_argument("-o", "--output", help="output JSON (default: standard output)")

    args = ap.parse_args(argv)
    if args.example_path:
        print(example_path())
        return 0
    if args.command == "cumulative":
        rows = cumulative(read_trials(args.input), zero=args.zero)
        if args.output:
            with open(args.output, "w", newline="", encoding="utf-8") as f:
                write_cumulative(rows, f)
        else:
            write_cumulative(rows, sys.stdout)
        return 0
    if args.command == "ois":
        r = ois(args.pc, args.rrr, args.i2, args.alpha, args.beta)
        r.update({f"{k}_rounded": v for k, v in round_ois(r["patients"], r["events"], args.pc).items()})
        print(json.dumps(r, indent=1))
        return 0
    if args.command == "simulate":
        sim = simulate(Scenario(args.sizes, args.pc, args.tau2, args.rrr, n_meta=args.n_meta), seed=args.seed)
        rows = required_table(sim, patient_width=args.width_patients, event_width=args.width_events)
        for r in rows:
            for k in list(r):
                if k != "threshold":
                    r[k] = format_required(r[k], 50000 if k.startswith("patients") else 5000)
        curves = {}
        for th in (0.30, 0.20):
            cur = overestimation_curve(sim.cum_patients, sim.rrr(), th, args.width_patients, 50000)
            curves[f"rrr_above_{int(th * 100)}"] = {"patients": cur["x"].astype(int).tolist(),
                                                    "proportion": [None if p != p else round(float(p), 6) for p in cur["p"]]}
        doc = {"scenario": vars(sim.scenario), "required": rows, "curves_patients": curves}
        text = json.dumps(doc, indent=1)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(text + "\n")
        else:
            print(text)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
