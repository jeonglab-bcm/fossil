#!/usr/bin/env python3
"""Human proteome scan on our sample (sample_proteome.py), Figs 8 and 9 and the text's examples.

The SPCH-SVM is trained on the full data set (all chains of the five CV folds) with the paper's
parameters. Candidates in a human protein are its C and H residues whose profile relative weight
is at least 0.015 (the paper's filter on the training residues). A protein is zinc-binding when at
least three residues have gated probability above 0.7.

The proteome total is estimated from the stratified sample: sum over strata of the stratum size
times the share called in it, with a binomial standard error.

It also reads two structures released after the paper: 5ZLQ (CZIB, the protein of Fig. 8) and
2HD5 (USP2, a UBP-family protease, the family of Fig. 9), and checks their zinc ligands.

Usage: scan_proteome.py CANDIDATES_DIR HUMAN_PROFILES_NPZ SAMPLE_TSV DOWNLOADS_DIR OUT_DIR
(CANDIDATES_DIR holds candidates.tsv and profiles.npz from run_svm.py prepare; DOWNLOADS_DIR holds
5zlq.cif.gz and 2hd5.cif.gz)
"""
import csv
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import spsvm

MIN_WEIGHT = 0.015
FIG8 = {"protein": "NP_060357.1", "residues": {"Cys31": 33, "Cys34": 36, "Cys65": 67, "Cys68": 70},
        "published": {"Cys31": "0.90", "Cys34": "0.98", "Cys65": "0.67", "Cys68": "0.82"}}
FIG9 = {"protein": "XP_374396.2", "residues": {"Cys140": 372, "Cys143": 375, "Cys187": 419, "Cys190": 422},
        "published": {"Cys140": "0.99", "Cys143": "0.99", "Cys187": "0.99", "Cys190": "0.99"}}
USP_MOTIF = re.compile(r"(?=(C..C.{43,50}C..C))")
ADAMTS_MOTIF = re.compile(r"(?=(H...H.....H))")


DONORS = {"SG", "ND1", "NE2", "OD1", "OD2", "OE1", "OE2"}


def zinc_ligands(path):
    """Side-chain donors within 3 A of each zinc ion: [[(chain, residue number, name), ...], ...]."""
    import gemmi

    m = gemmi.read_structure(str(path))[0]
    sites = []
    for c in m:
        for r in c:
            for z in r:
                if z.element.name == "Zn":
                    sites.append(sorted((c2.name, res.seqid.num, res.name) for c2 in m for res in c2 for a in res
                                        if a.name in DONORS and a.pos.dist(z.pos) <= 3.0))
    return sites


def later_structures(dl):
    cz = zinc_ligands(Path(dl) / "5zlq.cif.gz")
    pos = sorted({n for site in cz for _, n, _ in site})
    czib = {"passed": pos == [33, 36, 67, 70],
            "detail": f"5ZLQ (2018) binds zinc with Cys{', Cys'.join(map(str, pos))} of NP_060357.1, the paper's Cys31, Cys34, Cys65 and Cys68 (CX2CX30C), Cys65 included"}
    us = zinc_ligands(Path(dl) / "2hd5.cif.gz")
    nums = sorted(n for _, n, name in us[0] if name == "CYS") if us else []
    gaps = [b - a - 1 for a, b in zip(nums, nums[1:])]
    usp = {"passed": len(nums) == 4 and gaps[0] == 2 and 43 <= gaps[1] <= 50 and gaps[2] == 2,
           "detail": f"2HD5 (USP2, 2006) binds zinc with Cys{', Cys'.join(map(str, nums))}: a CX{gaps[0] if gaps else '?'}CX{gaps[1] if len(gaps) > 1 else '?'}CX{gaps[2] if len(gaps) > 2 else '?'}C site, as predicted for the UBP family"}
    return {"czib": czib, "usp": usp}


def estimate(sample, called):
    """Stratified estimate of the number of zinc proteins in the 27,960 of Build 35.1."""
    strata = defaultdict(lambda: {"n": 0, "called": 0, "size": 0})
    for r in sample:
        if r["group"].startswith("sample:"):
            s = strata[r["flags"]]
            s["n"] += 1
            s["called"] += called[r["protein"]]
            s["size"] = int(r["stratum_size"])
    total = var = 0.0
    for s in strata.values():
        p = s["called"] / s["n"]
        total += s["size"] * p
        var += s["size"] ** 2 * p * (1 - p) / s["n"]
    est = {"strata": dict(strata), "estimated_zinc_proteins": round(total), "standard_error": round(math.sqrt(var)),
           # agreement with the published calls (column 3 of Additional file 3) in the sample
           "published_called_share_ours": {k: round(v["called"] / v["n"], 3) for k, v in strata.items()}}
    # Previously identified (column 2 = X) proteins not confirmed: X/X called "-" plus X/- called "-".
    prev = [k for k in strata if k.startswith("X/")]
    est["previously_identified_not_confirmed"] = round(sum(strata[k]["size"] * (1 - strata[k]["called"] / strata[k]["n"]) for k in prev))
    est["new_predictions"] = round(sum(strata[k]["size"] * strata[k]["called"] / strata[k]["n"] for k in strata if not k.startswith("X/")))

    return est


