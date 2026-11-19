"""Tables 3, 4 and 5: GeCON modules from the real datasets and their GO enrichment.

GeneMANIA's 2014 data and FuncAssociate are not available, so every module is tested with one local
method: a hypergeometric test of each GO term (annotations propagated up is_a and part_of; NOT annotations
dropped) against the dataset's annotated genes, Benjamini-Hochberg within the module. Table 4 printed
GeneMANIA's Q values and Table 5 FuncAssociate's p values; we compare in kind: is the paper's term enriched
(Q < 0.05) in one of our modules of the same dataset?

Our settings (the paper gives neither the filters nor how modules were cut from the network):
- genes standardised (mean 0, sd 1) before GeCON: on raw or log values all edge angles sit near 45 or 135
  degrees and GeCON connects every pair (see the README);
- tau 20, theta 0.8 (0.7 and 0.9 as a sensitivity check; at 0.7 the GDS sets form one giant component); a module is a connected component with at least 5 genes;
- gene filters: the most variable probes (by sd of log2 values) up to the paper's gene count, one probe per
  gene symbol.

Usage: enrichment.py DOWNLOADS PAPER_VALUES.json OUT.json
"""
import gzip, json, os, re, sys
from collections import defaultdict
import numpy as np
from scipy.stats import hypergeom
import gecon

TAU, THETA, MIN_MODULE = 20.0, 0.8, 5
THETAS = [0.7, 0.8, 0.9]  # sensitivity
NAME_FIXES = {  # the paper's spelling -> the GO term name it means
    "aging regulation of": "regulation of aging",
    "response to neutrient": "response to nutrient",
    "DNA-dependent DNA replication": "DNA replication",
    "folic acid and derivative biosynthetic process": "folic acid-containing compound biosynthetic process",
    "cell cycle phase": "cell cycle process",
    "intracellular part": "intracellular anatomical structure",
}


def read_obo(path):
    terms, cur = {}, None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line == "[Term]":
            cur = {"parents": set(), "syn": []}
        elif line.startswith("[") and line.endswith("]"):
            cur = None
        elif cur is not None:
            if line.startswith("id: "):
                cur["id"] = line[4:]
                terms[cur["id"]] = cur
            elif line.startswith("name: "):
                cur["name"] = line[6:]
            elif line.startswith("namespace: "):
                cur["ns"] = line[11:]
            elif line.startswith("is_a: "):
                cur["parents"].add(line[6:16])
            elif line.startswith("relationship: part_of "):
                cur["parents"].add(line[22:32])
            elif line.startswith("synonym: "):
                m = re.match(r'synonym: "(.*)" (EXACT|NARROW|BROAD|RELATED)', line)
                if m and m.group(2) == "EXACT":
                    cur["syn"].append(m.group(1))
            elif line.startswith("is_obsolete: true"):
                cur["obsolete"] = True
            elif line.startswith("alt_id: "):
                terms[line[8:]] = cur
    return terms


def ancestors(terms):
    memo = {}

    def up(t):
        if t in memo:
            return memo[t]
        s = {t}
        for p in terms.get(t, {}).get("parents", ()):
            s |= up(p)
        memo[t] = s
        return s

    return up


def read_gaf(path, key):
    """gene key (symbol, or a yeast systematic name from the synonyms) -> set of GO ids."""
    ann = defaultdict(set)
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("!"):
                continue
            p = line.rstrip("\n").split("\t")
            if "NOT" in p[3]:
                continue
            names = {p[2].upper()}
            if key == "yeast":
                names |= {s.upper() for s in p[10].split("|") if re.match(r"^Y[A-P][LR]\d{3}[WC](-[A-Z])?$", s.upper())}
            for n in names:
                ann[n].add(p[4])
    return ann


def bh(p):
    p = np.asarray(p)
    n = len(p)
    o = np.argsort(p)
    q = np.empty(n)
    q[o] = np.minimum.accumulate((p[o] * n / np.arange(1, n + 1))[::-1])[::-1]
    return np.minimum(q, 1)


def gds_matrix(path):
    probes, sym, vals, inside = [], [], [], False
    with gzip.open(path, "rt", encoding="latin-1") as f:
        for line in f:
            if line.startswith("!dataset_table_begin"):
                inside = True
                next(f)
                continue
            if line.startswith("!dataset_table_end"):
                break
            if inside:
                p = line.rstrip("\n").split("\t")
                try:
                    v = [float(x) for x in p[2:]]
                except ValueError:
                    continue
                probes.append(p[0])
                sym.append(p[1])
                vals.append(v)
    return probes, sym, np.array(vals)


def top_variable(sym, X, n, log=True):
    L = np.log2(np.maximum(X, 1.0)) if log else X
    sd = L.std(1)
    order = np.argsort(-sd, kind="mergesort")
    keep, seen = [], set()
    for i in order:
        s = sym[i].upper()
        if s in seen or not s or s.startswith("---") or sd[i] == 0:
            continue
        seen.add(s)
        keep.append(i)
        if len(keep) == n:
            break
    return [sym[i].upper() for i in keep], L[keep]


def datasets(downloads):
    out = {}
    rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(downloads, "normcho_237_4class.txt"))][1:]
    rows = [r for r in rows if len(r) > 18]
    out["Yeast KY"] = ([r[0].upper() for r in rows], np.array([[float(v) for v in r[2:19]] for r in rows]), "yeast",
                       "normcho_237_4class.txt (the site's normalised variant), 237 genes x 17 conditions")
    _, sym, X = gds_matrix(os.path.join(downloads, "GDS3702.soft.gz"))
    g, L = top_variable(sym, X, 3000)
    out["GDS3702"] = (g, L, "rat", "GDS3702 log2 counts, the 3000 most variable genes, 12 samples")
    _, sym, X = gds_matrix(os.path.join(downloads, "GDS958.soft.gz"))
    g, L = top_variable(sym, X, 4000)
    out["GDS958"] = (g, L, "mouse", "GDS958 log2 counts, the 4000 most variable genes, 12 samples")
    return out


