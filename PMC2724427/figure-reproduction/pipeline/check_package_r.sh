#!/usr/bin/env bash
# Check the R package logitbias, as package-and-tutorial.md of Paper2Repro asks for an R package:
#   check_package_r.sh PKG_DIR OUT_JSON
# 1. R CMD build (builds the tarball and runs the vignette);
# 2. R CMD check --no-manual (installs it, runs the tests, rebuilds the vignette): any ERROR or
#    WARNING fails;
# 3. renders the vignette to TUTORIAL.md in a copy and compares it with the committed
#    tutorial/TUTORIAL.md (text) and the number of its figures. WRITE_TUTORIAL=1 first writes a
#    fresh rendering into the package's tutorial/ (after a change to the method or the tutorial).
# Writes {"passed": ..., "detail": ...} to OUT_JSON.
set -uo pipefail
pkg="$(cd "$1" && pwd)"; out="$2"
work="$(mktemp -d)"
fail=""
cp -r "$pkg" "$work/src"
( cd "$work" && R CMD build src > build.log 2>&1 ) || fail="R CMD build failed"
tarball=$(ls "$work"/logitbias_*.tar.gz 2>/dev/null | head -1)
status="not run"; tests="tests not run"
if [ -z "$fail" ]; then
  ( cd "$work" && LANG=en_US.UTF-8 R CMD check --no-manual "$tarball" > check.log 2>&1 ) || fail="R CMD check failed"
  status=$(grep -E "^Status:" "$work/check.log" | tail -1)
  case "$status" in *WARNING*|*ERROR*) fail="R CMD check: $status" ;; esac
  tests=$(grep -oE "\[ FAIL [0-9]+ \| WARN [0-9]+ \| SKIP [0-9]+ \| PASS [0-9]+ \]" "$work/logitbias.Rcheck/tests/testthat.Rout" | tail -1)
  tests=$(echo "$tests" | sed -E 's/\[ FAIL ([0-9]+) \| WARN ([0-9]+) \| SKIP ([0-9]+) \| PASS ([0-9]+) \]/\4 passed, \1 failed, \2 warnings, \3 skipped/')
fi
R CMD INSTALL "$work/src" > "$work/install.log" 2>&1 || fail="${fail:-install failed}"
render() {  # render the vignette into DIR/TUTORIAL.md with relative figure paths
  mkdir -p "$1" && cp "$work/src/vignettes/tutorial.Rmd" "$1/TUTORIAL.Rmd"
  ( cd "$1" && Rscript -e "rmarkdown::render('TUTORIAL.Rmd', output_format = rmarkdown::github_document(html_preview = FALSE), quiet = TRUE)" ) > "$work/render.log" 2>&1
  local rc=$?; rm -f "$1/TUTORIAL.Rmd"; return $rc
}
if [ "${WRITE_TUTORIAL:-0}" = 1 ]; then rm -rf "$pkg/tutorial" && render "$pkg/tutorial"; fi
render "$work/tut" || fail="${fail:-tutorial did not render}"
same="differs"
if cmp -s "$work/tut/TUTORIAL.md" "$pkg/tutorial/TUTORIAL.md"; then same="unchanged"; else fail="${fail:-TUTORIAL.md differs from a fresh rendering}"; diff "$work/tut/TUTORIAL.md" "$pkg/tutorial/TUTORIAL.md" | head -20 >&2; fi
nf_new=$(find "$work/tut" -name '*.png' | wc -l); nf_old=$(find "$pkg/tutorial" -name '*.png' | wc -l)
[ "$nf_new" = "$nf_old" ] || fail="${fail:-tutorial has $nf_new figures, committed $nf_old}"
version=$(grep -E "^Version:" "$pkg/DESCRIPTION" | awk '{print $2}')
passed=$([ -z "$fail" ] && echo true || echo false)
detail="logitbias $version: R CMD check $status; tests $tests; tutorial rendered, TUTORIAL.md $same, $nf_new figures${fail:+; FAILED: $fail}"
printf '{"passed": %s, "detail": "%s"}\n' "$passed" "$(echo "$detail" | sed 's/"/\\"/g')" > "$out"
cat "$out"
