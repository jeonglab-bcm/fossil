#!/usr/bin/env bash
# The R steps of the package check (Paper2Repro, package-and-tutorial.md):
#   check_package.sh PACKAGE_DIR OUT.json [--write]
# 1. R CMD build (runs the vignette), 2. R CMD check --no-manual (installs, runs the tests, rebuilds
# the vignette; any ERROR or WARNING fails), 3. the tutorial rendered to TUTORIAL.md and compared
# with the committed package/tutorial/TUTORIAL.md (--write replaces it instead).
set -uo pipefail
pkg=$(cd "$1" && pwd)
out=$2
write=${3:-}
work=$(mktemp -d)
export LANG=C.UTF-8 LC_ALL=C.UTF-8
cd "$work"
ok=true
R CMD build "$pkg" > build.log 2>&1 || ok=false
tarball=$(ls multds_*.tar.gz 2>/dev/null | head -1)
status="not run"
if [[ -n "$tarball" ]]; then
  R CMD check --no-manual "$tarball" > check.log 2>&1 || ok=false
  status=$(grep -E "^Status:" check.log | head -1)
  grep -qE "^Status: OK" check.log || ok=false
fi
tests=$(grep -hoE "\[ FAIL [0-9]+ \| WARN [0-9]+ \| SKIP [0-9]+ \| PASS [0-9]+ \]" multds.Rcheck/tests/testthat.Rout 2>/dev/null | tail -1)
mkdir -p tut lib
[[ -n "$tarball" ]] && R CMD INSTALL -l lib "$tarball" > install.log 2>&1 || ok=false
cp -r "$pkg/vignettes/." tut/
R_LIBS="$work/lib" Rscript -e "rmarkdown::render('tut/tutorial.Rmd', output_format = rmarkdown::github_document(html_preview = FALSE), output_file = 'TUTORIAL.md', output_dir = 'tut/out', quiet = TRUE)" > render.log 2>&1 || ok=false
same=false
if [[ ! -f tut/out/TUTORIAL.md ]]; then
  same=false
elif [[ "$write" == "--write" ]]; then
  mkdir -p "$pkg/tutorial" && cp tut/out/TUTORIAL.md "$pkg/tutorial/TUTORIAL.md"
  rm -rf "$pkg/tutorial/TUTORIAL_files"; [[ -d tut/out/TUTORIAL_files ]] && cp -r tut/out/TUTORIAL_files "$pkg/tutorial/"
  same=true
elif cmp -s tut/out/TUTORIAL.md "$pkg/tutorial/TUTORIAL.md"; then
  same=true
fi
[[ "$same" == true ]] || ok=false
detail="R CMD check: ${status#Status: }; tests ${tests:-not found}; tutorial rendered from the vignette $( [[ $same == true ]] && echo 'equals' || echo 'DIFFERS from' ) the committed TUTORIAL.md"
python3 - "$out" "$ok" "$detail" <<'PY'
import json, sys
json.dump({"passed": sys.argv[2] == "true", "detail": sys.argv[3]}, open(sys.argv[1], "w"), indent=1)
PY
echo "$detail"
for f in build.log check.log install.log render.log; do [[ "$ok" == true ]] || { echo "== $f"; tail -30 "$f"; }; done
rm -rf "$work"
