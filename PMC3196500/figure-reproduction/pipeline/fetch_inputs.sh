#!/usr/bin/env bash
# Download the paper's figure files, Tables S3 and S4 and the article XML, and check their SHA-256.
#
#   fetch_inputs.sh DIR [--sources LOCAL_DIR]
#
# Source: PMC's open-access copy on AWS (scripted downloads allowed). Fallback: Europe PMC's zip of the
# supplementary files and its full-text XML. --sources reuses local copies (same file names).
# Fig. 2 has two pinned copies: Europe PMC's zip holds the 996 x 1009 original, AWS a smaller one; the
# comparison uses the committed PNG of the original (published/), and verify_published.py checks it.
set -euo pipefail
out="$1"; shift
src=""
if [[ "${1:-}" == "--sources" ]]; then src="$2"; shift 2; fi
mkdir -p "$out"
base="${PMC_BASE:-https://pmc-oa-opendata.s3.amazonaws.com/PMC3196500.1}"  # PMC_BASE: tests the fallback
epmc="https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3196500"
declare -A SHA=(
  [pone.0025491.s001.tif]=b19d337290fefedf09fe88c93955ba688132d61eabe1c8f7649d6014b790ccf1
  [pone.0025491.s002.tif]=bf678e76464371c980ba41eb0c53861e6e1979bd59d5414ddca1e290745e19b6
  [pone.0025491.s003.tif]=32d6dc25831dbc1402a74e733309bb151baa4a99581e1328a5b8b06cb6cfcb66
  [pone.0025491.s004.tif]=20c755ab6c858a9a263ccfdd7408172c393d72d221890724a2263e4854833612
  [pone.0025491.s005.tif]=b19d337290fefedf09fe88c93955ba688132d61eabe1c8f7649d6014b790ccf1
  [pone.0025491.s006.tif]=bf678e76464371c980ba41eb0c53861e6e1979bd59d5414ddca1e290745e19b6
  [pone.0025491.s007.tif]=32d6dc25831dbc1402a74e733309bb151baa4a99581e1328a5b8b06cb6cfcb66
  [pone.0025491.s008.tif]=f1b794574e7f5acf10baa4f0bc767e63cbc7191f715ed0ac0eefb6d58d6824e3
  [pone.0025491.s009.tif]=2e8bb45283f290589ba13aa997819cf1e0ac57792eca8574e3ce89dfbcbc3405
  [pone.0025491.s010.tif]=b13a56090154fc90e3af47caef1ab9ad97c835c70564cd7726ab44bb46b78e37
  [pone.0025491.s011.tif]=eb8001d5c29020b928eb9b4a6aac08f95064b432d52656591b2231932b7b9815
  [pone.0025491.s012.tif]=5af238048f48e910e3c505621efc38d36f5f76c8fd3c0f18598261d8d88cdead
  [pone.0025491.s016.doc]=754ee755c3919a0334df8c15f2c7926245f43ee18c8e9907a896e0fb94c9705c
  [pone.0025491.s017.doc]=276270abaf7f5cefb0a43afb63dafdcf5ed7d33bd27218f5a2657cb8f7f8216c
  [pone.0025491.g002.jpg]="59bea4c56de9942658f9577a03fe55d0c0cf17e26611f4c766be72ab91822cd4 c46f35e07f6ac19b0ad9168207eb5269284772c768bd8205583f40a942020a2e"
  [PMC3196500.1.xml]=7197f717e07a8e72c2e6958b6f72c9784792e8801904c40e823feba0b59b5024
)
fallback() {
  local f="$1"
  if [[ "$f" == PMC3196500.1.xml ]]; then
    curl -fsSL --retry 3 -o "$out/$f" "$epmc/fullTextXML" || return 1
    return 0
  fi
  if [[ ! -f "$out/.epmc.zip" ]]; then
    curl -fsSL --retry 3 -o "$out/.epmc.zip" "$epmc/supplementaryFiles" || return 1
  fi
  python3 - "$out/.epmc.zip" "$f" "$out/$f" <<'PY'
import sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
name = next(n for n in z.namelist() if n.lower().endswith(sys.argv[2].lower()))
open(sys.argv[3], "wb").write(z.read(name))
PY
}
for f in "${!SHA[@]}"; do
  if [[ -n "$src" && -f "$src/$f" ]]; then
    cp "$src/$f" "$out/$f"
  elif [[ "$f" == pone.0025491.g002.jpg ]]; then
    # the original from Europe PMC first; AWS's smaller copy if Europe PMC fails
    fallback "$f" || curl -fsSL --retry 3 -o "$out/$f" "$base/$f"
  elif ! curl -fsSL --retry 3 -o "$out/$f" "$base/$f"; then
    echo "PMC AWS failed for $f; trying Europe PMC" >&2
    fallback "$f"
  fi
  got=$(sha256sum "$out/$f" | cut -d' ' -f1)
  ok=no
  for want in ${SHA[$f]}; do [[ "$got" == "$want" ]] && ok=yes; done
  if [[ "$ok" != yes ]]; then
    # Europe PMC's XML is another serialization of the same article: extract_published.py checks its tables.
    if [[ "$f" == PMC3196500.1.xml ]] && grep -q "The number of patients and events required" "$out/$f"; then
      echo "note: $f is not the pinned copy (sha256 $got)" >&2
    else
      echo "SHA-256 mismatch for $f: $got" >&2; exit 1
    fi
  fi
done
rm -f "$out/.epmc.zip"
echo "fetched ${#SHA[@]} files into $out" >&2
