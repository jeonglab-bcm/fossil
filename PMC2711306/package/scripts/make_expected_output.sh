#!/bin/bash
# Expected output of the bundled example, from the authors' own Matlab code run under GNU Octave:
# embed_novi.m (kuchaev.com/Denoising, denoising.zip, archived by the Wayback Machine) embeds
# geometric_numbered.txt in 2 dimensions, and the pairwise distances of its coordinates are
# written to geometric_expected_distances.csv. The authors' code is not in this repository.
#
# Usage: make_expected_output.sh AUTHORS_DIR SHIMS_DIR OCTAVE PYTHON
#   AUTHORS_DIR  folder holding embed_novi.m (unzipped denoising.zip)
#   SHIMS_DIR    PMC2711306/figure-reproduction/pipeline/octave_shims (spconvert, dist, mvnpdf)
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
data="$here/../src/geodenoise/data"
tmp=$(mktemp -d)
"$3" --no-gui --eval "addpath('$1'); addpath('$2'); A = dlmread('$data/geometric_numbered.txt'); L = embed_novi(A, 2); dlmwrite('$tmp/coords.txt', L, 'precision', '%.12g');"
"$4" "$here/coords_to_distances.py" "$tmp/coords.txt" "$data/geometric_expected_distances.csv"
rm -rf "$tmp"
