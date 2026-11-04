/* fossil charts: expected (the paper, in ink) against observed (ours, in green), in plain SVG.
 * No libraries. Colours come from CSS classes that read the site's tokens. */
(function () {
  "use strict";
  var SVG = "http://www.w3.org/2000/svg";

  /* ---------- numbers ---------- */

  function quantile(sorted, p) {
    // R's type 7, the one ggplot2's boxes use.
    var h = (sorted.length - 1) * p, lo = Math.floor(h), hi = Math.ceil(h);
    return sorted[lo] + (h - lo) * (sorted[hi] - sorted[lo]);
  }

  function boxStats(values) {
    var s = values.slice().sort(function (a, b) { return a - b; });
    var q1 = quantile(s, 0.25), q3 = quantile(s, 0.75), iqr = q3 - q1;
    var inside = s.filter(function (v) { return v >= q1 - 1.5 * iqr && v <= q3 + 1.5 * iqr; });
    return { lower: inside[0], q1: q1, median: quantile(s, 0.5), q3: q3, upper: inside[inside.length - 1], n: s.length };
  }

  function kaplanMeier(rows) {
    // rows: [time, event]. Returns { steps: [[t, S]], end }, the way survfit draws the curve.
    var obs = rows.slice().sort(function (a, b) { return a[0] - b[0]; });
    var n = obs.length, s = 1, steps = [[0, 1]], i = 0;
    while (i < obs.length) {
      var t = obs[i][0], d = 0, c = 0;
      while (i + c < obs.length && obs[i + c][0] === t) { d += obs[i + c][1]; c++; }
      if (d) { s *= 1 - d / n; steps.push([t, s]); }
      n -= c; i += c;
    }
    return { steps: steps, end: obs[obs.length - 1][0] };
  }

  function stepAt(steps, t) {
    var v = steps[0][1];
    for (var i = 0; i < steps.length && steps[i][0] <= t; i++) v = steps[i][1];
    return v;
  }

  function median(curve) {
    for (var i = 0; i < curve.steps.length; i++) if (curve.steps[i][1] <= 0.5) return curve.steps[i][0];
    return null;
  }

  function lineAt(points, x) {
    if (x < points[0][0] || x > points[points.length - 1][0]) return 0;
    var lo = 0, hi = points.length - 1;
    while (hi - lo > 1) { var mid = (lo + hi) >> 1; if (points[mid][0] <= x) lo = mid; else hi = mid; }
    var a = points[lo], b = points[hi];
    return b[0] === a[0] ? a[1] : a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]);
  }

  function peak(points) {
    return points.reduce(function (m, p) { return p[1] > m[1] ? p : m; }, points[0]);
  }

  function sharedArea(a, b, lo, hi) {
    // The area two densities have in common: 1 when they are the same curve, 0 when they never meet.
    var n = 4000, dx = (hi - lo) / n, sum = 0;
    for (var i = 0; i <= n; i++) {
      var x = lo + i * dx, w = (i === 0 || i === n) ? 0.5 : 1;
      sum += w * Math.min(lineAt(a, x), lineAt(b, x));
    }
    return sum * dx;
  }

  function meanGap(a, b, t1) {
    var n = 4000, sum = 0;
    for (var i = 0; i <= n; i++) { var t = t1 * i / n; sum += Math.abs(stepAt(a.steps, t) - stepAt(b.steps, t)); }
    return sum / (n + 1);
  }

  /* ---------- drawing helpers ---------- */

  function el(name, attrs, parent) {
    var e = document.createElementNS(SVG, name);
    for (var k in attrs) if (attrs[k] !== undefined) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  function text(parent, x, y, str, cls, anchor) {
    var t = el("text", { x: x, y: y, class: cls || "tick", "text-anchor": anchor || "middle" }, parent);
    t.textContent = str;
    return t;
  }

  function scale(d0, d1, r0, r1) {
    var f = function (v) { return r0 + (v - d0) * (r1 - r0) / (d1 - d0); };
    f.invert = function (p) { return d0 + (p - r0) * (d1 - d0) / (r1 - r0); };
    return f;
  }

  function niceTicks(lo, hi, count) {
    var span = hi - lo, step = Math.pow(10, Math.floor(Math.log10(span / count)));
    var err = span / count / step;
    if (err >= 7.5) step *= 10; else if (err >= 3.5) step *= 5; else if (err >= 1.5) step *= 2;
    var out = [];
    for (var v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) out.push(+v.toFixed(10));
    return out;
  }

  function fmt(v, nd) {
    if (v === null || v === undefined || isNaN(v)) return "none";
    var s = Math.abs(v).toFixed(nd);
    return (v < 0 && Number(s) !== 0 ? "−" : "") + s;
  }

  function signed(v, nd) { return (Number(Math.abs(v).toFixed(nd)) !== 0 && v > 0 ? "+" : "") + fmt(v, nd); }

  function stepPath(x, y, steps, end) {
    var d = "M" + x(steps[0][0]) + "," + y(steps[0][1]);
    for (var i = 1; i < steps.length; i++) d += "H" + x(steps[i][0]) + "V" + y(steps[i][1]);
    return d + "H" + x(end);
  }

  function linePath(x, y, pts) {
    return pts.map(function (p, i) { return (i ? "L" : "M") + x(p[0]).toFixed(1) + "," + y(p[1]).toFixed(1); }).join("");
  }

  /* One tooltip per chart, positioned inside the chart's frame; values lead, labels follow. */
  function tooltip(host) {
    var tip = document.createElement("div");
    tip.className = "tip";
    tip.setAttribute("role", "status");
    tip.hidden = true;
    host.appendChild(tip);
    return {
      show: function (px, py, head, rows) {
        tip.textContent = "";
        var h = document.createElement("p"); h.className = "tip-head"; h.textContent = head; tip.appendChild(h);
        rows.forEach(function (r) {
          var p = document.createElement("p"); p.className = "tip-row";
          var k = document.createElement("span"); k.className = "key key--" + r.key; p.appendChild(k);
          var v = document.createElement("strong"); v.textContent = r.value; p.appendChild(v);
          var l = document.createElement("span"); l.textContent = r.label; p.appendChild(l);
          tip.appendChild(p);
        });
        tip.hidden = false;
        var w = host.clientWidth, tw = tip.offsetWidth;
        tip.style.transform = "translate(" + Math.round(px + 14 + tw > w ? px - 14 - tw : px + 14) + "px," + Math.round(py) + "px)";
      },
      hide: function () { tip.hidden = true; }
    };
  }

  function sized(host, draw) {
    // Draw at the host's width, and again whenever that width changes.
    var last = 0;
    function go() {
      var w = Math.round(host.clientWidth);
      if (w && w !== last) { last = w; draw(w); }
    }
    go();
    if (window.ResizeObserver) new ResizeObserver(function () { requestAnimationFrame(go); }).observe(host);
  }

  /* ---------- a pair of curves with the gap between them shaded ---------- */
  // opts: { host, label, xLabel, yLabel, x: [lo, hi], y: [lo, hi], expected, observed, step: bool,
  //         at: function (x) -> head text for the readout, nd: decimals for values }
  function curvePair(opts) {
    var host = opts.host;
    var tip = null;
    sized(host, function (w) {
      host.textContent = "";
      var h = Math.max(220, Math.min(340, Math.round(w * 0.66)));
      var m = { t: 12, r: 14, b: 44, l: 48 };
      var svg = el("svg", { width: w, height: h, viewBox: "0 0 " + w + " " + h, role: "img", "aria-label": opts.label });
      host.appendChild(svg);
      tip = tooltip(host);
      var x = scale(opts.x[0], opts.x[1], m.l, w - m.r), y = scale(opts.y[0], opts.y[1], h - m.b, m.t);

      var axes = el("g", { class: "axes" }, svg);
      niceTicks(opts.y[0], opts.y[1], 5).forEach(function (v) {
        el("line", { x1: m.l, x2: w - m.r, y1: y(v), y2: y(v), class: "grid" }, axes);
        text(axes, m.l - 8, y(v) + 4, fmt(v, opts.yNd || 1), "tick", "end");
      });
      niceTicks(opts.x[0], opts.x[1], w < 420 ? 4 : 6).forEach(function (v) {
        text(axes, x(v), h - m.b + 18, fmt(v, opts.xNd || 0), "tick");
      });
      el("line", { x1: m.l, x2: w - m.r, y1: h - m.b, y2: h - m.b, class: "base" }, axes);
      text(axes, (m.l + w - m.r) / 2, h - 6, opts.xLabel, "axis-label");

      var ev = opts.step ? function (c, t) { return t > c.end ? null : stepAt(c.steps, t); } : function (c, t) { return lineAt(c, t); };
      var shared = opts.step ? Math.min(opts.expected.end, opts.observed.end) : opts.x[1];
      var lo = opts.x[0], n = Math.max(200, w * 2), up = [], dn = [];
      for (var i = 0; i <= n; i++) {
        var t = lo + (shared - lo) * i / n, a = ev(opts.expected, t), b = ev(opts.observed, t);
        up.push([t, Math.max(a, b)]); dn.push([t, Math.min(a, b)]);
      }
      el("path", { d: linePath(x, y, up) + dn.reverse().map(function (p) { return "L" + x(p[0]).toFixed(1) + "," + y(p[1]).toFixed(1); }).join("") + "Z", class: "gap" }, svg);

      [["expected", "exp"], ["observed", "obs"]].forEach(function (s) {
        var c = opts[s[0]];
        el("path", { d: opts.step ? stepPath(x, y, c.steps, c.end) : linePath(x, y, c), class: "curve curve--" + s[1] }, svg);
      });

      var cross = el("line", { y1: m.t, y2: h - m.b, class: "cross", visibility: "hidden" }, svg);
      var dots = [el("circle", { r: 4.5, class: "dot dot--exp", visibility: "hidden" }, svg),
                  el("circle", { r: 4.5, class: "dot dot--obs", visibility: "hidden" }, svg)];
      var hit = el("rect", { x: m.l, y: m.t, width: w - m.l - m.r, height: h - m.t - m.b, class: "hit" }, svg);
      var cur = null;

      function readAt(t) {
        cur = Math.max(opts.x[0], Math.min(opts.x[1], t));
        var a = ev(opts.expected, cur), b = ev(opts.observed, cur), px = x(cur);
        cross.setAttribute("x1", px); cross.setAttribute("x2", px); cross.setAttribute("visibility", "visible");
        [[a, dots[0]], [b, dots[1]]].forEach(function (p) {
          if (p[0] === null) { p[1].setAttribute("visibility", "hidden"); return; }
          p[1].setAttribute("cx", px); p[1].setAttribute("cy", y(p[0])); p[1].setAttribute("visibility", "visible");
        });
        var nd = opts.nd || 2, rows = [
          { key: "exp", value: a === null ? "ended" : fmt(a, nd), label: "Paper" },
          { key: "obs", value: b === null ? "ended" : fmt(b, nd), label: "Ours" }
        ];
        if (a !== null && b !== null) rows.push({ key: "gap", value: signed(b - a, nd), label: "Gap" });
        tip.show(px, m.t, opts.at(cur), rows);
      }
      function clear() {
        cross.setAttribute("visibility", "hidden");
        dots.forEach(function (d) { d.setAttribute("visibility", "hidden"); });
        tip.hide();
      }
      hit.addEventListener("pointermove", function (e) {
        var r = svg.getBoundingClientRect();
        readAt(x.invert(e.clientX - r.left));
      });
      hit.addEventListener("pointerleave", clear);
      host.onkeydown = function (e) {
        var stepSize = (opts.x[1] - opts.x[0]) / 50;
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          e.preventDefault();
          readAt((cur === null ? (opts.x[0] + opts.x[1]) / 2 : cur) + (e.key === "ArrowRight" ? stepSize : -stepSize));
        } else if (e.key === "Escape") { clear(); }
      };
      host.onfocus = function () { readAt(cur === null ? (opts.x[0] + opts.x[1]) / 2 : cur); };
      host.onblur = clear;
    });
  }

  /* ---------- Fig. 2: each method's box, the paper's above ours ---------- */
  // opts: { host, label, methods, expected: {method: box}, observed: {method: box}, matched }
  function boxPairs(opts) {
    var host = opts.host;
    sized(host, function (w) {
      host.textContent = "";
      var row = 40, m = { t: 8, r: 14, b: 40, l: 96 };
      var h = m.t + row * opts.methods.length + m.b;
      var svg = el("svg", { width: w, height: h, viewBox: "0 0 " + w + " " + h, role: "img", "aria-label": opts.label });
      host.appendChild(svg);
      var tip = tooltip(host);
      var x = scale(0, 1, m.l, w - m.r);
      var axes = el("g", { class: "axes" }, svg);
      [0, 0.25, 0.5, 0.75, 1].forEach(function (v) {
        el("line", { x1: x(v), x2: x(v), y1: m.t, y2: h - m.b, class: "grid" }, axes);
        text(axes, x(v), h - m.b + 18, fmt(v, v % 0.5 ? 2 : 1), "tick");
      });
      text(axes, (m.l + w - m.r) / 2, h - 6, "F.score", "axis-label");

      opts.methods.forEach(function (meth, i) {
        var y0 = m.t + i * row, g = el("g", { class: "row" + (meth === opts.matched ? " row--matched" : "") }, svg);
        el("rect", { x: 0, y: y0, width: w, height: row, class: "row-band" }, g);
        text(g, m.l - 10, y0 + row / 2 + 4, meth, "row-label", "end");
        var e = opts.expected[meth], o = opts.observed[meth];
        el("line", { x1: x(e.median), x2: x(o.median), y1: y0 + 13, y2: y0 + 27, class: "shift" }, g);
        [[e, y0 + 13, "exp"], [o, y0 + 27, "obs"]].forEach(function (b) {
          var s = b[0], cy = b[1];
          el("line", { x1: x(s.lower), x2: x(s.upper), y1: cy, y2: cy, class: "whisker whisker--" + b[2] }, g);
          el("rect", { x: x(s.q1), y: cy - 4, width: Math.max(2, x(s.q3) - x(s.q1)), height: 8, rx: 4, class: "iqr iqr--" + b[2] }, g);
          el("circle", { cx: x(s.median), cy: cy, r: 4.5, class: "dot dot--" + b[2] }, g);
        });
        function show() {
          tip.show(Math.max(x(Math.max(e.q3, o.q3)), m.l), y0, meth, [
            { key: "exp", value: fmt(e.median, 2), label: "Paper median, middle half " + fmt(e.q1, 2) + " to " + fmt(e.q3, 2) },
            { key: "obs", value: fmt(o.median, 2), label: "Ours, middle half " + fmt(o.q1, 2) + " to " + fmt(o.q3, 2) },
            { key: "gap", value: signed(o.median - e.median, 2), label: "Gap in medians" }
          ]);
          g.classList.add("row--on");
        }
        function hide() { tip.hide(); g.classList.remove("row--on"); }
        g.addEventListener("pointerenter", show);
        g.addEventListener("pointerleave", hide);
        g.setAttribute("tabindex", "0");
        g.setAttribute("aria-label", meth + ": paper median " + fmt(e.median, 2) + ", ours " + fmt(o.median, 2));
        g.addEventListener("focus", show);
        g.addEventListener("blur", hide);
      });
    });
  }

  window.FossilCharts = {
    boxStats: boxStats, kaplanMeier: kaplanMeier, median: median, stepAt: stepAt, lineAt: lineAt,
    peak: peak, sharedArea: sharedArea, meanGap: meanGap, fmt: fmt, signed: signed,
    curvePair: curvePair, boxPairs: boxPairs
  };
})();
