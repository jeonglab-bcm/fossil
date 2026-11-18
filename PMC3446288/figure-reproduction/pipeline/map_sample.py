#!/usr/bin/env python3
"""Map one sample's reads to mm9 and to the combinatorial junction database, as RAINMAN did.

Additional file 1: Bowtie (0.11.3; we use 1.0.0, the oldest Bowtie on Bioconda) with up to two
mismatches in the first 68 bp (-n 2 -l 68), the best hit by mismatch stratum (--best -k 1), against
the genome and the junction database together. We run the two indexes separately and keep, for each
read, the hit with fewer mismatches (genome on a tie). A junction hit counts only when the read covers
at least 4 bases on each side of the junction. Reads that map to neither are truncated from either
side in steps of 10 nt (65, 55, 45, 35 nt) and remapped; a read counts as recovered when either of its
two truncated versions maps, and every junction hit of a truncated version is counted.

Usage: map_sample.py READS.fastq.gz GENOME_INDEX JUNCTION_INDEX OUTDIR [--threads N]
Writes OUTDIR/junction_counts.tsv, OUTDIR/genome_hits.npz and OUTDIR/mapping_stats.json.
"""

import argparse
import gzip
import json
import os
import subprocess
import sys
import tempfile
import time

import numpy as np

BOWTIE = os.environ.get("BOWTIE", "bowtie")
OVERHANG = 4
TRUNCATIONS = (65, 55, 45, 35)


def bowtie(index, reads_path, threads, extra=()):
    cmd = [BOWTIE, "-p", str(threads), "-q", "-n", "2", "-l", "68", "--best", "-k", "1",
           "--suppress", "5,6,7", *extra, index, reads_path]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1 << 20)
    for line in p.stdout:
        yield line.rstrip("\n").split("\t")
    err = p.stderr.read()
    if p.wait() != 0:
        sys.exit(f"bowtie failed: {' '.join(cmd)}\n{err}")


def n_mismatches(field):
    return 0 if not field else field.count(",") + 1


FIRST = 1  # number of the first read in the file (SRA numbers spots consecutively from 1)


def read_index(name):
    # SRR094621.68 BMM_WT:1:1:1:68 length=75  ->  67 ; truncated reads: "67_65_5"
    head = name.split(" ", 1)[0]
    if "_" in head:
        return int(head.split("_", 1)[0])
    return int(head.rsplit(".", 1)[1]) - FIRST




