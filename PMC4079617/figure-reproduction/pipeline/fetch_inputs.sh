#!/usr/bin/env bash
# Download the paper's inputs and check their SHA-256.
#
#   fetch_inputs.sh DIR [--sources LOCAL_DIR]
#
# Files (PMC's open-access copy on AWS, which allows scripted downloads):
#   PMC4079617.1.xml          the article: Tables 1-3 and the text
#   1471-2288-14-82-S1.pdf    Additional file 1: alpha0 and beta0 of the 24 scenarios
#   1471-2288-14-82-S2.pdf    Additional file 2: Tables A1-A3 (n = 500)
#   PMC4079617.1.pdf          the article PDF, which embeds Fig. 1 at 1949 x 1444 px (300 dpi); PMC's own figure
#                             file (1471-2288-14-82-1.jpg) is 600 x 444 px
# Fallback: Europe PMC (the full-text XML, and the supplements as one zip). The simulation needs no input data.
# --sources reuses local copies (same file names) instead of downloading.
set -euo pipefail
out="$1"; shift
src=""
if [[ "${1:-}" == "--sources" ]]; then src="$2"; shift 2; fi
mkdir -p "$out"
base="${PMC_BASE:-https://pmc-oa-opendata.s3.amazonaws.com/PMC4079617.1}"  # PMC_BASE: tests the fallback
declare -A SHA=(
  [PMC4079617.1.xml]=86fb4d9c2d90276d4d59e4d5e4b44e4937307501bf37c3d08966b104183ffc60
  [1471-2288-14-82-S1.pdf]=a173bfa2c69abc0f59807d0a8dd1adf32c6f0c91a901c9376259cff4e0986cab
  [1471-2288-14-82-S2.pdf]=7dbfdbafe41925eb8b1a9c8537efc93dcc6c2daf184b32a60c61b543ca17e916
  [PMC4079617.1.pdf]=7413d9f877173238ff007c939d826a638a7bb53d6c9fe5fa882dd485587fdae2
)
epmc="https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4079617"
for f in PMC4079617.1.xml 1471-2288-14-82-S1.pdf 1471-2288-14-82-S2.pdf PMC4079617.1.pdf; do
  if [[ -n "$src" && -f "$src/$f" ]]; then
    cp "$src/$f" "$out/$f"
  elif ! curl -fsSL --retry 3 -o "$out/$f" "$base/$f"; then
    echo "PMC AWS failed for $f; trying Europe PMC" >&2
    case "$f" in
      *.xml) curl -fsSL --retry 3 -o "$out/$f" "$epmc/fullTextXML" ;;
      *-S?.pdf) curl -fsSL --retry 3 -o "$out/supp.zip" "$epmc/supplementaryFiles" && unzip -o -j -q "$out/supp.zip" "$f" -d "$out" ;;
      *) echo "no fallback for $f" >&2; exit 1 ;;
    esac
  fi
  got=$(sha256sum "$out/$f" | cut -d' ' -f1)
  if [[ "$got" != "${SHA[$f]}" ]]; then
    if [[ "$f" == *.xml ]] && grep -q "robustness to outliers between robust poisson" "$out/$f"; then
      echo "note: $f is not the pinned copy (sha256 $got); its tables are checked against the committed values" >&2
    else
      echo "SHA-256 mismatch for $f: $got" >&2; exit 1
    fi
  fi
done
echo "fetched 4 files into $out" >&2
