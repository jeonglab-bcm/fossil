#!/usr/bin/env bash
# Download the inputs, check each file's SHA-256 and unpack them into the working directory.
#   corpora/   the five unified PPI corpora, third-party mirror github.com/metalrt/ppi-dataset
#              at commit dd49ea3 (2021-07-04); -train/-test split by the mirror's author
#   medpost/   MedPost tagger (Smith et al. 2004; NCBI, public domain), built by build_medpost.sh
#   stanford-parser/  Stanford Lexicalized Parser 1.5.1 (2006-06-11; GPL), the version the
#              paper names
#   relex_page.html  Fundel et al.'s RelEx supplementary page (2014 Wayback capture), which
#              lists RelEx's relation restriction terms (extract_terms.py)
# Usage: fetch_inputs.sh [DIR]   (DIR: reuse local copies: ppi-dataset-<commit>.tar.gz,
#        medpost.tar.gz, StanfordParser-2006-06-11.tar.gz, relex_page.html)
set -euo pipefail
commit=dd49ea3217dd54043940a26f326108d1915f46df
sum256() { if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1; }
check() { local got; got=$(sum256 "$1"); [ "$got" = "$2" ] || { echo "$1: SHA-256 $got, expected $2" >&2; exit 1; }; }
get() {  # get FILE URL
  if [ -n "${DIR:-}" ] && [ -f "$DIR/$1" ]; then cp "$DIR/$1" "$1"; else curl -sfL --retry 3 "$2" -o "$1"; fi
}
DIR="${1:-}"

get "ppi-dataset-$commit.tar.gz" "https://codeload.github.com/metalrt/ppi-dataset/tar.gz/$commit"
mkdir -p corpora
tar xzf "ppi-dataset-$commit.tar.gz" --strip-components=2 -C corpora "ppi-dataset-$commit/csv_output"
declare -A xml=(
  [AIMed-train.xml]=4fe27945fcce31d4afc0c57fe176b45713ac76d73d7a89cb2183be0160826658
  [AIMed-test.xml]=c33b51337a12a8f86e74866857c1cb6df410e1d8c54fae28f41f1002210d9f7b
  [BioInfer-train.xml]=6bfdecaeda6e49b926c46b884d27dac7f6dfc439490c298bdb983446c75110dc
  [BioInfer-test.xml]=da6a486c91f7290309f758952b0d91275bfa120ef0fa76f94b2b1d23f31780d2
  [HPRD50-train.xml]=6100f3d9a6c26b7df1ca352d05b508a07adf5433b903bacfe540264593d8b926
  [HPRD50-test.xml]=9606c84b918b6331e7f4385d4c93c8b55200eef05fed86ab15eba3cc4070d911
  [IEPA-train.xml]=e267a560274fa90c242d07f1b13ea7a9da51296c5b4c3704b8227b35d7021647
  [IEPA-test.xml]=52a6d7dea45b174c0fd06e259e5aace730870087523e36556e558134f4c9a530
  [LLL-train.xml]=8833bf09ecaf6f15c578b14d8ae2ffdce3a00c6108447757215f25bb726f5c28
  [LLL-test.xml]=e26994753db514372c6d80a317a70ed94d9893e78aacecaacd017727b161a4e9
)
for f in "${!xml[@]}"; do check "corpora/$f" "${xml[$f]}"; done

get medpost.tar.gz https://ftp.ncbi.nlm.nih.gov/pub/lsmith/MedPost/medpost.tar.gz
check medpost.tar.gz 46be9a61cbf5e45dfcb73bcd716bdd3c92474f3cd6bfaa0d7fc390983852f925
mkdir -p medpost && tar xzf medpost.tar.gz -C medpost

get StanfordParser-2006-06-11.tar.gz https://downloads.cs.stanford.edu/nlp/software/StanfordParser-2006-06-11.tar.gz
check StanfordParser-2006-06-11.tar.gz 9d1859abcaee5b741bb26c11df891f61fff7c80aad8fc56befad2826fc9aef82
tar xzf StanfordParser-2006-06-11.tar.gz
mv stanford-parser-2006-06-11 stanford-parser

get relex_page.html "http://web.archive.org/web/20140722040650id_/http://www2.bio.ifi.lmu.de/publications/RelEx/"
check relex_page.html 33d79cfdd99e6d7c22a82b40630a523967b76ac7adf917055a00a7a47b35e8d0
