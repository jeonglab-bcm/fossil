#!/usr/bin/env bash
# Download the paper's open-access PDF (its figures are vector drawings, read by
# extract_published.py) and the eight figure JPEGs from PMC's open-access bucket, and check SHA-256.
#   fetch_inputs.sh DIR [--sources LOCAL_DIR]
# The data (TH.data::GBSG2) and the imputation packages come from R, not from here.
set -euo pipefail
out="${1:-downloads}"; shift || true
src=""
if [[ "${1:-}" == "--sources" ]]; then src="$2"; fi
mkdir -p "$out"
primary="https://pmc-oa-opendata.s3.amazonaws.com/PMC2824146.1"
mirror="https://pmc-oa-opendata.s3.us-east-1.amazonaws.com/PMC2824146.1"
while read -r sum name; do
  if [[ -n "$src" && -f "$src/$name" ]]; then
    cp "$src/$name" "$out/$name"
  else
    curl -sSfL --retry 3 --retry-delay 5 -o "$out/$name" "$primary/$name" \
      || curl -sSfL --retry 3 --retry-delay 5 -o "$out/$name" "$mirror/$name"
  fi
  echo "$sum  $out/$name" | sha256sum -c --quiet -
done <<'LIST'
aa1cd04c309d51a853850000fce89a7ccfc748275a6922e694bc93abf1f49095 PMC2824146.1.pdf
37d0e0560f4fe6d2b83676252885d6b0f96a20cb46b780a51f095ea31ba1d17d 1471-2288-10-7-1.jpg
e34022298652cc0d5225d6ec7afd853ed5d30f4f29f0c3e0061c2b228b77b69d 1471-2288-10-7-2.jpg
4550250dfdf82ae8c38a725d9cbd1d9c909a594d9c86cbc727540003e02227bf 1471-2288-10-7-3.jpg
fe172381151af367ba89fef443f0f1d1498c3240ec8572a72d8152fd0b40963a 1471-2288-10-7-4.jpg
582cc7d63eca2358c2c0c8cd886df545e893eddef245b0498cd52e11e79bac0f 1471-2288-10-7-5.jpg
f605603a9605b454c746f4ec6654b43bfe235c1a584f7b0f3911105c9e52cbf1 1471-2288-10-7-6.jpg
7c521409393c5808b2d6d68b17c15f872dd3a98f40eb116467ee71a0ee836757 1471-2288-10-7-7.jpg
cded9485c362a0e544f874bcf1e228ea136ce12cec52699aa8dd2f6d55b890dc 1471-2288-10-7-8.jpg
LIST
echo "inputs ok: $out"
