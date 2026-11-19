"""Every quantitative claim of the text, computed twice: from the paper's own Tables 1-8 (arithmetic: do we
compute each statement the way the paper did?) and from our run (observed: the only kind that sets a verdict).

Usage: claims.py PUBLISHED_VALUES_JSON SIMULATION_JSON OUT_JSON

A statement about printed table cells (a range, a sign, "every", "almost all") is evaluated on integers:
the paper's printed cells, and our values rounded half away from zero as the paper would have printed them.
A number the text gives (a range end, an average) is compared with our unrounded value at the text's
printed precision. Interpretations of vague words are in the field names: "almost all" is at least 90% of
the scenarios, "around" is within 1 point.
"""
import json
import math
import sys

import rommeta

TABLES = ("3", "4", "5", "6", "7", "8")
BIG = {"100/100", "134/66", "66/134"}
SMALL = {"10/10", "14/6", "6/14"}


def half_up(x):
    return math.floor(abs(x) + 0.5) * (1 if x >= 0 else -1)


class Cells:
    """The 2,268 cells of Tables 3-8, from the paper (printed integers) or our run (floats)."""

    def __init__(self, pub, sim=None, rounded=False):
        self.rows = []
        for n in TABLES:
            for i, prow in enumerate(pub["tables"][n]["rows"]):
                for col, printed in prow["cells"].items():
                    q, tau, m = col.split("|")
                    tol = None
                    if sim is None:
                        v = float(printed)
                    else:
                        s = sim["runs"]["main"][n][i]["tau0" if tau == "0" else "tau0.5"][m]
                        v = s[q]
                        se = s[f"{q}_se"]
                        if q in ("coverage", "power"):  # as in compare.py: p the mean of ours and the paper's
                            pp = (v + float(printed)) / 200
                            se = 100 * math.sqrt(max(pp * (1 - pp), 0) / 10_000)
                        tol = 0.5 + 3 * math.sqrt(2) * se
                        if rounded:
                            v = float(half_up(v))
                    self.rows.append({"table": n, "effect": prow["effect"], "n": prow["n"], "k": prow["k"],
                                      "tau": float(tau), "q": q, "m": m, "v": v, "tol": tol})

    def get(self, **kw):
        out = []
        for r in self.rows:
            ok = True
            for key, want in kw.items():
                val = r[key]
                if callable(want):
                    ok = want(val)
                elif isinstance(want, (set, tuple, list)):
                    ok = val in want
                else:
                    ok = val == want
                if not ok:
                    break
            if ok:
                out.append(r)
        return out

    def vals(self, **kw):
        return [r["v"] for r in self.get(**kw)]

    def ext(self, fn, sign=1, **kw):
        """The extreme cell (fn = min or max of sign x value): (sign x value, that cell's tolerance)."""
        r = fn(self.get(**kw), key=lambda r: sign * r["v"])
        return Stat(sign * r["v"], r["tol"])

    def mean(self, **kw):
        rs = self.get(**kw)
        v = sum(r["v"] for r in rs) / len(rs)
        if rs[0]["tol"] is None:
            return Stat(v, None)
        se = math.sqrt(sum(((r["tol"] - 0.5) / (3 * math.sqrt(2))) ** 2 for r in rs)) / len(rs)
        return Stat(v, 0.5 + 3 * math.sqrt(2) * se)

    def scenario(self, table, effect, n, k, tau):
        return {r["m"] + "|" + r["q"]: r["v"] for r in self.get(table=table, effect=effect, n=n, k=k, tau=tau)}

    def scenarios(self, tables=TABLES):
        keys = []
        for r in self.rows:
            key = (r["table"], r["effect"], r["n"], r["k"], r["tau"])
            if r["table"] in tables and key not in keys:
                keys.append(key)
        return keys


class Stat(float):
    """A number with the Monte Carlo tolerance it is compared at (None: printed precision)."""

    def __new__(cls, v, tol):
        x = float.__new__(cls, v)
        x.tol = tol
        return x


def yes(b):
    return "yes" if b else "no"


