#!/usr/bin/env bash
# The R steps of the package check (Paper2Repro package-and-tutorial.md, "Check an R package"):
# build (runs the vignette), R CMD check --no-manual in a fresh library, and render the tutorial
# to TUTORIAL.md, which must equal the committed one. Writes package.json (passed, detail).
#
#   check_r_package.sh PACKAGE_DIR OUT_JSON
set -uo pipefail
pkg=$(cd "$1" && pwd); out=$2
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
export LANG=C.UTF-8 LC_ALL=C.UTF-8 _R_CHECK_FORCE_SUGGESTS_=false
lib="$work/lib"; mkdir -p "$lib"
export R_LIBS_USER="$lib"
cp -r "$pkg" "$work/src"
ok=1; status=""; tests=""; tut=""
( cd "$work" && R CMD build src > build.log 2>&1 ) || ok=0
tarball=$(ls "$work"/pdscox_*.tar.gz 2>/dev/null | head -1)
if [ $ok = 1 ] && [ -n "$tarball" ]; then
  ( cd "$work" && R CMD check --no-manual "$tarball" > check.log 2>&1 ) || ok=0
  status=$(grep -E "^Status:" "$work/check.log" | tail -1)
  case "$status" in *ERROR*|*WARNING*) ok=0 ;; "") ok=0 ;; esac
  tests=$(grep -oE "\[ FAIL [0-9]+ \| WARN [0-9]+ \| SKIP [0-9]+ \| PASS [0-9]+ \]" "$work/pdscox.Rcheck/tests/testthat.Rout" 2>/dev/null | tail -1 \
    | sed -E 's/\[ FAIL ([0-9]+) \| WARN ([0-9]+) \| SKIP ([0-9]+) \| PASS ([0-9]+) \]/\4 passed, \1 failed, \3 skipped/')
else
  status="R CMD build failed"
fi
# Render the tutorial from the source package (installed into the fresh library) and compare.
R CMD INSTALL --library="$lib" "$tarball" > "$work/install.log" 2>&1 || ok=0
mkdir -p "$work/tut"
# Render inside the output folder, so the figure links in TUTORIAL.md are relative.
cp "$work/src/vignettes/tutorial.Rmd" "$work/tut/TUTORIAL.Rmd"
( cd "$work/tut" && Rscript -e 'rmarkdown::render("TUTORIAL.Rmd", output_format = rmarkdown::github_document(html_preview = FALSE), quiet = TRUE)' ) > "$work/render.log" 2>&1 || ok=0
rm -f "$work/tut/TUTORIAL.Rmd"
# TUTORIAL.md must equal the committed one line for line; its figures are compared by name only,
# since PNG bytes depend on the fonts and graphics libraries of the machine.
figs() { (cd "$1" && find . -name '*.png' | sort); }
if [ -f "$work/tut/TUTORIAL.md" ] && diff "$work/tut/TUTORIAL.md" "$pkg/tutorial/TUTORIAL.md" > "$work/tut.diff" 2>&1 \
   && [ "$(figs "$work/tut")" = "$(figs "$pkg/tutorial")" ]; then
  tut="tutorial rendering equals the committed TUTORIAL.md (figures by name)"
else
  first=$(grep -m1 -E '^[<>]' "$work/tut.diff" | cut -c1-120)
  tut="tutorial rendering differs from the committed TUTORIAL.md${first:+ (first difference: $first)}"; ok=0
  [ -n "${PACKAGE_WRITE:-}" ] && rm -rf "$pkg/tutorial" && cp -r "$work/tut" "$pkg/tutorial" && tut="$tut (written)"
fi
detail="R package pdscox: R CMD check ${status#Status: }; tests $tests; $tut"
python3 - "$out" "$ok" "$detail" <<'PY'
import json, sys
json.dump({"passed": sys.argv[2] == "1", "detail": sys.argv[3]}, open(sys.argv[1], "w"), indent=1)
PY
echo "$detail"
[ $ok = 1 ] || { tail -30 "$work/check.log" "$work/render.log" "$work/tut.diff" 2>/dev/null; }
exit 0
