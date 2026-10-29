"""Encode RNA-protein pairs as RPISeq's 599 features and write a Weka ARFF file.

The encoding follows "Usha's conjoint triads" in createARFF_test.pl of Dobbs-Lab/RPIMotif
(Muppirala's code, reused in the lab's 2014 RPIMotif method) line by line:

- protein: 343 counts of 3-mers over the 7-group alphabet {AGV}{ILFP}{YMTS}{HNQW}{RK}{DE}{C};
- RNA: T becomes U, then 256 counts of 4-mers over A, U, C, G;
- each block is scaled as (count - min) / max, Shen et al.'s normalization.

Two quirks of the Perl code are kept, because they change feature values:
- its filter for letters outside the alphabets never matches (the pattern is a string that
  includes the slashes), so an unknown letter stays in the sequence and is looked up as group 0
  (A, G, V for proteins; A for RNA);
- numbers are printed as Perl prints them, with 15 significant digits.

Usage:
  python encode.py arff OUT.arff POS.rpi NEG.rpi [--rpi369 S3.txt]
      Pairs in .rpi format (>name / protein / RNA). Positives first, then negatives, each in
      file order. --rpi369 keeps only the positives listed in Additional File 3.
  python encode.py arff-pairs OUT.arff PAIRS.tsv PROTEIN.fa RNA.fa
      Pairs as "protein<TAB>RNA<TAB>label" with sequences looked up by name (IPMiner format).
  python encode.py arff-unlabelled OUT.arff PAIRS.tsv
      Pairs as "name<TAB>protein sequence<TAB>RNA sequence"; class written as "?".
"""

import sys

PROTEIN_GROUPS = {}
for g, letters in enumerate(["AGV", "ILFP", "YMTS", "HNQW", "RK", "DE", "C"]):
    for a in letters:
        PROTEIN_GROUPS[a] = g
RNA_GROUPS = {"A": 0, "U": 1, "C": 2, "G": 3}


def perl_num(x):
    """A number as Perl's print writes it (%.15g)."""
    return "%.15g" % x


def protein_features(seq):
    counts = [0] * 343
    for i in range(len(seq) - 2):
        k = PROTEIN_GROUPS.get(seq[i], 0) * 49 + PROTEIN_GROUPS.get(seq[i + 1], 0) * 7 + PROTEIN_GROUPS.get(seq[i + 2], 0)
        counts[k] += 1
    lo, hi = min(counts), max(counts)
    return [(c - lo) / hi for c in counts]


def rna_features(seq):
    seq = seq.replace("T", "U")
    counts = [0] * 256
    for i in range(len(seq) - 3):
        k = 0
        for j in range(4):
            k = k * 4 + RNA_GROUPS.get(seq[i + j], 0)
        counts[k] += 1
    lo, hi = min(counts), max(counts)
    return [(c - lo) / hi for c in counts]


def features(protein, rna):
    return protein_features(protein.strip()) + rna_features(rna.strip())


def header():
    lines = ["@relation interactions", ""]
    lines += [f"@attribute P{i + 1} NUMERIC" for i in range(343)]
    lines += [f"@attribute R{i + 1} NUMERIC" for i in range(256)]
    lines += ["@attribute class {0,1}", "", "@data", ""]
    return "\n".join(lines) + "\n"


def row(protein, rna, label):
    v = features(protein, rna)
    return "{" + ",".join(f"{i} {perl_num(x)}" for i, x in enumerate(v)) + f",599 {label}" + "}\n"


def read_rpi(path):
    out = []
    lines = open(path).read().split("\n")
    i = 0
    while i < len(lines):
        if lines[i].startswith(">"):
            out.append((lines[i][1:].strip(), lines[i + 1].strip(), lines[i + 2].strip()))
            i += 3
        else:
            i += 1
    return out


def read_fasta(path):
    d, k = {}, None
    for line in open(path):
        line = line.strip()
        if line.startswith(">"):
            k = line[1:].upper()
            d[k] = ""
        elif k:
            d[k] += line
    return d


def read_s3(path):
    pairs = set()
    for line in open(path).read().split("\n")[4:]:
        if "\t" in line:
            p, r = line.split("\t")
            pairs.add(f"{p.strip()},{r.strip()}")
    return pairs


def main(argv):
    mode, out = argv[0], argv[1]
    with open(out, "w") as f:
        f.write(header())
        if mode == "arff":
            pos, neg = read_rpi(argv[2]), read_rpi(argv[3])
            if "--rpi369" in argv:
                keep = read_s3(argv[argv.index("--rpi369") + 1])
                pos = [p for p in pos if p[0] in keep]
            for _, p, r in pos:
                f.write(row(p, r, 1))
            for _, p, r in neg:
                f.write(row(p, r, 0))
        elif mode == "arff-pairs":
            prot, rna = read_fasta(argv[3]), read_fasta(argv[4])
            for line in open(argv[2]):
                if line.strip():
                    p, r, label = line.split()
                    f.write(row(prot[p.upper()], rna[r.upper()], int(label)))
        elif mode == "arff-unlabelled":
            for line in open(argv[2]):
                if line.strip() and not line.startswith("#"):
                    name, p, r = line.rstrip("\n").split("\t")[:3]
                    f.write(row(p, r, "?"))
        else:
            raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
