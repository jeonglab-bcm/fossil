import math, json
from mpmath import mp, mpf, log as mlog
def sum80(v):
    mp.prec = 64; s = mpf(0)
    for t in v: s = s + mpf(t)
    r = float(s); mp.dps = 60; return r
mp.dps = 60
ns = list(range(200, 10001, 200))
paper = {1600:184,2000:184,2600:-365,2800:-365,3000:-365,3200:365,3800:-365,4200:365,4400:365,4600:-728,4800:-365,5000:-365,5200:-728,5400:365,5600:1091,5800:-1091,6200:-728,6400:728,7800:1456,8000:-2184,8200:728,8600:728,9000:728,9200:-1456,9400:728,9600:2184,9800:-1456,10000:728}
def exact(n, pdec):
    P = [mpf(k)/10 for k in (1,2,3,4)] if pdec else [mpf(v) for v in (0.1,0.2,0.3,0.4)]
    ps = mpf(1)/200
    return sum(sum(mlog(pk + r*ps) for r in range(n)) for pk in P) - sum(mlog(1 + r*ps) for r in range(4*n))
EX = {pd: [exact(n, pd) for n in ns] for pd in (True, False)}
psi = 1/200; P = [0.1, 0.2, 0.3, 0.4]
rhos = {"psi/(1+psi)": psi/(1+psi), "1/(1+1/psi)": 1/(1+1/psi), "1/(1+200)": 1/(1+200.0)}
best = []
for rn, rho in rhos.items():
    for comb in ("seq", "ext"):
        for form in ("(1-r)p", "p(1-r)"):
            vals = []
            for n in ns:
                parts = []
                for pk in P:
                    a = (1 - rho) * pk if form == "(1-r)p" else pk * (1 - rho)
                    parts.append(sum80([math.log(a + (r) * rho) for r in range(n)]))
                den = sum80([math.log((1 - rho) + r * rho) for r in range(4 * n)])
                if comb == "seq":
                    s = 0.0
                    for q in parts: s = s + q
                    vals.append(s - den)
                else:
                    vals.append(sum80(parts) - den)
            for pd in (True, False):
                err = [(v - float(e)) / 1e-14 for v, e in zip(vals, EX[pd])]
                m = sum(1 for n, e in zip(ns, err) if abs(e - paper.get(n, 0)) < 40)
                best.append((m, rn, comb, form, pd, err))
                print(f"{m:2d}/50  rho={rn:12s} combine={comb} form={form} pdec={pd}", flush=True)
best.sort(key=lambda t: -t[0])
json.dump({"n": ns, "err": best[0][5], "desc": best[0][1:5]}, open("fig5_vgam_best.json", "w"))