def fmt(x, nd=0):
    return round(x, 3) if nd is None else round(x, 3)


# ---- claims about the simulation tables: each returns {field name: value} for a Cells source ----

def smd_bias(c, rc):
    small_all = {(r["table"], r["effect"], r["k"], r["tau"]): r["v"] for r in rc.get(n=SMALL, q="bias", m="SMD")}
    big_all = {(r["table"], r["effect"], r["k"], r["tau"]): r["v"] for r in rc.get(n=BIG, q="bias", m="SMD")}
    return {
        "Table 3, 10/10: mean SMD bias over its 18 cells (%) [Abstract: about 5% towards no effect]": c.mean(table="3", n="10/10", q="bias", m="SMD"),
        "Table 3, 10/10: smallest SMD bias towards no effect (%) [Results: (-)4 to 6%]": c.ext(min, -1, table="3", n="10/10", q="bias", m="SMD"),
        "Table 3, 10/10: largest SMD bias towards no effect (%) [Results: (-)4 to 6%]": c.ext(max, -1, table="3", n="10/10", q="bias", m="SMD"),
        "SMD bias with 100 patients per arm (or 134/66, 66/134) nearer 0 than with 10 in every row of Tables 3-8": yes(
            all(abs(big_all[k]) <= abs(small_all[k]) for k in small_all)),
    }


def rom_bias(c, rc):
    t5 = dict(table="5", effect=(0.5, 0.8), q="bias", m="RoM")
    return {
        "Table 5, effects 0.5 and 0.8: lowest RoM bias (%) [Abstract: -4 to 2%]": c.ext(min, **t5),
        "Table 5, effects 0.5 and 0.8: highest RoM bias (%) [Abstract: -4 to 2%]": c.ext(max, **t5),
        "Table 5, 10/10, tau 0, effects 0.5 and 0.8: largest RoM bias towards unity (%) [Results: up to 2-3%]":
            c.ext(max, -1, table="5", n="10/10", tau=0.0, effect=(0.5, 0.8), q="bias", m="RoM"),
        "Table 5, 100/100, tau 0.5: largest RoM bias away from unity (%) [Results: up to 1-2%]":
            c.ext(max, table="5", n="100/100", tau=0.5, q="bias", m="RoM"),
        "Tables 3-6, 100/100, tau 0: every RoM bias below 0.5% in magnitude (prints as 0) [Results]": yes(
            all(v == 0 for v in rc.vals(table=("3", "4", "5", "6"), n="100/100", tau=0.0, q="bias", m="RoM"))),
        "Table 7, 14/6, tau 0: RoM bias 0 or towards unity in every row [Results: 2:1 accentuates the bias]": yes(
            all(v <= 0 for v in rc.vals(table="7", n="14/6", tau=0.0, q="bias", m="RoM"))),
        "Table 8, 6/14, tau 0: RoM bias 0 or away from unity in every row [Results: 1:2 can reverse it]": yes(
            all(v >= 0 for v in rc.vals(table="8", n="6/14", tau=0.0, q="bias", m="RoM"))),
    }


def biased_rom_coverage(c, paper):
    """Abstract: where RoM bias towards no effect exceeds 1.5%, RoM covers 89-92%, MD 92-94%.
    The selection uses the paper's printed bias (-2 or less) or our unrounded bias (below -1.5)."""
    sel = [key for key in c.scenarios() if ((c.scenario(*key)["RoM|bias"] <= -2) if paper else (c.scenario(*key)["RoM|bias"] < -1.5))]
    keys = set(sel)

    def ext(fn, m):
        cells = [r for r in c.get(q="coverage", m=m) if (r["table"], r["effect"], r["n"], r["k"], r["tau"]) in keys]
        r = fn(cells, key=lambda r: r["v"])
        return Stat(r["v"], r["tol"])
    return {
        "Scenarios with RoM bias towards no effect over 1.5% (Tables 3-8): lowest RoM coverage (%) [Abstract: 89-92%]": ext(min, "RoM"),
        "Scenarios with RoM bias towards no effect over 1.5% (Tables 3-8): highest RoM coverage (%) [Abstract: 89-92%]": ext(max, "RoM"),
        "Scenarios with RoM bias towards no effect over 1.5% (Tables 3-8): lowest MD coverage (%) [Abstract: 92-94%]": ext(min, "MD"),
        "Scenarios with RoM bias towards no effect over 1.5% (Tables 3-8): highest MD coverage (%) [Abstract: 92-94%]": ext(max, "MD"),
    }, [f"Table {k[0]}, SMD {k[1]:g}, {k[2]}, k {k[3]}, tau {k[4]:g}" for k in sel]