def analyse(data, theta, terms, up, gafs, downloads, gaf_cache):
    res = {"datasets": {}}
    for ds, (genes, X, org, desc) in data.items():
        if org not in gaf_cache:
            gaf_cache[org] = read_gaf(os.path.join(downloads, gafs[org]), org)
        ann_raw = gaf_cache[org]
        Z = (X - X.mean(1, keepdims=True)) / X.std(1, keepdims=True)
        A, sup = gecon.gecon(Z, theta=theta, tau=TAU)
        mods = gecon.modules(A, MIN_MODULE)
        ann = {}
        for g in genes:
            s = set()
            for t in ann_raw.get(g, ()):
                s |= up(t)
            if s:
                ann[g] = s
        universe = [g for g in genes if g in ann]
        counts = defaultdict(int)
        for g in universe:
            for t in ann[g]:
                counts[t] += 1
        N = len(universe)
        mres = []
        for k, m in enumerate(mods):
            mg = [genes[i] for i in m if genes[i] in ann]
            mc = defaultdict(int)
            for g in mg:
                for t in ann[g]:
                    mc[t] += 1
            tids = [t for t, c in mc.items() if c >= 2 and t in terms and terms[t].get("ns") and t not in (
                "GO:0008150", "GO:0003674", "GO:0005575")]
            p = [hypergeom.sf(mc[t] - 1, N, counts[t], len(mg)) for t in tids]
            q = bh(p) if p else []
            hits = sorted(zip(q, p, tids), key=lambda x: (x[0], x[1], x[2]))  # ties by GO id, not set order
            mres.append({"module": k + 1, "genes": len(m), "annotated": len(mg),
                         "top": [{"go": t, "name": terms[t]["name"], "q": float(f"{qq:.3g}"), "p": float(f"{pp:.3g}"),
                                  "in_module": mc[t], "in_dataset": counts[t]} for qq, pp, t in hits[:5]],
                         "significant": {t: float(f"{qq:.3g}") for qq, pp, t in hits if qq < 0.05}})
        res["datasets"][ds] = {"source": desc, "genes": len(genes), "conditions": int(X.shape[1]), "annotated": N,
                               "edges": int(np.triu(A != 0, 1).sum()), "negative_edges": int(np.triu(A == -1, 1).sum()),
                               "modules": mres}
        print(ds, len(genes), "edges", res["datasets"][ds]["edges"], "modules", [m["genes"] for m in mres][:10], flush=True)
    return res


def paper_rows(res, pv, terms, by_name):
    out = {}
    # the paper's rows: is the term enriched in one of our modules of that dataset?
    for tab in ("table4", "table5"):
        rows = []
        for row in pv[tab]:
            ds, mod, name = row[0], row[1], row[2]
            fixed = NAME_FIXES.get(name, name)
            tid = by_name.get(fixed.lower())
            entry = {"dataset": ds, "module": mod, "term": name, "go": tid, "go_name": terms[tid]["name"] if tid else None}
            if ds not in res["datasets"]:
                entry["found"] = None
            else:
                best = None
                for m in res["datasets"][ds]["modules"]:
                    q = m["significant"].get(tid)
                    if q is not None and (best is None or q < best[1]):
                        best = (m["module"], q)
                entry["found"] = "yes" if best else "no"
                entry["our_module"], entry["our_q"] = (best if best else (None, None))
            rows.append(entry)
        out[tab] = rows
    return out


def main():
    downloads, paper, outp = sys.argv[1:4]
    pv = json.load(open(paper))
    terms = read_obo(os.path.join(downloads, "go-basic.obo"))
    up = ancestors(terms)
    by_name = {}
    for t in terms.values():
        if t.get("obsolete") or "name" not in t:
            continue
        by_name.setdefault(t["name"].lower(), t["id"])
        for s in t["syn"]:
            by_name.setdefault(s.lower(), t["id"])
    gafs = {"yeast": "YEAST-mod.gaf.gz", "rat": "RAT-mod.gaf.gz", "mouse": "MOUSE-mod.gaf.gz"}
    res = {"settings": {"tau": TAU, "theta": THETA, "min_module": MIN_MODULE, "standardise": True,
                        "test": "hypergeometric, BH within module, GO propagated over is_a and part_of",
                        "go_release": "2026-08-05"}, "datasets": {}}
    data = datasets(downloads)
    gaf_cache = {}
    sens = {}
    largest = {}
    for th in THETAS:
        r_th = analyse(data, th, terms, up, gafs, downloads, gaf_cache)
        rows_th = paper_rows(r_th, pv, terms, by_name)
        sens[f"{th:g}"] = {tab: sum(x["found"] == "yes" for x in rows_th[tab]) for tab in rows_th}
        largest[f"{th:g}"] = {d: max([m["genes"] for m in v["modules"]], default=0) for d, v in r_th["datasets"].items()}
        if th == THETA:
            res["datasets"] = r_th["datasets"]
            res.update(rows_th)
    res["theta_sensitivity_found"] = sens
    res["theta_largest_module"] = largest
    for tab in ("table4", "table5"):
        print(tab, [(r["dataset"], r["term"][:25], r["found"], r.get("our_q")) for r in res[tab]])
    print("found per theta", sens)
    json.dump(res, open(outp, "w"), indent=1)


if __name__ == "__main__":
    main()
