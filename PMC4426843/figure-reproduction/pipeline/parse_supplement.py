"""Convert the paper's Supplementary Tables S1-S5 (.xls) into tidy TSV files.

Usage: python parse_supplement.py SUPP_DIR OUT_DIR

Bleazard T, Lamb JA, Griffiths-Jones S. Bioinformatics 31(10):1592-1598 (2015), supplementary
data, CC BY 4.0. Values are copied as published.
"""
import csv
import sys
from pathlib import Path

import xlrd


def sheet(path, idx=0):
    return xlrd.open_workbook(str(path)).sheet_by_index(idx)


def num(x):
    return int(x) if isinstance(x, float) and x == int(x) else x


def write(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def study_ids(first_authors, species):
    """Disambiguate repeated first authors (Chen 2010 and Chen 2013b) by column order."""
    seen, out = {}, []
    for a in first_authors:
        seen[a] = seen.get(a, 0) + 1
        out.append(a if seen[a] == 1 else f"{a}{seen[a]}")
    return out


def main(src, out):
    src, out = Path(src), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    s1 = sheet(src / "supp_btv023_supplementary_table_1.xls")
    rows = []
    for r in range(3, s1.nrows):
        term, size, mean, p = s1.row_values(r)
        go_id, _, name = term.partition("~")
        rows.append([go_id, name, int(size), repr(mean), repr(p)])
    write(out / "s1_terms.tsv", ["go_id", "go_name", "term_size", "empirical_mean", "hyper_p"], rows)

    s2 = sheet(src / "supp_btv023_supplementary_table_2.xls")
    hdr = [str(c) for c in s2.row_values(2)]
    rows = [[num(c) for c in s2.row_values(r)] for r in range(3, s2.nrows)
            if any(str(c).strip() for c in s2.row_values(r))]
    write(out / "s2_studies.tsv", hdr, rows)

    b = xlrd.open_workbook(str(src / "supp_btv023_supplementary_table_3.xls"))
    lists = b.sheet_by_name("miRNA Lists")
    authors = [str(c) for c in lists.row_values(2)[1:]]
    species = [str(c) for c in lists.row_values(3)[1:]]
    ids = study_ids(authors, species)
    rows = []
    for j, sid in enumerate(ids, start=1):
        for r in range(5, lists.nrows):
            v = str(lists.cell_value(r, j)).strip()
            if v:
                rows.append([sid, species[j - 1], v])
    write(out / "s3_mirna_lists.tsv", ["study", "species", "mirna"], rows)
    rows = []
    for sname, tag in [("miRanda Targets", "miranda"), ("Intersection Targets", "intersection"),
                       ("CLIP Targets", "clip")]:
        s = b.sheet_by_name(sname)
        assert [str(c) for c in s.row_values(0)[1:]] == authors
        for j, sid in enumerate(ids, start=1):
            stated = int(s.cell_value(2, j))
            genes = [str(s.cell_value(r, j)).strip() for r in range(3, s.nrows)]
            genes = [g for g in genes if g]
            rows += [[tag, sid, species[j - 1], stated, g] for g in genes]
    write(out / "s3_targets.tsv", ["prediction", "study", "species", "stated_count", "gene"], rows)

    b = xlrd.open_workbook(str(src / "supp_btv023_supplementary_table_4.xls"))
    s = b.sheet_by_name("Summary")
    write(out / "s4_summary.tsv", [str(c) for c in s.row_values(2)],
          [[num(c) for c in s.row_values(r)] for r in range(3, s.nrows)])
    s = b.sheet_by_name("miRNA Lists")
    a4 = [str(c) for c in s.row_values(0)[1:]]
    write(out / "s4_mirna_lists.tsv", ["study", "mirna"],
          [[a, str(s.cell_value(r, j)).strip()] for j, a in enumerate(a4, start=1)
           for r in range(2, s.nrows) if str(s.cell_value(r, j)).strip()])

    s5 = sheet(src / "supp_btv023_supplementary_table_5.xls")
    rows = []
    for r in range(3, s5.nrows):
        term, size, obs, mean, p, bh = s5.row_values(r)
        go_id, _, name = term.partition("~")
        rows.append([go_id, name, int(size), repr(obs), repr(mean), repr(p), bh])
    write(out / "s5_axonogenesis.tsv",
          ["go_id", "go_name", "term_size", "observed_overlap", "mean_random_overlap",
           "empirical_p", "bh_005"], rows)
    print(s5.row_values(0)[0])


if __name__ == "__main__":
    main(*sys.argv[1:3])
