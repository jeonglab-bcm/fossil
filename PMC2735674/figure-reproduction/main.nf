#!/usr/bin/env nextflow

/*
 * Reproduction of Bleakley and Yamanishi (2009), doi:10.1093/bioinformatics/btp433:
 * bipartite local models for drug-target interaction prediction.
 *
 *   nextflow run PMC2735674/figure-reproduction/main.nf --outdir results
 *
 * The default run reads the committed leave-one-out score matrices for the enzyme, ion channel
 * and GPCR datasets and recomputes the nuclear-receptor ones, then rebuilds every table, figure,
 * prediction list, score and page from them. `--full` recomputes all four datasets from the
 * benchmark data, which is a few hours of CPU: the method fits one local support vector machine
 * for every drug-target pair in each direction.
 *
 * Options:
 *   --outdir DIR     where the run writes (default: results)
 *   --sources DIR    reuse already downloaded inputs instead of fetching them
 *   --full           recompute every score matrix, not only the nuclear-receptor ones
 *   --cpus N         processes the score step uses (default: 4)
 *   --skip_package   do not build and check the Python package (it needs network access)
 */

nextflow.enable.dsl = 2

params.outdir = 'results'
params.sources = ''
params.full = false
params.cpus = 4
params.skip_package = false

paper = "${projectDir}/.."
pipeline = "${projectDir}/pipeline"
params_dir = "${projectDir}/pipeline/params"

process FETCH {
    publishDir "${params.outdir}", mode: 'copy'

    output:
    path 'inputs'

    script:
    def sources = params.sources ? "--sources ${file(params.sources).toAbsolutePath()}" : ''
    """
    bash ${pipeline}/fetch_inputs.sh inputs ${sources}
    """
}

process SCORES {
    cpus params.cpus
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path inputs

    output:
    path 'scores'

    script:
    def full = params.full ? '--full' : ''
    """
    python3 ${pipeline}/run_scores.py --data ${inputs} --out scores \
        --committed ${projectDir}/output/scores --processes ${task.cpus} ${full}
    """
}

process PUBLISHED {
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path inputs

    output:
    path 'figure1_published.json', emit: curves
    path 'figure-1.png', emit: image

    script:
    """
    python3 ${pipeline}/published.py --pdf ${inputs}/PMC2735674.1.pdf \
        --out-image figure-1.png --out-json figure1_published.json
    """
}

process TABLES {
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path scores

    output:
    path 'tables.json'

    script:
    """
    python3 ${pipeline}/tables.py --scores ${scores} \
        --published ${params_dir}/published_tables.json --out tables.json
    """
}

process FIGURE1 {
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path scores
    path curves
    path image

    output:
    path 'fig1*.png', emit: renders
    path 'figure1_comparison.json', emit: comparison

    script:
    """
    python3 ${pipeline}/figure1.py --scores ${scores} --published ${curves} \
        --page-image ${image} --out-dir .
    """
}

process PREDICTIONS {
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path scores

    output:
    path 'predictions.json', emit: report
    path 'fig2_ours.png', emit: render

    script:
    """
    python3 ${pipeline}/predictions.py --scores ${scores} --published ${params_dir} --out-dir .
    """
}

process CLAIMS {
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path tables
    path comparison

    output:
    path 'claims.json'

    script:
    """
    python3 ${pipeline}/claims.py --tables ${tables} \
        --published ${params_dir}/published_tables.json --figure1 ${comparison} --out claims.json
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'

    output:
    path 'package.json'

    script:
    """
    python3 ${pipeline}/check_package.py ${paper}/package --json package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path outputs
    path inputs
    path package_report

    output:
    path 'results.json'

    script:
    def package_argument = package_report.name == 'no_package.json' ? '' : "--package-report ${package_report}"
    """
    python3 ${pipeline}/build_results.py --out-dir . --notes ${projectDir}/results_notes.json \
        --inputs ${inputs}/checksums.sha256 ${package_argument} --out results.json
    python3 ${pipeline}/check_results.py results.json --write --skip-files
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path results
    path outputs

    output:
    path 'report.md'

    script:
    def full = params.full ? '--full' : ''
    """
    python3 ${pipeline}/check_reproduction.py ${results} . ${projectDir}/output report.md ${full}
    """
}

process BUILD_PAGE {
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path results
    path outputs

    output:
    path 'site'

    script:
    """
    mkdir -p site
    python3 ${pipeline}/build_page.py --results ${results} --output . \
        --published ${projectDir}/published --template ${pipeline}/page_template.html \
        --out site/index.html
    """
}

workflow {
    inputs = FETCH()
    scores = SCORES(inputs)
    PUBLISHED(inputs)
    TABLES(scores)
    FIGURE1(scores, PUBLISHED.out.curves, PUBLISHED.out.image)
    PREDICTIONS(scores)
    CLAIMS(TABLES.out, FIGURE1.out.comparison)

    if (params.skip_package) {
        package_report = Channel.fromPath("${params_dir}/no_package.json")
    } else {
        package_report = PACKAGE()
    }

    outputs = TABLES.out
        .mix(FIGURE1.out.renders.flatten(), FIGURE1.out.comparison, PUBLISHED.out.curves,
             PREDICTIONS.out.report, PREDICTIONS.out.render, CLAIMS.out)
        .collect()

    RESULTS(outputs, inputs, package_report)
    CHECK(RESULTS.out, outputs)
    BUILD_PAGE(RESULTS.out, outputs)
}