def coverage(c, rc):
    sel = dict(table=("3", "4", "5", "6"), n="100/100", k=5, tau=0.5)
    at_min = []
    for m in ("MD", "SMD", "RoM"):
        lo = min(rc.vals(q="coverage", m=m))
        at_min += rc.get(q="coverage", m=m, v=lo)
    return {
        "Lowest coverage in Tables 3-8 (%) [Results: 87-88%]": c.ext(min, q="coverage"),
        "Each measure's lowest coverage (Tables 3-8) is at k 5, 100 patients per arm (or 134/66, 66/134), tau 0.5 [Results]": yes(
            all(r["k"] == 5 and r["n"] in BIG and r["tau"] == 0.5 for r in at_min)),
        "k 5, 100/100, tau 0.5 (Tables 3-6): lowest coverage (%) [Results: 87-88%]": c.ext(min, q="coverage", **sel),
        "k 5, 100/100, tau 0.5 (Tables 3-6): highest coverage (%) [Results: 87-88%]": c.ext(max, q="coverage", **sel),
        "k 5, 100/100, tau 0.5 (Tables 3-6): lowest I2 (%) [Results: I2 = 92-93%]": c.ext(min, q="i2", **sel),
        "k 5, 100/100, tau 0.5 (Tables 3-6): highest I2 (%) [Results: I2 = 92-93%]": c.ext(max, q="i2", **sel),
    }


def heterogeneity(c, rc):
    md_small = rc.vals(n=SMALL, q="i2", m="MD")
    rows = {}
    for r in rc.get(q="i2", n=SMALL):
        rows.setdefault((r["table"], r["effect"], r["k"]), {})[r["m"]] = r["v"]
    return {
        "MD I2 with 10 patients per arm (or 14/6, 6/14), Tables 3-8: every value 'around' 55-60%, within 1 point [Results]": yes(
            all(54 <= v <= 61 for v in md_small)),
        "Every I2 with 100 patients per arm (or 134/66, 66/134), Tables 3-8, all measures, above 90% [Results]": yes(
            all(v > 90 for v in rc.vals(n=BIG, q="i2"))),
        "SMD I2 below MD I2 with 10 patients per arm in every row of Tables 3, 4 and 5 [Results]": yes(
            all(v["SMD"] < v["MD"] for k, v in rows.items() if k[0] in ("3", "4", "5"))),
        "RoM I2 below MD I2 with 10 patients per arm in every row of Table 5 [Results]": yes(
            all(v["RoM"] < v["MD"] for k, v in rows.items() if k[0] == "5")),
    }


def power_close(rc):
    """Share of the 216 scenarios whose SMD and RoM power are each within 5 points of MD's (the Results
    compare SMD and RoM with MD in the sentences before)."""
    keys = rc.scenarios()
    ok = [abs(s["SMD|power"] - s["MD|power"]) <= 5 and abs(s["RoM|power"] - s["MD|power"]) <= 5
          for s in (rc.scenario(*k) for k in keys)]
    return sum(ok) / len(ok)


