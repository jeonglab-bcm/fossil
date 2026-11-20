#!/usr/bin/env bash
# Download the inputs of the PMC4232638 reproduction and check their SHA-256.
#
# Usage: fetch_inputs.sh OUT_DIR [--sources DIR]
#
# OUT_DIR/paper.pdf            the article (PMC open-access copy; Figs 2-4 are vector drawings in it)
# OUT_DIR/PMC4232638.xml       the article XML (Tables 1-4)
# OUT_DIR/supp/...             Additional file 2 (the 3,706 mutations) and the supplement PDFs we compare
#
# Primary source: the PMC open-access bucket on AWS (scripted downloads allowed). Fallback: Europe PMC
# (the article XML, and a zip of every supplement file). With --sources DIR the files are copied from a
# local folder holding the same names (paper.pdf, PMC4232638.xml, supp/).
# The paper is CC BY 4.0; its data are CC0. Nothing downloaded here is committed.
set -euo pipefail
out=$1
shift
src=""
if [[ "${1:-}" == "--sources" ]]; then src=$2; fi
mkdir -p "$out/supp"
S3=https://pmc-oa-opendata.s3.amazonaws.com/PMC4232638.1
EPMC=https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4232638

SUPP=(2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29)
declare -A SHA=(
  [paper.pdf]=c2fb4dd960dc2a199230fc2ff594366e591ba23518b6dcde30ce42ac43b675e2
  [supp/13059_2014_484_MOESM2_ESM.xlsx]=d11518f7b0244a07ce11169c28b0a8f8da6d7f6fc6af58f0c8af6fa5471430d6
  [supp/13059_2014_484_MOESM3_ESM.pdf]=667c826acc44463d54d54887947c6e4d9487af02154ca98ba43e771b2a9f2278
  [supp/13059_2014_484_MOESM5_ESM.pdf]=8ef58f9a82a8fafd4ffb748bcfc975b563ff238cd588213586fb6be8dbf5a3b7
  [supp/13059_2014_484_MOESM8_ESM.pdf]=570aec40e40f9ee798ebf9abf839ff671332cd2963b26e9d78a83a6cfbd304fc
  [supp/13059_2014_484_MOESM9_ESM.pdf]=c3f679bf0feed1fd360cdef53415aac1a552f37deddcbd9ec30f4f16131f09e7
  [supp/13059_2014_484_MOESM11_ESM.pdf]=08d2c9e7708f6a569865568452b58e92d001052650e006d2ac8ef7ad3a8be7d1
  [supp/13059_2014_484_MOESM13_ESM.pdf]=f3475d96c327979e9870c852c4c24888a03365183ce3b8b53454f12ff194e62b
  [supp/13059_2014_484_MOESM16_ESM.pdf]=901d97770dbd0fa47eca491b45c8d15c86cb71b2a8f43cb3541b8c2f04f00b2a
  [supp/13059_2014_484_MOESM17_ESM.pdf]=4128dd380d91f38cc62f303186693d06db1fa9b355e6fcaa0693d7c00228415b
  [supp/13059_2014_484_MOESM18_ESM.pdf]=4f707494dfe58b84eb1f8b8ed6899456249bd4dd53e3c6a8a6a6865574fff341
  [supp/13059_2014_484_MOESM19_ESM.pdf]=8c07d3b792ef6be13607aa5dcd1fbf384180f23a42368f7720d6fe03d1e919d5
  [supp/13059_2014_484_MOESM21_ESM.pdf]=d95dee4278cd5739a8952ad0fb4d7e96d15f0caf7b13445c53fe8ba2bd8add80
  [supp/13059_2014_484_MOESM22_ESM.pdf]=1c184cb051b2362c0e44309d4a57fb8468c329f7a66fafda62b760415120423e
  [supp/13059_2014_484_MOESM25_ESM.pdf]=1c8a8d27dd52bf5fda51fd193fac62dcd6edb28029e87ef05c34bacae69dfaa0
  [supp/13059_2014_484_MOESM27_ESM.pdf]=fca3cb1c1c300ca4f9d926eaefc0adf383bf1b8eb55ff1328d97cbd3105ba60b
  [supp/13059_2014_484_MOESM28_ESM.pdf]=aa210efe4904127a792cd6b135301ce55881d743bb505ee1350009615cf43061
  [supp/13059_2014_484_MOESM4_ESM.pdf]=3795b71e357fd8ec4e77e3c0cbb778b4fc0c71c5d809700f29820914036eed09
  [supp/13059_2014_484_MOESM6_ESM.pdf]=4ae42057c5940e9ff07a4f51df69c94ce03aa1aad826a5876a3b97a7a9ce6cff
  [supp/13059_2014_484_MOESM7_ESM.pdf]=51d25f16da67f840400b5c18ac7b68a01109a7bfd565db694178c790144448ab
  [supp/13059_2014_484_MOESM10_ESM.pdf]=79c98c184c07e56bfef275d98865c1c560bbc91e1f46bef33802f3502ab1ffd7
  [supp/13059_2014_484_MOESM12_ESM.pdf]=69dde8b9c38feb2aa2fc680a001b44d8b556db9f9de2bc5ab81cd83ea76cc005
  [supp/13059_2014_484_MOESM14_ESM.pdf]=1b940de2e24f1b816b0b5b1dfe9407bdb4497f7e3d291c49d194081e8a8dd626
  [supp/13059_2014_484_MOESM15_ESM.pdf]=ba2a1931b688abcebbaccc9d490974b91f4fc2d2d7d1919cf86784f7f7f2a0d7
  [supp/13059_2014_484_MOESM20_ESM.pdf]=4b9dc7a2bcb7254cb5078ed103c72819a0ccbd0c7dda1956a78d949f12cf491e
  [supp/13059_2014_484_MOESM23_ESM.pdf]=721f3a6c89665bea754aee8064a600776e5ce3b28173753c50d9fbea8ba51573
  [supp/13059_2014_484_MOESM24_ESM.pdf]=0692bbb6f8eb6200ca2d73d636c81c8831a97a5b7515bf95340f08fafb3137fe
  [supp/13059_2014_484_MOESM26_ESM.pdf]=cb5562c39c97ac9e7b06e02430733904bf6b8863f6a6d11013b16b2dc89bbe52
  [supp/13059_2014_484_MOESM29_ESM.pdf]=f142dd80c17c2d5886ff7401d48527c05798b0d189d29101a4731877af8d1e8e
)
# The article XML: the AWS copy, or Europe PMC's rendering of it (both give the same tables).
XML_SHA=(375ed01447dbc6d3aeb75101ba933dc9a5051ddeddb4d2206fe750fa67f26f29 28950790f17b8b8c817b5644f7c22fe43eaf750066cad87d3ebc8b5d3dbb5891)

