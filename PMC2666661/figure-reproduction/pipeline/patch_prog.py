"""Write a copy of Breiman and Cutler's Random Forests 5.1 (prog.f) set up for one data set, for the
port check (port_check.py). prog.f itself is downloaded by fetch_inputs.sh and is not in this
repository.

  patch_prog.py PROG_F OUT_F --mdim P --seed S [--rf1]

Changes, each a literal replacement that must match exactly once:
  * parameters: P variables, 500 training cases, 2 classes, every variable categorical with 3
    levels, mtry 35, 5000 trees, importance on, proximities and other outputs off, seed S;
  * the importance file lists every variable (prog.f writes only the 25 most important) together
    with T_v, the number of trees that split on it;
  * with --rf1, the revised tree builder of Meng et al. (2009), as we read its Methods: each tree
    starts with all variables in its pool; after a node splits on variable v, every other
    variable whose r^2 with v exceeds R (the 0/1 matrix in data.ld) leaves the pool, and the
    mtry candidates of later nodes of that tree are drawn from the pool.
"""

import argparse
import sys

COMMON = "\tcommon /rf1c/ irf1,npool,ipool(500),ntv(500),ldm(500,500)\n\tinteger irf1,npool,ipool,ntv\n\tinteger*1 ldm\n"


def sub(text, old, new, count=1):
    n = text.count(old)
    if n != count:
        sys.exit(f"patch_prog: expected {count} match(es) of {old!r}, found {n}")
    return text.replace(old, new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prog")
    ap.add_argument("out")
    ap.add_argument("--mdim", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--rf1", action="store_true")
    a = ap.parse_args()
    if a.mdim > 500:
        sys.exit("patch_prog: at most 500 variables")
    s = open(a.prog, encoding="latin-1").read()

    s = sub(s, "mdim=9,ntrain=214,nclass=6,maxcat=1,", f"mdim={a.mdim},ntrain=500,nclass=2,maxcat=3,")
    s = sub(s, "mtry0=2,ndsize=1,jbt=500,look=100,lookcls=1,", "mtry0=35,ndsize=1,jbt=5000,look=5000,lookcls=0,")
    s = sub(s, "imp=1,interact=0,impn=1,", "imp=1,interact=0,impn=0,")
    s = sub(s, "nprox=1,nrnn=ntrain,", "nprox=0,nrnn=ntrain,")
    s = sub(s, "isumout\t= \t1,", "isumout\t= \t0,")
    s = sub(s, "iprotout=\t1,", "iprotout=\t0,")
    s = sub(s, "iproxout=\t1,", "iproxout=\t0,")
    s = sub(s, "ioutlierout=\t1)", "ioutlierout=\t0)")
    s = sub(s, "iseed=4351", f"iseed={a.seed}")
    # every variable categorical, 3 levels (genotype codes 1, 2, 3)
    s = sub(s, "\tdo m=1,mdim\n\t\tcat(m)=1\n\tenddo\n",
            "\tdo m=1,mdim\n\t\tcat(m)=3\n\tenddo\n")

    # common block in the main program, findbestsplit, buildtree and varimp
    s = sub(s, "\treal code\nc\n", "\treal code\n" + COMMON + "c\n")
    s = sub(s, "\treal randomu\nc\n\texternal unpack\n", "\treal randomu\n" + COMMON + "c\n\texternal unpack\n")
    s = sub(s, "\tinteger nbestcat(maxcat,nrnodes)\nc\n\tcall zerv(nodestatus,nrnodes)\n",
            "\tinteger nbestcat(maxcat,nrnodes)\n" + COMMON + "\tinteger ip,jp\n"
            "c\n\tnpool=mdim\n\tdo ip=1,mdim\n\t\tipool(ip)=ip\n\tenddo\n"
            "\tcall zerv(nodestatus,nrnodes)\n")
    s = sub(s, "\tinteger nout,mr,nn,n,jj,k\n\treal right,rightimp\n",
            "\tinteger nout,mr,nn,n,jj,k\n\treal right,rightimp\n" + COMMON)

    # read the LD matrix and the RF1 switch after the training data
    s = sub(s, "\tclose(16)\n",
            "\tclose(16)\n"
            f"\tirf1={1 if a.rf1 else 0}\n"
            "\tdo m=1,mdim\n\t\tntv(m)=0\n\tenddo\n"
            "\tif(irf1.eq.1) then\n\t\topen(18,file='data.ld',status='old')\n"
            "\t\tdo n=1,mdim\n\t\t\tread(18,*) (ldm(n,m),m=1,mdim)\n\t\tenddo\n"
            "\t\tclose(18)\n\tendif\n")

    # draw split candidates from the tree's pool
    s = sub(s, "\t\tk=int(mdimt*randomu())+1\n\t\tmvar=msm(k)\n",
            "\t\tif(irf1.eq.1) then\n\t\t\tk=int(npool*randomu())+1\n"
            "\t\t\tif(k.gt.npool) k=npool\n\t\t\tmvar=ipool(k)\n"
            "\t\telse\n\t\t\tk=int(mdimt*randomu())+1\n"
            "\t\t\tif(k.gt.mdimt) k=mdimt\n\t\t\tmvar=msm(k)\n\t\tendif\n")

    # after a split on msplit, drop its LD partners from the pool
    s = sub(s, "\t\t\tbestvar(kbuild)=msplit\n",
            "\t\t\tbestvar(kbuild)=msplit\n"
            "\t\t\tif(irf1.eq.1) then\n\t\t\t\tjp=0\n\t\t\t\tdo ip=1,npool\n"
            "\t\t\t\t\tif(ipool(ip).eq.msplit.or.ldm(msplit,ipool(ip)).eq.0) then\n"
            "\t\t\t\t\t\tjp=jp+1\n\t\t\t\t\t\tipool(jp)=ipool(ip)\n\t\t\t\t\tendif\n"
            "\t\t\t\tenddo\n\t\t\t\tnpool=jp\n\t\t\tendif\n")

    # count T_v
    s = sub(s, "\t\tif(nodestatus(jj).ne.-1) iv(bestvar(jj))=1\n\tenddo\n",
            "\t\tif(nodestatus(jj).ne.-1) iv(bestvar(jj))=1\n\tenddo\n"
            "\tdo jj=1,mdim\n\t\tif(iv(jj).eq.1) ntv(jj)=ntv(jj)+1\n\tenddo\n")

    # write every variable's importance and T_v
    s = sub(s, "\t\tdo k=1,min0(mdimt,25)\n\t\t\tm=muse(k)\n",
            "\t\topen(31,file='imp-all',status='unknown')\n"
            "\t\tdo m=1,mdim\n\t\t\twrite(31,'(i5,f14.8,i8)') m,100*avimp(m),ntv(m)\n\t\tenddo\n"
            "\t\tclose(31)\n"
            "\t\tdo k=1,min0(mdimt,25)\n\t\t\tm=muse(k)\n")
    open(a.out, "w", encoding="latin-1").write(s)


if __name__ == "__main__":
    main()
