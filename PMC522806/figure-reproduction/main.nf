// Reproduce PMC522806 (Liu, Cui, Jiang and Ma 2004, "A combinational feature selection and ensemble
// neural network method for classification of gene expression data"). The authors' Matlab code was
// never released; the method is the package PMC522806/package (cfsenn), implemented from the paper.
//
// Run from the repository root:
//   nextflow run PMC522806/figure-reproduction/main.nf --outdir results [--full] [--sources DIR]
//
// Steps: download the seven Kent Ridge datasets and check their SHA-256; run every classification
// (test sets over five seeds, LOOCV, 10-fold CV over three fold assignments, 20 random DLBCL 22/25
// splits, the Discussion's controls and the hypothesis tests); redraw Figs 3 and 4 on the published
// pixel grid; compare with the paper; check the package; write results.json and the results page;
// check the run against the committed outputs.
//
// Without --full, the slow experiments (ovarian and prostate-training LOOCV, and the LOOCV
// hypothesis tests: about 3.5 of 4.5 CPU-hours) rerun every 25th fold and take the rest from the
// committed output/runs; the reruns must equal the committed folds. With --full every fold runs
// (about 75 minutes on 4 cores).

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.full = false
params.jobs = 4

params.pipe = "${projectDir}/pipeline"
params.published = "${projectDir}/published"
params.committed = "${projectDir}/output"
params.notes = "${projectDir}/results_notes.json"
params.pkg = "${projectDir}/../package"
params.pkgsrc = "${projectDir}/../package/src"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process RUN {
    publishDir "${params.outdir}", mode: 'copy', pattern: '{runs,*.json}'
    cpus params.jobs
    input:
    path downloads
    output:
    path 'runs'
    path 'accuracy.json', emit: accuracy
    path 'datasets.json', emit: datasets
    path 'reran.json'
    script:
    """
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/experiments.py ${downloads} . --jobs ${params.jobs} \
        ${params.full ? '' : '--reuse ' + params.committed + '/runs'}
    """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path accuracy
    output:
    path 'fig*'
    script:
    """
    ${params.python} ${params.pipe}/figures.py ${params.published} ${accuracy} .
    """
}

process COMPARE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path accuracy
    path datasets
    path figs
    output:
    path 'comparison.json', emit: comparison
    path 'tables.json', emit: tables
    script:
    """
    mkdir -p r && cp ${accuracy} ${datasets} figures.json r/
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/compare.py r .
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path pkg  // the package folder, staged as a copy, so a change to it reruns this step
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${params.pipe}/check_package.py ${pkg} --json package.json || true
    test -s package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path comparison
    path pkg
    path notes  // results_notes.json, so an edit to it reruns this step
    output:
    path 'results.json'
    script:
    """
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py ${notes} ${comparison} results.json \
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
    path notes
    output:
    path 'site', emit: site
    path 'report.md'
    script:
    """
    ${params.python} ${params.pipe}/build_page.py ${results} f ${params.published} site ${tables}
    ${params.python} ${params.pipe}/check_results.py ${results} --markdown --root ${projectDir}/.. > report.md || true
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path comparison
    path tables
    path site
    path runs
    path 'f/*'
    output:
    path 'check.json'
    script:
    """
    mkdir -p fresh && cp f/* fresh/ && cp -r ${runs} fresh/runs && cp ${comparison} ${tables} ${results} fresh/
    ${params.python} ${params.pipe}/check_reproduction.py fresh ${params.committed} ${projectDir}/.. check.json
    cat check.json >> report.md || true
    """
}

workflow {
    dl = FETCH()
    run = RUN(dl)
    fg = FIGURES(run.accuracy)
    cmp = COMPARE(run.accuracy, run.datasets, fg.collect())
    pk = PACKAGE(Channel.fromPath(params.pkg, type: 'dir'))
    notes = Channel.fromPath(params.notes)
    res = RESULTS(cmp.comparison, pk, notes)
    pg = PAGE(res, cmp.tables, fg.collect(), Channel.fromPath(params.notes))
    CHECK(res, cmp.comparison, cmp.tables, pg.site, run[0], fg.mix(run.accuracy, run.datasets).flatten().collect())
}
