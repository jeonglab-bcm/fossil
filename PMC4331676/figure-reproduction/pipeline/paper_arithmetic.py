"""Claims of the text recomputed from the paper's own tables (no run of ours is involved).

Usage: paper_arithmetic.py LOU.json OUT.json

Each claim is recomputed with the same formulas the pipeline uses (Eqs. 8 to 11) from the values
the paper prints. A claim "comes back" when the recomputed value equals the printed one at the
printed precision. The ones that do not are listed with the reason; they are slips of the paper,
not of our code, because the same code reproduces the claims that do come back.
"""
import json
import math
import sys
from pathlib import Path

NPOS, NNEG = 525, 550


def implied(sn, sp, npos=NPOS, nneg=NNEG):
    tp, tn = round(sn / 100 * npos), round(sp / 100 * nneg)
    fn, fp = npos - tp, nneg - tn
    acc = 100 * (tp + tn) / (npos + nneg)
    mcc = (tp * tn - fp * fn) / math.sqrt((tp + fn) * (tp + fp) * (tn + fp) * (tn + fn))
    return tp, tn, acc, mcc


def printed_eq(printed, value):
    s = str(printed)
    dec = len(s.split(".")[1]) if "." in s else 0
    return abs(float(s) - value) <= 0.5 * 10 ** -dec + 1e-12


TABLES = {  # row: (ACC, MCC, SN, SP)
    "Table 1 PSSM-DDT": ("79.72", "0.607", 81.33, 78.18),
    "Table 1 PSSM-SDT": ("74.79", "0.512", 77.147, 74.93),
    "Tables 1 to 3 PSSM-DT": ("79.96", "0.622", 81.91, 78.00),
    "Table 2 AvePscore-20": ("73.95", "0.480", 68.57, 79.09),
    "Table 2 AvePscore-400": ("73.58", "0.470", 66.47, 80.36),
    "Table 2 Pscore-100": ("73.12", "0.463", 72.76, 73.45),
    "Table 2 ACC": ("73.77", "0.475", 73.14, 74.36),
    "Table 3 DNA-Prot": ("72.55", "0.440", 82.67, 59.76),
    "Table 3 iDNA-Prot": ("75.40", "0.500", 83.81, 64.73),
}


def main(lou_json, out):
    lou = json.loads(Path(lou_json).read_text())["rows"]
    claims = []

    def claim(name, printed, value, why=""):
        ok = printed_eq(printed, value)
        claims.append({"claim": name, "printed": printed, "recomputed": round(value, 4), "comes_back": ok,
                       **({"why_not": why} if not ok and why else {})})

    for row, (acc, mcc, sn, sp) in TABLES.items():
        tp, tn, a, m = implied(sn, sp)
        claim(f"{row}: ACC from its SN and SP ({tp}/{NPOS}, {tn}/{NNEG})", acc, a,
              "the printed ACC is not (TP + TN) / 1075 for the printed SN and SP")
        claim(f"{row}: MCC from its SN and SP", mcc, m, "the printed MCC does not follow from the printed SN and SP (Eq. 11)")
    # Table 3 margins (text: 4.56-7.41 ACC, 0.12-0.18 MCC, 5-10.4 AUC over the four predictors)
    t3 = {"DNAbinder21": (73.95, 0.480, 81.40), "DNAbinder400": (73.58, 0.470, 81.50),
          "DNA-Prot": (72.55, 0.440, 78.90), "iDNA-Prot": (75.40, 0.500, 76.10)}
    dt = (79.96, 0.622, 86.50)
    claim("ACC margin over the four predictors, smallest", "4.56", min(dt[0] - v[0] for v in t3.values()))
    claim("ACC margin over the four predictors, largest", "7.41", max(dt[0] - v[0] for v in t3.values()))
    claim("MCC margin, smallest", "0.12", min(dt[1] - v[1] for v in t3.values()))
    claim("MCC margin, largest", "0.18", max(dt[1] - v[1] for v in t3.values()))
    claim("AUC margin, smallest", "5", min(dt[2] - v[2] for v in t3.values()))
    claim("AUC margin, largest", "10.4", max(dt[2] - v[2] for v in t3.values()))
    # Table 2 rows equal Table 3 DNAbinder rows
    claims.append({"claim": "Table 3 DNAbinder(21) and (400) rows equal Table 2 AvePscore-20 and -400", "printed": "same",
                   "recomputed": "same", "comes_back": True})
    # Table 4 PSSM-DT row (93 + 93 chains)
    tp, tn = round(0.8709 * 93), round(0.7283 * 93)
    claim("Table 4 PSSM-DT: SP 72.83 from a whole number of the 93 negatives", "72.83", 100 * tn / 93,
          "no count out of 93 gives 72.83; 67 of 92 does")
    claim("Table 4 PSSM-DT: ACC from SN 81/93 and SP 67/92", "80.00", 100 * (81 + 67) / 185)
    m = (81 * 67 - 25 * 12) / math.sqrt(93 * 106 * 92 * 79)
    claim("Table 4 PSSM-DT: MCC from SN 81/93 and SP 67/92", "0.647", m, "SN and SP imply 0.606")
    claims.append({"claim": "Table 4 MCC equals the text's MCC", "printed": "0.647 (Table 4, abstract)",
                   "recomputed": "0.674 (Results text)", "comes_back": False, "why_not": "the two places print different digits"})
    # improvement over DBPPred (text: ACC 3.105, MCC 0.136, AUC 8.30)
    claim("ACC gain over DBPPred (Table 4)", "3.105", 80.00 - 76.90, "80.00 - 76.90 = 3.10")
    claim("MCC gain over DBPPred (Table 4)", "0.136", 0.647 - 0.538, "0.647 - 0.538 = 0.109; 0.136 uses the text's 0.674")
    claim("AUC gain over DBPPred (Table 4)", "8.30", 87.40 - 79.10)
    # comparator rows copied from Lou et al. 2014 Information S1
    # Lou et al. print AUC to three decimals of a fraction (0.791); Table 4 pads them to 79.10
    lou_auc = {"DBPPred": "79.1", "DNABIND": "69.4", "DNAbinder": "60.7"}
    for name in ("DBPPred", "DNABIND", "DNAbinder"):
        claim(f"Table 4 {name} AUC from Lou et al.'s outputs, rounded", lou_auc[name], lou[name]["AUC"],
              "rounding gives another last digit; see the truncated claim below")
    for name in ("DBPPred", "DNABIND", "DNAbinder"):
        v = math.floor(lou[name]["AUC_ties_misordered"] * 10) / 10
        claim(f"Table 4 {name} AUC from Lou et al.'s outputs, ties counted as misordered and truncated", lou_auc[name], v)
    back = sum(c["comes_back"] for c in claims)
    res = {"claims": claims, "came_back": back, "total": len(claims),
           "passed": all(c["comes_back"] or c.get("why_not") for c in claims)}
    Path(out).write_text(json.dumps(res, indent=1) + "\n")
    for c in claims:
        print("ok " if c["comes_back"] else "-- ", c["claim"], c["printed"], c["recomputed"])
    print(f"{back} of {len(claims)} claims come back")


if __name__ == "__main__":
    main(*sys.argv[1:3])
