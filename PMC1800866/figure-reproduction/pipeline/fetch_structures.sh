#!/usr/bin/env bash
# Download the mmCIF file of every PDB entry named in Additional file 1.
# Current entries come from RCSB; obsolete ones (and RCSB stubs without coordinates) from the
# wwPDB obsolete archive.
# Usage: fetch_structures.sh IDS_FILE OUTDIR   (IDS_FILE: one 4-character PDB code per line)
set -euo pipefail
ids=$1; out=$2; mkdir -p "$out"
fetch() {
  id=$(echo "$1" | tr 'A-Z' 'a-z'); f="$2/$id.cif.gz"
  has_atoms() { zcat "$1" 2>/dev/null | grep -qm1 -E '^(ATOM|HETATM)'; }
  [ -s "$f" ] && has_atoms "$f" && return 0
  # RCSB serves a coordinate-free stub for some obsolete entries: fall through to the archive.
  curl -sfL --retry 3 -o "$f" "https://files.rcsb.org/download/$id.cif.gz" && has_atoms "$f" && return 0
  mid=${id:1:2}
  # The archived mmCIF of an obsolete entry has no sequence table; its PDB-format file has SEQRES.
  curl -sfL --retry 3 -o "$f" "https://files.wwpdb.org/pub/pdb/data/structures/obsolete/mmCIF/$mid/$id.cif.gz" &&
    curl -sfL --retry 3 -o "$2/$id.pdb.gz" "https://files.wwpdb.org/pub/pdb/data/structures/obsolete/pdb/$mid/pdb$id.ent.gz" &&
    { echo "$id obsolete" >&2; return 0; }
  echo "$id MISSING" >&2; rm -f "$f"
}
export -f fetch
xargs -P 8 -I{} bash -c 'fetch {} '"$out" < "$ids"
