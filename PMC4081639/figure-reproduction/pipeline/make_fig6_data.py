"""Fig. 6 data: join timings, then scale each method by one constant to the paper's box medians (least squares in log10)."""
import csv, json
import numpy as np
rows = list(csv.DictReader(open("fig6_mesh_native.csv"))) + [dict(r, n=str(int(float(r["n"])))) for r in csv.DictReader(open("fig6_vgam.csv"))]
with open("fig6_data.csv", "w") as f:
    f.write("n,method,runtime_us\n")
    for r in rows: f.write("%s,%s,%s\n" % (r["n"].strip('"'), r["method"].strip('"'), r["runtime_us"]))
ours = {}
for r in csv.DictReader(open("fig6_data.csv")): ours.setdefault((int(float(r["n"])), r["method"]), []).append(float(r["runtime_us"]))
paper = json.load(open("fig6_paper.json"))
med = {(int(k.split("|")[0]), k.split("|")[1]): v for k, v in paper["medians"].items()}
fac = {}
for m in ("mesh", "VGAM"):
    lr = [np.log10(np.median(ours[k]) / med[k]) for k in med if k[1] == m]
    fac[m] = float(10 ** np.mean(lr))
    print(f"fig6: {m} ours/paper by n {[round(float(10 ** v), 1) for v in lr]}  factor {fac[m]:.2f}")
json.dump({"paper_medians": paper["medians"], "factor": fac, "ylim": paper["ylim"]}, open("fig6_scale.json", "w"), indent=1)
with open("fig6_data_scaled.csv", "w") as f:
    f.write("n,method,runtime_us\n")
    for r in csv.DictReader(open("fig6_data.csv")):
        f.write("%s,%s,%.6f\n" % (r["n"], r["method"], float(r["runtime_us"]) / fac[r["method"]]))
