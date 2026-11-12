"""Build the gene-identifier tables the pipeline uses, from NCBI Gene and GEO platform annotations.

Usage: build_annotation.py RAW_DIR OUTDIR

NCBI's gene_info and gene_history and GEO's .annot files are regenerated continually, so they
cannot be pinned by checksum. This script was run once (on the files downloaded on the date in
annotation/README.md) and its small outputs are committed; the pipeline reads only those.

RAW_DIR holds Homo_sapiens.gene_info.gz, gene_history_human.tsv.gz (tax 9606 rows of
gene_history.gz), GPL96.annot.gz, GPL8300.annot.gz, GPL2695.annot.gz, GPL3044_table.tsv and
GPL3289_table.tsv (the platform tables of the GPL3044 and GPL3289 family SOFT files), and
c2.symbols.gmt.

Writes (tab-separated, gzip):
  symbol_entrez.tsv.gz   C2 symbols and the paper's printed CORG symbols -> Entrez Gene ID and
                         how it was found (symbol, synonym, history, unmapped)
  entrez_symbol.tsv.gz   Entrez Gene ID -> current official symbol (all human genes)
  probe_entrez_<GPL>.tsv.gz   probe -> Entrez Gene ID (single-gene probes) for GPL96, GPL8300, GPL2695
  clone_entrez.tsv.gz    IMAGE clone -> Entrez Gene ID (from GPL2695's annotation)
  spot_clone_<GPL>.tsv.gz     spot -> clone (SPOT_ID) for GPL3044 and GPL3289
"""

from __future__ import annotations

import csv
import gzip
import sys
from collections import defaultdict
from pathlib import Path

import prepare_data as P
from compare import TABLE1, TABLE_S2


def write(path, rows, header):
    with gzip.open(path, "wt", encoding="utf-8", newline="") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")


def annot(path):
    probe, clone = {}, {}
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        header = None
        for line in f:
            if line.startswith(("!", "#", "^")):
                continue
            parts = line.rstrip("\n").split("\t")
            if header is None:
                header = parts
                i_id, i_gene = header.index("ID"), header.index("Gene ID")
                i_clone = header.index("Platform_CLONEID") if "Platform_CLONEID" in header else None
                continue
            gid = parts[i_gene] if len(parts) > i_gene else ""
            if gid and "///" not in gid:
                probe[parts[i_id]] = gid
                if i_clone is not None and parts[i_clone]:
                    clone[parts[i_clone]] = gid
    return probe, clone


def main(raw: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    tables = P.entrez_tables_from(raw / "Homo_sapiens.gene_info.gz", raw / "gene_history_human.tsv.gz")
    symbol, synonyms, history, display = tables
    c2 = P.read_gmt(raw / "c2.symbols.gmt")
    syms = sorted({g for m in c2.values() for g in m}
                  | {s for tb in (TABLE1, TABLE_S2) for rows in tb.values() for r in rows for s in r[4].split()})
    rows = []
    used = set()
    for s in syms:
        gid, how = P.symbol_to_entrez(s, tables)
        rows.append((s, gid or "", how))
        if gid:
            used.add(gid)
    write(out / "symbol_entrez.tsv.gz", rows, ["symbol", "entrez", "how"])
    clone_all = {}
    for gpl in ("GPL96", "GPL8300", "GPL2695"):
        probe, clone = annot(raw / f"{gpl}.annot.gz")
        used |= set(probe.values())
        clone_all.update(clone)
        write(out / f"probe_entrez_{gpl}.tsv.gz", sorted(probe.items()), ["probe", "entrez"])
    write(out / "clone_entrez.tsv.gz", sorted(clone_all.items()), ["clone", "entrez"])
    for gpl in ("GPL3044", "GPL3289"):
        spots = []
        for p in csv.DictReader(open(raw / f"{gpl}_table.tsv", encoding="utf-8"), delimiter="\t"):
            if p["SPOT_ID"]:
                spots.append((p["ID"], p["SPOT_ID"]))
        write(out / f"spot_clone_{gpl}.tsv.gz", spots, ["spot", "clone"])
    write(out / "entrez_symbol.tsv.gz", sorted(display.items(), key=lambda kv: int(kv[0])), ["entrez", "symbol"])


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
