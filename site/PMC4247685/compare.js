/* The expected-and-observed page for Curry 2014: draws each figure's pair of curves (or boxes) from
 * compare-data.js and works out the gaps between them. Needs charts.js. */
(function () {
  "use strict";
  var D = window.FOSSIL_COMPARE, C = window.FossilCharts;

  /* Everything the page states, worked out from the data. Pure: no page needed. */
  function summarise() {
    var out = {};

    var f2 = D.fig2, moved = [], inside = 0, sameBest = 0, best = {}, observed = {};
    f2.structures.forEach(function (s) {
      observed[s] = {};
      f2.methods.forEach(function (m) {
        var e = f2.expected[s][m], o = C.boxStats(f2.observed[s][m]);
        observed[s][m] = o;
        moved.push(Math.abs(o.median - e.median));
        if (e.median >= o.q1 && e.median <= o.q3) inside++;
      });
      var top = function (get) {
        return f2.methods.reduce(function (a, m) { return get(m) > get(a) ? m : a; });
      };
      best[s] = { paper: top(function (m) { return f2.expected[s][m].median; }),
                  ours: top(function (m) { return observed[s][m].median; }) };
      if (best[s].paper === best[s].ours) sameBest++;
    });
    out.fig2 = { observed: observed, best: best, inside: inside, boxes: moved.length, sameBest: sameBest,
                 meanMoved: moved.reduce(function (a, b) { return a + b; }, 0) / moved.length };

    out.fig3 = {};
    ["bicluster", "control"].forEach(function (g) {
      var e = D.fig3.expected[g], o = D.fig3.observed[g];
      out.fig3[g] = { shared: C.sharedArea(e, o, -1.05, 1.05), peakPaper: C.peak(e)[0], peakOurs: C.peak(o)[0] };
    });

    [["fig4", ["bicluster", "control"]], ["fig5", ["Group1", "Group2"]]].forEach(function (f) {
      out[f[0]] = {};
      f[1].forEach(function (g) {
        var e = D[f[0]].expected[g], o = C.kaplanMeier(D[f[0]].observed[g]);
        out[f[0]][g] = { paper: e, ours: o, medianPaper: C.median(e), medianOurs: C.median(o),
                         gap: C.meanGap(e, o, Math.min(e.end, o.end)), n: D[f[0]].observed[g].length };
      });
    });
    return out;
  }

  if (typeof document === "undefined") { if (typeof module !== "undefined") module.exports = summarise; return; }

  var S = summarise(), fmt = C.fmt;
  document.documentElement.classList.add("has-charts");

  function stats(id, items) {
    var dl = document.getElementById(id);
    dl.textContent = "";
    items.forEach(function (it) {
      var div = document.createElement("div");
      var dt = document.createElement("dt"); dt.textContent = it[0]; div.appendChild(dt);
      var dd = document.createElement("dd"); dd.textContent = it[1]; div.appendChild(dd);
      dl.appendChild(div);
    });
  }

  /* Fig. 2 */
  D.fig2.structures.forEach(function (s) {
    C.boxPairs({
      host: document.getElementById("fig2-" + s),
      label: "Fig. 2, " + s + " structure: each method's box in the paper and in our rerun",
      methods: D.fig2.methods, expected: D.fig2.expected[s], observed: S.fig2.observed[s], matched: "GABi." + s
    });
  });
  stats("fig2-stats", [
    ["Medians apart, on average", fmt(S.fig2.meanMoved, 2) + " F.score"],
    ["Paper medians inside our middle half", S.fig2.inside + " of " + S.fig2.boxes],
    ["Same best method", S.fig2.sameBest + " of " + D.fig2.structures.length + " structures"]
  ].concat(D.fig2.structures.map(function (s) {
    return ["Best on " + s, "Paper " + S.fig2.best[s].paper + ", ours " + S.fig2.best[s].ours];
  })));

  /* Fig. 3 */
  [["bicluster", "Bicluster tumours"], ["control", "Control set"]].forEach(function (g) {
    C.curvePair({
      host: document.getElementById("fig3-" + g[0]),
      label: "Fig. 3, " + g[1] + ": density of pair-wise correlations, the paper's curve and ours",
      xLabel: "Pair-wise correlation", x: [-1, 1], y: [0, 2.7], yNd: 1, xNd: 1, nd: 2,
      expected: D.fig3.expected[g[0]], observed: D.fig3.observed[g[0]],
      at: function (v) { return "Correlation " + fmt(v, 2); }
    });
  });
  stats("fig3-stats", [
    ["Area the curves share, bicluster", Math.round(S.fig3.bicluster.shared * 100) + "%"],
    ["Area the curves share, control set", Math.round(S.fig3.control.shared * 100) + "%"],
    ["Peak, bicluster", "Paper " + fmt(S.fig3.bicluster.peakPaper, 2) + ", ours " + fmt(S.fig3.bicluster.peakOurs, 2)],
    ["Peak, control set", "Paper " + fmt(S.fig3.control.peakPaper, 2) + ", ours " + fmt(S.fig3.control.peakOurs, 2)]
  ]);

  /* Figs 4 and 5 */
  function survival(fig, groups, unit, xMax, nd) {
    groups.forEach(function (g) {
      var s = S[fig][g[0]];
      C.curvePair({
        host: document.getElementById(fig + "-" + g[0]),
        label: "Fig. " + fig.slice(3) + ", " + g[1] + ": progression-free survival, the paper's curve and ours",
        xLabel: "Time (" + unit + ")", x: [0, xMax], y: [0, 1], yNd: 1, xNd: 0, nd: 2, step: true,
        expected: s.paper, observed: s.ours,
        at: function (v) { return fmt(v, nd) + " " + unit; }
      });
    });
    var items = [];
    groups.forEach(function (g) {
      var s = S[fig][g[0]];
      items.push(["Median, " + g[2], "Paper " + fmt(s.medianPaper, nd) + ", ours " + fmt(s.medianOurs, nd) + " " + unit]);
    });
    groups.forEach(function (g) {
      items.push(["Mean gap, " + g[2], fmt(S[fig][g[0]].gap, 3)]);
    });
    stats(fig + "-stats", items);
  }
  survival("fig4", [["bicluster", "bicluster tumours", "bicluster"], ["control", "control set", "control set"]],
           "months", Math.ceil(Math.max(S.fig4.bicluster.ours.end, S.fig4.control.ours.end, 131) / 10) * 10, 1);
  survival("fig5", [["Group1", "most correlated tumours", "most correlated"], ["Group2", "least correlated tumours", "least correlated"]],
           "days", 1750, 0);
})();
