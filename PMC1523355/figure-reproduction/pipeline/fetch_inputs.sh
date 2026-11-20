#!/usr/bin/env bash
# Download the paper's figure and its article XML (Tables 1-5), and check their SHA-256.
#
#   fetch_inputs.sh DIR [--sources LOCAL_DIR]
#
# The paper is a pure simulation: it has no input data and no supplement. Source: PMC's open-access copy
# on AWS (scripted downloads allowed); fallback: the same bucket through its regional endpoint, and
# Europe PMC's full-text XML for the article. --sources reuses local copies (same file names).
set -euo pipefail
out="$1"; shift
src=""
if [[ "${1:-}" == "--sources" ]]; then src="$2"; shift 2; fi
mkdir -p "$out"
base="${PMC_BASE:-https://pmc-oa-opendata.s3.amazonaws.com/PMC1523355.1}"  # PMC_BASE: tests the fallback
mirror="https://pmc-oa-opendata.s3.us-east-1.amazonaws.com/PMC1523355.1"
declare -A SHA=(
  [1471-2288-6-18-1.jpg]=6fba733238396e8e437e6d826eb628e7f95a12b8d919a218571ab03189057de3
  [PMC1523355.1.xml]=b4bdb4c758dc7f6cd05699b661197acc5a3fef4e8a7d56da892e8b7e95471b3b
)
fallback() {
  local f="$1"
  if curl -fsSL --retry 3 -o "$out/$f" "$mirror/$f"; then return 0; fi
  if [[ "$f" == PMC1523355.1.xml ]]; then
    curl -fsSL --retry 3 -o "$out/$f" "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC1523355/fullTextXML"
    return $?
  fi
  return 1
}
for f in "${!SHA[@]}"; do
  if [[ -n "$src" && -f "$src/$f" ]]; then
    cp "$src/$f" "$out/$f"
  elif ! curl -fsSL --retry 3 -o "$out/$f" "$base/$f"; then
    echo "PMC AWS failed for $f; trying the fallback" >&2
    fallback "$f"
  fi
  got=$(sha256sum "$out/$f" | cut -d' ' -f1)
  if [[ "$got" != "${SHA[$f]}" ]]; then
    # Europe PMC's XML is another serialization of the same article: accept it when it is the paper,
    # since extract_published.py checks every printed value against the committed published_values.json.
    if [[ "$f" == PMC1523355.1.xml ]] && grep -q "Multivariable risk prediction can greatly enhance" "$out/$f"; then
      echo "note: $f is not the pinned copy (sha256 $got); its tables are checked by extract_published.py" >&2
    else
      echo "SHA-256 mismatch for $f: $got" >&2; exit 1
    fi
  fi
done
echo "fetched ${#SHA[@]} files into $out" >&2
