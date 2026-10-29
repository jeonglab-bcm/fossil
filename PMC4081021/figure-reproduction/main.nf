// Reproduce PMC4081021 (Hasenauer et al. 2014, ODE constrained mixture modelling): Figs 2B-G,
// 3B-D, 4B-D, 5B-C and 6, Tables 1 and 2 and Supporting Information S1 Table 1, and the
// comparison page that site/PMC4081021/index.html is copied from.
// Run: nextflow run main.nf --outdir results [--python python3] [--sources DIR] [--refit]
// --refit also refits the 24 conversion-reaction models from scratch (2000 starts each) and
// checks every saved optimum with exact gradients (needs jax and diffrax).

process FETCH {
    output:
    path 'sources', emit: sources
    script:
    """
    bash ${projectDir}/pipeline/fetch_inputs.sh ${params.sources ?: ''}
    """
}

process PORT {
    publishDir params.outdir, mode: 'copy'
    input:
    path sources
    output:
    path 'port_check.json'
    script:
    """
    ${params.python} ${projectDir}/pipeline/check_port.py --sources ${sources} --out port_check.json
    """
}

process REFIT {
    publishDir params.outdir, mode: 'copy'
    input:
    path sources
    output:
    path 'refit', emit: dir
    path 'optima_check.json', emit: optima
    script:
    """
    sh ${projectDir}/pipeline/refit_all.sh ${sources} refit ${params.python}
    ${params.python} ${projectDir}/pipeline/check_optima.py --sources ${sources} --out optima_check.json
    """
}

process FIGURES {
    publishDir params.outdir, mode: 'copy'
    input:
    path sources
    path refit
    output:
    path 'output/*'
    script:
    def r = params.refit ? "--refit-dir ${refit}" : ''
    """
    ${params.python} ${projectDir}/pipeline/compare.py --sources ${sources} --published ${projectDir}/published --out output
    ${params.python} ${projectDir}/pipeline/render.py --sources ${sources} --out output
    ${params.python} ${projectDir}/pipeline/make_tables.py --sources ${sources} --published ${projectDir}/published ${r} --out output/tables.json
    if [ -n "${r}" ]; then
      ${params.python} ${projectDir}/pipeline/compare.py --sources ${sources} --published ${projectDir}/published --out output --figs 2 --fits refit ${r} --tag _refit
    fi
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
    ${params.python} ${projectDir}/pipeline/check_reproduction.py --dir . > report.md
    """
}

process BUILD_PAGE {
    publishDir "${params.outdir}/site", mode: 'copy'
    input:
    path outputs
    output:
    path 'index.html'
    script:
    """
    ${params.python} ${projectDir}/pipeline/build_page.py . ${projectDir}/published index.html
    """
}

workflow {
    src = FETCH().sources
    port = PORT(src)
    if (params.refit) {
        rf = REFIT(src)
        figs = FIGURES(src, rf.dir)
        CHECK(figs.mix(port, rf.optima).collect())
        BUILD_PAGE(figs.mix(port, rf.optima).collect())
    } else {
        // NO_REFIT is an empty placeholder for the refit folder
        figs = FIGURES(src, file("${projectDir}/NO_REFIT"))
        CHECK(figs.mix(port).collect())
        BUILD_PAGE(figs.mix(port).collect())
    }
}
