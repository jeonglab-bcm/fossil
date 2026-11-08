// Reproduce PMC2850872 (Yu, Liu, Valdez, Gwinn and Khoury 2010, "Application of support vector
// machine modeling for prediction of common diseases: the case of diabetes and pre-diabetes"):
// Table 1 from the NHANES 1999-2004 files, Tables 2 and 3 and Figure 2 over 10 random splits,
// the text's logistic regression AUCs and DeLong tests, a check against R, the package check,
// results.json and the results page.
//
// Run (from the repository root):
//   nextflow run PMC2850872/figure-reproduction/main.nf --outdir results [--search] [--sources DIR]
//
// --search   rerun grid.py's search for C and gamma on every split and kernel (about 80 minutes on
//            4 cores). Without it the C and gamma of the committed run (output/grid.csv) are used
//            and everything else is recomputed.
// --sources  a folder with local copies of the NHANES .xpt files.

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${projectDir}/pipeline/fetch_inputs.sh downloads ${params.sources ?: ''}
    """
}

process COHORT {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'analytic.csv', emit: analytic
    path 'table1.json', emit: table1
    script:
    """
    ${params.python} ${projectDir}/pipeline/cohort.py ${downloads} .
    """
}

process MODELS {
    publishDir "${params.outdir}", mode: 'copy', pattern: '*.csv'
    cpus params.jobs
    input:
    path analytic
    output:
    path '*_reps.csv', emit: reps
    path 'grid.csv', emit: grid
    path 'roc_rep0.csv', emit: roc
    path 'r_input_*.csv', emit: rin
    path 'r_params_*.json', emit: rpar
    script:
    def grid = params.search ? '' : "--grid ${projectDir}/output/grid.csv"
    """
    PYTHONWARNINGS=ignore ${params.python} ${projectDir}/pipeline/run_models.py ${analytic} . --reps ${params.reps} --jobs ${params.jobs} ${grid}
    """
}

process R_CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path rin
    path rpar
    output:
    path 'r_check.json'
    script:
    """
    ${params.rscript} ${projectDir}/pipeline/r_check.R . r_check.json
    """
}

process FIG2 {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path roc
    output:
    path 'fig2_*'
    script:
    """
    ${params.python} ${projectDir}/pipeline/compare_fig2.py ${projectDir}/published/figure-2.jpg ${roc} .
    """
}

process TABLES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path table1
    path reps
    path grid
    output:
    path 'tables.json'
    script:
    """
    ${params.python} ${projectDir}/pipeline/make_tables.py . tables.json
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${projectDir}/../../tools/paper2repro/check_package.py ${projectDir}/../package --json package.json || true
    test -s package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path tables
    path table1
    path reps
    path fig
    path rcheck
    path pkg
    output:
    path 'results.json'
    script:
    """
    ${params.python} ${projectDir}/pipeline/make_results.py ${projectDir}/results_notes.json . results.json
    ${params.python} ${projectDir}/../../tools/paper2repro/check_results.py results.json --write --skip-files
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path files, stageAs: 'run/*'
    output:
    path 'report.md'
    script:
    """
    ${params.python} ${projectDir}/pipeline/check_reproduction.py run ${projectDir}/output ${projectDir}/../results.json report.md
    """
}

process BUILD_PAGE {
    publishDir "${params.outdir}/site", mode: 'copy'
    input:
    path files, stageAs: 'run/*'
    output:
    path 'index.html'
    script:
    """
    ${params.python} ${projectDir}/pipeline/build_page.py run ${projectDir}/published index.html
    """
}

workflow {
    downloads = FETCH()
    c = COHORT(downloads)
    m = MODELS(c.analytic)
    r = R_CHECK(m.rin, m.rpar)
    f = FIG2(m.roc)
    t = TABLES(c.table1, m.reps, m.grid)
    k = PACKAGE()
    res = RESULTS(t, c.table1, m.reps, f, r, k)
    outs = c.analytic.mix(c.table1, m.reps.flatten(), m.grid, m.roc, r, f.flatten(), t, k, res).collect()
    CHECK(outs)
    BUILD_PAGE(outs)
}
