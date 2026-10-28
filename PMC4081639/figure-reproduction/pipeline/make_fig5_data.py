"""Fig. 5 data: VGAM = best R-code variant (fig5_vgam_best.json); mesh = authors' library (fig5_errs.json)."""
import json
b = json.load(open("fig5_vgam_best.json")); e = json.load(open("fig5_errs.json"))
with open("fig5_data.csv", "w") as f:
    f.write("n,method,error\n")
    for n, v in zip(b["n"], b["err"]): f.write("%d,VGAM,%.6f\n" % (n, v))
    for n, v in zip(e["n"], e["lib_mesh|dbl"]): f.write("%d,mesh,%.6f\n" % (n, v))
print("fig5: VGAM variant", b["desc"])
