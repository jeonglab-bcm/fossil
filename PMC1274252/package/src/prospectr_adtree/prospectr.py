"""PROSPECTR: score genes with the published alternating decision tree (Adie et al. 2005, Figure 2).

A gene starts at "Start" (0), follows every rule whose feature is known, and adds the value of the
branch it takes. A negative score means the gene looks more like a known disease gene. The paper
normalises a score a to 1 / (1 + e^a), so higher normalised scores mean more likely disease genes.
"""

from __future__ import annotations

import json
import math
from importlib import resources

FEATURES = {
    "gene_length": "Gene length (bp)",
    "cds_length": "CDS length (bp)",
    "utr3_length": "Length of 3' UTR (bp)",
    "exons": "Number of exons",
    "gc": "GC content (%)",
    "signal_peptide": "Signal peptide predicted (1 or 0)",
    "paralog_identity": "% protein identity of the best human paralog",
    "mouse_identity": "% protein identity of the mouse homolog (0 if none)",
    "rat_identity": "% protein identity of the rat homolog (0 if none)",
    "worm_identity": "% protein identity of the worm homolog (0 if none)",
    "mouse_ka": "Ka between the human gene and its mouse homolog",
}

# Table 4 groups the rules by these names
FEATURE_GROUPS = {
    "signal_peptide": "Signal peptide",
    "mouse_identity": "Mouse homolog % identity",
    "utr3_length": "Length of 3' UTR",
    "exons": "Number of exons",
    "rat_identity": "Rat homolog % identity",
    "worm_identity": "Worm homolog % identity",
    "gc": "GC",
    "cds_length": "CDS length",
    "gene_length": "Gene length",
    "mouse_ka": "Mouse homolog Ka",
    "paralog_identity": "Paralog % identity",
}


def published_tree() -> dict:
    """The 15-rule tree of the paper's Figure 2 (bundled as data/prospectr_fig2.json)."""
    with resources.files(__package__).joinpath("data", "prospectr_fig2.json").open(encoding="utf-8") as f:
        return json.load(f)


def _test(node: dict, value: float) -> bool:
    op, t = node["op"], node["threshold"]
    if op == ">=":
        return value >= t
    if op == ">":
        return value > t
    if op == "==":
        return value == t
    raise ValueError(f"unknown operator {op!r}")


def _paths(tree: dict, gene: dict):
    """Yield (rule, branch, value) for every rule the gene reaches, in rule order."""
    reached = {None}
    for node in sorted(tree["nodes"], key=lambda n: n["id"]):
        if node["parent"] not in reached:
            continue
        v = gene.get(node["feature"])
        if v is None or (isinstance(v, float) and math.isnan(v)):
            continue
        yes = _test(node, float(v))
        yield node, "yes" if yes else "no", node["yes" if yes else "no"]
        if yes:
            reached.add(node["id"])


def score(gene: dict, tree: dict | None = None) -> float:
    """Raw PROSPECTR score of one gene (a dict of FEATURES; a missing or None feature is unknown)."""
    tree = tree or published_tree()
    total = tree["root"]
    for _, _, v in _paths(tree, gene):
        total += v
    return total


def normalise(raw: float) -> float:
    """The paper's normalisation, 1 / (1 + e^raw): between 0 and 1, higher = more likely disease."""
    return 1.0 / (1.0 + math.exp(raw))


def contributions(gene: dict, tree: dict | None = None, by: str = "feature") -> dict[str, float]:
    """Share of each feature in the gene's cumulative absolute score (the Table 4 measure).

    ``by='feature'`` adds the absolute values of every rule on a feature; ``by='net'`` takes the
    absolute value of the feature's summed contribution. Shares add up to 1 (empty if no rule fired)."""
    tree = tree or published_tree()
    parts: dict[str, float] = {}
    for node, _, v in _paths(tree, gene):
        f = node["feature"]
        if by == "feature":
            parts[f] = parts.get(f, 0.0) + abs(v)
        elif by == "net":
            parts[f] = parts.get(f, 0.0) + v
        else:
            raise ValueError("by must be 'feature' or 'net'")
    if by == "net":
        parts = {k: abs(v) for k, v in parts.items()}
    total = sum(parts.values())
    return {k: v / total for k, v in parts.items()} if total > 0 else {}


def average_contributions(genes: list[dict], tree: dict | None = None, by: str = "feature") -> dict[str, float]:
    """Mean share of each feature over ``genes`` (a feature a gene does not use counts as 0)."""
    tree = tree or published_tree()
    sums: dict[str, float] = {}
    n = 0
    for g in genes:
        c = contributions(g, tree, by)
        if not c:
            continue
        n += 1
        for k, v in c.items():
            sums[k] = sums.get(k, 0.0) + v
    if n == 0:
        raise ValueError("no gene reached any rule")
    return {k: v / n for k, v in sorted(sums.items(), key=lambda kv: -kv[1])}


def rank_in_locus(target_score: float, other_scores: list[float]) -> float:
    """Where a target gene falls in its locus ranked from the most disease-like (lowest raw score):
    the fraction of the list at or above it, ties counted against the target (0 < r <= 1)."""
    better_or_equal = sum(1 for s in other_scores if s <= target_score)
    return (better_or_equal + 1) / (len(other_scores) + 1)


def features_from_prospectr_arff(row: dict, paralog_zero_unknown: bool = True) -> dict:
    """Map a row of the PROSPECTR web site's ARFF files (2006) onto the Figure 2 features.

    The ARFFs have no CDS length: it is cDNA length minus both UTRs. Their paralog identity is 0 for
    every gene; the paper enters "unknown" for genes without a paralog, so 0 is read as unknown
    unless ``paralog_zero_unknown`` is False. Ka is the ARFF's ``mouse_dn``."""
    def get(k):
        return row.get(k)

    cdna, u3, u5 = get("cdna_length"), get("len_3utr"), get("len_5utr")
    cds = cdna - u3 - u5 if None not in (cdna, u3, u5) else None
    par = get("paralog_identity")
    if paralog_zero_unknown and par == 0:
        par = None
    return {
        "gene_length": get("gene_length"),
        "cds_length": cds,
        "utr3_length": u3,
        "exons": get("exons"),
        "gc": get("gc"),
        "signal_peptide": get("sigpep"),
        "paralog_identity": par,
        "mouse_identity": get("mouse_identity"),
        "rat_identity": get("rat_identity"),
        "worm_identity": get("worm_identity"),
        "mouse_ka": get("mouse_dn"),
    }
