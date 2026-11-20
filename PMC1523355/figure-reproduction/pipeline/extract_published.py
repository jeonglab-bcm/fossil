"""Read the printed values of Tables 1-5 from the article XML, and Fig. 1B's from its image transcription.

Usage: extract_published.py ARTICLE_XML OUT.json [--check COMMITTED.json]

Tables 1-5 are XML tables: their cells are read by row label, as printed (strings, so the printed
precision travels with them). Fig. 1B is a table drawn inside the figure image; its 16 numbers are
transcribed below, once, from figure-reproduction/published/figure-1.jpg. --check compares the result with
the committed output/published_values.json and exits 1 on any difference.
"""
import html
import json
import re
import sys

# Fig. 1B: rows = study population's average CER; per row power (AUROC) for one RF and for the 4-RF score.
FIG1B = {
    "1.5%": {"one_rf": [".28", ".54"], "four_rf": [".77", ".61"]},
    "3%": {"one_rf": [".25", ".55"], "four_rf": [".74", ".63"]},
    "6%": {"one_rf": [".19", ".55"], "four_rf": [".60", ".65"]},
    "9%": {"one_rf": [".14", ".56"], "four_rf": [".44", ".66"]},
}


def text(cell):
    t = re.sub(r"<[^>]+>", "", cell)
    return html.unescape(t).replace("–", "-").replace("−", "-").strip()


def rows_of(xml, tid):
    m = re.search(rf'<table-wrap[^>]*id="{tid}".*?</table-wrap>', xml, re.S)
    if not m:
        raise SystemExit(f"no table {tid}")
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", m.group(0), re.S):
        cells = [text(c) for c in re.findall(r"<td[^>]*?(?:/>|>(.*?)</td>)", tr, re.S)]
        cells = [c for c in cells if c != ""]
        if cells:
            out.append(cells)
    return out


def num(s):
    """'-.19†' -> '-.19'; '(.53)' -> '.53'; '6%' -> '6'."""
    m = re.search(r"-?\d*\.?\d+", s.replace(",", ""))
    if not m:
        raise ValueError(s)
    return m.group(0)


def table1(xml):
    rows = rows_of(xml, "T1")
    out = {}
    names = {"Risk factor absent": "rf_absent", "Risk factor present": "rf_present",
             "0-1 Risk factors": "idx_0_1", "≥ 2 Risk factors": "idx_ge2",
             "0 Risk factors": "k0", "1 Risk factors": "k1", "2 Risk factors": "k2",
             "3 Risk factors": "k3", "≥ 4 Risk factors": "k_ge4"}
    for r in rows:
        for label, key in names.items():
            if r[0].startswith(label):
                share = re.search(r"\(([\d.]+)%", r[0]).group(1)
                out[key] = {"share": share, "cer": num(r[1]), "rrr": num(r[2]), "nnt": num(r[3])}
                if len(r) > 4:
                    out[key]["power"] = num(r[4])
    power = {"conventional": out["rf_absent"].pop("power"), "dichotomized": out["idx_0_1"].pop("power"),
             "continuous": out["k0"].pop("power")}
    foot = num(re.search(r"Risk Index was ([\d.]+)", xml).group(1))
    return {"groups": out, "power": power, "auroc_continuous": foot}


def grid(xml, tid, cols):
    rows = rows_of(xml, tid)
    out = {}
    for r in rows:
        vals = r[-len(cols):]
        lead = r[: len(r) - len(cols)]
        if lead and re.fullmatch(r"\d\.\d", lead[-1]):
            out[lead[-1]] = dict(zip(cols, vals))
    return out


def table3(xml):
    g = grid(xml, "T3", ["1", "3", "6"])
    return {o: {k: {"power": num(v.split("(")[0]), "auroc": num(v.split("(")[1])} for k, v in r.items()} for o, r in g.items()}


def table4(xml):
    rows = rows_of(xml, "T4")
    out = {}
    for r in rows:
        name = r[0].lower()
        for key in ("perfect", "uniform", "incomplete reverse", "reverse"):
            if name.startswith(key):
                out[key.replace(" ", "_")] = {"weights": r[1:4], "auroc": num(r[4]), "power": num(r[5])}
                break
    return out


def table5(xml):
    rows = rows_of(xml, "T5")
    out = {}
    for r in rows:
        if len(r) == 3 and re.fullmatch(r"\d", r[0]):
            out[r[0]] = {"conventional": num(r[1]), "risk_stratified": num(r[2])}
    return out


def main():
    args = sys.argv[1:]
    check = None
    if "--check" in args:
        i = args.index("--check")
        check = args[i + 1]
        del args[i:i + 2]
    xml_path, out = args
    xml = open(xml_path, encoding="utf-8").read()
    pv = {
        "source": "PMC1523355.1.xml (Tables 1-5); Fig. 1B transcribed from figure-1.jpg",
        "table1": table1(xml),
        "table2": grid(xml, "T2", ["10%", "25%", "50%"]),
        "table3": table3(xml),
        "table4": table4(xml),
        "table5": table5(xml),
        "fig1b": FIG1B,
    }
    for k, v in pv["table2"].items():
        pv["table2"][k] = {c: num(x) for c, x in v.items()}
    s = json.dumps(pv, indent=1, ensure_ascii=False) + "\n"
    open(out, "w", encoding="utf-8").write(s)
    if check:
        same = json.load(open(check, encoding="utf-8")) == pv
        print(f"published values {'match' if same else 'DIFFER from'} {check}", file=sys.stderr)
        sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()
