"""Fig. 5: CPU time of GeCON and ARACNE against the number of genes, 50 time points.

The paper's Java programs are gone; this times the gecon package (Python, NumPy) and minet's ARACNE (R,
C++, including the mutual-information matrix). Inputs are random log-normal matrices (seed 1): the run time
of both methods depends on the matrix size, not on its values. Sizes are the six points of Fig. 5.

Usage: timing.py OUT.json [--sizes 250,1000,...] [--reps 3] [--rscript Rscript]
"""
import json, os, platform, subprocess, sys, tempfile, time
import numpy as np
import gecon

SIZES = [250, 1000, 1500, 2000, 2585, 3000]


def main():
    out = sys.argv[1]
    sizes = [int(s) for s in sys.argv[sys.argv.index("--sizes") + 1].split(",")] if "--sizes" in sys.argv else SIZES
    reps = int(sys.argv[sys.argv.index("--reps") + 1]) if "--reps" in sys.argv else 3
    rscript = sys.argv[sys.argv.index("--rscript") + 1] if "--rscript" in sys.argv else "Rscript"
    here = os.path.dirname(os.path.abspath(__file__))
    rng = np.random.default_rng(1)
    rows = []
    for n in sizes:
        X = np.exp(rng.normal(size=(n, 50)))
        ts = []
        for _ in range(reps):
            t0 = time.process_time()
            gecon.gecon(X)
            ts.append(time.process_time() - t0)
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "x.tsv")
            with open(p, "w") as f:
                f.write("gene\t" + "\t".join(f"t{i}" for i in range(50)) + "\n")
                for i, row in enumerate(X):
                    f.write(f"g{i}\t" + "\t".join(f"{v:.6g}" for v in row) + "\n")
            r = subprocess.run([rscript, os.path.join(here, "timing.R"), p, str(reps)], check=True, capture_output=True, text=True)
            mim, ar, tot = [float(v) for v in r.stdout.split()]
        rows.append({"genes": n, "gecon_s": round(float(np.median(ts)), 3), "aracne_mim_s": mim, "aracne_s": ar, "aracne_total_s": tot})
        print(rows[-1], flush=True)
    cpu = platform.processor() or platform.machine()
    try:
        cpu = [l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")][0]
    except Exception:
        pass
    json.dump({"note": "re-measured; times depend on the machine", "cpu": cpu, "reps": reps, "rows": rows}, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
