import csv, json, sys
import numpy as np
from mpmath import mp, mpf, loggamma
mp.dps = 50
X=[2,3,1]; Pp=[mpf(2)/10, mpf(3)/10, mpf(5)/10]
def exact(psi):
    psi=mpf(psi); N=sum(X)
    return -(loggamma(1/psi+N)-loggamma(1/psi)) + sum(loggamma(Pp[i]/psi+X[i]) - loggamma(Pp[i]/psi) for i in range(3))
# NOTE: p uses exact decimals .2,.3,.5; also try double-rounded p
Pd=[mpf(0.2),mpf(0.3),mpf(0.5)]
def exact_d(psi):
    psi=mpf(psi); N=sum(X)
    return -(loggamma(1/psi+N)-loggamma(1/psi)) + sum(loggamma(Pd[i]/psi+X[i]) - loggamma(Pd[i]/psi) for i in range(3))
rows=list(csv.DictReader(open("eq6_grids.csv")))
cache={}
tr=json.load(open("paper_traces.json"))["figure-2"]
trx=np.array([t[0] for t in tr]); trmin=np.array([t[1] for t in tr]); trmax=np.array([t[2] for t in tr])
gx=np.polyfit([2.5e-11,5e-11,7.5e-11,1e-10],[214.5,307,400,493],1)
gy=np.polyfit([2.5e-4,-2.5e-4,-5e-4],[94,323.5,438],1)
def raster(ps,es):
    xs=np.polyval(gx,ps); ys=np.polyval(gy,es)
    cmin={}; cmax={}
    for i in range(len(xs)-1):
        n=int(abs(xs[i+1]-xs[i])*4)+2
        for t in np.linspace(0,1,n):
            x=int(round(xs[i]+(xs[i+1]-xs[i])*t)); y=ys[i]+(ys[i+1]-ys[i])*t
            cmin[x]=min(cmin.get(x,1e9),y); cmax[x]=max(cmax.get(x,-1e9),y)
    return cmin,cmax
groups={}
for r in rows: groups.setdefault(r["grid"],[]).append(r)
res=[]
for g,rs in groups.items():
    ps=np.array([float(r["psi"]) for r in rs])
    for ex_name,exf in (("dec",exact),("dbl",exact_d)):
        ex=[]
        for r in rs:
            k=(r["psi"],ex_name)
            if k not in cache: cache[k]=exf(mpf(float(r["psi"])))
            ex.append(cache[k])
        for v in ("v1","v2","v3"):
            es=np.array([float(mpf(float(r[v]))-e) for r,e in zip(rs,ex)])
            cmin,cmax=raster(ps,es)
            d=[]
            for x,a,b in zip(trx,trmin,trmax):
                if x in cmin: d.append(abs(cmin[x]-a)+abs(cmax[x]-b))
            res.append((float(np.mean(d)) if d else 1e9, g, v, ex_name, float(es.min()), float(es.max())))
res.sort()
for r in res[:12]: print("%.2f %-10s %s %s  min %.3g max %.3g"%r)