def power(c, rc):
    t3 = sum(rc.vals(table="3", q="power", m="MD"))
    return {
        "Scenarios of Tables 3-8 whose SMD and RoM power lie within 5 points of MD's (%)": 100 * power_close(rc),
        "Power within 5 points across the methods in 'almost all' scenarios (at least 90%) [Results]": yes(power_close(rc) >= 0.9),
        "MD power lower with 2:1 arms (Table 7) than with 1:1 (Table 3), summed over the 36 settings [Results]": yes(
            sum(rc.vals(table="7", q="power", m="MD")) < t3),
        "MD power lower with 1:2 arms (Table 8) than with 1:1 (Table 3), summed over the 36 settings [Results]": yes(
            sum(rc.vals(table="8", q="power", m="MD")) < t3),
    }


def main_claim(c, rc):
    return {
        "MD relatively bias-free: MD bias averaged over the 216 scenarios within 0.5% of 0 (Tables 3-8)": yes(
            abs(sum(c.vals(q="bias", m="MD"))) / 216 < 0.5),
        "SMD biased towards no effect with 10 patients per arm in every scenario (Tables 3-8)": yes(
            all(v < 0 for v in rc.vals(n=SMALL, q="bias", m="SMD"))),
        "RoM bias between -4% and 2% in every scenario (Tables 3-8)": yes(all(-4 <= v <= 2 for v in rc.vals(q="bias", m="RoM"))),
        "Statistical power similar: SMD and RoM within 5 points of MD in at least 90% of scenarios": yes(power_close(rc) >= 0.9),
    }


CLAIMS = {  # id: (function, expected values in field order)
    "text_smd_bias": (smd_bias, ["-5", "4", "6", "yes"]),
    "text_rom_bias": (rom_bias, ["-4", "2", "3", "2", "yes", "yes", "yes"]),
    "text_coverage": (coverage, ["87", "yes", "87", "88", "92", "93"]),
    "text_heterogeneity": (heterogeneity, ["yes", "yes", "yes", "yes"]),
    "text_power": (power, [None, "yes", "yes", "yes"]),
    "text_main_claim": (main_claim, ["yes", "yes", "yes", "yes"]),
}


def fields(expected, ours, arith, extra=None):
    out = []
    for (name, o), (_, a), e in zip(ours.items(), arith.items(), expected):
        if e is None:  # not printed by the paper: shown, not compared
            continue
        f = {"name": name, "expected": e, "observed": o if isinstance(o, str) else round(o, 3),
             "arithmetic": a if isinstance(a, str) else round(a, 3)}
        if getattr(o, "tol", None) is not None:
            f["tolerance"] = {"abs": round(0.5 * 10 ** -_decimals(e) + (o.tol - 0.5), 3)}
        out.append(f)
    return out


def _decimals(s):
    return len(s.split(".")[1]) if "." in s else 0


def table1_consistency(pub):
    """Table 1: each printed estimate against the midpoint of its CI, and each p from its CI (normal, z 1.96)."""
    out = []
    for param, d in pub["table1"]["parameters"].items():
        for m in ("MD", "SMD", "RoM"):
            est, ci, p = d["Estimate"][m], d["95% CI"][m], d["p-value"][m]
            if est == "--":
                continue
            lo, hi = (float(x) for x in ci.split(" to "))
            if m == "RoM":
                mid, se = math.exp((math.log(lo) + math.log(hi)) / 2), (math.log(hi) - math.log(lo)) / (2 * 1.96)
                z = (math.log(lo) + math.log(hi)) / 2 / se
            else:
                mid, se = (lo + hi) / 2, (hi - lo) / (2 * 1.96)
                z = mid / se
            pv = float(rommeta.two_sided_p(z))
            out.append({"name": f"{param}, {m}: estimate at the midpoint of its CI", "expected": est, "observed": round(mid, 4)})
            if p.startswith("<"):
                out.append({"name": f"{param}, {m}: p below {p[1:]} from its CI", "expected": "yes", "observed": yes(pv < float(p[1:]))})
            else:
                out.append({"name": f"{param}, {m}: p from its CI", "expected": p, "observed": round(pv, 4)})
    return out


