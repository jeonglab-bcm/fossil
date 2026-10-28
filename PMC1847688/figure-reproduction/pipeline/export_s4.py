"""Export Additional File 4 (a BIFF .xls workbook, one sheet) to CSV cell by cell.

Usage: python export_s4.py S4.xls S4_LIMPIC.csv
Numbers are written as the shortest repr of the stored double, error cells as their Excel
text (#DIV/0!), blanks as empty fields.
"""

import csv
import sys

import xlrd


def main(src, dst):
    sheet = xlrd.open_workbook(src).sheet_by_index(0)
    with open(dst, "w", newline="") as f:
        w = csv.writer(f)
        for r in range(sheet.nrows):
            row = []
            for c in range(sheet.ncols):
                cell = sheet.cell(r, c)
                if cell.ctype == xlrd.XL_CELL_NUMBER:
                    row.append(repr(cell.value))
                elif cell.ctype == xlrd.XL_CELL_ERROR:
                    row.append(xlrd.error_text_from_code[cell.value])
                else:
                    row.append(str(cell.value))
            w.writerow(row)


if __name__ == "__main__":
    main(*sys.argv[1:3])