get() {  # get URL FILE
  curl -sSfL --retry 3 --retry-delay 5 -o "$2" "$1"
}

if [[ -n "$src" ]]; then
  cp "$src/paper.pdf" "$src/PMC4232638.xml" "$out/"
  for i in "${SUPP[@]}"; do
    f=$(ls "$src/supp/13059_2014_484_MOESM${i}_ESM".* | head -1)
    cp "$f" "$out/supp/"
  done
else
  get "$S3/PMC4232638.1.pdf" "$out/paper.pdf"
  get "$S3/PMC4232638.1.xml" "$out/PMC4232638.xml" || get "$EPMC/fullTextXML" "$out/PMC4232638.xml"
  ok=1
  for i in "${SUPP[@]}"; do
    ext=pdf
    [[ $i == 2 ]] && ext=xlsx
    get "$S3/13059_2014_484_MOESM${i}_ESM.$ext" "$out/supp/13059_2014_484_MOESM${i}_ESM.$ext" || { ok=0; break; }
  done
  if [[ $ok == 0 ]]; then
    echo "AWS copy failed; trying the Europe PMC supplement zip" >&2
    get "$EPMC/supplementaryFiles" "$out/supp.zip"
    (cd "$out/supp" && unzip -oq ../supp.zip && rm ../supp.zip)
  fi
fi

fail=0
for f in "${!SHA[@]}"; do
  have=$(sha256sum "$out/$f" | cut -d' ' -f1)
  if [[ "$have" != "${SHA[$f]}" ]]; then echo "SHA-256 mismatch: $f ($have)" >&2; fail=1; fi
done
have=$(sha256sum "$out/PMC4232638.xml" | cut -d' ' -f1)
if [[ "$have" != "${XML_SHA[0]}" && "$have" != "${XML_SHA[1]}" ]]; then echo "SHA-256 mismatch: PMC4232638.xml ($have)" >&2; fail=1; fi
[[ $fail == 0 ]] && echo "inputs ok: $((${#SHA[@]} + 1)) files" >&2
exit $fail
