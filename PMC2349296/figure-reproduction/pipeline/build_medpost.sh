#!/usr/bin/env bash
# Build the MedPost tokenizer and tagger (NCBI, public domain) in an unpacked medpost.tar.gz.
# Usage: build_medpost.sh MEDPOST_DIR
# MedPost's own makefile also builds a parser module that needs libpcre; RelEx does not use it,
# so only the tokenizer and the tagger are compiled here. -fpermissive and -w accept 2008 C++. -O2 segfaults (undefined behaviour in the 2008 code), so -O0.
set -euo pipefail
cd "$1"
CXX="${CXX:-g++}"
FLAGS="-O0 -w -fpermissive -Isrc/lib"
# Source fix: NUM_ABB is sizeof(array) in bytes, not the number of entries, so the abbreviation
# loop in MPtok::tok_15 reads past the end of common_abb and segfaults on x86_64. Count entries.
sed -i 's|^#define NUM_ABB (sizeof common_abb)$|#define NUM_ABB (sizeof common_abb / sizeof common_abb[0])|' src/MPtok.C
grep -q 'sizeof common_abb / sizeof common_abb\[0\]' src/MPtok.C
# Source fix: MPtag's constructor leaves `lex` uninitialized and the tagger's "lex" command
# deletes it before assigning it, so the tagger frees a garbage pointer.
grep -qP '^\tlex = NULL;' src/MPtag.C || sed -i 's|^\talpha_array = NULL;$|\tlex = NULL;\n\talpha_array = NULL;|' src/MPtag.C
grep -qP '^\tlex = NULL;' src/MPtag.C
# Source fix: run_tokenizer() is declared int but falls off its end (undefined behaviour; UBSan
# aborts there). On the ubuntu-24.04 runner the tokenizer lost its last buffered output, the
# last 18 AIMed sentences. Return explicitly and flush.
python3 - <<'PY'
p = "src/tokenizer.C"
s = open(p).read()
old = "\tdelete[] save_text;\n}\n"
new = "\tdelete[] save_text;\n\tfflush(ofp);\n\treturn 1;\n}\n"
if new not in s:
    assert s.count(old) == 1, "run_tokenizer end not found"
    open(p, "w").write(s.replace(old, new))
PY
objs=()
for f in src/MPtag.C src/MPlex.C src/MPtok.C src/lib/Btree.C src/lib/runn.C; do
  o="${f%.C}.o"; $CXX $FLAGS -c "$f" -o "$o"; objs+=("$o")
done
$CXX $FLAGS src/tagger.C "${objs[@]}" -o util/tagger
$CXX $FLAGS src/tokenizer.C "${objs[@]}" -o util/tokenizer
# The equivalent of util/install.perl: point the wrapper script at this directory.
sed -i -e "s|^MEDPOST_HOME=.*|MEDPOST_HOME=$(pwd)|" -e 's|^INSTALL_DATE=.*|INSTALL_DATE="built"|' medpost
chmod +x medpost
echo "Abl binds to the SH3 domain of Grb2 ." | ./medpost
