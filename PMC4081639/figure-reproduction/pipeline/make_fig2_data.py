"""Fig. 2 data on the paper's grid psi = seq(1e-11, 1e-10, length.out = 300), error = Eq. (6) - exact.

Writes fig2_data.csv (Eq. 6 with R's x86 arithmetic: lgammafn without FMA, 80-bit sum) and
fig2_data_native.csv (Eq. 6 from this platform's R, column v1 of eq6_grids.csv).
"""
import csv, json, math, platform
from mpmath import mp, mpf, loggamma

M_LN_SQRT_2PI = 0.918938533204672741780329736406
def lgammafn(x):  # R nmath lgammafn, branch x > 4934720, plain double operations
    assert x > 4934720.0
    return (M_LN_SQRT_2PI + (x - 0.5) * math.log(x)) - x
def sum80(v):
    mp.prec = 64; s = mpf(0)
    for t in v: s = s + mpf(t)
    r = float(s); mp.dps = 50; return r

X = [2.0, 3.0, 1.0]; P = [0.2, 0.3, 0.5]; N = 6.0
mp.dps = 50; Pm = [mpf(0.2), mpf(0.3), mpf(0.5)]
rows = [r for r in csv.DictReader(open("eq6_grids.csv")) if r["grid"] == "len300"]
assert len(rows) == 300
emu, nat = [], []
for r in rows:
    psi = float(r["psi"]); pm = mpf(psi)
    ex = -(loggamma(1 / pm + 6) - loggamma(1 / pm)) + sum(loggamma(Pm[i] / pm + X[i]) - loggamma(Pm[i] / pm) for i in range(3))
    a = [p / psi for p in P]; inv = 1.0 / psi
    v = -(lgammafn(inv + N) - lgammafn(inv)) + sum80([lgammafn(ai + xi) - lgammafn(ai) for ai, xi in zip(a, X)])
    emu.append((r["psi"], float(mpf(v) - ex))); nat.append((r["psi"], float(mpf(float(r["v1"])) - ex)))
for name, rows_ in (("fig2_data.csv", emu), ("fig2_data_native.csv", nat)):
    with open(name, "w") as f:
        f.write("psi,error\n")
        for p, e in rows_: f.write("%s,%.17g\n" % (p, e))
diff = sum(1 for (_, a), (_, b) in zip(emu, nat) if a != b)
json.dump({"machine": platform.machine(), "system": platform.system(), "native_vs_x86_emulation_differ": diff}, open("fig2_summary.json", "w"))
print(f"fig2: {diff} of 300 points differ between this platform's R and the x86 emulation ({platform.machine()})")
