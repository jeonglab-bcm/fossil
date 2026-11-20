#!/usr/bin/env bash
# Download the article XML (Tables 1-8 and the text) and check its SHA-256.
#
#   fetch_inputs.sh DIR [--sources LOCAL_DIR]
#
# Source: PMC's open-access copy on AWS (scripted downloads allowed); fallback: Europe PMC's full-text XML,
# a different serialization of the same article (checked by its title; the tables are then checked by
# extract_published.py --check). The simulation itself needs no input data.
# --sources reuses a local copy (same file name) instead of downloading.
set -euo pipefail
out="$1"; shift
src=""
if [[ "${1:-}" == "--sources" ]]; then src="$2"; shift 2; fi
mkdir -p "$out"
base="${PMC_BASE:-https://pmc-oa-opendata.s3.amazonaws.com/PMC2430201.1}"  # PMC_BASE: tests the fallback
f=PMC2430201.1.xml
sha=f92a433a350173d068807976b93d6ce8fa1cda0fce5fd0898a2b666352dd2fc0
if [[ -n "$src" && -f "$src/$f" ]]; then
  cp "$src/$f" "$out/$f"
elif ! curl -fsSL --retry 3 -o "$out/$f" "$base/$f"; then
  echo "PMC AWS failed for $f; trying Europe PMC" >&2
  curl -fsSL --retry 3 -o "$out/$f" "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2430201/fullTextXML"
fi
got=$(sha256sum "$out/$f" | cut -d' ' -f1)
if [[ "$got" != "$sha" ]]; then
  if grep -q "ratio of means method as an alternative" "$out/$f"; then
    echo "note: $f is not the pinned copy (sha256 $got); its tables are checked by extract_published.py --check" >&2
  else
    echo "SHA-256 mismatch for $f: $got" >&2; exit 1
  fi
fi
echo "fetched $f into $out" >&2
