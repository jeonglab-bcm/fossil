#!/usr/bin/env python3
"""A reimplementation of RelEx (Fundel, Küffner & Zimmer, Bioinformatics 23:365, 2007), following
the description in Pyysalo et al. 2008 (M&M, "RelEx") and in Fundel et al.

Neither the original RelEx nor Pyysalo et al.'s reimplementation was released. This version:
  * takes MedPost (Penn tag set) tags and Stanford Parser 1.5.1 collapsed typed dependencies,
    as both papers did (preprocess.py, parse step);
  * chunks noun phrases from the dependency graph, as Pyysalo et al. did instead of fnTBL:
    a noun and its nn/amod/det/num/number/poss/possessive/quantmod modifiers, if contiguous,
    and every multi-token entity, form one chunk;
  * applies rules 1, 2a, 2b and 3, enumeration expansion, a negation filter and the relation
    restriction terms (Fundel et al.'s list of 175 stems, recovered from the archived
    supplementary page; extract_terms.py).
Our choices where the papers give no detail are marked "CHOICE".

Usage: relex.py TOKENS_DIR PARSE_DIR TERMS OUT_DIR [--filtered]
"""

from __future__ import annotations

import csv
import json
import sys
import re
from collections import defaultdict, deque
from itertools import combinations
from pathlib import Path

CORPORA = ["AIMed", "BioInfer", "HPRD50", "IEPA", "LLL"]

CHUNK_RELS = {"nn", "amod", "det", "num", "number", "poss", "possessive", "quantmod"}
NOUN_TAGS = {"NN", "NNS", "NNP", "NNPS"}
SUBJ_RELS = {"nsubj", "nsubjpass"}
# Rule 2: "of, by, to, on, for, in, through, or with" (Fundel et al.)
R2_PREPS = {"of", "by", "to", "on", "for", "in", "through", "with"}
# Fundel et al. give examples ("not", "without", "lack", "unable"); CHOICE: the rest of the list.
NEGATION = {"not", "n't", "no", "without", "lack", "lacks", "lacked", "lacking", "unable",
            "fail", "fails", "failed", "neither", "nor", "cannot", "absence", "independent",
            "independently"}
ENUM_RELS_PREFIX = ("conj_", "dep", "appos")


def load_terms(path: Path) -> set[str]:
    terms = set()
    for line in path.read_text().splitlines():
        if ":" in line and not line.startswith("word-stem"):
            terms.update(w.strip().lower() for w in line.split(":", 1)[1].split("|") if w.strip())
    return terms


def read_parses(path: Path) -> list[list[tuple[str, int, int]] | None]:
    """Dependencies per sentence (0-based gov, dep), in input order; None if skipped."""
    # Stanford Parser 1.5.1 does not escape '<' or '&' in words, so its "XML" is not
    # well-formed; read the fixed line format instead.
    out: list = []
    rel = gov = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if m := re.match(r'<s id="\d+"( skipped="true")?', line):
            out.append(None if m.group(1) else [])
        elif m := re.match(r'<dep type="([^"]*)">', line):
            rel = m.group(1)
        elif m := re.match(r'<governor idx="(\d+)">', line):
            gov = int(m.group(1)) - 1
        elif m := re.match(r'<dependent idx="(\d+)">', line):
            out[-1].append((rel, gov, int(m.group(1)) - 1))
    return out


class UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


