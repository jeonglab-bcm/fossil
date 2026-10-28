import os as _os
_SRC = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "fig5_score.py")
import math, json
from mpmath import mp, mpf, log as mlog
mp.dps=60
exec(open(_SRC).read().split("paper=")[0].split("lib=")[0])
ns=list(range(200,10001,200))
lib=[tuple(map(float,l.split())) for l in open("fig5_lib.txt")]
# reuse functions
src=open(_SRC).read()
exec(src[src.index("def exact"):src.index("paper=")])
vg={1600:184,2000:184,2600:-365,2800:-365,3000:-365,3200:365,3800:-365,4200:365,4400:365,4600:-728,4800:-365,5000:-365,5200:-728,5400:365,5600:1091,5800:-1091,6200:-728,6400:728,7800:1456,8000:-2184,8200:728,8600:728,9000:728,9200:-1456,9400:728,9600:2184,9800:-1456,10000:728}
me={9400:-728,9600:728}
psi=0.005
exd={True:[exact(n,True) for n in ns], False:[exact(n,False) for n in ns]}
cands={"lib_mesh":[l[0] for l in lib],"lib_vgam":[l[1] for l in lib],
       "R_vgam_ext":[r_vgam(n,True) for n in ns],"R_vgam_dbl":[r_vgam(n,False) for n in ns]}
res={}
for name,vals in cands.items():
    for pdec in (True,False):
        err=[(v-float(e))/1e-14 for v,e in zip(vals,exd[pdec])]
        ref=me if "mesh" in name else vg
        match=sum(1 for n,e in zip(ns,err) if abs(e-ref.get(n,0))<40)
        res[f"{name}|{'dec' if pdec else 'dbl'}"]=err
        bad={n:round(e) for n,e in zip(ns,err) if abs(e-ref.get(n,0))>=40}
        print(f"{name:11s} {'dec' if pdec else 'dbl'}: {match}/50 match  mismatches {bad}")
res["n"]=ns
json.dump(res,open("fig5_errs.json","w"))
