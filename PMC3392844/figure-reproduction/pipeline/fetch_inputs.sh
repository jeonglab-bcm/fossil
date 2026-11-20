#!/usr/bin/env bash
# Download the inputs and check their SHA-256, then unpack Liu et al.'s training file.
#
#   fetch_inputs.sh DIR [--paper] [--sources LOCAL_DIR]
#
# Always: Zhang et al. 2015 (PMC4634905, BMC Bioinformatics, CC BY 4.0), Additional file 1, which holds
# Liu et al.'s processed training data as the authors sent it ("Liu's data orignally from authors.zip" ->
# merged_data/random_group_cv_data.indication: 832 drugs, every feature bit and the 5-fold assignment of
# each drug for each ADR). Source: PMC's open-access copy on AWS; fallback: Springer's static content.
# --paper: also the paper's PDF and XML (PMC AWS, no fallback), for extract_published.py (--extract).
# --sources reuses local copies (same file names) instead of downloading.
set -euo pipefail
out="$1"; shift
src=""; paper=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --sources) src="$2"; shift 2 ;;
    --paper) paper=1; shift ;;
    *) echo "unknown argument $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$out"
ZIP=12859_2015_774_MOESM1_ESM.zip
declare -A SHA=([$ZIP]=6733ca5650274a6ae987ef92eabc31a43b9ae196420ea73f8a4ff5bd2a6466bc)
declare -A URL=([$ZIP]="https://pmc-oa-opendata.s3.amazonaws.com/PMC4634905.1/$ZIP")
declare -A ALT=([$ZIP]="https://static-content.springer.com/esm/art%3A10.1186%2Fs12859-015-0774-y/MediaObjects/$ZIP")
if [[ $paper == 1 ]]; then
  SHA[PMC3392844.1.pdf]=7dc617e64af5ee3ae7c1e0c109ce553c5d64c92e0988f3f97200799c81a97cbc
  SHA[PMC3392844.1.xml]=7ada8cc2cbed085a46c37761b9ae5a998d667e8eef19dcef3576fcc7e968ad94
  URL[PMC3392844.1.pdf]="https://pmc-oa-opendata.s3.amazonaws.com/PMC3392844.1/PMC3392844.1.pdf"
  URL[PMC3392844.1.xml]="https://pmc-oa-opendata.s3.amazonaws.com/PMC3392844.1/PMC3392844.1.xml"
fi
for f in "${!SHA[@]}"; do
  if [[ -n "$src" && -f "$src/$f" ]]; then
    cp "$src/$f" "$out/$f"
  elif ! curl -fsSL --retry 3 -o "$out/$f" "${URL[$f]}"; then
    if [[ -n "${ALT[$f]:-}" ]]; then
      echo "PMC AWS failed for $f; trying ${ALT[$f]}" >&2
      curl -fsSL --retry 3 -o "$out/$f" "${ALT[$f]}"
    else
      echo "download failed: $f" >&2; exit 1
    fi
  fi
  got=$(sha256sum "$out/$f" | cut -d' ' -f1)
  if [[ "$got" != "${SHA[$f]}" ]]; then echo "SHA-256 mismatch for $f: $got" >&2; exit 1; fi
done
# Zip in a zip in a zip; take only the training file and the ADR list.
python3 - "$out/$ZIP" "$out" <<'PY'
import io, sys, zipfile, hashlib
z1 = zipfile.ZipFile(sys.argv[1])
z2 = zipfile.ZipFile(io.BytesIO(z1.read("source codes and datasets 2015-09-05.zip")))
inner = "source codes and datasets 2015-09-05/Liu dataset and experiments/Liu's dataset/Liu's data orignally from authors.zip"
z3 = zipfile.ZipFile(io.BytesIO(z2.read(inner)))
want = {"merged_data/random_group_cv_data.indication": "a95d1113e7e6c0f426befa4e9b9ad9e8c9b5f69be7907ed47b72b78e36a0d9b8",
        "merged_data/ade_feature_list": "5b75829e6e919510588b3469573b118748082eaa7cce76c53e162c91e24bf2f5"}
for name, sha in want.items():
    data = z3.read(name)
    if hashlib.sha256(data).hexdigest() != sha:
        sys.exit(f"SHA-256 mismatch for {name}")
    open(f"{sys.argv[2]}/{name.split('/')[-1]}", "wb").write(data)
# The first edition of SIDER (2009-11-20), which Liu et al. compiled their labels from: the drug-side effect pairs.
sider = "source codes and datasets 2015-09-05/Liu dataset and experiments/Liu's dataset/raw data for the first edition of SIDER database.zip"
z4 = zipfile.ZipFile(io.BytesIO(z2.read(sider)))
data = z4.read("2315_1_data_set_32910_ktf1bt 2/costart_adverse_effects.tsv")
if hashlib.sha256(data).hexdigest() != "f438cd1890483760b28d8554d24feeda982d05ddafbd6598960a7ac733a566e3":
    sys.exit("SHA-256 mismatch for costart_adverse_effects.tsv")
open(f"{sys.argv[2]}/sider1_costart_adverse_effects.tsv", "wb").write(data)
PY
echo "fetched ${#SHA[@]} files into $out" >&2