def main():
    pub_path, sim_path, out = sys.argv[1:4]
    pub = json.load(open(pub_path))
    sim = json.load(open(sim_path))
    paper = Cells(pub)
    ours, ours_r = Cells(pub, sim), Cells(pub, sim, rounded=True)
    doc = {"_about": __doc__.strip().split("\n\n")[0]}
    for cid, (fn, expected) in CLAIMS.items():
        doc[cid] = {"fields": fields(expected, fn(ours, ours_r), fn(paper, paper))}
        if cid == "text_power":
            doc[cid]["shown"] = {"ours": round(100 * power_close(ours_r), 1), "paper": round(100 * power_close(paper), 1)}
    o, sel_o = biased_rom_coverage(ours, paper=False)
    a, sel_a = biased_rom_coverage(paper, paper=True)
    doc["text_biased_rom_coverage"] = {"fields": fields(["89", "92", "92", "94"], o, a),
                                       "selected": {"ours": sel_o, "paper": sel_a}}
    # 1,000 patients per arm (results not shown in the paper): coverage 87-88%, I2 99%
    ex = sim["extra"]["n1000"]

    def cell(q, fn):
        cs = [(e["result"][m][q], e["result"][m][f"{q}_se"]) for e in ex for m in ("MD", "SMD", "RoM")]
        v, se = fn(cs, key=lambda c: c[0])
        return {"observed": round(v, 3), "tolerance": {"abs": round(0.5 + 3 * math.sqrt(2) * se, 3)}}
    doc["text_n1000"] = {"fields": [
        {"name": "1000/1000, k 5, tau 0.5, SD 40: lowest coverage of the three measures and three effects (%) [Results: 87-88%, not shown]", "expected": "87", **cell("coverage", min)},
        {"name": "1000/1000, k 5, tau 0.5, SD 40: highest coverage (%) [Results: 87-88%, not shown]", "expected": "88", **cell("coverage", max)},
        {"name": "1000/1000, k 5, tau 0.5, SD 40: lowest I2 (%) [Results: 99%, not shown]", "expected": "99", **cell("i2", min)},
        {"name": "1000/1000, k 5, tau 0.5, SD 40: highest I2 (%) [Results: 99%, not shown]", "expected": "99", **cell("i2", max)}]}
    # Methods: analytic statements
    tau2 = 0.25  # tau = 0.5 SD units; s2 of an MD = 2/n SD units squared
    i2n = {n: 100 * tau2 / (tau2 + 2 / n) for n in (10, 100)}
    second = 100 * 0.5 * (0.7**2 / 10)  # (1/2) f''(mu)^2 Var^2 / (f'(mu)^2 Var) for f = ln, cv 0.7, n 10
    mean, sd, skew = rommeta.mixture_moments()
    doc["text_methods"] = {"fields": [
        {"name": "Expected I2 at tau 0.5 with 10 patients per arm, tau2/(tau2 + s2) (%)", "expected": "56", "observed": round(i2n[10], 3), "arithmetic": round(i2n[10], 3)},
        {"name": "Expected I2 at tau 0.5 with 100 patients per arm (%)", "expected": "93", "observed": round(i2n[100], 3), "arithmetic": round(i2n[100], 3)},
        {"name": f"Second-order delta term at SD/mean 0.7, n 10: below 2.5% of the variance (it is {second:.2f}%)", "expected": "yes", "observed": yes(second < 2.5), "arithmetic": yes(second < 2.5)},
        {"name": "Skewed mixture: overall mean ('unity')", "expected": "1.0", "observed": round(mean, 4), "arithmetic": round(mean, 4)},
        {"name": "Skewed mixture: overall SD ('similar to' 40% of the mean)", "expected": "0.4", "observed": round(sd, 4), "arithmetic": round(sd, 4)},
        {"name": "Skewed mixture: skewness (third standardized moment)", "expected": "0.88", "observed": round(skew, 4), "arithmetic": round(skew, 4)}]}
    doc["table1_consistency"] = {"fields": table1_consistency(pub)}
    json.dump(doc, open(out, "w"), indent=1)
    open(out, "a").write("\n")
    print(f"{out}: {sum(len(v['fields']) for k, v in doc.items() if not k.startswith('_'))} fields", file=sys.stderr)


if __name__ == "__main__":
    main()
