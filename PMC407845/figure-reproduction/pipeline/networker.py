"""Run MA-Networker (package manetworker) on the rebuilt compendium and Lee et al. 2002 ChIP data.

  networker.py DOWNLOADS OUTDIR

Writes to OUTDIR:
  compendium.json   arrays per source against the paper's library
  selection.json    backward selection: selected TFs, drop order, overlap with the paper's 37
  table1.json       Table 1 counts for our run and for each variant tested (see VARIANTS)
  tfap.tsv          activity profiles (t-values) of Hap4, Ndd1 and Ste12 over all arrays (Fig. 1b)
  run.npz           genes, TFs, coupling and classes for the downstream steps (not committed)

The main run is the method as the paper states it, with these choices where it is silent (each is
an assumption in results_notes.json): ChIP log2 ratios with missing values set to 0 in the
regression; TF activity profiles are the regression t-values (Fig. 1b plots them on a +-10 axis);
coupling is a one-sided test for positive correlation (in Fig. 1c every B+/C+ gene couples
positively); Benjamini-Hochberg at 5% per TF over all its genes; a gene has expression data when it
is measured in at least half of the arrays.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

import data
import manetworker as mn

PAPER_TFS = ("Abf1 Ace2 Arg81 Bas1 Cad1 Dal81 Dig1 Fhl1 Fkh2 Gal4 Gat3 Gcn4 Hal9 Hap4 Hir1 Hir2 Hsf1 "
             "Leu3 Mbp1 Mcm1 Met31 Msn4 Mss11 Ndd1 Nrg1 Rlm1 Sig1 Sko1 Sok2 Stb1 Ste12 Sum1 Swi4 Swi5 "
             "Thi2 Yap1 Yap6").split()
DELETION_TFS = ["Dig1", "Gcn4", "Hir2", "Mbp1", "Swi4", "Swi5", "Yap1"]
ALPHA = 0.005 / 751          # the paper's threshold, with its 751 arrays
BIND_P = 1e-3
FDR = 0.05
MIN_MEASURED = 0.5           # share of arrays a gene must be measured in to be classified

# Each variant changes one choice of the main run (hypotheses for the Table 1 differences).
VARIANTS = {
    "main": {},
    "coef_profile": {"profile": "coef"},
    "two_sided": {"sided": "two"},
    "fdr_all_pairs": {"scope": "all"},
    "fdr_bound_only": {"scope": "bound"},
    "any_measurement": {"min_measured": None},
    "paper_37_fixed": {"tfs": "paper"},   # sensitivity only: the paper's 37 TFs put into our run
}


def deletion_columns(arrays, source, tf):
    """Hughes 2000 arrays of a deletion of `tf` (alone or with others), e.g. 'dig1', 'dig1, dig2'."""
    pat = re.compile(rf"(^|[^a-z0-9]){tf.lower()}([^a-z0-9]|$)")
    return [j for j, (a, s) in enumerate(zip(arrays, source)) if s == "Hughes_2000" and pat.search(a.lower())]


def single_deletion_column(arrays, source, tf):
    """The Hughes 2000 array of the single deletion (label exactly the gene name)."""
    cols = [j for j in deletion_columns(arrays, source, tf) if arrays[j].strip().strip('"').lower() == tf.lower()]
    return cols[0] if cols else None


def classes_for(E, LR, P, fit_t, fit_coef, idx, avail_expr, profile="t", sided="one", scope="per_tf"):
    F = fit_t if profile == "t" else fit_coef
    c = mn.coupling(E, F)
    p = c["p"]
    if sided == "one":
        p = np.where(c["r"] > 0, p / 2, 1 - p / 2)
    bnd = P[:, idx] < BIND_P
    avail = avail_expr[:, None] & np.isfinite(LR[:, idx])
    cp = mn.coupled(p, FDR, scope, bound=bnd & avail)
    cls = mn.classify(bnd, cp, avail)
    return cls, c["r"], p


def main(downloads, outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    C = data.compendium(downloads)
    L = data.lee(downloads)
    A = data.align(C, L)
    genes, tfs, E = A["genes"], A["tfs"], A["E"]
    LR = mn.log_ratio(A["ratio"])
    P = A["p"]
    inlee = np.isfinite(LR).any(1) | ~np.isnan(P).all(1)
    Bf = mn.fill_binding(LR)
    n_meas = (~np.isnan(E)).sum(1)

    per_source = {}
    for s in C["source"]:
        per_source[s] = per_source.get(s, 0) + 1
    comp = {
        "arrays": E.shape[1], "arrays_paper": 751, "genes_expression": len(C["genes"]),
        "genes_lee": len(L["genes"]), "genes_union": len(genes), "genes_paper": 6382,
        "sources": {s: {"paper": n, "ours": per_source.get(s, 0)} for s, n in data.PAPER_SOURCES.items()},
        "note": "Protchenko 2001 and Yun 2000 share one SGD file (same SHA-256); it is counted once, under Yun 2000.",
    }
    (out / "compendium.json").write_text(json.dumps(comp, indent=1) + "\n")

    # Step 1: backward selection on the genes in Lee's file
    sel = mn.backward_select(E[inlee], Bf[inlee], ALPHA, names=tfs)
    idx = sel["selected"]
    fit_sel = sel["fit"]
    minp = np.nanmin(fit_sel["p"], axis=1)
    ranked = sorted(zip([tfs[i] for i in idx], minp), key=lambda x: x[1])
    paper_rank = {t: k + 1 for k, (t, _) in enumerate(ranked)}
    selection = {
        "alpha": ALPHA, "n_tfs": len(tfs), "n_selected": len(idx), "n_selected_paper": 37,
        "selected": [t for t, _ in ranked],
        "neglog10_min_p": {t: round(float(-np.log10(max(p, 1e-300))), 3) for t, p in ranked},
        "dropped_last": [{"tf": tfs[i], "min_p": float(p)} for i, p in sel["dropped"][-10:]],
        "paper_tfs_selected": sorted(set(PAPER_TFS) & {tfs[i] for i in idx}),
        "paper_tfs_not_selected": sorted(set(PAPER_TFS) - {tfs[i] for i in idx}),
        "selected_not_in_paper": sorted({tfs[i] for i in idx} - set(PAPER_TFS)),
        "top37_overlap": len(set(PAPER_TFS) & {t for t, _ in ranked[:37]}),
        "rank_of_paper_tfs": {t: paper_rank.get(t) for t in PAPER_TFS},
    }
    (out / "selection.json").write_text(json.dumps(selection, indent=1) + "\n")

    idx_paper = [tfs.index(t) for t in PAPER_TFS]
    fit_paper = mn.regress_activities(E[inlee], Bf[inlee], keep=idx_paper)
    avail_half = n_meas >= np.ceil(MIN_MEASURED * E.shape[1])
    avail_any = n_meas >= 3

    table = {"columns": list(mn.CLASSES), "paper_tfs": PAPER_TFS, "variants": {}}
    keep_main = None
    for name, v in VARIANTS.items():
        use_paper = v.get("tfs") == "paper"
        ix = idx_paper if use_paper else idx
        fit = fit_paper if use_paper else fit_sel
        av = avail_any if v.get("min_measured", MIN_MEASURED) is None else avail_half
        cls, r, p = classes_for(E, LR, P, fit["t"], fit["coef"], ix, av, v.get("profile", "t"),
                                v.get("sided", "one"), v.get("scope", "per_tf"))
        cnt = mn.class_counts(cls)
        names = [tfs[i] for i in ix]
        table["variants"][name] = {
            "change": v, "tfs": names,
            "counts": {t: [int(x) for x in row] for t, row in zip(names, cnt)},
        }
        if name == "main":
            keep_main = (names, cls, r, p)
    (out / "table1.json").write_text(json.dumps(table, indent=1) + "\n")

    names, cls, r, p = keep_main
    # Fig. 1b profiles
    k = [names.index(t) for t in ("Hap4", "Ndd1", "Ste12")]
    with open(out / "tfap.tsv", "w", encoding="utf-8") as f:
        f.write("array\tsource\tfile\tHap4\tNdd1\tSte12\n")
        for j in range(E.shape[1]):
            vals = "\t".join(f"{fit_sel['t'][i, j]:.4f}" for i in k)
            f.write(f"{C['arrays'][j]}\t{C['source'][j]}\t{C['file'][j]}\t{vals}\n")

    # Leave-one-out for the deletion analysis: refit without the TF's own Hughes deletion arrays
    loo_cls, loo_info = [], {}
    for tf in DELETION_TFS:
        drop = deletion_columns(C["arrays"], C["source"], tf)
        keepc = np.setdiff1d(np.arange(E.shape[1]), drop)
        fit_l = mn.regress_activities(E[inlee][:, keepc], Bf[inlee], keep=idx)
        cl, _, _ = classes_for(E[:, keepc], LR, P, fit_l["t"], fit_l["coef"], idx, avail_half)
        loo_cls.append(cl[:, names.index(tf)] if tf in names else np.full(len(genes), 3))
        sc = single_deletion_column(C["arrays"], C["source"], tf)
        loo_info[tf] = {"excluded_arrays": [C["arrays"][j] for j in drop],
                        "deletion_array": C["arrays"][sc] if sc is not None else None}
    hughes_del = np.column_stack([
        E[:, single_deletion_column(C["arrays"], C["source"], tf)] / np.log2(10) for tf in DELETION_TFS
    ])  # back to Hughes' log10 ratios
    (out / "loo.json").write_text(json.dumps(loo_info, indent=1) + "\n")

    np.savez_compressed(
        out / "run.npz", genes=np.array(genes), tfs=np.array(names), classes=cls.astype(np.int8),
        r=r.astype(np.float32), p=p.astype(np.float32), lee_logratio=LR[:, [tfs.index(t) for t in names]].astype(np.float32),
        lee_p=P[:, [tfs.index(t) for t in names]].astype(np.float32), all_tfs=np.array(tfs),
        loo_classes=np.column_stack(loo_cls).astype(np.int8), deletion_tfs=np.array(DELETION_TFS),
        hughes_deletion=hughes_del.astype(np.float32), spot=np.array([""] * len(genes)),
    )
    print(f"{E.shape[1]} arrays, {len(genes)} genes; {len(idx)} TFs selected "
          f"({len(selection['paper_tfs_selected'])} of the paper's 37)")


if __name__ == "__main__":
    main(*sys.argv[1:3])
