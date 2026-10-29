"""Additional File 3 (Excel 97 workbook, one filled sheet) as CSV.

Numbers are written as Python's shortest round-trip form, and whole numbers without ".0".
Usage: export_af3.py S3.xls OUT.csv
"""
import csv
import sys

import xlrd

book = xlrd.open_workbook(sys.argv[1])
sheets = [s for s in book.sheets() if s.nrows]
assert len(sheets) == 1, [s.name for s in book.sheets()]
with open(sys.argv[2], 'w', newline='') as out:
    w = csv.writer(out)
    for r in range(sheets[0].nrows):
        w.writerow([(str(int(v)) if v == int(v) else repr(v)) if isinstance(v, float) else v
                    for v in sheets[0].row_values(r)])
