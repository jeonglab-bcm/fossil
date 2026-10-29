#!/bin/bash
# Fetch Code S1 (pcbi.1003686.s001.zip: the authors' MATLAB code, data and saved results) and
# unpack it as ./sources/ODEMM_implementation_v01. PLOS refuses scripted downloads, so the file
# comes from Europe PMC's supplementary-file bundle. Usage: fetch_inputs.sh [LOCAL_DIR]
# LOCAL_DIR may already hold pcbi.1003686.s001.zip.
set -euo pipefail
SHA=9af34704abfbae91cd10f26d24dd24eb60b5ec706c34115a9edbd11a41dab57d
mkdir -p sources
if [ -n "${1:-}" ] && [ -f "$1/pcbi.1003686.s001.zip" ]; then
  cp "$1/pcbi.1003686.s001.zip" sources/
else
  curl -fsSL -o bundle.zip "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4081021/supplementaryFiles"
  unzip -o -q bundle.zip pcbi.1003686.s001.zip -d sources
  rm bundle.zip
fi
echo "$SHA  sources/pcbi.1003686.s001.zip" | shasum -a 256 -c -
unzip -o -q sources/pcbi.1003686.s001.zip -x '__MACOSX/*' '*.DS_Store' -d sources
rm sources/pcbi.1003686.s001.zip
