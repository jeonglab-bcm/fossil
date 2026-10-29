// Reproduce what can be reproduced of PMC1955748 (Standley et al. 2007, ASH): checks of the
// training set, Additional Files 2 to 4 and the paper's derived numbers.
// Run: nextflow run main.nf --outdir results [--python python3] [--sources DIR]

process FETCH {
    output:
    path '1471-2105-8-116-S1.txt', emit: af1
    path '1471-2105-8-116-S2.tiff', emit: af2
    path '1471-2105-8-116-S3.xls', emit: af3
    path '1471-2105-8-116-S4.tiff', emit: af4
    path 'cath-domain-*', emit: cath
    path 'dir.cla.scop.1.69.txt', emit: scop
    path 'aaindex2', emit: aaindex
    path 'BLOSUM62', emit: b62
    path 'blosum62_3.blast', emit: b62_3
    script:
    """
    bash ${projectDir}/pipeline/fetch_inputs.sh ${params.sources ?: ''}
    """
}

process CHECK_AF2 {
    publishDir params.outdir, mode: 'copy'
    input:
    path af2
    output:
    path 'af2_check.txt'
    script:
    """
    ${params.python} ${projectDir}/pipeline/check_af2.py ${af2} ${projectDir}/af2_matrix.txt > af2_check.txt
    """
}

process EXPORT_AF3 {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path af3
    output:
    path 'additional-file-3.csv'
    script:
    """
    ${params.python} ${projectDir}/pipeline/export_af3.py ${af3} additional-file-3.csv
    """
}

process CATH_SCOP {
    publishDir params.outdir, mode: 'copy'
    input:
    path cath
    path scop
    path af1
    path af3csv
    output:
    path 'cath_scop.json'
    script:
    """
    ${params.python} ${projectDir}/pipeline/cath_scop.py . . ${af1} ${af3csv} cath_scop.json
    """
}

process MATRICES {
    publishDir params.outdir, mode: 'copy'
    input:
    path b62
    path b62_3
    path aaindex
    path af4
    output:
    path 'matrices.json', emit: json
    path 'af4_overlay.png'
    script:
    """
    ${params.python} ${projectDir}/pipeline/matrices.py ${projectDir}/af2_matrix.txt ${b62} ${b62_3} ${aaindex} ${af4} .
    """
}

process ARITHMETIC {
    publishDir params.outdir, mode: 'copy'
    output:
    path 'arithmetic.json'
    script:
    """
    ${params.python} ${projectDir}/pipeline/arithmetic.py arithmetic.json
    """
}

process CHECK {
    publishDir params.outdir, mode: 'copy'
    input:
    path af2_check
    path cath_scop
    path matrices
    path arithmetic
    output:
    path 'report.md'
    script:
    """
    ${params.python} ${projectDir}/pipeline/check_reproduction.py ${af2_check} ${cath_scop} ${matrices} ${arithmetic} > report.md
    """
}

workflow {
    inputs = FETCH()
    af2 = CHECK_AF2(inputs.af2)
    af3csv = EXPORT_AF3(inputs.af3)
    cs = CATH_SCOP(inputs.cath, inputs.scop, inputs.af1, af3csv)
    mx = MATRICES(inputs.b62, inputs.b62_3, inputs.aaindex, inputs.af4)
    CHECK(af2, cs, mx.json, ARITHMETIC())
}
