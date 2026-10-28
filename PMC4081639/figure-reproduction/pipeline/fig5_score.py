import math, numpy as np
from mpmath import mp, mpf, log as mlog
mp.dps=60
ns=list(range(200,10001,200))
lib=[tuple(map(float,l.split())) for l in open("fig5_lib.txt")]
psi=0.005
def exact(n, pdec=True):
    P=[mpf(1)/10,mpf(2)/10,mpf(3)/10,mpf(4)/10] if pdec else [mpf(0.1),mpf(0.2),mpf(0.3),mpf(0.4)]
    ps=mpf(1)/200 if pdec else mpf(0.005)
    s=mpf(0)
    for pk in P:
        s+=sum(mlog(pk+r*ps) for r in range(n))
    s-=sum(mlog(1+r*ps) for r in range(4*n))
    return s
def r_vgam(n, ext=True):
    rho=psi/(1+psi); P=[0.1,0.2,0.3,0.4]
    def rsum(v):
        if not ext: return math.fsum(v) if False else float(np.sum(np.array(v))) if False else sum_d(v)
        mp.prec=64; s=mpf(0)
        for t in v: s=s+mpf(t)
        r=float(s); mp.dps=60; return r
    tot=[]
    for pk in P:
        tot.append(rsum([math.log(pk*(1-rho)+r*rho) for r in range(n)]))
    a=sum(tot)  # R: sum(sapply(...)) also ext-accumulated
    a=rsum(tot) if ext else a
    b=rsum([math.log((1-rho)+r*rho) for r in range(4*n)])
    return a-b
def sum_d(v):
    s=0.0
    for t in v: s+=t
    return s
paper={1600:184,2000:184,2600:-365,2800:-365,3000:-365,3200:365,3800:-365,4200:365,4400:365,4600:-728,4800:-365,5000:-365,5200:-728,5400:365,5600:1091,5800:-1091,6200:-728,6400:728,7800:1456,8000:-2184,8200:728,8600:728,9000:728,9200:-1456,9600:2184,9800:-1456,10000:728}
ex_dec=[exact(n,True) for n in ns]
cands={}
cands["lib_mesh"]=[l[0] for l in lib]; cands["lib_vgam"]=[l[1] for l in lib]
cands["R_vgam_ext"]=[r_vgam(n,True) for n in ns]
cands["R_vgam_dbl"]=[r_vgam(n,False) for n in ns]
ex_dbl=[exact(n,False) for n in ns]
out={}
for name,vals in cands.items():
    for exn,ex in (("dec",ex_dec),("dbl",ex_dbl)):
        err=[float((mpf(v)-e)/mpf(1e-14)) for v,e in zip(vals,ex)]
        out[(name,exn)]=err
        nz={n:round(e) for n,e in zip(ns,err) if abs(e)>150}
        hit=sum(1 for n in paper if n in nz and abs(nz[n]-paper[n])<60)
        print(f"{name:12s} {exn}: nonzero={len(nz):2d}  matches paper VGAM marks {hit}/{len(paper)}  ", dict(list(nz.items())[:6]))
import json
json.dump({f"{k[0]}|{k[1]}":v for k,v in out.items()}|{"n":ns}, open("fig5_errs.json","w"))