def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reads")
    ap.add_argument("genome")
    ap.add_argument("junctions")
    ap.add_argument("outdir")
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    t0 = time.time()
    tmp = tempfile.mkdtemp(dir=a.outdir)
    plain = os.path.join(tmp, "reads.fq")
    with gzip.open(a.reads, "rb") as fi, open(plain, "wb") as fo:
        while chunk := fi.read(1 << 24):
            fo.write(chunk)
    n = os.path.getsize(plain)
    global FIRST
    with open(plain, "rb") as f:
        FIRST = int(f.readline().split(b" ", 1)[0].rsplit(b".", 1)[1])
        n = (sum(1 for _ in f) + 1) // 4
    print(f"{n} reads", file=sys.stderr)

    chroms = []
    g_mm = np.full(n, 99, np.int8)
    g_chrom = np.zeros(n, np.int8)
    g_pos = np.zeros(n, np.int32)
    for f in bowtie(a.genome, plain, a.threads):
        i = read_index(f[0])
        if f[2] not in chroms:
            chroms.append(f[2])
        g_mm[i] = n_mismatches(f[4] if len(f) > 4 else "")
        g_chrom[i] = chroms.index(f[2])
        g_pos[i] = int(f[3])
    print(f"genome pass {time.time() - t0:.0f}s, {(g_mm < 99).sum()} mapped", file=sys.stderr)

    # A read with a perfect genome hit cannot lose to a junction hit (ties go to the genome), so only
    # the other reads go through the junction database.
    jpath = os.path.join(tmp, "for_junctions.fq")
    with open(plain) as fi, open(jpath, "w") as fo:
        for k, line in enumerate(fi):
            if g_mm[k // 4] != 0:
                fo.write(line)
    counts = {}
    is_junction = np.zeros(n, bool)
    j_mm = np.full(n, 99, np.int8)
    for f in bowtie(a.junctions, jpath, a.threads):
        i = read_index(f[0])
        mm = n_mismatches(f[4] if len(f) > 4 else "")
        j_mm[i] = mm
        name = f[2]
        jid, left = name.rsplit(":", 1)
        off = int(f[3])
        if off <= int(left) - OVERHANG and off + 75 >= int(left) + OVERHANG and mm < g_mm[i]:
            is_junction[i] = True
            counts[jid] = counts.get(jid, 0) + 1
    os.remove(jpath)
    print(f"junction pass {time.time() - t0:.0f}s, {is_junction.sum()} junction reads", file=sys.stderr)

    genome_final = (g_mm < 99) & ~is_junction
    unmapped = (g_mm == 99) & ~is_junction
    stats = {"reads": int(n), "genome": int(genome_final.sum()), "junction": int(is_junction.sum()),
             "junction_reads_full_length": int(is_junction.sum()), "truncation": {}}

    # Truncation rounds on reads that map nowhere (also not as a junction read without overhang).
    pending = np.flatnonzero(unmapped)
    trunc_counts = {}
    trunc_genome = []
    recovered_total = 0
    with open(plain) as f:
        seqs = {}
        want = set(pending.tolist())
        for k, line in enumerate(f):
            r = k // 4
            if k % 4 == 1 and r in want:
                seqs[r] = line.rstrip("\n")
            elif k % 4 == 3 and r in want:
                seqs[r] = (seqs[r], line.rstrip("\n"))
    os.remove(plain)
    for L in TRUNCATIONS:
        path = os.path.join(tmp, f"t{L}.fq")
        with open(path, "w") as fo:
            for r in pending:
                s, q = seqs[r]
                if len(s) <= L:
                    continue
                fo.write(f"@{r}_{L}_3\n{s[:L]}\n+\n{q[:L]}\n")  # 3' end trimmed
                fo.write(f"@{r}_{L}_5\n{s[-L:]}\n+\n{q[-L:]}\n")  # 5' end trimmed
        hit = {}
        gm = {}
        for fl in bowtie(a.genome, path, a.threads):
            key = fl[0].split(" ", 1)[0]
            gm[key] = (n_mismatches(fl[4] if len(fl) > 4 else ""), fl[2], int(fl[3]))
        jpath = path + ".j.fq"
        with open(path) as fi, open(jpath, "w") as fo:
            rec = []
            for line in fi:
                rec.append(line)
                if len(rec) == 4:
                    g = gm.get(rec[0][1:].split(" ", 1)[0].rstrip("\n"))
                    if g is None or g[0] != 0:
                        fo.writelines(rec)
                    rec = []
        jn = {}
        for fl in bowtie(a.junctions, jpath, a.threads):
            key = fl[0].split(" ", 1)[0]
            mm = n_mismatches(fl[4] if len(fl) > 4 else "")
            jid, left = fl[2].rsplit(":", 1)
            off = int(fl[3])
            if off <= int(left) - OVERHANG and off + L >= int(left) + OVERHANG:
                jn[key] = (mm, jid)
        recovered = set()
        jreads = 0
        for key in set(gm) | set(jn):
            r = int(key.split("_", 1)[0])
            g = gm.get(key)
            j = jn.get(key)
            if j is not None and (g is None or j[0] < g[0]):
                trunc_counts[j[1]] = trunc_counts.get(j[1], 0) + 1
                jreads += 1
            elif g is not None:
                trunc_genome.append((g[1], g[2]))
            recovered.add(r)
        stats["truncation"][str(L)] = {"input": int(len(pending)), "recovered": len(recovered),
                                       "junction_hits": jreads}
        recovered_total += len(recovered)
        pending = np.array([r for r in pending if r not in recovered], dtype=np.int64)
        os.remove(path)
        os.remove(jpath)
        print(f"truncation {L}: {len(recovered)} recovered, {time.time() - t0:.0f}s", file=sys.stderr)
    os.rmdir(tmp)
    stats["truncation_recovered"] = int(recovered_total)
    stats["unmapped"] = int(len(pending))
    stats["seconds"] = round(time.time() - t0)

    with open(os.path.join(a.outdir, "junction_counts.tsv"), "w") as fo:
        fo.write("junction\treads\treads_truncated\n")
        for jid in sorted(set(counts) | set(trunc_counts)):
            fo.write(f"{jid}\t{counts.get(jid, 0)}\t{trunc_counts.get(jid, 0)}\n")
    sel = np.flatnonzero(genome_final)
    tc = [chroms.index(c) if c in chroms else chroms.append(c) or len(chroms) - 1 for c, _ in trunc_genome]
    np.savez_compressed(
        os.path.join(a.outdir, "genome_hits.npz"),
        chroms=np.array(chroms), chrom=g_chrom[sel], pos=g_pos[sel],
        trunc_chrom=np.array(tc, np.int8), trunc_pos=np.array([p for _, p in trunc_genome], np.int32),
    )
    with open(os.path.join(a.outdir, "mapping_stats.json"), "w") as fo:
        json.dump(stats, fo, indent=1)
    print(json.dumps(stats), file=sys.stderr)


if __name__ == "__main__":
    main()
