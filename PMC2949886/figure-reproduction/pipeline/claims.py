"""The paper's claims in the text, computed from our run (and, for text.arithmetic, from the paper's
own numbers).

usage: claims.py RUN_DIR OUT_JSON

Each claim becomes fields {name, expected, observed}: "yes"/"no" for comparisons, the printed label
for the FDR-bias test, numbers as strings at the paper's precision. Every rule that turns a sentence
into a comparison is written next to it below.
"""
import json
import sys
from pathlib import Path

FR = [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, .99]


def k(x):
    return f"{round(x, 2) + 0.0:g}"


def yn(b):
    return "yes" if b else "no"


class Ours:
    """Accessors on our run."""

    def __init__(self, run):
        self.S = json.loads((run / "sim_sd0.1.json").read_text())
        self.one = json.loads((run / "one_sd0.1.json").read_text())      # Fig. S4 data set
        self.one0 = json.loads((run / "one_sd0.json").read_text())       # Fig. 6 data set (no noise term)
        self.L = json.loads((run / "leukemia.json").read_text())["main"]
        self.post = [r for r in self.S["post"] if r["dataset"] <= 100]

    def curve(self, f, m, field, st="curves"):
        node = self.S[st][f][m]["0.05"]
        return {x: node[k(x)][field] for x in FR if k(x) in node}

    def level(self, f, a, x):
        return self.S["levels"][f]["BH"][k(a)][k(x)]["power"]

    def leuk(self, n, f, q, x):
        return self.L[f"n{n}"][f][int(round(x * 10))][{"fdr": 1, "power": 2}[q]]

    def label(self, which, f, i):
        return (self.one0 if which == "fig6" else self.one)["test"][f]["label"][i]

    def post_mean(self, f, sit, fr, q):
        v = [r[q] for r in self.post if r["filter"] == f and r["situation"] == sit and abs(r["fraction"] - fr) < 1e-9]
        return sum(v) / len(v)


class Paper:
    """The same accessors on the values read from the published vector figures."""

    def __init__(self, pub):
        self.P = pub

    def _series(self, fig, panel, name):
        return {round(x, 2): y for x, y in self.P[fig]["panels"][panel]["series"][name]}

    def curve(self, f, m, field, st="curves"):
        if field == "pi0":
            s = self._series("fig3", "main", f)          # as the caption labels the curves
        elif st == "wilcoxon":
            s = self._series("figS6", field, f)
        else:
            s = self._series("fig4" if field == "fdr" else "figS2", m, f)
        return {x: s[round(x, 2)] for x in FR if round(x, 2) in s}

    def level(self, f, a, x):
        return self._series("fig5", f, f"{x:g}")[round(a, 2)]

    def leuk(self, n, f, q, x):
        return self._series("fig7" if q == "fdr" else "figS5", "main", f"{f}.n{n}")[round(x, 2)]

    def label(self, which, f, i):
        if which != "fig6" or f != "foldchange":
            return None                     # the test labels of Fig. S4 are not text in the PDF
        return list(self.P["fig6"]["panels"]["foldchange"]["test_labels"].values())[i]

    def post_mean(self, f, sit, fr, q):
        """The fitted line at the middle of no-filtering's range (the figures give lines, not means)."""
        lines = self.P["figS8" if q == "fdr" else "figS9"]["panels"][f]["lines"]
        x = sum(lines["C10"]["x"]) / 2
        if sit == "A":
            return x
        l = lines[f"{sit}{int(round(fr * 100))}"]
        return l["intercept"] + l["slope"] * x


