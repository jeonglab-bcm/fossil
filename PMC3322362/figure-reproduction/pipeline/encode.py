"""Encode RNA-protein pairs as RPISeq's 599 features and write them as an ARFF file.

Built from the paper's Methods ("Alternative representations of protein and RNA sequences"):

- protein: the conjoint triad representation of Shen et al. (ref. 28). The 20 amino acids are
  put in 7 groups, {A,G,V} {I,L,F,P} {Y,M,T,S} {H,N,Q,W} {R,K} {D,E} {C}, and the sequence is
  described by the frequencies of its 343 (7 x 7 x 7) group 3-mers;
- RNA: the frequencies of its 256 (4 x 4 x 4 x 4) 4-mers of A, C, G, U;
- each block holds "normalized frequencies". The paper defers to ref. 28 for the
  normalization; we use Shen et al.'s d = (f - min) / max over the block, which is also what
  the authors' later published code (Dobbs-Lab/RPIMotif, createARFF_test.pl) computes.

Where the paper is silent:
- a 3-mer or 4-mer containing a letter outside the alphabet (X, N, ...) is not counted. Only
  RNAs have such letters in the RPI2241 files (65 of the 4,482 pairs, mostly N); no
  protein does;
- T in an RNA is read as U (21 pairs carry a T).

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


def kmer_features(seq, groups, k, size):
    """Counts of the k-mers over `groups` (k-mers with an unknown letter are skipped),
    normalized as (count - min) / max."""
    counts = [0] * size
    codes = [groups.get(c) for c in seq]
    n = len(set(groups.values()))
    for i in range(len(codes) - k + 1):
        window = codes[i:i + k]
        if None in window:
            continue
        idx = 0
        for c in window:
            idx = idx * n + c
        counts[idx] += 1
    lo, hi = min(counts), max(counts)
    return [(c - lo) / hi if hi else 0.0 for c in counts]


def protein_features(seq):
    return kmer_features(seq.upper(), PROTEIN_GROUPS, 3, 343)


def rna_features(seq):
    return kmer_features(seq.upper().replace("T", "U"), RNA_GROUPS, 4, 256)


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
    return "{" + ",".join(f"{i} {x!r}" for i, x in enumerate(v)) + f",599 {label}" + "}\n"


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
