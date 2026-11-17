#!/usr/bin/env bash
# Download every input of the PMC3098087 reproduction and check its SHA-256.
#   fetch_inputs.sh DIR [--sources LOCAL_DIR]
# - The paper (PDF, vector figures), its six figure files and Additional files 1-14, from PMC's
#   open-access copy on AWS (fallback: Europe PMC's zip of the supplementary files).
# - The Sotiriou et al. (2003) breast cancer data, BRB-ArrayTools project, from the NCI BRB data
#   archive (fallback: the Wayback Machine's capture of the same file).
# - sma 0.5.15 from the CRAN archive, for the port check of DLDA and DQDA (fallback: a CRAN mirror).
# With --sources, files already in LOCAL_DIR (any depth) are copied instead of downloaded.
set -euo pipefail
dir=${1:?usage: fetch_inputs.sh DIR [--sources LOCAL_DIR]}
src=""
if [[ "${2:-}" == "--sources" ]]; then src=${3:?}; fi
mkdir -p "$dir"
cd "$dir"
S3=https://pmc-oa-opendata.s3.amazonaws.com/PMC3098087.1
while read -r sha name url fallback; do
  [[ -z "$sha" || "$sha" == \#* ]] && continue
  if [[ -n "$src" ]]; then
    hit=$(find "$src" -name "$name" -type f | head -1 || true)
    [[ -n "$hit" ]] && cp "$hit" "$name"
  fi
  if [[ ! -f "$name" ]] || ! echo "$sha  $name" | sha256sum -c --status; then
    curl -fsSL --retry 3 -o "$name" "$url" || true
  fi
  if ! echo "$sha  $name" | sha256sum -c --status; then
    if [[ "$fallback" == europepmc ]]; then
      [[ -f epmc.zip ]] || curl -fsSL --retry 3 -o epmc.zip "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3098087/supplementaryFiles"
      unzip -o -q epmc.zip "$name"
    elif [[ "$fallback" != "-" ]]; then
      curl -fsSL --retry 3 -o "$name" "$fallback"
    fi
  fi
  echo "$sha  $name" | sha256sum -c
done <<LIST
5246f69cb9cea98e479f36cef93792d2fac20ee24ebdb99002d72e27082d1931 PMC3098087.1.pdf $S3/PMC3098087.1.pdf -
0715612eebf7eb9af7e18db9ad8c67eb45dd14961989e7d558dafe4f8ea942cf 1471-2105-11-523-1.jpg $S3/1471-2105-11-523-1.jpg europepmc
841053709429c4a61ac53a3a4e16ad32d2f492c624a32b1b7a6ba4b861d0f685 1471-2105-11-523-2.jpg $S3/1471-2105-11-523-2.jpg europepmc
f6cb3130ae332ad4e1d201564924e5ba1a951c1f7bcb5298ac7fcead476d16cc 1471-2105-11-523-3.jpg $S3/1471-2105-11-523-3.jpg europepmc
a3074b844e59014e8bab0580cc15eb6fef566ba49c334e83fc1d6a7dd24e4a37 1471-2105-11-523-4.jpg $S3/1471-2105-11-523-4.jpg europepmc
11c7f655e68aed639fc300912b5faf6aee69f2f628c36a1f82759e923005edad 1471-2105-11-523-5.jpg $S3/1471-2105-11-523-5.jpg europepmc
05e15b6f5e44efe9949c343f48113463c4e039fca856fabf712f2c1078ab2723 1471-2105-11-523-6.jpg $S3/1471-2105-11-523-6.jpg europepmc
d102837073e81d3e948b8fb9d117d0c1742e7ed891ec4e64817f1b8f019f038b 1471-2105-11-523-S1.PDF $S3/1471-2105-11-523-S1.PDF europepmc
17fd4b3f9024a4b6aaaf010ed8c49e9a94e27422d53333c42c031cf4655e93c6 1471-2105-11-523-S2.PDF $S3/1471-2105-11-523-S2.PDF europepmc
0989bccc1e06dcaf854e366d7f6c6e3c91c1051bbe626bdccbb207b2b3449b29 1471-2105-11-523-S3.PDF $S3/1471-2105-11-523-S3.PDF europepmc
bae6ee470f0f46d07631c28937810d740399b53f53831e06eb8768b4a6d81d0c 1471-2105-11-523-S4.PDF $S3/1471-2105-11-523-S4.PDF europepmc
1938c867d04f7682c8406d856d0eac233f49d720c17132696fb330bd68ce09e9 1471-2105-11-523-S5.PDF $S3/1471-2105-11-523-S5.PDF europepmc
67b51985936cb63f772be1b0ac091f34e2cb90df951d9cee28e37cdb224bd160 1471-2105-11-523-S6.PDF $S3/1471-2105-11-523-S6.PDF europepmc
60aed0a80080bf399b8a8ca476c9a26a36a504d3bfca1de50cbdf533ab770b4d 1471-2105-11-523-S7.PDF $S3/1471-2105-11-523-S7.PDF europepmc
b0f9c29d5631b5dfb1d0786a830b3599ee9bac90649e2d4a093ec17fbf83135a 1471-2105-11-523-S8.PDF $S3/1471-2105-11-523-S8.PDF europepmc
fbb0ef3858fffdd979109d898d1bfa6413872bda7a4d0bc2f50ac945daa76503 1471-2105-11-523-S9.PDF $S3/1471-2105-11-523-S9.PDF europepmc
1ee06a296ebb3565b32c45ebfd856121c9b3ae75d12fa6b3abaf412215840315 1471-2105-11-523-S10.PDF $S3/1471-2105-11-523-S10.PDF europepmc
453ba4965aee14aae54460a5bff10b4a4a9eb3ce993a5cb496525843de6b753c 1471-2105-11-523-S11.PDF $S3/1471-2105-11-523-S11.PDF europepmc
a45eaae05b7dec437d5d3eb3510b630ed9d3a650ce17c11a952871529c5193c8 1471-2105-11-523-S12.PDF $S3/1471-2105-11-523-S12.PDF europepmc
9972a4b7ce020a81fdf18097249fd6f7cadbd97a1800d63eb8b04f87f05bd5d2 1471-2105-11-523-S13.PDF $S3/1471-2105-11-523-S13.PDF europepmc
a6e35040f4baa2b107167a569b003f5d8aaa80fe5990a4a9d9befb863a57b783 1471-2105-11-523-S14.PDF $S3/1471-2105-11-523-S14.PDF europepmc
f94c0be17ee2306d153f1b4439e27b1f8fce97eba6f24f85fa9fad8f68514eef Sotiriou-Breast-PNAS-2003-Project.zip https://brb.nci.nih.gov/data_archive/Sotiriou-Breast-PNAS-2003-Project.zip https://web.archive.org/web/20250830054405id_/https://brb.nci.nih.gov/data_archive/Sotiriou-Breast-PNAS-2003-Project.zip
bf4a54c1b4ad27978d71eaf0a2589eda3288ab64c27f7066962a8acadcc4934c sma_0.5.15.tar.gz https://cran.r-project.org/src/contrib/Archive/sma/sma_0.5.15.tar.gz https://cloud.r-project.org/src/contrib/Archive/sma/sma_0.5.15.tar.gz
LIST
rm -rf sotiriou && mkdir sotiriou && unzip -q Sotiriou-Breast-PNAS-2003-Project.zip -d sotiriou
