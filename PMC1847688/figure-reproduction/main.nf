// Reproduce PMC1847688 (Mantini et al. 2007, LIMPIC): Figs 2-9 and LIMPIC's rows of Tables 1-3.
// Run: nextflow run main.nf --outdir results [--python python3] [--sources DIR] [--octave]
// --octave also runs the authors' MATLAB code in GNU Octave and checks that the Python
// port gives the same peaks, classes and signals.

process FETCH {
    output:
    path 'S1', emit: s1
    path 'S2', emit: s2
    path 'S3', emit: s3
    path 'S4.xls', emit: s4
    script:
    """
    bash ${projectDir}/pipeline/fetch_inputs.sh ${params.sources ?: ''}
    """
}

process EXPORT_S4 {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path s4
    output:
    path 'S4_LIMPIC.csv'
    script:
    """
    ${params.python} ${projectDir}/pipeline/export_s4.py ${s4} S4_LIMPIC.csv
    """
}

process LIMPIC {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path s2
    path s3
    output:
    path 'limpic', emit: dir
    script:
    """
    ${params.python} ${projectDir}/pipeline/run_limpic.py ${s2} ${s3}/Plasma limpic
    """
}

process LIMPIC_OCTAVE {
    input:
    path s1
    path s2
    path s3
    output:
    path 'octave', emit: dir
    script:
    """
    mkdir octave
    octave-cli ${projectDir}/pipeline/octave/run_limpic.m ${s1}/limpic_v1.1 ${s2} ${s3}/Plasma octave
    """
}

process CHECK_PORT {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path python_dir
    path octave_dir
    output:
    path 'port_check.json'
    script:
    """
    ${params.python} ${projectDir}/pipeline/check_port.py ${python_dir} ${octave_dir} port_check.json
    """
}

process COMPARE {
    publishDir params.outdir, mode: 'copy'
    input:
    path limpic
    path s4csv
    output:
    path 'output/*'
    script:
    """
    ${params.python} ${projectDir}/pipeline/compare.py ${limpic} ${projectDir}/published ${s4csv} output
    ${params.python} ${projectDir}/pipeline/make_tables.py ${limpic} ${s4csv} output/tables.json
    """
}

process CHECK {
    publishDir params.outdir, mode: 'copy'
    input:
    path outputs
    output:
    path 'report.md'
    script:
    """
    ${params.python} ${projectDir}/pipeline/check_reproduction.py comparison.json tables.json > report.md
    """
}

workflow {
    inputs = FETCH()
    s4csv = EXPORT_S4(inputs.s4)
    limpic = LIMPIC(inputs.s2, inputs.s3)
    if (params.octave) {
        octave = LIMPIC_OCTAVE(inputs.s1, inputs.s2, inputs.s3)
        CHECK_PORT(limpic.dir, octave.dir)
    }
    out = COMPARE(limpic.dir, s4csv)
    CHECK(out.collect())
}
