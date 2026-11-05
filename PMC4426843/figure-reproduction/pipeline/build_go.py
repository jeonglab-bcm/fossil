"""Gene-to-GO biological process table from the Ensembl 75 BioMart MySQL dumps.

Usage: python build_go.py MART_DIR SPECIES OUT.tsv
  SPECIES: hsapiens or mmusculus

Writes one row per (gene_id, gene_name, go_id, go_name, evidence) for biological_process terms.
Annotations are used as Ensembl lists them (no propagation to ancestor terms).
"""
import gzip
import re
import sys
from pathlib import Path


def columns(sql, table):
    cols, inside = [], False
    for line in gzip.open(sql, "rt", errors="replace"):
        if line.startswith(f"CREATE TABLE `{table}`"):
            inside = True
            continue
        if inside:
            m = re.match(r"\s+`([^`]+)`", line)
            if m:
                cols.append(m.group(1))
            elif line.startswith(")"):
                return cols
    raise SystemExit(f"table {table} not in {sql}")


def rows(path, cols, keep):
    idx = [cols.index(k) for k in keep]
    for line in gzip.open(path, "rt", errors="replace"):
        f = line.rstrip("\n").split("\t")
        yield [None if f[i] == "\\N" else f[i] for i in idx]


def main(mart, sp, out):
    mart = Path(mart)
    sql = mart / "ensembl_mart_75.sql.gz"
    tm = f"{sp}_gene_ensembl__translation__main"
    go = f"{sp}_gene_ensembl__go_GO__dm"
    tcols = columns(sql, tm)
    gcols = columns(sql, go)
    tl = {}
    for key, gid, name, bt in rows(mart / f"{tm}.txt.gz", tcols,
                                   ["translation_id_1068_key", "stable_id_1023",
                                    "display_label_1074", "biotype_1020"]):
        tl[key] = (gid, name or "", bt)
    seen = set()
    n_missing = 0
    with open(out, "w") as fo:
        fo.write("gene_id\tgene_name\tgene_biotype\tgo_id\tgo_name\tevidence\n")
        for key, acc, ns, name, ev in rows(mart / f"{go}.txt.gz", gcols,
                                           ["translation_id_1068_key", "dbprimary_acc_1074",
                                            "namespace_1003", "name_1006", "linkage_type_1024"]):
            if ns != "biological_process" or acc is None:
                continue
            if key not in tl:
                n_missing += 1
                continue
            gid, gname, bt = tl[key]
            r = (gid, gname, bt, acc, name, ev)
            if r in seen:
                continue
            seen.add(r)
            fo.write("\t".join(r) + "\n")
    print(f"{len(seen)} gene-term-evidence rows; {n_missing} rows with unknown translation",
          file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:4])
