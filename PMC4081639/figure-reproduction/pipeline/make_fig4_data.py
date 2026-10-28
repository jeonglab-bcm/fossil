"""Fig. 4 data: aod,dirmult = the Fig. 2 series; mesh = authors' lldmn library (fig4_mesh.txt) minus exact."""
import csv
from mpmath import mp, mpf, loggamma
mp.dps = 50
X = [2, 3, 1]; P = [mpf(0.2), mpf(0.3), mpf(0.5)]
f2 = list(csv.DictReader(open("fig2_data.csv")))
psis = [l.split()[1] for l in open("fig4_in.txt")]
mesh = [float(l) for l in open("fig4_mesh.txt")]
assert len(mesh) == 300 and all(float(a["psi"]) == float(b) for a, b in zip(f2, psis))
with open("fig4_data.csv", "w") as f:
    f.write("psi,method,error\n")
    for r, m in zip(f2, mesh):
        psi = mpf(float(r["psi"]))
        ex = -(loggamma(1 / psi + 6) - loggamma(1 / psi)) + sum(loggamma(P[i] / psi + X[i]) - loggamma(P[i] / psi) for i in range(3))
        f.write("%s,mesh,%.17g\n" % (r["psi"], float(mpf(m) - ex)))
    for r in f2: f.write("%s,aod_dirmult,%s\n" % (r["psi"], r["error"]))
print("fig4: wrote 600 rows")
