#!/usr/bin/env bash
# Check the R package as the skill's R steps say: R CMD build (runs the vignette), R CMD check
# --no-manual in a fresh library, and render the tutorial to TUTORIAL.md and compare it with the
# committed one. Writes OUT_JSON with passed and a detail line.
#
# usage: check_package.sh PACKAGE_DIR OUT_JSON   (WRITE_TUTORIAL=1: save the rendered tutorial first)
set -uo pipefail
pkg=$(cd "$1" && pwd)
out=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
work=$(mktemp -d)
lib="$work/lib"
mkdir -p "$lib"
export R_LIBS_USER="$lib"
cd "$work"
ok=true
R CMD build "$pkg" > build.log 2>&1 || ok=false
tarball=$(ls epiforest_*.tar.gz 2>/dev/null | head -1)
status="not run"
tests="not run"
if $ok && [[ -n "$tarball" ]]; then
  _R_CHECK_FORCE_SUGGESTS_=false R CMD check --no-manual "$tarball" > check.log 2>&1 || ok=false
  status=$(grep -E "^Status:" check.log | tail -1)
  grep -qE "^Status: (OK|[0-9]+ NOTEs?)$" check.log || ok=false
  tests=$(grep -cE "^test_that\(" "$pkg/tests/testthat/"*.R)
fi
# the tutorial, rendered from the vignette, must equal the committed TUTORIAL.md
R CMD INSTALL --no-docs -l "$lib" "$pkg" > install.log 2>&1 || ok=false
mkdir -p tut
# render a copy next to its output, so the figure paths in TUTORIAL.md are relative
cp "$pkg/vignettes/tutorial.Rmd" tut/TUTORIAL.Rmd
(cd tut && Rscript -e "rmarkdown::render('TUTORIAL.Rmd', output_format = rmarkdown::github_document(html_preview = FALSE), output_file = 'TUTORIAL.md')") > render.log 2>&1 || ok=false
if [[ "${WRITE_TUTORIAL:-}" == 1 ]]; then
  rm -rf "$pkg/tutorial" && mkdir -p "$pkg/tutorial" && cp -r tut/TUTORIAL.md tut/TUTORIAL_files "$pkg/tutorial/"
fi
same_tutorial=false
if [[ -f tut/TUTORIAL.md ]] && diff -q tut/TUTORIAL.md "$pkg/tutorial/TUTORIAL.md" > /dev/null 2>&1; then
  same_tutorial=true
else
  ok=false
fi
detail="R CMD check: ${status:-no status}; ${tests} testthat blocks; vignette rebuilt; TUTORIAL.md rendered from it $( $same_tutorial && echo 'is the committed one' || echo 'differs from the committed one')"
python3 -c "import json,sys; json.dump({'passed': sys.argv[1] == 'true', 'detail': sys.argv[2]}, open(sys.argv[3], 'w'), indent=1)" "$ok" "$detail" "$out"
cat "$out"
for f in build.log check.log render.log; do [[ -f $f ]] && { echo "== $f"; tail -5 $f; }; done
$ok