def evaluate(D):
    C = {}
    yn_ = lambda b: None if b is None else yn(b)
    bh, abh = D.curve("foldchange", "BH", "fdr"), D.curve("foldchange", "aBH", "fdr")
    flat = all(max(D.curve(f, "BH", "fdr")[x] for x in FR[:10]) - D.curve(f, "BH", "fdr")[0] < 0.005
               for f in ("variance", "signal"))
    by_all = all(v < 0.05 for f in ("foldchange", "signal", "variance") for v in D.curve(f, "BY", "fdr").values())
    C["text.fig4"] = [
        ("BH: the fold-change filter raises the achieved FDR more the more is removed (x = 0, 0.2, ..., 0.8)",
         all(bh[a] < bh[b] for a, b in zip(FR[0:9:2], FR[2:9:2]))),
        ("aBH: the same", all(abh[a] < abh[b] for a, b in zip(FR[0:9:2], FR[2:9:2]))),
        ("BH: the variance and signal filters do not raise the achieved FDR (by 0.005 or more, x up to 0.9)", flat),
        ("aBH is above 5% with no filtering", abh[0] > 0.05),
        ("q-value is above 5% with no filtering", D.curve("variance", "qvalue", "fdr")[0] > 0.05),
        ("BY is below 5% over the entire range (all filters, x up to 0.99)", by_all)]
    pi = {f: D.curve(f, "BH", "pi0") for f in ("foldchange", "signal", "variance")}
    xs = FR[1:]
    C["text.fig3"] = [
        ("fold change is the best realistic filter (lowest pi0 at every x from 0.1 to 0.99)",
         all(pi["foldchange"][x] < min(pi["signal"][x], pi["variance"][x]) for x in xs)),
        ("text: signal is the worst realistic filter (highest pi0 at every x)",
         all(pi["signal"][x] > pi["variance"][x] for x in xs)),
        ("text: signal is only slightly better than random (pi0 below 0.8 at every x)", all(pi["signal"][x] < 0.8 for x in xs)),
        ("caption: from bottom to top, fold change, signal, variance (signal below variance at every x)",
         all(pi["signal"][x] < pi["variance"][x] for x in xs))]
    levels = [round(0.05 * i, 2) for i in range(1, 20)] + [0.99]
    C["text.fig5"] = [
        ("signal and variance filters always give less power after filtering (every BH level, every x)",
         all(D.level(f, a, x) < D.level(f, a, 0) for f in ("signal", "variance") for a in levels for x in FR[1:])),
        ("fold change gives more power for BH levels up to 0.1 and x up to 0.5",
         all(D.level("foldchange", a, x) > D.level("foldchange", a, 0) for a in (0.05, 0.1) for x in (.1, .2, .3, .4, .5)))]
    lab = lambda w, f, i: D.label(w, f, i)
    C["text.biastest"] = [
        ("fold change: the test rejects even at 10% removed (Fig. S4 data set)",
         None if lab("S4", "foldchange", 1) is None else lab("S4", "foldchange", 1) == "***"),
        ("fold change: the same on the Fig. 6 data set", lab("fig6", "foldchange", 1) == "***"),
        ("signal: null p-values approximately uniform at every x (no p below 0.001)",
         None if lab("S4", "signal", 0) is None else all(lab("S4", "signal", i) != "***" for i in range(11))),
        ("variance: the same",
         None if lab("S4", "variance", 0) is None else all(lab("S4", "variance", i) != "***" for i in range(11)))]
    lk = D.leuk
    C["text.leukemia"] = [
        ("signal and variance: achieved FDR stays around 5% (mean over x = 0 to 0.8 within 0.025 of 0.05, every size)",
         all(abs(sum(lk(n, f, "fdr", x) for x in FR[:9]) / 9 - 0.05) < 0.025 for n in (8, 16, 24) for f in ("signal", "variance"))),
        ("fold change: achieved FDR rises with x (x = 0.8 above x = 0 by 0.05 or more, every size)",
         all(lk(n, "foldchange", "fdr", .8) - lk(n, "foldchange", "fdr", 0) >= 0.05 for n in (8, 16, 24))),
        ("power rises with sample size (8 < 16 < 24 at x = 0)",
         lk(8, "signal", "power", 0) < lk(16, "signal", "power", 0) < lk(24, "signal", "power", 0)),
        ("fold change raises power; signal and variance have no or the opposite effect (gain below 0.02; x = 0.5 against 0, every size)",
         all(lk(n, "foldchange", "power", .5) > lk(n, "foldchange", "power", 0)
             and lk(n, "signal", "power", .5) - lk(n, "signal", "power", 0) < 0.02
             and lk(n, "variance", "power", .5) - lk(n, "variance", "power", 0) < 0.02 for n in (8, 16, 24)))]
    dif = max(abs(D.curve(f, "BH", q, "wilcoxon")[x] - D.curve(f, "BH", q)[x])
              for f in ("foldchange", "signal", "variance") for q in ("fdr", "power") for x in FR
              if x in D.curve(f, "BH", q, "wilcoxon") and x in D.curve(f, "BH", q))
    C["text.wilcoxon"] = [("Wilcoxon FDR and power curves very similar to the t test's (differ by less than 0.05)", dif < 0.05)]
    pm = D.post_mean
    fl = ("foldchange", "signal", "variance")
    C["text.postfdr"] = [
        ("filtering after the correction (10, 20%) does not bias the FDR (mean within 0.01 of no filtering, every filter)",
         all(abs(pm(f, "C", fr, "fdr") - pm(f, "A", 0, "fdr")) < 0.01 for f in fl for fr in (.1, .2))),
        ("filtering after the correction loses a little power (every filter)",
         all(pm(f, "C", fr, "power") < pm(f, "A", 0, "power") for f in fl for fr in (.1, .2))),
        ("fold change before the correction (25, 50%) biases the FDR (mean above no filtering by 0.01 or more)",
         all(pm("foldchange", "B", fr, "fdr") - pm("foldchange", "A", 0, "fdr") >= 0.01 for fr in (.25, .5))),
        ("fold change is the only filter that gains power when used before the correction",
         all(pm("foldchange", "B", fr, "power") > pm("foldchange", "A", 0, "power") for fr in (.25, .5))
         and all(pm(f, "B", fr, "power") <= pm(f, "A", 0, "power") for f in ("signal", "variance") for fr in (.25, .5)))]
    return {key: [{"name": n, "value": yn_(v)} for n, v in rows] for key, rows in C.items()}


