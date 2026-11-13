"""The pipeline's check step.

usage: check_reproduction.py RESULTS_JSON RUN_DIR COMMITTED_OUTPUT REPORT_MD [--full]

Fails (exit 1) when
* check_results.py finds a broken rule or a stale verdict in results.json;
* an expected output is missing;
* the data sets rerun from scratch (sim_check.json) differ from the committed records;
* the downloaded paper's figures are not the committed comparison copies (fetch.json);
* the package check failed;
* the fresh run differs from the committed outputs (compare_runs.py: numbers to 1e-6 relative,
  images by decoded pixels).
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
IGNORE = ["package.json", "sim_check.json", "fetch.json", "report.md", "site/*", "sim/*", "checks/swsfs_variants.json"]


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
    if not full:
        ok &= rc == 0

    lines.append("**PASS**" if ok else "**FAIL**")
    Path(report).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
