"""One-off hypothesis test for the Fig. 2 labels (not part of the pipeline run): dimension 7 counts at
epsilon 0.2-0.5 on the Collins and BioGRID copies of Yhigh, with low-confidence cuts 1.85 and 1.86.
Run from PMC2711306/work with the full-run networks in net/; writes fig2_label_hypotheses.json
(committed as output/run/fig2_label_hypotheses.json)."""
import numpy as np, geodenoise as gd, sys, json
sys.path.insert(0,'../figure-reproduction/pipeline')
from yeast import nonedge_universe, labels, grid_points
rows=[l.rstrip('\n').split('\t') for l in open('../sources/collins/combined_scores.txt') if not l.startswith('#')]
paper=[(1776,10725),(3454,26718),(4312,47227),(4793,73331)]
def run(net, lowcut):
    low=[(r[0].upper(),r[2].upper()) for r in rows if lowcut<=float(r[4])<3.19]
    ni,nj=nonedge_universe(net); pos=labels(net,ni,nj,low)
    D=gd.pairwise_distances(gd.embed(net,7)); g=grid_points(D[ni,nj],pos,pos.sum(),(~pos).sum(),[0.2,0.3,0.4,0.5])
    return int(pos.sum()), [(p['tp'],p['fp']) for p in g]
out={}
for name,path in [('collins','net/yhigh.tsv'),('biogrid','net/yhigh_biogrid.tsv')]:
    net=gd.read_network(path)
    for cut in (1.85,1.86):
        out[f'{name} low>={cut}']=run(net,cut); print(name,cut,out[f'{name} low>={cut}'],flush=True)
out['paper']=paper
json.dump(out,open('fig2_label_hypotheses.json','w'),indent=1)
