#!/bin/bash
# The R package checks (Paper2Repro package-and-tutorial.md, "Check an R package"):
#   1. R CMD build: builds the tarball and runs the vignette
#   2. R CMD check --no-manual: installs it, runs the tests, rebuilds the vignette (ERROR or WARNING fails)
#   3. knitr renders the tutorial to TUTORIAL.md, which must equal the committed one
# Usage: check_package.sh <package dir> <out package.json> [--write]   (--write updates the committed tutorial)
set -uo pipefail
pkg=$(cd "$1" && pwd); out=$2; write=${3:-}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
cp -r "$pkg" "$work/src"
cd "$work"
ok=true; detail=""
R CMD build --no-manual src > build.log 2>&1 || { ok=false; detail="R CMD build failed; "; tail -20 build.log; }
tgz=$(ls filterfdr_*.tar.gz 2>/dev/null | head -1)
status="not run"; tests="?"
if [ -n "$tgz" ]; then
  _R_CHECK_FORCE_SUGGESTS_=false R CMD check --no-manual "$tgz" > check.log 2>&1
  status=$(grep -E '^Status:' check.log | sed 's/^Status: //')
  tests=$(grep -ohE '\[ FAIL [0-9]+ \| WARN [0-9]+ \| SKIP [0-9]+ \| PASS [0-9]+ \]' filterfdr.Rcheck/tests/testthat.Rout* 2>/dev/null | tail -1)
  if grep -qE '^Status: .*(ERROR|WARNING)' check.log || ! grep -q '^Status:' check.log; then ok=false; tail -40 check.log; fi
fi
mkdir -p tut lib && cp -r src/vignettes/tutorial.Rmd tut/
# render against the package just built, in a library of its own; a chunk error fails the render
[ -n "$tgz" ] && R CMD INSTALL --library=lib "$tgz" > install.log 2>&1
(cd tut && R_LIBS="$work/lib${R_LIBS:+:$R_LIBS}" Rscript -e 'knitr::opts_chunk$set(fig.path = "TUTORIAL_files/", error = FALSE); knitr::knit("tutorial.Rmd", "TUTORIAL.md", quiet = TRUE)' > ../knit.log 2>&1) \
  || { ok=false; detail="${detail}tutorial render failed; "; cat knit.log; }
tut="same as committed"
if [ "$write" = "--write" ]; then
  rm -rf "$pkg/tutorial/TUTORIAL_files"; cp tut/TUTORIAL.md "$pkg/tutorial/"; cp -r tut/TUTORIAL_files "$pkg/tutorial/" 2>/dev/null
  tut="written"
elif ! diff -q tut/TUTORIAL.md "$pkg/tutorial/TUTORIAL.md" > /dev/null; then
  ok=false; tut="differs from the committed tutorial/TUTORIAL.md"; diff tut/TUTORIAL.md "$pkg/tutorial/TUTORIAL.md" | head -20
fi
rver=$(Rscript -e 'cat(as.character(getRversion()))')
detail="${detail}R CMD check (R ${rver}): ${status}; tests ${tests}; tutorial ${tut}"
printf '{"passed": %s, "detail": "%s"}\n' "$ok" "$detail" > "$OLDPWD/$out" 2>/dev/null || printf '{"passed": %s, "detail": "%s"}\n' "$ok" "$detail" > "$out"
echo "$detail"
$ok
