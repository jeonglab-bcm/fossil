"""Write the archived PROSPECTR sets restricted to the paper's Table 1 features.

  prepare.py DOWNLOADS OUTDIR

The 2006 ARFFs carry 64 features; Table 1 of the paper lists 23. This keeps the ones the ARFFs
have (gene, cDNA, protein, UTR lengths, exons, GC, transmembrane, signal peptide, paralog identity,
mouse/rat/worm/fly identity, mouse Ka, Ks and Ka/Ks) and adds CDS length (cDNA minus both UTRs),
which Figure 2 uses and the ARFFs lack. Distance to the nearest gene, the paralog flag, yeast and
Arabidopsis identity and the CpG flags are not in the ARFFs.
"""

import sys
from pathlib import Path

from prospectr_adtree import read_arff

TABLE1 = ["gene_length", "cds_length", "cdna_length", "residue_length", "len_3utr", "len_5utr", "exons",
          "gc", "transmembrane", "sigpep", "paralog_identity", "mouse_identity", "rat_identity",
          "worm_identity", "fly_identity", "mouse_dn", "mouse_ds", "mouse_dnds"]
SETS = {"omim_trainingset.arff": "table1_training.arff", "hgmd_testset.arff": "table1_hgmd.arff",
        "pocus_testset.arff": "table1_pocus.arff"}


def fmt(v):
    if v is None:
        return "?"
    return repr(int(v)) if float(v).is_integer() else repr(v)


def write(src, dst):
    d = read_arff(src)
    idx = {a.name: i for i, a in enumerate(d.attributes)}
    with open(dst, "w", newline="\n") as f:
        f.write("@relation table1_features\n")
        for name in TABLE1:
            if name in ("transmembrane", "sigpep"):
                f.write(f"@attribute {name} {{0,1}}\n")
            else:
                f.write(f"@attribute {name} numeric\n")
        f.write("@attribute phenotype {disease,normal}\n@data\n")
        for r in d.rows:
            vals = []
            for name in TABLE1:
                if name == "cds_length":
                    c, u3, u5 = (r[idx[k]] for k in ("cdna_length", "len_3utr", "len_5utr"))
                    v = None if None in (c, u3, u5) else c - u3 - u5
                elif name in ("transmembrane", "sigpep"):
                    v = r[idx[name]]
                    vals.append("?" if v is None else d.attributes[idx[name]].values[int(v)])
                    continue
                else:
                    v = r[idx[name]]
                vals.append(fmt(v))
            vals.append(d.class_attribute.values[int(r[d.class_index])])
            f.write(",".join(vals) + "\n")


def main(downloads, outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    for src, dst in SETS.items():
        write(Path(downloads) / src, out / dst)


if __name__ == "__main__":
    main(*sys.argv[1:3])
