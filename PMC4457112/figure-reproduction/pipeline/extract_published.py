#!/usr/bin/env python3
"""Read Tables 1-3 of the paper from its PMC XML into published_values.json.

Values stay strings, as printed, so their precision is known.
Usage: extract_published.py PMC4457112.xml OUT.json
"""
import json
import re
import sys

from lxml import etree


def cells(tr):
    return ["".join(c.itertext()).strip() for c in tr.findall("./th") + tr.findall("./td")]


def main(src, out):
    root = etree.parse(src).getroot()
    res = {}
    for tid, key in (("ocu025-T1", "table1"), ("ocu025-T2", "table2")):
        tw = root.find(f".//table-wrap[@id='{tid}']")
        body = {}
        for tr in tw.findall(".//tbody/tr"):
            c = cells(tr)
            if len(c) != 4:
                continue
            m = c[0].upper()
            for col, v in zip(("cv", "2011", "2012"), c[1:]):
                v = v.replace(" ", " ")
                if m == "AUC":
                    mm = re.match(r"([\d.]+)\s*(?:\(([\d.]+),\s*([\d.]+)\))?", v)
                    body[f"{col}.auc"] = mm.group(1)
                    if mm.group(2):
                        body[f"{col}.auc_ci_low"] = mm.group(2)
                        body[f"{col}.auc_ci_high"] = mm.group(3)
                elif m == "MSE":
                    with_, without = v.split("/")
                    if with_.strip() != "*":
                        body[f"{col}.mse"] = with_.strip()
                    body[f"{col}.mse_sigmoid"] = without.strip()
                else:
                    name = {"AVERAGE_PRECISION": "average_precision", "F1": "f1", "ACCURACY": "accuracy"}[m]
                    body[f"{col}.{name}"] = v
        res[key] = body
    tw = root.find(".//table-wrap[@id='ocu025-T3']")
    t3, measure = {}, None
    cols = ("forward_selection", "chisq", "posthoc", "plus_pubtypes")
    for tr in tw.findall(".//tbody/tr"):
        c = cells(tr)
        if len([x for x in c if x]) == 1:
            measure = {"AUC": "auc", "AVERAGE_PRECISION": "average_precision", "F1": "f1", "MSE": "mse",
                       "NUMBER OF FEATURES": "n_features"}[c[0].upper()]
            continue
        model = "citation_only" if "ONLY" in c[0].upper() else "citation_plus_mesh"
        for col, v in zip(cols, c[1:]):
            t3[f"{model}.{col}.{measure}"] = v.replace(",", "") if measure == "n_features" else v
    res["table3"] = t3
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
        fh.write("\n")
    print(out, {k: len(v) for k, v in res.items()})


if __name__ == "__main__":
    main(*sys.argv[1:3])
