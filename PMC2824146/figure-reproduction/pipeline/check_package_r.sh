#!/usr/bin/env bash
# The R package steps of the paper2repro skill, in a fresh user library:
#   1. R CMD build (runs the vignette)  2. R CMD check --no-manual (tests, vignette)
#   3. render the vignette to TUTORIAL.md and compare it with the committed tutorial/TUTORIAL.md
# Writes a JSON report: passed, detail, and each step's status.
#   check_package_r.sh PKG_DIR OUT.json [--write]   (--write: update the committed TUTORIAL.md)
set -uo pipefail
pkg="$(cd "$1" && pwd)"; out="$(realpath -m "$2")"; write="${3:-}"
work="$(mktemp -d)"; lib="$work/lib"; mkdir -p "$lib"
export R_LIBS_USER="$lib" _R_CHECK_FORCE_SUGGESTS_=false LANG=C.UTF-8 LC_ALL=C.UTF-8
cd "$work"
cp -r "$pkg" src
build_ok=false; check_ok=false; tut_ok=false; status="not run"; tests="?"
if R CMD build --no-manual src > build.log 2>&1; then build_ok=true; fi
tar=$(ls misscox_*.tar.gz 2>/dev/null | head -1)
if $build_ok && [[ -n "$tar" ]]; then
  R CMD check --no-manual "$tar" > check.log 2>&1
  status=$(grep -E '^Status:' check.log | tail -1)
  if grep -qE '^Status: OK|^Status: [0-9]+ NOTE' check.log; then check_ok=true; fi
  tests=$(grep -oE '\[ FAIL [0-9]+ \| WARN [0-9]+ \| SKIP [0-9]+ \| PASS [0-9]+ \]' misscox.Rcheck/tests/testthat.Rout 2>/dev/null | tail -1)
  R CMD INSTALL -l "$lib" "$tar" > install.log 2>&1
fi
mkdir -p tut
Rscript -e "rmarkdown::render('src/vignettes/tutorial.Rmd', output_format = rmarkdown::github_document(html_preview = FALSE), output_file = 'TUTORIAL.md', output_dir = '$work/tut', quiet = TRUE)" > tut.log 2>&1
if [[ "$write" == "--write" ]]; then mkdir -p "$pkg/tutorial" && cp tut/TUTORIAL.md "$pkg/tutorial/TUTORIAL.md"; fi
if cmp -s tut/TUTORIAL.md "$pkg/tutorial/TUTORIAL.md"; then tut_ok=true; fi
passed=false; if $build_ok && $check_ok && $tut_ok; then passed=true; fi
detail="R CMD build $($build_ok && echo ok || echo failed); R CMD check: ${status#Status: }; testthat ${tests:-none}; TUTORIAL.md $($tut_ok && echo 'same as the vignette rendered now' || echo 'differs from the vignette rendered now')"
python3 - "$out" "$passed" "$detail" <<'PY'
import json, sys
json.dump({"passed": sys.argv[2] == "true", "detail": sys.argv[3]}, open(sys.argv[1], "w"), indent=1)
PY
cat "$out"
if ! $check_ok; then tail -40 check.log 2>/dev/null; tail -20 build.log; fi
$passed
