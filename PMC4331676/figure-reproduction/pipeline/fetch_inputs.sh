#!/usr/bin/env bash
# Download the inputs of the PMC4331676 reproduction into DIR and check their SHA-256.
#   fetch_inputs.sh DIR [SOURCES]
# SOURCES: a folder with local copies (same file names); used instead of downloading when present.
set -euo pipefail
DIR=${1:-downloads}
SOURCES=${2:-}
mkdir -p "$DIR"

fetch() {  # name sha256 url [fallback-url]
  local name=$1 sha=$2 url=$3 alt=${4:-}
  if [ -n "$SOURCES" ] && [ -f "$SOURCES/$name" ]; then
    cp "$SOURCES/$name" "$DIR/$name"
  else
    curl -sSfL --retry 3 --retry-delay 5 -o "$DIR/$name" "$url" ||
      { [ -n "$alt" ] && curl -sSfL --retry 3 --retry-delay 5 -o "$DIR/$name" "$alt"; }
  fi
  echo "$sha  $DIR/$name" | sha256sum -c --quiet - || { echo "checksum failed: $name" >&2; exit 1; }
}

PMC=https://pmc-oa-opendata.s3.amazonaws.com
# Additional file 1 of the paper (CC BY 4.0): the benchmark, 525 + 550 PDB chains with sequences.
fetch 1752-0509-9-S1-S10-S1.pdf a4df5d045e285452cf80045b58092b3b0468d5818f4f6243ab19361b2acb22da \
  $PMC/PMC4331676.1/1752-0509-9-S1-S10-S1.pdf
# Lou et al. 2014 (PLoS One, CC BY): Dataset S2 (PDB186) and Information S1 (predictions of six tools).
fetch pone.0086703.s002.txt 797f36f6a023e48bbdbafbef449db1a560f9bd0ff263778a2a63ab9d35f03ab8 \
  $PMC/PMC3901691.1/pone.0086703.s002.txt \
  'https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0086703.s002'
fetch pone.0086703.s003.txt 405ca0a4ebd6d733c5c68c3e523fd9ae8c4825c106126fead99fd4406c34397f \
  $PMC/PMC3901691.1/pone.0086703.s003.txt \
  'https://journals.plos.org/plosone/article/file?type=supplementary&id=10.1371/journal.pone.0086703.s003'
# The published figures (CC BY 4.0), for comparison.
fetch 1752-0509-9-S1-S10-1.jpg d11602d7fc2c2b94f9ff153b2bddca8b4a77731a8be4f2578c38966db46b23e6 $PMC/PMC4331676.1/1752-0509-9-S1-S10-1.jpg
fetch 1752-0509-9-S1-S10-2.jpg befbcffe40c00a24058bcd169405433f4f77a37d4a1c4e3a846a6839f4015a4c $PMC/PMC4331676.1/1752-0509-9-S1-S10-2.jpg
fetch 1752-0509-9-S1-S10-3.jpg e3bc7781d5507a87d68e48b6581c3935b63dfed753456e7cf21c69a44db4ad13 $PMC/PMC4331676.1/1752-0509-9-S1-S10-3.jpg
fetch 1752-0509-9-S1-S10-4.jpg 105dfacae1dc38dbcdfd4a24502a2d24c487f52fb8191785544ed5cb7a729c03 $PMC/PMC4331676.1/1752-0509-9-S1-S10-4.jpg
fetch 1752-0509-9-S1-S10-5.jpg 9fdf001e63354d4f5298b4f76e4ef6aaceaaa39da6eac52f63d1ba1bdd6d8299 $PMC/PMC4331676.1/1752-0509-9-S1-S10-5.jpg
fetch 1752-0509-9-S1-S10-6.jpg 83609201da11ddac10dc0de3e1e3104f6a5ed166d117f82f30e2478fcedff022 $PMC/PMC4331676.1/1752-0509-9-S1-S10-6.jpg
# 1AKH (MATa1/MATalpha2 homeodomains on DNA), for Fig. 2C.
fetch 1AKH.cif caf4ef567e1c06e1f84da497c139fa7ae4bb86e84949f3b18998c14140d74e1d https://files.rcsb.org/download/1AKH.cif
echo "inputs ok"
