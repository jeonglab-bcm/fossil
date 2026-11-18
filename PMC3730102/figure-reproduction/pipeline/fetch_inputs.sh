#!/usr/bin/env bash
# Download every input of the PMC3730102 reproduction (Lee et al. 2013, CoLP) and check its SHA-256.
#
#   fetch_inputs.sh OUTDIR [--sources DIR]
#
# --sources DIR copies the files from a local folder laid out like OUTDIR (PMC3730102/sources) instead.
#
# OUTDIR/geo       GEO series matrices (GSE5281, GSE5390, GSE3185, GSE4271), the GSE9885 family file
#                  (two-colour channel values) and the platform annotations (NCBI GEO; paced and retried,
#                  GEO answers 403 to bursts of requests)
# OUTDIR/go        GO annotations of human proteins and the ontology, release 2007-01-01
#                  (GO archive on S3; fallback release.geneontology.org)
# OUTDIR/ppi       HPRD, Reactome and BioGRID from the Pathway Commons 2011 archive (download.baderlab.org);
#                  Ramani et al. 2005 Additional data file 4 (PMC open-access copy on AWS)
# OUTDIR/uniprot   human Swiss-Prot entries: sequence, gene names, InterPro and GeneID cross-references
#                  (UniProt REST). UniProt has no pinned download by release: its checksum is checked and
#                  a mismatch is reported as a warning, with the release that was served.
# OUTDIR/paper     the paper's figure files (PMC open-access copy on AWS), for the comparison only
set -euo pipefail

out="${1:?usage: fetch_inputs.sh OUTDIR [--sources DIR]}"
src=""
if [ "${2:-}" = "--sources" ]; then src="${3:?--sources needs a folder}"; fi
mkdir -p "$out"/{geo,go,ppi/ramani,uniprot,paper}

GEO=https://ftp.ncbi.nlm.nih.gov/geo
GOS3=https://s3.amazonaws.com/go-data-product-release/2007-01-01
GOWEB=https://release.geneontology.org/2007-01-01
PC1=https://download.baderlab.org/PathwayCommons/PC1/last_release-2011/tab_delim_network/by_source
PMC=https://pmc-oa-opendata.s3.amazonaws.com
UNIPROT='https://rest.uniprot.org/uniprotkb/stream?compressed=true&format=tsv&fields=accession,id,gene_primary,gene_synonym,xref_interpro,xref_geneid,sequence&query=%28organism_id%3A9606%29%20AND%20%28reviewed%3Atrue%29'

sha() { sha256sum "$1" | cut -d' ' -f1; }

fetch() {  # dest sha256 url [fallback-url]
    local dest="$1" want="$2" url="$3" alt="${4:-}" i
    if [ -n "$src" ] && [ -f "$src/$dest" ]; then
        cp "$src/$dest" "$out/$dest"
    else
        # GEO answers 403 to bursts of requests: pause before each GEO file and back off for up to
        # about 14 minutes (30 s, 60 s, ... 180 s) before giving up.
        case "$url" in *ncbi.nlm.nih.gov*) sleep "${GEO_PAUSE:-5}" ;; esac
        for i in 1 2 3 4 5 6 7; do
            if curl -sSfL --retry 3 --retry-delay 5 -o "$out/$dest" "$url"; then break; fi
            if [ -n "$alt" ] && curl -sSfL --retry 3 -o "$out/$dest" "$alt"; then break; fi
            rm -f "$out/$dest"
            [ "$i" -lt 7 ] && sleep $((i * 30))
        done
    fi
    [ -s "$out/$dest" ] || { echo "download failed: $dest" >&2; exit 1; }
    local got; got=$(sha "$out/$dest")
    if [ "$want" = "warn" ]; then return 0; fi
    [ "$got" = "$want" ] || { echo "checksum mismatch: $dest ($got)" >&2; exit 1; }
    echo "ok $dest"
}

fetch geo/GSE5281_series_matrix.txt.gz 4cf3d2e7948f712fe9a145fcc2e8f34767eb2715284011148b3204c732e68e36 $GEO/series/GSE5nnn/GSE5281/matrix/GSE5281_series_matrix.txt.gz
fetch geo/GSE5390_series_matrix.txt.gz 45e25025a559ff950f3de44d750d378262badc028c937198ee569c99d37290a9 $GEO/series/GSE5nnn/GSE5390/matrix/GSE5390_series_matrix.txt.gz
fetch geo/GSE3185-GPL8300_series_matrix.txt.gz 89e1fafac292d352498d87d79263a32ac793e37669fa5df4793b39972d082ab6 $GEO/series/GSE3nnn/GSE3185/matrix/GSE3185-GPL8300_series_matrix.txt.gz
fetch geo/GSE3185-GPL96_series_matrix.txt.gz 85016898fb77b0c3ce34f3d3c4bad7d8e5a85dd5e7f9a911cb46b932e521707d $GEO/series/GSE3nnn/GSE3185/matrix/GSE3185-GPL96_series_matrix.txt.gz
fetch geo/GSE4271-GPL96_series_matrix.txt.gz 956b97238cd0a75d0c82e166d716b1e3ee21c73a24e77ca75b1243e43b67ebad $GEO/series/GSE4nnn/GSE4271/matrix/GSE4271-GPL96_series_matrix.txt.gz
fetch geo/GSE4271-GPL97_series_matrix.txt.gz 11f36ea5263808058f6b3f07b8025da3e3d66accaaa2ac578f4a1031bf222207 $GEO/series/GSE4nnn/GSE4271/matrix/GSE4271-GPL97_series_matrix.txt.gz
fetch geo/GSE9885_family.soft.gz a3f7585e1a8ad3593fb6f6a0933985899ca3ee488838afe6b1a10e3c72b43129 $GEO/series/GSE9nnn/GSE9885/soft/GSE9885_family.soft.gz
fetch geo/GPL96.annot.gz 88e0b22362bac779eb220b3b185c80faa6510a92b9358eaad159a561ab4351c4 $GEO/platforms/GPLnnn/GPL96/annot/GPL96.annot.gz
fetch geo/GPL97.annot.gz 57f68da95e962424620581ba7d9615fce57452770726d49c4266a621ac8d07f5 $GEO/platforms/GPLnnn/GPL97/annot/GPL97.annot.gz
fetch geo/GPL570.annot.gz d7cd44352127b1e34f3a720ebea86093ef255a38f1612a85a2962b71bde8f394 $GEO/platforms/GPLnnn/GPL570/annot/GPL570.annot.gz
fetch geo/GPL8300.annot.gz 318e71026be4c7c5abafe8c4d87b694d8c8acfc3c87ce6022d12d697482749fe $GEO/platforms/GPL8nnn/GPL8300/annot/GPL8300.annot.gz
fetch geo/GPL885.annot.gz e660d2b3f48f70231dbb93191b40a152c8d185186359b70e116044ee2e432c68 $GEO/platforms/GPLnnn/GPL885/annot/GPL885.annot.gz
fetch geo/GPL887.annot.gz 484b3b053e2ea7e9d924b9f4394d5b32de85e3a010b4f43f35dd9b140f658834 $GEO/platforms/GPLnnn/GPL887/annot/GPL887.annot.gz

