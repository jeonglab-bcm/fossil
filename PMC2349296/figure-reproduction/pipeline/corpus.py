"""Load the five unified PPI corpora (simple Turku XML) and evaluate pairs under the paper's rules.

The rules (Pyysalo et al. 2008, Materials and methods, "Evaluation methods and metrics"):
  * no directionality: REL(P1,P2) == REL(P2,P1);
  * no interaction type;
  * entity identity by occurrence: a pair matches only the same two entity occurrences.

The mirror (github.com/metalrt/ppi-dataset) splits each corpus into -train.xml and -test.xml.
The split is the mirror author's; the paper evaluates whole corpora, so both files are merged.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

CORPORA = ["AIMed", "BioInfer", "HPRD50", "IEPA", "LLL"]


@dataclass
class Entity:
    id: str
    text: str
    spans: list[tuple[int, int]]  # character spans, end exclusive


@dataclass
class Sentence:
    id: str
    doc: str
    text: str
    entities: list[Entity]
    interactions: set[frozenset[str]]  # undirected pairs of entity ids; self-pairs are 1-sets
    raw_interactions: int = 0
    extra: dict = field(default_factory=dict)


def parse_offsets(s: str) -> list[tuple[int, int]]:
    """'12-17,20-25' -> [(12, 17), (20, 25)].

    The original Turku format has inclusive end offsets; this mirror's are end-exclusive
    (text[a:b] equals the entity text for all 8,443 entity spans), so they are used as given.
    """
    out = []
    for part in s.split(","):
        a, b = part.split("-")
        out.append((int(a), int(b)))
    return out


def load(corpus: str, data_dir: Path) -> list[Sentence]:
    sentences: list[Sentence] = []
    for part in ("train", "test"):
        root = ET.parse(data_dir / f"{corpus}-{part}.xml").getroot()
        for doc in root.iter("document"):
            for s in doc.iter("sentence"):
                ents = [
                    Entity(e.get("id"), e.get("text"), parse_offsets(e.get("charOffset")))
                    for e in s.findall("entity")
                ]
                ints = s.findall("interaction")
                pairs = {frozenset((i.get("e1"), i.get("e2"))) for i in ints}
                sentences.append(
                    Sentence(s.get("id"), doc.get("id"), s.get("text"), ents, pairs, len(ints))
                )
    return sentences


def filter_noninteracting(sentences: list[Sentence]) -> list[Sentence]:
    """Table 4: keep only entities that take part in at least one interaction."""
    out = []
    for s in sentences:
        used = set().union(*s.interactions) if s.interactions else set()
        ents = [e for e in s.entities if e.id in used]
        out.append(Sentence(s.id, s.doc, s.text, ents, s.interactions, s.raw_interactions, s.extra))
    return out


def candidate_pairs(s: Sentence) -> list[frozenset[str]]:
    """All unordered pairs of distinct entity occurrences in the sentence."""
    return [frozenset((a.id, b.id)) for a, b in combinations(s.entities, 2)]


def score(predicted: dict[str, set[frozenset[str]]], sentences: list[Sentence]) -> dict:
    tp = fp = fn = 0
    for s in sentences:
        pred = predicted.get(s.id, set())
        gold = s.interactions
        tp += len(pred & gold)
        fp += len(pred - gold)
        fn += len(gold - pred)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "P": p, "R": r, "F": f}