class Sentence:
    def __init__(self, rec, deps, entities):
        self.words = rec["words"]
        self.tags = rec["tags"]
        self.n = len(self.words)
        self.deps = deps
        self.ent_tokens = {e: t for e, t in rec["entities"].items() if e in entities}
        self.entity_token_set = {t for ts in self.ent_tokens.values() for t in ts}
        self._chunk()

    # --- chunking ---------------------------------------------------------------------------
    def _chunk(self):
        uf = UF(self.n)
        for toks in self.ent_tokens.values():  # an entity is never split across chunks
            for a, b in zip(toks, toks[1:]):
                uf.union(a, b)
        for rel, g, d in self.deps:
            nounish = self.tags[g] in NOUN_TAGS or g in self.entity_token_set
            if rel in CHUNK_RELS and nounish:
                lo, hi = min(g, d), max(g, d)
                # CHOICE: only merge contiguous material (no verbs/preps/punctuation in between)
                between = range(lo + 1, hi)
                if all(self.tags[k] in NOUN_TAGS | {"JJ", "DT", "CD", "POS", "PRP$", "HYPH", "VBN", "VBG", "NNP"}
                       or k in self.entity_token_set for k in between):
                    uf.union(g, d)
        roots = {}
        self.chunk_of = []
        for i in range(self.n):
            r = uf.find(i)
            self.chunk_of.append(roots.setdefault(r, len(roots)))
        self.chunks = defaultdict(list)
        for i, c in enumerate(self.chunk_of):
            self.chunks[c].append(i)
        self.ent_chunk = {}
        for e, toks in self.ent_tokens.items():
            if toks:
                self.ent_chunk[e] = self.chunk_of[toks[0]]
        self.chunk_ents = defaultdict(list)
        for e, c in self.ent_chunk.items():
            self.chunk_ents[c].append(e)
        # chunk graph
        self.out_edges = defaultdict(list)  # gov chunk -> [(rel, dep chunk)]
        self.in_edges = defaultdict(list)   # dep chunk -> [(rel, gov chunk)]
        self.und = defaultdict(set)
        self.neg_of = defaultdict(set)
        for rel, g, d in self.deps:
            cg, cd = self.chunk_of[g], self.chunk_of[d]
            if rel == "neg":
                self.neg_of[cg].add(d)
            if cg == cd:
                continue
            self.out_edges[cg].append((rel, cd))
            self.in_edges[cd].append((rel, cg))
            self.und[cg].add(cd)
            self.und[cd].add(cg)
        self.pos = {c: min(t) for c, t in self.chunks.items()}

    def is_verb(self, c):
        return any(self.tags[t].startswith("VB") for t in self.chunks[c])

    def words_of(self, chunks):
        """Non-entity words of the chunks plus negation dependents attached to them."""
        ws = []
        for c in chunks:
            ws += [self.words[t].lower() for t in self.chunks[c] if t not in self.entity_token_set]
            ws += [self.words[t].lower() for t in self.neg_of[c]]
        return ws

    def path(self, a, b, allowed=None):
        """Shortest undirected chunk path a..b (inclusive), optionally within `allowed`."""
        prev = {a: None}
        q = deque([a])
        while q:
            x = q.popleft()
            if x == b:
                break
            for y in self.und[x]:
                if y not in prev and (allowed is None or y in allowed):
                    prev[y] = x
                    q.append(y)
        if b not in prev:
            return None
        p = [b]
        while prev[p[-1]] is not None:
            p.append(prev[p[-1]])
        return p[::-1]

    def enumeration(self, c):
        """Protein chunks reachable from c through conj_*/dep/appos edges between protein chunks."""
        seen = {c}
        q = deque([c])
        while q:
            x = q.popleft()
            for rel, y in self.out_edges[x] + self.in_edges[x]:
                if y not in seen and y in self.chunk_ents and rel.startswith(ENUM_RELS_PREFIX):
                    seen.add(y)
                    q.append(y)
        return seen


# --- rules -----------------------------------------------------------------------------------
NOMINAL_RELS = ("prep_", "nn", "appos", "conj_", "dep", "poss", "amod", "num")
RELPRON = {"which", "that", "who", "whom", "whose"}


def nominal_subtree(s: Sentence, c: int) -> set[int]:
    """c and the chunks below it through nominal relations (CHOICE: a base-NP chunker splits
    "the N-terminus of CCR2" into two chunks; the start point may be any protein chunk inside
    the subject phrase)."""
    seen = {c}
    q = deque([c])
    while q:
        x = q.popleft()
        for rel, y in s.out_edges[x]:
            if y not in seen and rel.startswith(NOMINAL_RELS) and not s.is_verb(y):
                seen.add(y)
                q.append(y)
    return seen


