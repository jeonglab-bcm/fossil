#!/usr/bin/env python3
"""Preprocessing for RelEx: MedPost input, token alignment, Stanford Parser input.

  preprocess.py medpost-input DATA_DIR OUT_DIR
      Writes, per corpus, <C>.orig.mp_in (sentence text, for Table 3 token counts) and
      <C>.split.mp_in (text with a space inserted at every entity boundary that falls inside a
      whitespace-delimited word, so that every entity is a whole number of tokens).
      Both use MedPost's -idtext format: an id line, then a text line.

  preprocess.py align DATA_DIR MP_DIR OUT_DIR
      Reads MedPost output (<C>.orig.mp_out, <C>.split.mp_out; '-idtext -id -penn -nosegment'),
      aligns the tokens to character offsets and writes:
        <C>.tokens.json    per sentence: tokens, tags, offsets, entity -> token indices
        <C>.parse_in       one sentence per line, word/TAG, for Stanford Parser 1.5.1
        tokens_medpost.csv per-sentence average of MedPost tokens on the unmodified text

The paper does not say how entity names that are only part of a word ("p53-dependent") were
handled; splitting at entity boundaries is our choice.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import CORPORA, load  # noqa: E402

# Penn Treebank conventions expected by the 2006 WSJ-trained grammar.
BRACKETS = {"(": "-LRB-", ")": "-RRB-", "[": "-LSB-", "]": "-RSB-", "{": "-LCB-", "}": "-RCB-"}


def split_text(text: str, spans: list[tuple[int, int]]) -> tuple[str, list[int]]:
    """Insert a space at entity boundaries inside words. Returns the new text and a map from
    new character index to original index (-1 for inserted spaces)."""
    cuts = set()
    for a, b in spans:
        for x in (a, b):
            if 0 < x < len(text) and not text[x - 1].isspace() and not text[x].isspace():
                cuts.add(x)
    out, back = [], []
    for i, ch in enumerate(text):
        if i in cuts:
            out.append(" ")
            back.append(-1)
        out.append(ch)
        back.append(i)
    return "".join(out), back


def write_medpost_input(data_dir: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for c in CORPORA:
        with open(out / f"{c}.orig.mp_in", "w") as fo, open(out / f"{c}.split.mp_in", "w") as fs:
            for s in load(c, data_dir):
                spans = [sp for e in s.entities for sp in e.spans]
                text = " ".join(s.text.split())  # one line per sentence
                fo.write(f"{s.id}\n{text}\n")
                fs.write(f"{s.id}\n{split_text(s.text, spans)[0].replace(chr(10), ' ')}\n")


def read_medpost(path: Path) -> dict[str, list[tuple[str, str]]]:
    lines = path.read_text().splitlines()
    out = {}
    for i in range(0, len(lines) - 1, 2):
        toks = []
        for t in lines[i + 1].split():
            w, _, tag = t.rpartition("/")
            toks.append((w, tag))
        out[lines[i].strip()] = toks
    return out


def align(tokens: list[str], text: str) -> list[tuple[int, int]]:
    offs, pos = [], 0
    for w in tokens:
        j = text.find(w, pos)
        if j < 0 or text[pos:j].strip():
            raise ValueError(f"cannot align {w!r} at {pos} in {text!r}")
        offs.append((j, j + len(w)))
        pos = j + len(w)
    return offs


def write_alignment(data_dir: Path, mp_dir: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    counts = []
    for c in CORPORA:
        sents = load(c, data_dir)
        orig = read_medpost(mp_dir / f"{c}.orig.mp_out")
        split = read_medpost(mp_dir / f"{c}.split.mp_out")
        missing = [s.id for s in sents if s.id not in orig or s.id not in split]
        if missing:
            raise SystemExit(f"{c}: MedPost output lacks {len(missing)} sentences, e.g. {missing[:3]}")
        counts.append({"corpus": c, "tokens_medpost": sum(len(orig[s.id]) for s in sents) / len(sents)})
        records = []
        with open(out / f"{c}.parse_in", "w") as fp:
            for s in sents:
                spans_all = [sp for e in s.entities for sp in e.spans]
                stext, back = split_text(s.text, spans_all)
                words = [w for w, _ in split[s.id]]
                tags = [t for _, t in split[s.id]]
                offs_new = align(words, stext)
                # back-map to original character offsets
                offs = [(back[a], back[b - 1] + 1) for a, b in offs_new]
                ent_tokens = {}
                for e in s.entities:
                    idx = [k for k, (a, b) in enumerate(offs)
                           if any(a < eb and b > ea for ea, eb in e.spans)]
                    ent_tokens[e.id] = idx
                records.append({"id": s.id, "words": words, "tags": tags, "offsets": offs,
                                "entities": ent_tokens,
                                "interactions": sorted(sorted(p) for p in s.interactions)})
                pw = []
                for w, t in zip(words, tags):
                    if w in BRACKETS:
                        w = t = BRACKETS[w]
                    pw.append(f"{w}/{t}")
                fp.write(" ".join(pw) + "\n")
        (out / f"{c}.tokens.json").write_text(json.dumps(records))
        unaligned = sum(1 for r in records for v in r["entities"].values() if not v)
        print(f"{c}: {len(records)} sentences, {unaligned} entities without tokens")
    with open(out / "tokens_medpost.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["corpus", "tokens_medpost"])
        w.writeheader()
        w.writerows(counts)


if __name__ == "__main__":
    if sys.argv[1] == "medpost-input":
        write_medpost_input(Path(sys.argv[2]), Path(sys.argv[3]))
    elif sys.argv[1] == "align":
        write_alignment(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
    else:
        raise SystemExit(__doc__)
