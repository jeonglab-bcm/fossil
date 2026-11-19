#!/usr/bin/env bash
# Download PubMed baseline files and check each one's SHA-256 against the committed manifest.
# Usage: fetch_inputs.sh DIR NNNN,NNNN,... [--sources DIR]
#   --sources DIR: copy local files instead of downloading (still checked).
# The full run streams all 1,334 files itself (extract_medline.py) and records their SHA-256.
set -euo pipefail
out=$1; files=$2; shift 2
src=""
if [[ "${1:-}" == "--sources" ]]; then src=$2; fi
here=$(cd "$(dirname "$0")" && pwd)
manifest="$here/../output/baseline_manifest.json"
base="https://ftp.ncbi.nlm.nih.gov/pubmed/baseline"
mkdir -p "$out"
for n in ${files//,/ }; do
  f="pubmed26n${n}.xml.gz"
  want=$(python3 -c "import json,sys; m=json.load(open(sys.argv[1])); print(next(x['sha256'] for x in m['files'] if x['file']==sys.argv[2]))" "$manifest" "$f")
  if [[ -n "$src" && -f "$src/$f" ]]; then
    cp "$src/$f" "$out/$f"
  else
    curl -sS --retry 5 --retry-all-errors -o "$out/$f" "$base/$f"
  fi
  got=$(sha256sum "$out/$f" | cut -d' ' -f1)
  if [[ "$got" != "$want" ]]; then
    echo "SHA-256 mismatch for $f: $got, manifest $want" >&2
    exit 1
  fi
  echo "$f ok"
done
