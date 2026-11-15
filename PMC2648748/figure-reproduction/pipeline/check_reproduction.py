"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR COMMITTED_OUTPUT REPORT_MD [--full]

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* an expected output is missing;
* the data sets rerun from scratch (sim_check.json) differ from the committed records;
* the downloaded paper's figures are not the committed comparison copies (fetch.json);
* the package check failed;
* the fresh run differs from the committed outputs (compare_runs.py: numbers to 1e-6 relative);
  our renders and the negative controls are compared pixel for pixel inside the scored frames
  (compare.py's masks: the six panels, legend and BEAM bars masked). Text outside those regions
  (titles, tick and axis labels) is rasterized differently by different FreeType/fontconfig
  setups with the same font file, so it is not compared; the pixel scores in comparison.json,
  which only see the masked regions, are compared as numbers.
With --full every data set was simulated again; the comparison with the committed outputs is then
reported, not enforced (the same code and seeds, so it should still match).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = ["published_values.json", "fetch.json", "summary.json", "comparison.json", "sim_check.json",
            "fig2_ours.png", "fig2_overlay.png", "fig3_ours.png", "fig3_overlay.png",
            "checks/model_variants.json", "checks/bstat_null.json", "checks/swsfs_variants.json", "package.json"]
# Run records that hold timings or this run's own state; the committed sim/ and checks/swsfs_variants
# are inputs of the default run.
IGNORE = ["package.json", "sim_check.json", "fetch.json", "report.md", "site/*", "sim/*", "checks/swsfs_variants.json",
          "fig*.png", "controls/*"]
RENDERS = ["fig2_ours.png", "fig2_overlay.png", "fig3_ours.png", "fig3_overlay.png",
           "controls/fig2_minus5.png", "controls/fig2_plus5.png", "controls/fig2_wrong_model.png",
           "controls/fig2_wrong_r2.png", "controls/fig3_minus2.png", "controls/fig3_plus2.png",
           "controls/fig3_wrong_model.png"]


def renders_in_frames(rundir, committed):
    """Compare our renders with the committed ones inside the scored regions; return (ok, table)."""
    import numpy as np
    from PIL import Image
    sys.path.insert(0, str(HERE))
    from compare import masks
    pub_values = json.loads((Path(rundir) / "published_values.json").read_text())
    pub = {k: np.asarray(Image.open(HERE.parent / "published" / f"figure-{k[-1]}.png").convert("L"), float)
           for k in ("fig2", "fig3")}
    mk = {k: masks(pub[k], k, pub_values) for k in pub}
    rows, ok = ["| File | Inside the scored frames | Pixels compared |", "| --- | --- | --- |"], True
    for f in RENDERS:
        kind = Path(f).name[:4]
        a, b = Path(rundir) / f, Path(committed) / f
        if not a.exists() or not b.exists():
            rows.append(f"| {f} | missing | |")
            ok = False
            continue
        x = np.asarray(Image.open(a).convert("RGB"), int)
        y = np.asarray(Image.open(b).convert("RGB"), int)
        if x.shape != y.shape:
            rows.append(f"| {f} | size differs | |")
            ok = False
            continue
        m = mk[kind]
        n = int((np.abs(x - y).max(axis=2)[m] > 0).sum())
        rows.append(f"| {f} | {'same' if n == 0 else f'{n} pixels differ'} | {int(m.sum())} |")
        ok &= n == 0
    return ok, "\n".join(rows)


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    results, rundir, committed, report = sys.argv[1:5]
    full = "--full" in sys.argv
    rundir = Path(rundir)
    lines = ["# PMC2648748 reproduction check", ""]
    ok = True

    rc, out = run([sys.executable, str(HERE / "check_results.py"), results, "--markdown", "--skip-files"])
    lines += ["## results.json", "", out.strip(), ""]
    ok &= rc == 0

    missing = [e for e in EXPECTED if not (rundir / e).exists()]
    if missing:
        ok = False
        lines += ["## Missing outputs", ""] + [f"- {m}" for m in missing] + [""]

    sc = json.loads((rundir / "sim_check.json").read_text()) if (rundir / "sim_check.json").exists() else {"passed": False, "datasets": []}
    lines += ["## Data sets rerun from scratch", "", "| Setting | Data set | SNPs selected | Same as committed |", "| --- | --- | --- | --- |"]
    for r in sc["datasets"]:
        lines.append(f"| model {r['model']}, MAF {r['maf']}, r2 {r['r2']} | {r['rep']} | {r['k']} | "
                     + ("yes" if not r["differences"] else "no: " + "; ".join(r["differences"][:3])) + " |")
    lines.append("")
    ok &= bool(sc["passed"])

    fe = json.loads((rundir / "fetch.json").read_text()) if (rundir / "fetch.json").exists() else None
    if fe:
        st = fe["pdf"]["status"]
        same = [f["same_as_committed"] for f in fe["figures"]]
        lines += ["## Inputs", "", f"The paper's PDF: {st}; Figs 2 and 3 from it are the committed copies: "
                  + ("yes" if all(same) else "not checked (PDF unavailable)" if st == "unavailable" else "no"), ""]
        ok &= st == "unavailable" or all(same)

    pk = json.loads((rundir / "package.json").read_text()) if (rundir / "package.json").exists() else {"passed": False}
    lines += ["## Package", "", pk.get("detail", "no report"), ""]
    ok &= bool(pk.get("passed"))

    rc, out = run([sys.executable, str(HERE / "compare_runs.py"), str(rundir), committed, "--ignore", *IGNORE])
    lines += ["## Fresh run against the committed outputs", "", out.strip(), ""]
    rok, table = renders_in_frames(rundir, committed)
    lines += ["Renders and controls, inside the scored frames (text outside them depends on the font rasterizer):",
              "", table, ""]
    if not full:
        ok &= rc == 0 and rok

    lines.append("**PASS**" if ok else "**FAIL**")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
