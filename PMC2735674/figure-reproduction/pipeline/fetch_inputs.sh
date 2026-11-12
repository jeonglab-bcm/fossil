#!/usr/bin/env bash
# Download every input of the PMC2735674 reproduction into a folder and check its SHA-256.
#
#   fetch_inputs.sh [DIR]            download into DIR (default: inputs)
#   fetch_inputs.sh DIR --sources S  copy from a local folder S instead of downloading
#
# Two sources:
#   - the twelve benchmark files of Yamanishi et al. (2008), from the Kyoto supplement page. The
#     paper works with this exact dataset (its Section 2.1), and the page says it is not updated.
#   - the article PDF from the PMC open-access mirror on AWS. Figure 1 is vector art in that PDF,
#     so the pipeline reads the published precision-recall curves out of it. The PDF itself is not
#     redistributed: it stays in sources/ and .gitignore keeps it out of the repository.
set -euo pipefail

DIR="${1:-inputs}"
SOURCES=""
if [ "${2:-}" = "--sources" ]; then SOURCES="${3:?--sources needs a folder}"; fi

KYOTO="http://web.kuicr.kyoto-u.ac.jp/supp/yoshi/drugtarget"
PMC="https://pmc-oa-opendata.s3.amazonaws.com/PMC2735674.1"

mkdir -p "$DIR"
cd "$DIR"

cat > checksums.sha256 <<'EOF'
bf73f8f0c1a71f9fe92d1e0d8a1065a1122b383532cd47fc73df1cb0d9ba6c10  e_admat_dgc.txt
28105b9570c91b4eac688eaf92db2e4aacb7117bc8665cab527fc5d45cd83606  e_simmat_dc.txt
14816c2bba2193d62f52ab53bd51fe9a490b28e98cf33df392a5da2bf24e5607  e_simmat_dg.txt
ac9df3498bc12af5174503e5f1e09ce26a6d78d753861a5eca55425f9f9ae2c9  ic_admat_dgc.txt
c1078ca88528d75ddb43d4ed2559391d7d8f5375ec572e6e9112e519d9cdbbf9  ic_simmat_dc.txt
e15626145623124ad42a45412c544d5fed5e079003727df784d29ed3ca72efef  ic_simmat_dg.txt
49b2a8a0139dac3116399618bfefc9d1afcc276ce31b7de4e241d1b6e62ef8ab  gpcr_admat_dgc.txt
ba9c1cf096f0f688d1341fec22ebdecb63162005394d3b5ec3e2f2ef3fd40df9  gpcr_simmat_dc.txt
c58c4311d2086a6914208ed0914598528ce54ade88eb52b0f737eedcaf5001e4  gpcr_simmat_dg.txt
74256ec88b415dbdb93735e93797955e82587f3154988e99787a4e604111963b  nr_admat_dgc.txt
f80e101f284934b85c5dc7601ecaca2cc86c62a946141b2587f3ac8482c9a7c1  nr_simmat_dc.txt
5bf651f310b037320fe5d8aa61dfa15e0d8af4b0fd50c3969201085e64b631e1  nr_simmat_dg.txt
22780b068eb828fe17f447a8ebb71b5ab3c3d0ef3f115163e584575e926d99df  bind_orfhsa_drug_nr.txt
b2c81d3fade1defa1cbeff55c819155ab211370227a58380a28f70f7313a93d5  PMC2735674.1.pdf
EOF

# The Kyoto page is the only place that serves the benchmark files. Every one of them is also in
# the Wayback Machine, whose `id_` captures are byte for byte the original, so a capture is the
# fallback when the page does not answer. The checksum check at the end covers both routes.
wayback() {  # wayback <original url> <file>
  local stamp
  stamp=$(curl -fsS --retry 2 --max-time 60 \
    "https://web.archive.org/cdx/search/cdx?url=${1#http://}&output=txt&filter=statuscode:200&limit=1" \
    | awk '{print $2}')
  [ -n "$stamp" ] || return 1
  curl -fsSL --retry 2 --max-time 120 -o "$2" "https://web.archive.org/web/${stamp}id_/$1"
}

get() {  # get <url> <file>
  if [ -n "$SOURCES" ]; then
    local found
    found=$(find "$SOURCES" -name "$2" -print -quit)
    [ -n "$found" ] || { echo "not in $SOURCES: $2" >&2; exit 1; }
    cp "$found" "$2"
    return
  fi
  if curl -fsSL --retry 3 --retry-delay 5 --max-time 300 -o "$2" "$1"; then
    return
  fi
  echo "falling back to the Wayback Machine for $2" >&2
  wayback "$1" "$2"
}

for set in e ic gpcr nr; do
  for kind in admat_dgc simmat_dc simmat_dg; do
    get "$KYOTO/${set}_${kind}.txt" "${set}_${kind}.txt"
  done
done
get "$KYOTO/bind_orfhsa_drug_nr.txt" bind_orfhsa_drug_nr.txt
get "$PMC/PMC2735674.1.pdf" PMC2735674.1.pdf

sha256sum -c checksums.sha256
echo "inputs ready in $(pwd)"