def resolve_relpron(s: Sentence, subj: int, verb: int) -> int:
    """'A, which binds B': the subject 'which' stands for the noun the relative clause modifies
    (CHOICE: Stanford Parser 1.5.1 does not resolve it)."""
    toks = s.chunks[subj]
    if len(toks) == 1 and s.words[toks[0]].lower() in RELPRON:
        for rel, g in s.in_edges[verb]:
            if rel == "rcmod":
                return g
    return subj


def rule1(s: Sentence):
    """effector-relation-effectee. Yields (start chunk, end chunk, path chunks, LCA)."""
    subj_edges = [(g, resolve_relpron(s, d, g)) for d in range(len(s.chunks))
                  for rel, g in s.in_edges[d] if rel in SUBJ_RELS]
    if not subj_edges:
        prot = list(s.chunk_ents)
        for a, b in combinations(prot, 2):
            p = s.path(a, b)
            if p:
                yield a, b, p, None
        return
    subj_verbs = {g for g, _ in subj_edges}
    for v, subj in subj_edges:
        # partial tree: descendants of v, not entering another clause with its own subject
        part = {v}
        q = deque([v])
        while q:
            x = q.popleft()
            for rel, y in s.out_edges[x]:
                if y in part or (y in subj_verbs and y != v):
                    continue
                part.add(y)
                q.append(y)
        subj_tree = nominal_subtree(s, subj)
        part.add(subj)
        starts = {c for c in subj_tree if c in s.chunk_ents}
        for c in list(starts):
            starts |= s.enumeration(c)
        if not starts:
            continue
        part |= subj_tree
        for a in starts:
            for b in s.chunk_ents:
                if b in starts or b not in part:
                    continue
                p = s.path(a, b, allowed=part | starts)
                if not p or v not in p:
                    continue
                endpos = s.pos[b]
                enum_b = s.enumeration(b)
                # terms after the end chunk invalidate the path unless LCA or enumerated with end
                if any(s.pos[c] > endpos and c != v and c not in enum_b for c in p):
                    continue
                # "A binds and activates B": drop the first of two coordinated verbs
                drop = set()
                for x, y in zip(p, p[1:]):
                    if s.is_verb(x) and s.is_verb(y) and any(
                            r in ("conj_and", "conj_but", "conj_whereas") and t == y for r, t in s.out_edges[x]):
                        drop.add(x)
                yield a, b, [c for c in p if c not in drop] or p, v


def rule2a(s: Sentence):
    edges = defaultdict(list)
    par = {}
    for g in list(s.out_edges):
        for rel, d in s.out_edges[g]:
            if rel.startswith("prep_") and rel[5:] in R2_PREPS:
                edges[g].append(d)
                par.setdefault(d, g)
    nodes = set(edges) | set(par)
    prot = [c for c in s.chunk_ents if c in nodes]
    for a, b in combinations(prot, 2):
        p = s.path(a, b, allowed=nodes)
        if not p:
            continue
        # every step must be a prep edge of the chain
        if not all(y in edges.get(x, []) or x in edges.get(y, []) for x, y in zip(p, p[1:])):
            continue
        # at least one link joins two protein-containing chunks
        if not any((x in s.chunk_ents and y in s.chunk_ents) for x, y in zip(p, p[1:])):
            continue
        # extend upward to the head of the chain (the relation noun, "Activation of A by B")
        top = min(p, key=lambda c: depth(c, par))
        ext = list(p)
        while top in par and top in s.chunk_ents:
            top = par[top]
            ext.append(top)
        yield a, b, ext, None


def depth(c, par):
    k = 0
    while c in par and k < 50:
        c = par[c]
        k += 1
    return k


