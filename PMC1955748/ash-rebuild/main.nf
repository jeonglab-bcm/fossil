// Rebuilt ASH (PMC1955748, Standley et al. 2007) against Additional File 3.
// Run: nextflow run main.nf --outdir results [--python python3] [--sources DIR]

process FETCH {
    output:
    path '1471-2105-8-116-S3.xls', emit: af3
    path 'cath-domain-boundaries-v3_0_0.txt', emit: bounds
    script:
    """
    bash ${projectDir}/../figure-reproduction/pipeline/fetch_inputs.sh ${params.sources ?: ''}
    """
}

process EXPORT_AF3 {
    input:
    path af3
    output:
    path 'additional-file-3.csv'
    script:
    """
    ${params.python} ${projectDir}/../figure-reproduction/pipeline/export_af3.py ${af3} additional-file-3.csv
    """
}

process ALIGN_AF3 {
    publishDir params.outdir, mode: 'copy'
    input:
    path bounds
    path af3csv
    output:
    path 'af3_pairs.json'
    script:
    """
    mkdir -p cif
    cd ${projectDir}/pipeline && ${params.python} af3_test.py \$OLDPWD/${bounds} \$OLDPWD/${af3csv} \
        ${projectDir}/../figure-reproduction/af2_matrix.txt \$OLDPWD/cif \$OLDPWD/af3_pairs.json
    """
}

process COMPARE {
    publishDir params.outdir, mode: 'copy'
    input:
    path pairs
    output:
    path 'af3_comparison.json'
    path 'af3_scatter.png'
    path 'report.md'
    script:
    """
    cd ${projectDir}/pipeline && ${params.python} compare_af3.py \$OLDPWD/${pairs} \$OLDPWD > \$OLDPWD/report.md
    """
}

workflow {
    inputs = FETCH()
    COMPARE(ALIGN_AF3(inputs.bounds, EXPORT_AF3(inputs.af3)))
}
