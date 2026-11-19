// Reproduce PMC507884 (Szabo et al. 2004, "Statistical modeling for selecting housekeeper genes").
// The authors' code was never released; the method is the R package PMC507884/package (hkselect),
// rebuilt from the paper's text.
//
// Run from the repository root (R with the packages of pipeline/install_r.sh, Python with
// requirements.txt):
//   nextflow run PMC507884/figure-reproduction/main.nf --outdir results [--full] [--sources DIR] [--cpus N]
//
// Default (CI, about 5 minutes): download the breast cancer data, Vandesompele et al.'s data and the
// R file of Fig. 3 and check their SHA-256; install hkselect from the repository; fit every model
// and redo every table and claim; draw Figs 1-3 on the published pixel grid and score them with
// negative controls; check the package; write results.json and the results page; check the run
// against the committed outputs. The variant fits that test why Table 3 differs (about 100 fits,
// 20 minutes on one core) are read from output/hypotheses.json.
// --full: rerun those variant fits too.

params.outdir = 'results'
params.python = 'python3'
params.rscript = 'Rscript'
params.sources = null
params.full = false
params.cpus = 4

params.pipe = "${projectDir}/pipeline"
params.published = "${projectDir}/published"
params.committed = "${projectDir}/output"
params.notes = "${projectDir}/results_notes.json"
params.pkg = "${projectDir}/../package"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process INSTALL {
    output:
    path 'rlib'
    script:
    """
    mkdir rlib
    R CMD INSTALL --no-test-load --library=rlib ${params.pkg} > install.log 2>&1 || { cat install.log; exit 1; }
    """
}

process PREPARE {
    input:
    path downloads
    output:
    path 'data'
    script:
    """
    ${params.rscript} ${params.pipe}/prepare_data.R ${downloads} data
    """
}

process ANALYSIS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path data
    path rlib
    output:
    path 'analysis.json', emit: analysis
    path 'fig3_bars.csv', emit: bars
    script:
    """
    R_LIBS=rlib ${params.rscript} ${params.pipe}/analysis.R ${data} .
    """
}

// Variant fits behind Table 3's cause: rerun with --full, read from output/ otherwise.
process HYPOTHESES {
    publishDir "${params.outdir}", mode: 'copy'
    cpus params.cpus
    input:
    path data
    path rlib
    output:
    path 'hypotheses.json'
    script:
    if (params.full)
        """
        R_LIBS=rlib ${params.rscript} ${params.pipe}/hypotheses.R ${data} hypotheses.json ${task.cpus}
        """
    else
        """
        cp ${params.committed}/hypotheses.json .
        """
}

process READ_PUBLISHED {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'published_fig3.json'
    script:
    """
    ${params.python} ${params.pipe}/read_published.py ${downloads}/MOESM5.eps published_fig3.json
    """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path data
    path bars
    output:
    path 'fig*.png', emit: png
    path 'figures.json', emit: json
    script:
    """
    mkdir figdata && cp ${data}/*.csv ${bars} figdata/
    ${params.python} ${params.pipe}/figures.py ${params.published} figdata .
    """
}

process COMPARE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path analysis
    path figures
    path pubfig3
    output:
    path 'comparison.json', emit: comparison
    path 'tables.json', emit: tables
    script:
    """
    ${params.python} ${params.pipe}/compare.py ${analysis} ${figures} ${pubfig3} ${params.pipe}/paper_values.json .
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    bash ${params.pipe}/check_r_package.sh ${params.pkg} package.json
    test -s package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path comparison
    path hypotheses
    path pkg
    path rlib
    output:
    path 'results.json'
    script:
    """
    R_LIBS=rlib ${params.rscript} ${params.pipe}/env_versions.R env.json
    ${params.python} ${params.pipe}/env_versions_py.py env.json
    ${params.python} ${params.pipe}/build_results.py ${params.notes} ${comparison} ${hypotheses} results.json \
        --package ${pkg} --inputs ${params.pipe}/fetch_inputs.sh --env env.json --date \$(date -u +%F)
    ${params.python} ${params.pipe}/check_results.py results.json --write --root ${projectDir}/..
    """
}

process PAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path tables
    path 'f/*'
    output:
    path 'site', emit: site
    path 'report.md'
    script:
    """
    ${params.python} ${params.pipe}/build_page.py ${results} ${tables} f ${params.published} site
    ${params.python} ${params.pipe}/check_results.py ${results} --markdown --root ${projectDir}/.. > report.md || true
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path analysis
    path bars
    path hypotheses
    path pubfig3
    path figures
    path comparison
    path tables
    path 'f/*'
    output:
    path 'check.json'
    script:
    """
    mkdir -p fresh && cp f/* ${results} ${analysis} ${bars} ${hypotheses} ${pubfig3} ${figures} ${comparison} ${tables} fresh/
    ${params.python} ${params.pipe}/check_reproduction.py fresh ${params.committed} ${projectDir}/.. check.json
    """
}

workflow {
    dl = FETCH()
    lib = INSTALL()
    data = PREPARE(dl)
    an = ANALYSIS(data, lib)
    hy = HYPOTHESES(data, lib)
    pf = READ_PUBLISHED(dl)
    figs = FIGURES(data, an.bars)
    cmp = COMPARE(an.analysis, figs.json, pf)
    pk = PACKAGE()
    res = RESULTS(cmp.comparison, hy, pk, lib)
    PAGE(res, cmp.tables, figs.png.collect())
    CHECK(res, an.analysis, an.bars, hy, pf, figs.json, cmp.comparison, cmp.tables, figs.png.collect())
}
