"""Parse the benchmark (Additional file 1, a PDF) and PDB186 (Lou et al. 2014, Dataset S2).

Usage: parse_datasets.py S1.pdf lou_s002.txt OUTDIR

Writes OUTDIR/benchmark.fasta, OUTDIR/pdb186.fasta (headers ">ID|label", label 1 binds DNA)
and OUTDIR/datasets.json (counts and every defect of the supplement, handled as listed there).
"""
import json
import re
import sys
from pathlib import Path

import fitz  # pymupdf


def parse_benchmark(pdf):
    text = "".join(page.get_text() for page in fitz.open(pdf))
    pos_at = text.index("(1).525 DNA-binding proteins")
    neg_at = text.index("(2).550 non DNA-binding proteins")
    records = []
    stray = []
    for label, block in ((1, text[pos_at:neg_at]), (0, text[neg_at:])):
        for chunk in block.split(">")[1:]:
            lines = chunk.strip().splitlines()
            pid = lines[0].strip()
            raw = "".join(l.strip() for l in lines[1:])
            seq = re.sub(r"[^A-Za-z]", "", raw).upper()
            if seq != raw.upper().replace(" ", ""):
                stray.append({"id": pid, "removed": re.sub(r"[A-Za-z ]", "", raw)})
            records.append((pid, label, seq))
    return records, stray


def parse_pdb186(path):
    records = []
    for line in Path(path).read_text().splitlines()[1:]:
        f = line.split()
        if len(f) == 4:
            records.append((f[0], 1 if f[2] == "Yes" else 0, f[3].upper()))
    return records


def write_fasta(path, records):
    with open(path, "w") as out:
        for pid, label, seq in records:
            out.write(f">{pid}|{label}\n{seq}\n")


def main(pdf, s002, outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    bench, stray = parse_benchmark(pdf)
    pdb186 = parse_pdb186(s002)
    ids = [r[0] for r in bench]
    assert len(set(ids)) == len(ids) == 1075, len(ids)
    npos = sum(r[1] for r in bench)
    assert (npos, len(bench) - npos) == (525, 550)
    assert len(pdb186) == 186 and sum(r[1] for r in pdb186) == 93
    write_fasta(out / "benchmark.fasta", bench)
    write_fasta(out / "pdb186.fasta", pdb186)
    dna = [pid for pid, _, s in bench if set(s) <= set("ACGTU")]
    with_x = [pid for pid, _, s in bench if "X" in s]
    no_chain = [pid for pid, _, _ in bench if re.fullmatch(r"[0-9][A-Za-z0-9]{3}", pid)]
    short = [pid for pid, _, s in bench if len(s) < 50]
    shared = sorted(set(ids) & {r[0] for r in pdb186})
    info = {
        "benchmark": {"sequences": len(bench), "positives": npos, "negatives": len(bench) - npos,
                      "length_min": min(len(s) for _, _, s in bench),
                      "length_max": max(len(s) for _, _, s in bench)},
        "pdb186": {"sequences": len(pdb186), "positives": 93, "negatives": 93},
        "defects": {
            "dna_strands_among_positives": dna,
            "negatives_with_X": with_x,
            "ids_without_chain_letter": no_chain,
            "shorter_than_50": short,
            "stray_characters_removed": stray,
            "chain_ids_in_both_benchmark_and_pdb186": shared,
        },
        "handling": "All 1,075 sequences are used as supplied (digits from the PDF removed). "
                    "The DNA strands and X-containing sequences are dropped only in a sensitivity run.",
    }
    (out / "datasets.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info["benchmark"]), {k: len(v) for k, v in info["defects"].items()})


if __name__ == "__main__":
    main(*sys.argv[1:4])