fetch go/goa_human.2007-01-01.gaf.gz 0e2a4c68ec509d36e58f4d16a5834cc1ad3b6250c92de9ab6262e99883a2f3f4 $GOS3/annotations/goa_human.gaf.gz $GOWEB/annotations/goa_human.gaf.gz
fetch go/gene_ontology.2007-01-01.obo 7ecc89dfee018b89c8fc347d16f67d9d6e4280fe29a514ccf2126c1191452494 $GOS3/ontology/gene_ontology.obo $GOWEB/ontology/gene_ontology.obo

fetch ppi/hprd-edge-attributes.txt.zip 0d03985c5dabefd091de7caabb44960d86ba5072423c3aae12e0c1baa5072c3c $PC1/hprd-edge-attributes.txt.zip
fetch ppi/hprd-node-attributes.txt.zip c754e6841a20cf736a2fb180c55f5f3dbb3b16f094049c07dd48d1297e78a6f7 $PC1/hprd-node-attributes.txt.zip
fetch ppi/reactome-edge-attributes.txt.zip 25ab191097ee04a08467354d90e45ed032ee7ea7f00334bfbb8f376be6aa9329 $PC1/reactome-edge-attributes.txt.zip
fetch ppi/reactome-node-attributes.txt.zip 0eac2c2eecde158ffa36a167ce162a93f22f612399c1a93e3a9805e492f9e19f $PC1/reactome-node-attributes.txt.zip
fetch ppi/biogrid-edge-attributes.txt.zip b644702f6e8b18382a8d5e18397cf705c0fbcd0e207ee9e81e429e34fc409845 $PC1/biogrid-edge-attributes.txt.zip
fetch ppi/biogrid-node-attributes.txt.zip fac16224219ebd4df948b29aa697fd8213fb69cfb856ac081b55889fff970da0 $PC1/biogrid-node-attributes.txt.zip
for f in "$out"/ppi/*.zip; do unzip -o -q "$f" -d "$out/ppi"; done
fetch ppi/ramani/gb-2005-6-5-r40-S4.txt c7c210198a232b889d486d9f80253cca5949b580ab9b8273234222de968958cd $PMC/PMC1175952.1/gb-2005-6-5-r40-S4.txt

for f in 1283fig2.jpg:ccf9a8f5bbbd0258933e3681ea450a41510d02433ac94b036109810f8c4dd4e1 \
         1283fig3.jpg:cb4457270ae913f9282245ab832377c80d60ca7cfa468774eac0c483414922d3 \
         1283fig4.jpg:af1a728c5f16b4597e7f24fc1a567d1745deb857e7345f77875b6e6c7aeafac9 \
         1283fig5.jpg:5d399c64577109af5f773759ed86ceeb37c060a201d5d7a3edfa1643abeeda38 \
         1283fig6.jpg:9591bc4e5b163aaafc5e97e9b5c71a570b9fc3c9755cca3a8257861250ce4abe; do
    fetch "paper/${f%%:*}" "${f##*:}" "$PMC/PMC3730102.1/${f%%:*}"
done

UNIPROT_SHA=6b1c2cbb0ecea692d24119add60fc13aba9bec86291d4d3e6e9d36418d24697b  # release 2026_04
fetch uniprot/human_sprot.tsv.gz warn "$UNIPROT"
got=$(sha "$out/uniprot/human_sprot.tsv.gz")
if [ "$got" != "$UNIPROT_SHA" ]; then
    rel=$(curl -sSI "https://rest.uniprot.org/uniprotkb/search?query=reviewed:true&size=1" | tr -d '\r' | awk -F': ' 'tolower($1)=="x-uniprot-release"{print $2}')
    echo "WARNING: UniProt file differs from release 2026_04 (served: ${rel:-unknown}); results may move" >&2
    echo "${rel:-unknown}" > "$out/uniprot/RELEASE"
else
    echo "2026_04" > "$out/uniprot/RELEASE"
    echo "ok uniprot/human_sprot.tsv.gz"
fi