def main(run, out):
    run = Path(run)
    ours = evaluate(Ours(run))
    paper = evaluate(Paper(json.loads((run / "published_values.json").read_text())))
    C = {}
    for key in ours:
        C[key] = [{"name": o["name"], "expected": "yes", "observed": o["value"], "paper_figure_gives": p["value"]}
                  for o, p in zip(ours[key], paper[key])]
    one0 = json.loads((run / "one_sd0.json").read_text())
    C["fig6.labels"] = [{"name": f"x = {x:g}", "expected": e, "observed": o}
                        for x, e, o in zip(FR, ["0.3"] + ["***"] * 10, one0["test"]["foldchange"]["label"])]
    # arithmetic on the paper's own numbers
    C["text.arithmetic"] = {
        "nonnull": {"name": "non-null features: m (1 - pi0) = 5000 x 0.2", "expected": "4000", "observed": "1000"},
        "querec_low": {"name": "Querec et al.: 7 false of 65 genes, as a percentage", "expected": "11",
                       "observed": f"{100 * 7 / 65:.0f}"},
        "querec_high": {"name": "Querec et al.: 7 false of 33 tested genes, as a percentage", "expected": "20",
                        "observed": f"{100 * 7 / 33:.0f}"},
    }
    Path(out).write_text(json.dumps(C, indent=1))
    for key, v in C.items():
        vals = v.values() if isinstance(v, dict) else v
        print(key, "ours", [f["observed"] for f in vals], "paper", [f.get("paper_figure_gives") for f in vals])


if __name__ == "__main__":
    main(*sys.argv[1:3])
