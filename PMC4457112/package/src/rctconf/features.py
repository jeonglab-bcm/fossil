"""Feature sets of a MEDLINE citation.

Cohen et al. (2015) built "approximately 45 million unique binary and numeric features" in feature
sets of three kinds: text of the title and abstract (n-grams of length 1-3), bibliographic fields
(journal, authors, author count) and MEDLINE annotation (MeSH terms, publication types). The exact
list is in the journal supplement, which could not be obtained. The sets here follow the paper and
the same group's description of the same pipeline (Cohen et al. 2018, PMC6146117): n-grams after
tokenizing on whitespace and punctuation, lower-casing and removing the stop words of McCallum's
Bag-Of-Words library; no stemming.

Every feature is binary. A feature is a 64-bit hash of its set name and value, so feature sets can be
built on millions of citations without holding a string vocabulary in memory.
"""

from __future__ import annotations

import hashlib
import re
from importlib import resources

import numpy as np

CITATION_SETS = (
    "title_unigrams",
    "title_bigrams",
    "title_trigrams",
    "abstract_unigrams",
    "abstract_bigrams",
    "abstract_trigrams",
    "journal",
    "authors",
    "author_count",
    "keywords",
)
MESH_SETS = ("mesh_terms", "mesh_major", "mesh_qualified", "chemicals")
PUBTYPE_SETS = ("pubtypes",)
ALL_SETS = CITATION_SETS + MESH_SETS + PUBTYPE_SETS

RCT_PUBTYPE = "D016449"  # Randomized Controlled Trial; the label, never a feature

_TOKEN = re.compile(r"[a-z0-9]+")


def _load_stopwords() -> frozenset[str]:
    text = (resources.files(__package__) / "data" / "stoplist_smart_libbow.txt").read_text(encoding="utf-8")
    return frozenset(w.strip() for w in text.splitlines() if w.strip())


STOPWORDS = _load_stopwords()


def tokens(text: str) -> list[str]:
    """Lower-case tokens split on whitespace and punctuation, stop words removed."""
    return [t for t in _TOKEN.findall((text or "").lower()) if t not in STOPWORDS]


def ngrams(toks: list[str], n: int) -> list[str]:
    return [" ".join(toks[i : i + n]) for i in range(len(toks) - n + 1)]


def _split(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if str(v)]
    return [v for v in str(value).split("|") if v]


def raw_features(record: dict, sets=ALL_SETS, author_bins=None) -> dict[str, set[str]]:
    """Feature strings of one citation, by set.

    record keys: title, abstract, journal, authors ("|"-joined or a list), n_authors, mesh
    (descriptor UIs, "*" before a major topic), mesh_qual ("D.../Q..." pairs), chemicals, keywords,
    pubtypes. Missing keys give empty sets.
    author_bins: cut points for author_count (from mdl_cut_points); without them the raw count is used.
    """
    out: dict[str, set[str]] = {}
    need_title = any(s.startswith("title_") for s in sets)
    need_abs = any(s.startswith("abstract_") for s in sets)
    tt = tokens(record.get("title", "")) if need_title else []
    at = tokens(record.get("abstract", "")) if need_abs else []
    mesh = _split(record.get("mesh"))
    for s in sets:
        if s.startswith("title_") or s.startswith("abstract_"):
            toks = tt if s.startswith("title_") else at
            n = {"unigrams": 1, "bigrams": 2, "trigrams": 3}[s.split("_", 1)[1]]
            out[s] = set(ngrams(toks, n))
        elif s == "journal":
            j = (record.get("journal") or "").strip().lower()
            out[s] = {j} if j else set()
        elif s == "authors":
            out[s] = {a.lower() for a in _split(record.get("authors"))}
        elif s == "author_count":
            n = record.get("n_authors")
            if n is None:
                n = len(_split(record.get("authors")))
            n = int(n)
            out[s] = {f"bin{int(np.searchsorted(author_bins, n, side='right'))}" if author_bins is not None else str(n)}
        elif s == "keywords":
            out[s] = {k.strip().lower() for k in _split(record.get("keywords")) if k.strip()}
        elif s == "mesh_terms":
            out[s] = {m.lstrip("*") for m in mesh}
        elif s == "mesh_major":
            out[s] = {m[1:] for m in mesh if m.startswith("*")}
        elif s == "mesh_qualified":
            out[s] = set(_split(record.get("mesh_qual")))
        elif s == "chemicals":
            out[s] = set(_split(record.get("chemicals")))
        elif s == "pubtypes":
            out[s] = {p for p in _split(record.get("pubtypes")) if p != RCT_PUBTYPE}
        else:
            raise ValueError(f"unknown feature set {s!r}; known: {', '.join(ALL_SETS)}")
    return out


def feature_hash(set_name: str, value: str) -> int:
    """Stable unsigned 64-bit hash of a feature (BLAKE2b, 8 bytes)."""
    d = hashlib.blake2b((set_name + "\x1f" + value).encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(d, "little")


def hashed_features(records, sets=ALL_SETS, author_bins=None) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Hashed features of many citations: {set: (indptr, hashes)} in CSR layout.

    hashes[indptr[i]:indptr[i+1]] are the sorted unique feature hashes of record i in that set.
    """
    acc = {s: ([0], []) for s in sets}
    for rec in records:
        raw = raw_features(rec, sets, author_bins)
        for s in sets:
            hs = sorted({feature_hash(s, v) for v in raw[s]})
            ptr, vals = acc[s]
            vals.extend(hs)
            ptr.append(ptr[-1] + len(hs))
    return {s: (np.asarray(p, dtype=np.int64), np.asarray(v, dtype=np.uint64)) for s, (p, v) in acc.items()}