def main(cand_dir, human_npz, sample_tsv, dl, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    profiles = spsvm.read_profiles(Path(cand_dir) / "profiles.npz")
    cands = defaultdict(dict)
    folds = {}
    for r in csv.DictReader(open(Path(cand_dir) / "candidates.tsv"), delimiter="\t"):
        if r["variant"] == "CH" and r["set"] == "cv":
            cands[r["chain"]][int(r["pos"])] = int(r["label"])
            folds[r["chain"]] = r["fold"]
    train = [spsvm.Chain(c, profiles[c].sequence, spsvm.descriptors(profiles[c]), cands[c]) for c in sorted(cands)]
    model = spsvm.SPSVM("CH").fit(train)

    # Sensitivity (a hypothesis test, not agreement): Platt constants refitted to the held-out
    # margins of our profiles over the paper's five CV folds, in place of those of Additional file 1.
    lm, ly, sm, sy = [], [], [], []
    for k in "01234":
        m = spsvm.SPSVM("CH").fit([c for c in train if folds[c.name] != k])
        for c in train:
            if folds[c.name] != k:
                continue
            loc, sp = m.margins(c)
            for p, f in loc.items():
                lm.append(f)
                ly.append(c.candidates[p])
            for (i, j), f in sp.items():
                sm.append(f)
                sy.append(1 if (c.candidates[i] and c.candidates[j]) else 0)
    la, lb = spsvm.fit_platt(lm, ly)
    sa, sb = spsvm.fit_platt(sm, sy)
    refit = {"local": dict(model.params["local"], A=la, B=lb), "semipattern": dict(model.params["semipattern"], A=sa, B=sb)}

    human = spsvm.read_profiles(human_npz)
    sample = list(csv.DictReader(open(sample_tsv), delimiter="\t"))
    called, probs, called_refit, probs_refit = {}, {}, {}, {}
    for r in sample:
        n = r["protein"]
        ch = spsvm.chain_from_profile(n, human[n], residues="CH", min_weight=MIN_WEIGHT)
        loc, sp = model.margins(ch)
        pr = spsvm.gate(loc, sp, model.params)
        probs[n] = pr
        called[n] = spsvm.predict_protein(pr, 0.7, 3)
        probs_refit[n] = spsvm.gate(loc, sp, refit)
        called_refit[n] = spsvm.predict_protein(probs_refit[n], 0.7, 3)
    with open(out / "human_predictions.tsv", "w") as f:
        f.write("protein\tgroup\tflags\tcalled\tresidues_above_0.7\n")
        for r in sample:
            n = r["protein"]
            f.write(f"{n}\t{r['group']}\t{r['flags']}\t{int(called[n])}\t{sum(v['gated'] > 0.7 for v in probs[n].values())}\n")

    est = estimate(sample, called)
    sens = {"platt": {"local": [round(la, 4), round(lb, 4)], "semipattern": [round(sa, 4), round(sb, 4)],
                      "paper_local": [model.params["local"]["A"], model.params["local"]["B"]],
                      "paper_semipattern": [model.params["semipattern"]["A"], model.params["semipattern"]["B"]]},
            "proteome": estimate(sample, called_refit),
            "fig8": {k: round(probs_refit[FIG8["protein"]][p - 1]["gated"], 2) for k, p in FIG8["residues"].items()},
            "fig9": {k: round(probs_refit[FIG9["protein"]][p - 1]["gated"], 2) for k, p in FIG9["residues"].items()}}

    def fig(spec):
        pr = probs[spec["protein"]]
        return {k: {"position": p, "ours": round(pr[p - 1]["gated"], 2) if (p - 1) in pr else None,
                    "published": spec["published"][k]} for k, p in spec["residues"].items()}

    # USP family: proteins with a CX2CX(43-50)CX2C motif whose four cysteines are all above 0.7.
    usp = [r["protein"] for r in sample if r["group"] == "family:USP" or (r["protein"] == FIG9["protein"])]
    usp_hit = []
    for n in usp:
        seq = human[n].sequence
        for m in USP_MOTIF.finditer(seq):
            s = m.start()
            g = m.group(1)
            pos = [s, s + 3, s + len(g) - 4, s + len(g) - 1]
            if all(probs[n].get(p, {"gated": 0})["gated"] > 0.7 for p in pos):
                usp_hit.append(n)
                break
    adam = [r["protein"] for r in sample if r["group"] == "family:ADAMTS"]
    third, first_two = [], 0
    for n in adam:
        seq = human[n].sequence
        for m in ADAMTS_MOTIF.finditer(seq):
            s = m.start()
            pos = [s, s + 4, s + 10]
            if all(p in probs[n] for p in pos):
                v = [probs[n][p]["gated"] for p in pos]
                first_two += v[0] > 0.7 and v[1] > 0.7
                third.append(v[2])
                break
    res = {"proteome": est, "fig8": fig(FIG8), "fig9": fig(FIG9),
           "usp": {"proteins": len(usp), "with_predicted_cx2cx43_50cx2c": len(usp_hit), "called": sum(called[n] for n in usp)},
           "adamts": {"proteins": len(adam), "with_motif": len(third), "first_two_h_above_0.7": first_two,
                      "third_h_mean": round(sum(third) / len(third), 2) if third else None},
           "fig8_top4": sorted(p + 1 for p in sorted(probs[FIG8["protein"]], key=lambda q: -probs[FIG8["protein"]][q]["gated"])[:4]),
           "fig8_called": called[FIG8["protein"]], "fig9_called": called[FIG9["protein"]],
           "later": later_structures(dl),
           "sensitivity_platt_refit": sens}
    json.dump(res, open(out / "proteome.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:6])