def rule2b(s: Sentence):
    """Surface version: NP (prep NP)+ with >= 2 of the prepositions."""
    order = sorted(s.chunks, key=lambda c: s.pos[c])
    i = 0
    while i < len(order):
        seq = [order[i]]
        j = i + 1
        while j + 1 < len(order) and len(s.chunks[order[j]]) == 1 and \
                s.words[s.chunks[order[j]][0]].lower() in R2_PREPS:
            seq += [order[j], order[j + 1]]
            j += 2
        nps = seq[::2]
        npreps = (len(seq) - 1) // 2
        if npreps >= 2:
            direct = any(nps[k] in s.chunk_ents and nps[k + 1] in s.chunk_ents for k in range(len(nps) - 1))
            prot = [c for c in nps if c in s.chunk_ents]
            if direct:
                for a, b in combinations(prot, 2):
                    yield a, b, seq, None
        i = max(j - 1, i + 1) if npreps else i + 1


def rule3(s: Sentence):
    for g in list(s.out_edges):
        for rel, d in s.out_edges[g]:
            if rel != "prep_between":
                continue
            members = [d] + [y for r, y in s.out_edges[d] if r == "conj_and"]
            members += [y for r, y in s.out_edges[g] if r == "prep_between" and y != d]
            members = [m for m in dict.fromkeys(members) if m in s.chunk_ents]
            if len(members) >= 2:
                for a, b in combinations(members, 2):
                    yield a, b, [g, a, b], None
            elif len(members) == 1 and len(s.chunk_ents[members[0]]) >= 2:
                yield members[0], members[0], [g, members[0]], None


RULES = {"1": rule1, "2a": rule2a, "2b": rule2b, "3": rule3}


def extract(s: Sentence, terms: set[str], rules=("1", "2a", "2b", "3")) -> set[frozenset[str]]:
    out = set()
    for r in rules:
        for a, b, path, lca in RULES[r](s):
            words = s.words_of(path)
            if any(w in NEGATION for w in words):
                continue
            if not any(w in terms for w in words):
                continue
            ea, eb = s.enumeration(a), s.enumeration(b)
            ents_a = [e for c in ea for e in s.chunk_ents[c]]
            ents_b = [e for c in eb for e in s.chunk_ents[c]]
            for x in ents_a:
                for y in ents_b:
                    if x != y and not (x in s.chunk_ents.get(a, []) and y in s.chunk_ents.get(a, []) and a != b):
                        out.add(frozenset((x, y)))
    return out


def run(tokens_dir: Path, parse_dir: Path, terms: set[str], filtered: bool, rules=("1", "2a", "2b", "3")):
    results = {}
    for c in CORPORA:
        recs = json.loads((tokens_dir / f"{c}.tokens.json").read_text())
        parses = read_parses(parse_dir / f"{c}.parse.xml")
        if len(parses) != len(recs):
            raise SystemExit(f"{c}: {len(parses)} parses for {len(recs)} sentences")
        tp = fp = fn = 0
        for rec, deps in zip(recs, parses):
            gold = {frozenset(p) for p in rec["interactions"]}
            ents = set(rec["entities"])
            if filtered:
                ents = set().union(*map(set, gold)) if gold else set()
            pred = extract(Sentence(rec, deps or [], ents), terms, rules) if deps is not None else set()
            tp += len(pred & gold)
            fp += len(pred - gold)
            fn += len(gold - pred)
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        results[c] = {"tp": tp, "fp": fp, "fn": fn, "P": p, "R": r, "F": f}
    return results


def main():
    tokens_dir, parse_dir, terms_path, out = map(Path, sys.argv[1:5])
    terms = load_terms(terms_path)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for variant, filt in (("unfiltered", False), ("filtered", True)):
        for c, r in run(tokens_dir, parse_dir, terms, filt).items():
            rows.append({"corpus": c, "variant": variant, **r})
            print(f"{c:9s} {variant:10s} P={r['P']:.3f} R={r['R']:.3f} F={r['F']:.3f} "
                  f"(tp {r['tp']} fp {r['fp']} fn {r['fn']})")
    with open(out / "relex.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
