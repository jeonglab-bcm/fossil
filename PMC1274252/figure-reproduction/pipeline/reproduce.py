"""Every number of the reproduction except the figure renders.

  reproduce.py DOWNLOADS T1DIR WEKADIR PUBLISHED_VALUES OUT.json [--quick]

DOWNLOADS  the fetched inputs (fetch_inputs.sh): the three 2006 ARFFs, dump.tab, Additional File 1
T1DIR      the same sets restricted to Table 1's features (prepare.py)
WEKADIR    Weka 3.4.3's run of the download page's recipe (WekaRun.java): main/ and table1/
--quick    skip the cross-validations of the 10- and 20-rule trees (CI runs them; a few minutes)

The method comes from the package prospectr_adtree: the ADTree port for the retrained trees, the
published Figure 2 tree for PROSPECTR's own scores. The port is checked against Weka here.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import prospectr_adtree as pa
from prospectr_adtree.prospectr import FEATURE_GROUPS

SETS = {"training": "omim_trainingset.arff", "hgmd": "hgmd_testset.arff", "oligogenic": "pocus_testset.arff"}
T1SETS = {"training": "table1_training.arff", "hgmd": "table1_hgmd.arff", "oligogenic": "table1_pocus.arff"}
WEKA_SET = {"training": "training", "hgmd": "hgmd", "oligogenic": "pocus"}


def pct(x):
    return 100.0 * x


def fmt(x, nd):
    return f"{x:.{nd}f}"


def classes(d):
    return [int(r[d.class_index]) for r in d.rows]


# ---- retrained trees (the download page's recipe) ----------------------------------------------
def run_tree(train, tests, iterations=15, cv=True):
    model = pa.ADTree(iterations, "zpure").fit(train)
    out = {"tree": model.to_weka_string(), "splitters": [], "sets": {}}
    for s in model.splitters():
        out["splitters"].append({"order": s.order, "attribute": s.attribute, "split": s.split,
                                 "nominal": s.nominal,
                                 "values": [s.children[0].value, s.children[1].value],
                                 "branches": [s.comparison(0), s.comparison(1)]})
    out["parents"] = _parents(model)
    for name, d in [("training", train)] + list(tests.items()):
        sc = model.scores(d)
        out["sets"][name] = pa.evaluate(classes(d), sc) | {"scores": sc}
    if cv:
        rows = pa.cross_validate(train, iterations, "zpure", 10, 1)
        rows.sort(key=lambda r: r["index"])
        ev = pa.evaluate([r["class"] for r in rows], [r["score"] for r in rows])
        out["sets"]["cv10"] = ev | {"scores": [r["score"] for r in rows], "folds": [r["fold"] for r in rows]}
    return model, out


def _parents(model):
    """order of each splitter -> (order of the splitter above it, branch), or None at the root."""
    res = {}

    def walk(node, parent):
        for s in node.children:
            res[s.order] = parent
            for b, c in enumerate(s.children):
                walk(c, (s.order, b))
    walk(model.root, None)
    return res


# ---- the port against Weka ---------------------------------------------------------------------
def read_weka(dirpath):
    d = Path(dirpath)
    tree = (d / "tree.txt").read_text()
    tree = tree[tree.index("Alternating"):].strip()
    scores = {}
    for name in ("training", "hgmd", "pocus", "cv"):
        with open(d / f"scores_{name}.tsv") as f:
            scores[name] = {int(r["index"]): (int(r["fold"]), float(r["score"])) for r in csv.DictReader(f, delimiter="\t")}
    return tree, scores, json.load(open(d / "weka.json"))


def port_check(run, weka_dir, label):
    tree, scores, wj = read_weka(weka_dir)
    res = {"label": label, "tree_identical": run["tree"].strip() == tree}
    worst = 0.0
    folds_equal = True
    for ours, theirs in (("training", "training"), ("hgmd", "hgmd"), ("oligogenic", "pocus"), ("cv10", "cv")):
        sc = run["sets"][ours]["scores"]
        w = scores[theirs]
        worst = max(worst, max(abs(w[i][1] - s) for i, s in enumerate(sc)))
        if ours == "cv10":
            folds_equal = all(w[i][0] == f for i, f in enumerate(run["sets"]["cv10"]["folds"]))
    stats_equal = True
    for ours, theirs in (("training", "training"), ("hgmd", "hgmd"), ("oligogenic", "pocus"), ("cv10", "cv10")):
        for k in ("pct_correct", "kappa", "precision_disease", "recall_disease", "auc_disease"):
            if abs(run["sets"][ours][k] - wj[theirs][k]) > 1e-12:
                stats_equal = False
    res.update({"max_abs_score_diff": worst, "cv_folds_identical": folds_equal, "statistics_identical": stats_equal})
    res["passed"] = res["tree_identical"] and worst <= 1e-12 and folds_equal and stats_equal
    return res


# ---- comparisons ---------------------------------------------------------------------------------
def table3_fields(ev, pub, rates=None):
    f = [
        {"name": "accuracy (%)", "expected": pub["accuracy"], "observed": round(ev["pct_correct"], 4)},
        {"name": "precision (%)", "expected": pub["precision"], "observed": round(pct(ev["precision_disease"]), 4)},
        {"name": "recall (%)", "expected": pub["recall"], "observed": round(pct(ev["recall_disease"]), 4)},
        {"name": "AUC", "expected": pub["auc"], "observed": round(ev["auc_disease"], 6)},
        {"name": "kappa", "expected": pub["kappa"], "observed": round(ev["kappa"], 6)},
    ]
    if rates:
        f.append({"name": "text: controls called disease (%)", "expected": rates["fp_rate"],
                  "observed": round(pct(ev["fp_rate_disease"]), 4)})
        if "tp" in rates:
            f.append({"name": "text: disease genes found (n)", "expected": rates["tp"], "observed": ev["confusion"][0][0]})
            f.append({"name": "text: controls called disease (n)", "expected": rates["fp"], "observed": ev["confusion"][1][0]})
    return f


FIG2_MAP = {  # Figure 2 feature -> archived ARFF attribute
    "mouse_identity": "mouse_identity", "signal_peptide": "sigpep", "exons": "exons", "gene_length": "gene_length",
    "paralog_identity": "paralog_identity", "rat_identity": "rat_identity", "utr3_length": "len_3utr",
    "cds_length": "cds_length", "mouse_ka": "mouse_dn", "worm_identity": "worm_identity", "gc": "gc",
}


def fig2_fields(run, published):
    """Each published rule against the retrained tree: is there a rule on the same feature in the same
    place (at the root, or under the same parent rule), and with what threshold and values?"""
    nodes = {n["id"]: n for n in published["nodes"]}
    ours = run["splitters"]
    parents = run["parents"]
    by_order = {s["order"]: s for s in ours}
    matched = {}
    fields = []
    for n in sorted(published["nodes"], key=lambda n: n["id"]):
        att = FIG2_MAP[n["feature"]]
        parent = matched.get(n["parent"]) if n["parent"] else None
        cands = []
        for s in ours:
            if s["attribute"] != att or s["order"] in matched.values():
                continue
            p = parents[s["order"]]
            if n["parent"] is None and p is None:
                cands.append(s)
            elif n["parent"] is not None and p is not None and parent is not None and p[0] == parent and p[1] == 1:
                cands.append(s)
        s = None
        if cands:
            if n["op"] == "==":
                s = cands[0]
            else:
                s = min(cands, key=lambda c: abs(c["split"] - n["threshold"]))
        if s:
            matched[n["id"]] = s["order"]
        lab = f"rule {n['id']} ({n['label']})"
        fields.append({"name": f"{lab}: feature in the same place", "expected": "yes", "observed": "yes" if s else "no"})
        if n["op"] == "==":
            thr_obs = "sigpep" if s else "absent"
            no_v, yes_v = (s["values"][0], s["values"][1]) if s else (None, None)
        else:
            # Weka's cut x >= c on whole counts is x > c - 0.5 (31.5 is "> 31")
            thr_obs = round(s["split"] - (0.5 if n["op"] == ">" else 0.0), 3) if s else "absent"
            no_v, yes_v = (s["values"][0], s["values"][1]) if s else (None, None)
            fields.append({"name": f"{lab}: threshold", "expected": _num(n["threshold"]), "observed": thr_obs})
        fields.append({"name": f"{lab}: value if no", "expected": _num(n["no"]),
                       "observed": round(no_v, 3) if no_v is not None else "absent"})
        fields.append({"name": f"{lab}: value if yes", "expected": _num(n["yes"]),
                       "observed": round(yes_v, 3) if yes_v is not None else "absent"})
    return fields, matched


def _num(x):
    s = repr(float(x))
    return s[:-2] if s.endswith(".0") else s


def fig2_tree_on(d, paralog_zero_unknown=True):
    tree = pa.published_tree()
    genes = [pa.features_from_prospectr_arff(r, paralog_zero_unknown) for r in d.as_dicts()]
    sc = [pa.score(g, tree) for g in genes]
    return genes, sc, pa.evaluate(classes(d), sc)


def table4(genes, cls, scores, which, by):
    if which == "disease":
        sel = [g for g, c in zip(genes, cls) if c == 0]
    elif which == "predicted":
        sel = [g for g, s in zip(genes, scores) if pa.evaluation.predict(s) == 0]
    else:
        sel = genes
    return pa.average_contributions(sel, by=by)


def table4_fields(avg, pub):
    return [{"name": f"{FEATURE_GROUPS[k]} (%)", "expected": v, "observed": round(100 * avg.get(k, 0.0), 3)}
            for k, v in pub.items()]


# ---- Table 2, Figure 1, correlations --------------------------------------------------------------
def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def table2(train, pub):
    from scipy.stats import chi2_contingency, mannwhitneyu
    lab = train.labels()
    rows = {"gene_length_kb": ("gene_length", 1e-3), "cdna_length_bp": ("cdna_length", 1),
            "protein_length_aa": ("residue_length", 1), "utr3_length_bp": ("len_3utr", 1),
            "exons": ("exons", 1), "mouse_brh_identity_pct": ("mouse_identity", 1)}
    fields, detail = [], {}
    for key, (att, scale) in rows.items():
        col = train.column(att)
        dis = [v * scale for v, l in zip(col, lab) if l == "disease" and v is not None]
        nor = [v * scale for v, l in zip(col, lab) if l == "normal" and v is not None]
        p = mannwhitneyu(nor, dis, alternative="two-sided").pvalue
        md, mn = median(dis), median(nor)
        detail[key] = {"control_median": mn, "disease_median": md, "p": p, "n_control": len(nor), "n_disease": len(dis)}
        P = pub[key]
        fields += [{"name": f"{key}: control median", "expected": P["control"], "observed": round(mn, 3)},
                   {"name": f"{key}: disease median", "expected": P["disease"], "observed": round(md, 3)},
                   {"name": f"{key}: P < {P['p_bound']}", "expected": "yes", "observed": "yes" if p < P["p_bound"] else "no"}]
    sig = train.column("sigpep")
    dis = [v for v, l in zip(sig, lab) if l == "disease"]
    nor = [v for v, l in zip(sig, lab) if l == "normal"]
    tab = [[sum(1 for v in nor if v == 1), sum(1 for v in nor if v == 0)],
           [sum(1 for v in dis if v == 1), sum(1 for v in dis if v == 0)]]
    p = chi2_contingency(tab, correction=False).pvalue
    P = pub["signal_peptide_pct"]
    detail["signal_peptide_pct"] = {"control": 100 * tab[0][0] / len(nor), "disease": 100 * tab[1][0] / len(dis), "p": p}
    fields += [{"name": "signal_peptide_pct: control", "expected": P["control"], "observed": round(100 * tab[0][0] / len(nor), 3)},
               {"name": "signal_peptide_pct: disease", "expected": P["disease"], "observed": round(100 * tab[1][0] / len(dis), 3)},
               {"name": f"signal_peptide_pct: P < {P['p_bound']}", "expected": "yes", "observed": "yes" if p < P["p_bound"] else "no"}]
    # sensitivity: mouse identity without the genes that have no mouse homolog (0)
    col = train.column("mouse_identity")
    detail["mouse_brh_identity_pct_without_zeros"] = {
        "control_median": median([v for v, l in zip(col, lab) if l == "normal" and v]),
        "disease_median": median([v for v, l in zip(col, lab) if l == "disease" and v])}
    return fields, detail


def fig1_hist(values, cap, mode="overflow"):
    """Ten bars of width cap/10 from 0, each (lo, hi]; 'overflow': the tenth bar holds everything above
    the ninth edge; 'within': only (9w, 10w], larger values left out; 'gap': the tenth bar holds values
    above the cap and (9w, 10w] is left out (the labels read literally)."""
    w = cap / 10.0
    vals = [v for v in values if v is not None]
    counts = [0] * 10
    for v in vals:
        k = max(0, math.ceil(v / w - 1e-9) - 1)
        if mode == "overflow":
            k = min(k, 9)
        elif mode == "within":
            if k > 9:
                continue
        elif mode == "gap":
            if k == 9:
                continue
            k = min(k, 9)
        counts[k] += 1
    return [100.0 * c / len(vals) for c in counts]


def fig1(train, pub):
    lab = train.labels()
    out = {}
    for panel, P in pub.items():
        if panel.startswith("_"):
            continue
        col = train.column(P["feature"])
        res = {"labels": P["labels"], "variants": {}}
        for mode in ("overflow", "within", "gap"):
            res["variants"][mode] = {cls: fig1_hist([v for v, l in zip(col, lab) if l == cls], P["cap"], mode)
                                     for cls in ("disease", "normal")}
        ours = res["variants"]["overflow"]
        fields = []
        for cls in ("disease", "normal"):
            for i, (e, o) in enumerate(zip(P[cls], ours[cls])):
                if e is None:
                    continue
                fields.append({"name": f"{cls}, bar {P['labels'][i]}", "expected": e, "observed": math.floor(o + 1e-9)})
        res["fields"] = fields
        # matches under each binning and rounding rule, for the cause
        res["sensitivity"] = {}
        for mode, h in res["variants"].items():
            for rule, fn in (("truncate", lambda x: math.floor(x + 1e-9)), ("round", lambda x: math.floor(x + 0.5))):
                hits = sum(1 for cls in ("disease", "normal") for e, o in zip(P[cls], h[cls])
                           if e is not None and int(e) == fn(o))
                res["sensitivity"][f"{mode}/{rule}"] = hits
        res["n_fields"] = len(fields)
        out[panel] = res
    return out


def spearman(train):
    from scipy.stats import spearmanr
    g = train.column("gene_length")
    res = {}
    for att, key in (("exons", "exons"), ("len_3utr", "utr3_length")):
        x = [(a, b) for a, b in zip(g, train.column(att)) if a is not None and b is not None]
        res[key] = spearmanr([a for a, _ in x], [b for _, b in x]).statistic
    return res


# ---- the authors' genome-wide scores --------------------------------------------------------------
def read_dump(path):
    with open(path) as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_af1(path):
    import xlrd
    book = xlrd.open_workbook(str(path))
    sh = book.sheet_by_index(0)
    head = [str(c.value).strip() for c in sh.row(0)]
    rows = []
    for i in range(1, sh.nrows):
        r = {h: sh.cell_value(i, j) for j, h in enumerate(head)}
        if str(r.get("Symbol", "")).strip():
            rows.append(r)
    return rows


def genome(dump_path, af1_path, pub):
    dump = read_dump(dump_path)
    raw = [float(r["Raw_score"]) for r in dump]
    norm = [float(r["Normalized_score"]) for r in dump]
    err_e = max(abs(1 / (1 + math.exp(a)) - n) for a, n in zip(raw, norm))
    gamma = 0.5772156649015329
    err_g = max(abs(1 / (1 + gamma ** a) - n) for a, n in zip(raw, norm))
    af1 = read_af1(af1_path)
    af_scores = [float(r["Score"]) for r in af1]
    af_raw = [math.log(1 / s - 1) for s in af_scores]
    af_raw_3dp = max(abs(a - round(a, 3)) for a in af_raw)
    by_id = {r["Gene_stable_id"]: r for r in dump}
    in_dump = [by_id.get(str(r["Ensembl gene ID"]).strip()) for r in af1]
    af_in_dump = [float(d["Normalized_score"]) for d in in_dump if d]
    candidates = sum(1 for r in af1 if str(r.get("Possible role in disease", "")).strip())
    n_known = sum(1 for r in dump if r["Is_known"] == "1")
    res = {
        "dump_genes": len(dump), "dump_known": n_known,
        "dump_over_075": sum(1 for n in norm if n > 0.75),
        "dump_under_03": sum(1 for n in norm if n < 0.3),
        "dump_known_over_075": sum(1 for r, n in zip(dump, norm) if n > 0.75 and r["Is_known"] == "1"),
        "dump_known_under_03": sum(1 for r, n in zip(dump, norm) if n < 0.3 and r["Is_known"] == "1"),
        "dump_called_disease_pct": 100.0 * sum(1 for a in raw if a <= 0) / len(raw),
        "normalisation_max_err_e": err_e, "normalisation_max_err_euler_mascheroni": err_g,
        "af1_genes": len(af1), "af1_min_score": min(af_scores), "af1_candidates": candidates,
        "af1_raw_scores_on_3dp_grid_max_err": af_raw_3dp,
        "af1_in_dump": len(af_in_dump), "af1_over_075_in_dump": sum(1 for s in af_in_dump if s > 0.75),
        "af1_max_in_dump": max(af_in_dump) if af_in_dump else None,
        "dump_max_raw": max(raw), "dump_min_raw": min(raw),
    }
    W = pub["whole_genome"]
    fields = [
        {"name": "genes scoring over 0.75", "expected": W["over_075"], "observed": res["dump_over_075"]},
        {"name": "genes scoring under 0.3", "expected": W["under_03"], "observed": res["dump_under_03"]},
        {"name": "Additional File 1 genes that score over 0.75 in dump.tab", "expected": W["af1_genes"],
         "observed": res["af1_over_075_in_dump"]},
    ]
    return res, fields


# ---- the paper's arithmetic -----------------------------------------------------------------------
def arithmetic(pub):
    """Claims recomputed from the paper's own numbers. Percentages: the paper truncates."""
    T, R = pub["table3"], pub["text_rates"]
    claims = []

    def claim(name, expected, observed, ok=None):
        if ok is None:
            ok = _same(expected, observed)
        claims.append({"claim": name, "expected": expected, "observed": observed, "follows": bool(ok)})

    for s in ("training", "cv10", "hgmd", "oligogenic"):
        rec, fpr = float(R[s]["recall"]) / 100, float(R[s]["fp_rate"]) / 100
        if s in ("hgmd", "oligogenic"):
            n = R[s]["n_disease"]
            tp, fp = int(R[s]["tp"]), int(R[s]["fp"])
            rec_c, fpr_c = tp / n, fp / n
            claim(f"{s}: {R[s]['tp']} of {n} disease genes = {R[s]['recall']}%", R[s]["recall"], round(100 * rec_c, 2),
                  _close_any(R[s]["recall"], 100 * rec_c))
            claim(f"{s}: {R[s]['fp']} of {n} controls = {R[s]['fp_rate']}%", R[s]["fp_rate"], round(100 * fpr_c, 2),
                  _close_any(R[s]["fp_rate"], 100 * fpr_c))
            acc = (tp + n - fp) / (2 * n)
            prec = tp / (tp + fp)
        else:
            acc = (rec + 1 - fpr) / 2
            prec = rec / (rec + fpr)
        kap = 2 * acc - 1
        claim(f"Table 3 {s}: accuracy from the text's rates", T[s]["accuracy"], _trunc(100 * acc, T[s]["accuracy"]),
              _close_any(T[s]["accuracy"], 100 * acc))
        claim(f"Table 3 {s}: precision from the text's rates", T[s]["precision"], _trunc(100 * prec),
              _close_any(T[s]["precision"], 100 * prec))
        claim(f"Table 3 {s}: recall = the text's recall", T[s]["recall"], R[s]["recall"])
        claim(f"Table 3 {s}: kappa from the text's rates (balanced sets)", T[s]["kappa"], round(kap, 2),
              _close_any(T[s]["kappa"], kap))
    L = pub["lopez_bigas"]
    claim("Lopez-Bigas: 189 of 260 = 72%", L["prospectr_pct"], round(100 * 189 / 260, 2), _close_any(L["prospectr_pct"], 100 * 189 / 260))
    claim("Lopez-Bigas: 123 of 260 = 47%", L["lb_pct"], round(100 * 123 / 260, 2), _close_any(L["lb_pct"], 100 * 123 / 260))
    k_p = _kappa_balanced(189 / 260, 0.44)
    k_l = _kappa_balanced(123 / 260, 0.31)
    claim("Lopez-Bigas comparison: PROSPECTR kappa 0.282 (recall 189/260, FP rate 44%)", L["prospectr_kappa"], round(k_p, 3),
          _close_any(L["prospectr_kappa"], k_p))
    claim("Lopez-Bigas comparison: Lopez-Bigas kappa 0.158 (recall 123/260, FP rate 31%)", L["lb_kappa"], round(k_l, 3),
          _close_any(L["lb_kappa"], k_l))
    A = pub["artificial_loci"]
    for s in ("hgmd", "omim", "pocus"):
        n = A[s]["n"]
        for k, v in A[s].items():
            if k.startswith("top"):
                count, p = v
                x = 100 * int(count) / n
                claim(f"artificial loci {s}: {count} of {n} = {p}%", p, round(x, 2), _close_any(p, x))
    W = pub["whole_genome"]
    claim("whole genome: 36 of 97 = ~33%", W["over_075_known_pct"], round(100 * 36 / 97, 2), _close_any("33", 100 * 36 / 97))
    claim("whole genome: 35 of 4,357 = ~0.8%", W["under_03_known_pct"], round(100 * 35 / 4357, 3), _close_any("0.8", 100 * 35 / 4357))
    claim("whole genome: 36/97 against ~9% is 'more than threefold'", "yes", "yes" if (36 / 97) / 0.09 > 3 else "no")
    claim("Additional File 1: 9 of 61 = ~15%", W["af1_candidates_pct"], round(100 * 9 / 61))
    T4 = pub["table4"]
    claim("phylogenetic extent ~34% = mouse + rat + worm identity (Table 4)", pub["phylogenetic_share"],
          int(T4["mouse_identity"]) + int(T4["rat_identity"]) + int(T4["worm_identity"]))
    claim("Table 4 adds up to 100% (within rounding of 11 values)", "yes",
          "yes" if abs(sum(int(v) for v in T4.values()) - 100) <= 5.5 else "no")
    E = pub["enrichment"]
    claim("abstract and conclusion give the same top enrichment fold", E["abstract"].get("20"), E["conclusion"].get("20", "25 (conclusion)"),
          "20" in E["conclusion"])
    M = pub["mutation_types"]
    for k, (n, p) in M.items():
        n = int(n)
        whole = [c for c in range(n + 1) if math.floor(100 * c / n) == int(p) or round(100 * c / n) == int(p)]
        claim(f"mutation types: {p}% of {n} {k}-only genes is a whole number of genes", "yes", "yes" if whole else "no")
    return claims


