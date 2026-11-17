#!/usr/bin/env bash
# Download the paper's figures, its article XML and Additional file 1, and check their SHA-256.
#
#   fetch_inputs.sh DIR [--sources LOCAL_DIR]
#
# Source: PMC's open-access copy on AWS (scripted downloads allowed); fallback: Europe PMC's
# supplementary-files zip (figures and Additional file 1) and its full-text XML.
# --sources reuses local copies (same file names) instead of downloading.
set -euo pipefail
out="$1"; shift
src=""
if [[ "${1:-}" == "--sources" ]]; then src="$2"; shift 2; fi
mkdir -p "$out"
base="${PMC_BASE:-https://pmc-oa-opendata.s3.amazonaws.com/PMC3022898.1}"  # PMC_BASE: tests the fallback
declare -A SHA=(
  [1471-2288-11-1-1.jpg]=4ad3c91768d0c05a57745e6dd21e00562a365fe5c7b3f4fd5b9380cde016392e
  [1471-2288-11-1-2.jpg]=d63e7540c3cfbcc73884ab057ee1a507fd81ff54485144f294a23593778093dc
  [1471-2288-11-1-3.jpg]=706c2933bc936b8ce3a957d4fa190d29c5a1c6da32bb4ce83d70e1903827751a
  [1471-2288-11-1-4.jpg]=8da79b4d2b6f3eb16d02800a3b6001ee073a01e26a2736ea783983135ea2b203
  [1471-2288-11-1-S1.DOC]=f4bd31f1898812be015cc0af2f1d628b4dc9d1b16d73c0deeac9524a32263433
  [PMC3022898.1.xml]=040b539a660c1299a4db574e774a5e144a08df3fb4d01937fe0ce65a5e72078b
)
fallback() {  # Europe PMC: one zip of all supplementary files and figures; the article XML
  local f="$1"
  if [[ "$f" == PMC3022898.1.xml ]]; then
    curl -fsSL --retry 3 -o "$out/$f" "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3022898/fullTextXML" || return 1
    return 0
  fi
  if [[ ! -f "$out/.epmc.zip" ]]; then
    curl -fsSL --retry 3 -o "$out/.epmc.zip" "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3022898/supplementaryFiles" || return 1
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
  elif ! curl -fsSL --retry 3 -o "$out/$f" "$base/$f"; then
    echo "PMC AWS failed for $f; trying Europe PMC" >&2
    fallback "$f"
  fi
  got=$(sha256sum "$out/$f" | cut -d' ' -f1)
  # Europe PMC's XML is a different serialization of the same article; only the AWS copy is pinned.
  if [[ "$got" != "${SHA[$f]}" ]]; then
    if [[ "$f" == PMC3022898.1.xml ]] && grep -q "Evaluation of exposure-specific risks" "$out/$f"; then
      echo "note: $f is not the pinned copy (sha256 $got); tables are checked by extract_published.py" >&2
    else
      echo "SHA-256 mismatch for $f: $got" >&2; exit 1
    fi
  fi
done
rm -f "$out/.epmc.zip"
echo "fetched ${#SHA[@]} files into $out" >&2
