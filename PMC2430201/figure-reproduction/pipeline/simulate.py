"""Run the simulation study of Tables 3-8 with the package rommeta, and the variants that test the paper's
unstated choices.

Usage: simulate.py PUBLISHED_VALUES_JSON OUT_JSON [--reps N]

Every scenario of Tables 3-8 (6 tables x 18 rows x tau 0 and 0.5 = 216) with 10,000 replicates, as the
paper, from its own seed: [base, table, row, tau index], base 20080521 for the main run and 20080522 for
a second run that measures how far two runs of one design stray. Variants, on the main run's seeds
(so they share its sampling noise):

  het_experimental_only  heterogeneity as one shift of SD tau on the experimental mean only
  het_shared             the same shift on both means (the difference keeps no heterogeneity)
  skew_multiplicative    Table 6: the experimental arm is the control mixture times the true RoM
  skew_standardized      Table 6: the mixture rescaled to mean 100 and SD 40 exactly, then shifted
  draw_values            Table 3: every patient drawn, instead of each arm's mean and SD
  negative_drop_replicate  Table 5: a replicate with a non-positive mean is left out entirely
  sd_pool_literal        Table 4: the pooled SD with the Appendix's stray "- 1"
  no_hedges              Table 3: SMD without the small-sample correction

Extra scenarios: 1,000 patients per arm, k = 5, tau = 0.5, SD 40 (the Results' "results not shown").
"""
import json
import sys
import time

import rommeta
from rommeta import Scenario, run_scenario

MAIN, SECOND = 20080521, 20080522
TAUS = (0.0, 0.5)
VARIANTS = {
    "het_experimental_only": (("3", "4", "5", "7", "8"), {"heterogeneity": "experimental_only"}, (0.5,)),
    "het_shared": (("3", "4", "5", "7", "8"), {"heterogeneity": "shared"}, (0.5,)),
    "skew_multiplicative": (("6",), {"skew_shift": "multiplicative"}, TAUS),
    "skew_standardized": (("6",), {"skew_shift": "standardized"}, TAUS),
    "draw_values": (("3",), {"draw": "values"}, TAUS),
    "negative_drop_replicate": (("5",), {"negative": "drop_replicate"}, TAUS),
    "sd_pool_literal": (("4",), {"sd_pool_literal": True}, TAUS),
    "no_hedges": (("3",), {"small_sample_correction": False}, TAUS),
}


def scenario(t, row, tau):
    ne, nc = (int(x) for x in row["n"].split("/"))
    return Scenario(sd=t["sd"], effect=row["effect"], n_exp=ne, n_contr=nc, k=row["k"], tau=tau,
                    distribution=t["distribution"])


def run_tables(pub, base, reps, tables=None, taus=TAUS, **opts):
    out = {}
    for n, t in pub["tables"].items():
        if tables and n not in tables:
            continue
        rows = []
        for i, row in enumerate(t["rows"]):
            r = {"effect": row["effect"], "n": row["n"], "k": row["k"]}
            for j, tau in enumerate(TAUS):
                if tau in taus:
                    r[f"tau{tau:g}"] = run_scenario(scenario(t, row, tau), reps, seed=[base, int(n), i, j], **opts)
            rows.append(r)
        out[n] = rows
    return out


def main():
    args = sys.argv[1:]
    reps = 10_000
    if "--reps" in args:
        i = args.index("--reps")
        reps = int(args[i + 1])
        del args[i:i + 2]
    pub_path, out_path = args
    pub = json.load(open(pub_path))
    t0 = time.time()
    doc = {"about": "Performance of MD, SMD and RoM per scenario (rommeta.summarize; percentages). "
                    "runs.main is our result; runs.second the same design with other seeds; variants test unstated choices.",
           "rommeta": rommeta.__version__, "replicates": reps, "seeds": {"main": MAIN, "second": SECOND},
           "runs": {"main": run_tables(pub, MAIN, reps), "second": run_tables(pub, SECOND, reps)}, "variants": {}}
    print(f"main and second runs: {time.time() - t0:.0f} s", file=sys.stderr)
    for name, (tables, opts, taus) in VARIANTS.items():
        doc["variants"][name] = {"tables": list(tables), "options": opts,
                                 "runs": run_tables(pub, MAIN, reps, tables=tables, taus=taus, **opts)}
        print(f"variant {name}: {time.time() - t0:.0f} s", file=sys.stderr)
    doc["extra"] = {"n1000": [
        {"effect": e, "n": "1000/1000", "k": 5, "tau": 0.5, "sd": 40,
         "result": run_scenario(Scenario(sd=40, effect=e, n_exp=1000, n_contr=1000, k=5, tau=0.5), reps, seed=[MAIN, 1000, i])}
        for i, e in enumerate((0.2, 0.5, 0.8))]}
    json.dump(doc, open(out_path, "w"), indent=1)
    open(out_path, "a").write("\n")
    print(f"{out_path}: {time.time() - t0:.0f} s", file=sys.stderr)


if __name__ == "__main__":
    main()