def _kappa_balanced(recall, fpr):
    acc = (recall + 1 - fpr) / 2
    return 2 * acc - 1


def _trunc(x, like="1"):
    dec = len(str(like).split(".")[1]) if "." in str(like) else 0
    f = 10 ** dec
    v = math.floor(x * f + 1e-9) / f
    return f"{v:.{dec}f}" if dec else str(int(v))


def _same(a, b):
    try:
        return abs(float(str(a).replace(",", "")) - float(str(b).replace(",", ""))) < 1e-9
    except ValueError:
        return str(a) == str(b)


def _close_any(expected, x):
    """Matches by rounding or by truncation at the printed precision."""
    s = str(expected)
    dec = len(s.split(".")[1]) if "." in s else 0
    f = 10 ** dec
    e = float(s)
    return abs(round(x * f) / f - e) < 1e-9 or abs(math.floor(x * f + 1e-9) / f - e) < 1e-9


# ---- main -------------------------------------------------------------------------------------------
def main(downloads, t1dir, wekadir, published_values, out, quick=False):
    dl, t1 = Path(downloads), Path(t1dir)
    pub = json.load(open(published_values))
    data = {k: pa.read_arff(dl / v) for k, v in SETS.items()}
    t1data = {k: pa.read_arff(t1 / v) for k, v in T1SETS.items()}
    res = {"inputs": {k: {"disease": d.labels().count("disease"), "normal": d.labels().count("normal"),
                          "attributes": len(d.attributes) - 1} for k, d in data.items()}}
    items = {}

    # retrained, all 64 features (the download page's recipe), and Table 1 features only
    tests = {k: data[k] for k in ("hgmd", "oligogenic")}
    _, main_run = run_tree(data["training"], tests)
    _, t1_run = run_tree(t1data["training"], {k: t1data[k] for k in ("hgmd", "oligogenic")})
    res["port_check"] = [port_check(main_run, Path(wekadir) / "main", "all 64 features"),
                         port_check(t1_run, Path(wekadir) / "table1", "Table 1 features")]
    # Table 3 as the paper reports it is the Figure 2 tree's performance (below); the retrained tree's
    # rows test the download page's recipe, and cross-validation exists only for a retrained tree
    items["table3.cv10"] = table3_fields(main_run["sets"]["cv10"], pub["table3"]["cv10"], pub["text_rates"]["cv10"])
    for name in ("training", "hgmd", "oligogenic"):
        items[f"table3.retrained.{name}"] = table3_fields(main_run["sets"][name], pub["table3"][name], pub["text_rates"][name])
    published_tree = pa.published_tree()
    items["fig2"], matched = fig2_fields(main_run, published_tree)
    t1_fields, t1_matched = fig2_fields(t1_run, published_tree)

    # the published tree on the archived sets
    fig2tree = {}
    for mode, flag in (("paralog_unknown", True), ("paralog_zero", False)):
        fig2tree[mode] = {}
        for name, d in data.items():
            genes, sc, ev = fig2_tree_on(d, flag)
            fig2tree[mode][name] = ev | {"scores": sc}
            if mode == "paralog_unknown" and name == "training":
                tgenes, tsc, tcls = genes, sc, classes(d)
    for name in ("training", "hgmd", "oligogenic"):
        items[f"table3.{name}"] = table3_fields(fig2tree["paralog_unknown"][name],
                                                         pub["table3"][name], pub["text_rates"][name])
    t4 = {}
    for which in ("disease", "predicted", "all"):
        for by in ("feature", "net"):
            t4[f"{which}/{by}"] = table4(tgenes, tcls, tsc, which, by)
    items["table4"] = table4_fields(t4["predicted/net"], pub["table4"])
    t4_hits = {k: sum(_close_any(e, 100 * v.get(f, 0.0)) for f, e in pub["table4"].items()) for k, v in t4.items()}

    # variants for the claims about other trees
    variants = {}
    if not quick:
        for b in (10, 20):
            _, r = run_tree(data["training"], {}, b)
            variants[f"B{b}"] = {k: {kk: v[kk] for kk in ("pct_correct", "kappa", "auc_disease", "recall_disease", "fp_rate_disease")}
                                 for k, v in r["sets"].items()}
    _, lo = run_tree(data["training"].select(["gene_length", "residue_length"]), {}, 15, cv=False)
    variants["length_only"] = {"training": {k: lo["sets"]["training"][k] for k in ("pct_correct", "recall_disease", "fp_rate_disease")},
                               "tree": lo["tree"]}
    items["text.length_only"] = [
        {"name": "disease genes found, training set (%)", "expected": pub["length_only"]["recall"],
         "observed": round(pct(lo["sets"]["training"]["recall_disease"]), 4)},
        {"name": "controls called disease, training set (%)", "expected": pub["length_only"]["fp_rate"],
         "observed": round(pct(lo["sets"]["training"]["fp_rate_disease"]), 4)}]
    if not quick:
        m15 = main_run["sets"]["cv10"]
        items["text.node_count"] = []
        for b in (10, 20):
            v = variants[f"B{b}"]["cv10"]
            items["text.node_count"] += [
                {"name": f"{b} rules: lower cross-validated accuracy than 15", "expected": "yes",
                 "observed": "yes" if v["pct_correct"] < m15["pct_correct"] else "no"},
                {"name": f"{b} rules: lower cross-validated AUC than 15", "expected": "yes",
                 "observed": "yes" if v["auc_disease"] < m15["auc_disease"] else "no"}]

    t2_fields, t2 = table2(data["training"], pub["table2"])
    items["table2"] = t2_fields
    f1 = fig1(data["training"], pub["figure1"])
    for panel, r in f1.items():
        items[f"fig1.{panel}"] = r["fields"]
    sp = spearman(data["training"])
    items["text.spearman"] = [
        {"name": "gene length and number of exons", "expected": pub["spearman_gene_size"]["exons"], "observed": round(sp["exons"], 4)},
        {"name": "gene length and 3' UTR length", "expected": pub["spearman_gene_size"]["utr3_length"], "observed": round(sp["utr3_length"], 4)}]

    gres, gfields = genome(dl / "dump.tab", dl / "1471-2105-6-55-S1.xls", pub)
    gfields.append({"name": "share of the genome called disease (%)", "expected": pub["lopez_bigas"]["prospectr_genome_pct"],
                    "observed": round(gres["dump_called_disease_pct"], 3)})
    items["text.whole_genome"] = gfields
    claims = arithmetic(pub)

    res.update({
        "runs": {"main": {k: v for k, v in main_run.items() if k != "sets"} | {"sets": _strip(main_run["sets"])},
                 "table1": {k: v for k, v in t1_run.items() if k != "sets"} | {"sets": _strip(t1_run["sets"])}},
        "fig2_matched": {str(k): v for k, v in matched.items()},
        "fig2_table1_features": {"fields_matched": sum(1 for f in t1_fields if _match(f)), "fields": len(t1_fields),
                                 "matched_rules": len(t1_matched)},
        "fig2_all_features": {"fields_matched": sum(1 for f in items["fig2"] if _match(f)), "fields": len(items["fig2"]),
                              "matched_rules": len(matched)},
        "fig2tree": {m: _strip(v) for m, v in fig2tree.items()},
        "table4_variants": t4, "table4_hits": t4_hits,
        "variants": variants, "table2": t2, "fig1": f1, "spearman": sp, "genome": gres, "arithmetic": claims,
        "roc": {name: main_run["sets"][name]["roc"] for name in ("training", "hgmd", "oligogenic", "cv10")},
        "roc_fig2tree": {name: fig2tree["paralog_unknown"][name]["roc"] for name in ("training", "hgmd", "oligogenic")},
        "items": items,
        # the same fields under dot-free keys, for tools/check_results.py paths (item_list.key=fig1_a...)
        "item_list": [{"key": k.replace(".", "_"), "id": k, "fields": v} for k, v in items.items()],
    })
    json.dump(res, open(out, "w"), indent=1, default=float)


def _match(f):
    from numbers import Number
    e, o = f["expected"], f["observed"]
    try:
        e2 = float(e)
        s = str(e)
        tol = 0.5 * 10 ** (-(len(s.split(".")[1]) if "." in s else 0))
        return isinstance(o, Number) and abs(e2 - o) <= tol + 1e-12
    except ValueError:
        return e == o


def _strip(sets):
    return {k: {kk: vv for kk, vv in v.items() if kk not in ("scores", "folds", "roc")} for k, v in sets.items()}


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    main(*a[:5], quick="--quick" in sys.argv)
