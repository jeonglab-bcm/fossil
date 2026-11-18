#!/bin/bash
# The authors' TopHat 1.0.14 alignments (GEO GSE26561) are what TopHat contributes to the junction set.
# Junctions from a TopHat SAM (stdin): chrom donor acceptor reads (NH-weighted) reads_NH1
awk -F'\t' 'BEGIN{OFS="\t"} !/^@/ && $6 ~ /N/ {
  nh=1; for(i=12;i<=NF;i++) if($i ~ /^NH:i:/) nh=substr($i,6)+0;
  pos=$4-1; c=$6;
  while (match(c,/^[0-9]+[MNDIS]/)) { len=substr(c,1,RLENGTH-1)+0; op=substr(c,RLENGTH,1); c=substr(c,RLENGTH+1);
    if (op=="M"||op=="D") pos+=len; else if (op=="N") { k=$3 "\t" pos "\t" pos+len; w[k]+=1/nh; if(nh==1) u[k]++; pos+=len } }
} END { for (k in w) printf "%s\t%.4f\t%d\n", k, w[k], u[k] }'
