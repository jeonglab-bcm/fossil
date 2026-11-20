// Reproduce PMC4079617 (Chen, Shi, Qian and Azen 2014, "Comparison of robustness to outliers between robust
// poisson models and log-binomial models when estimating relative risks for common binary outcomes: a simulation
// study"). The authors' SAS 9.2 program and the COPY macro are lost; the method is the package
// PMC4079617/package (robustrr), implemented from the paper's text.
//
// Run from the repository root, with the pinned requirements and the package installed:
//   pip install -r PMC4079617/figure-reproduction/requirements.txt ./PMC4079617/package
//   nextflow run PMC4079617/figure-reproduction/main.nf --outdir results [--sources DIR] [--jobs N]
// Needs pdftotext and pdfimages (poppler-utils) for the published values and figure.
//
// Every step runs every time (about 8 minutes on 4 cores): the downloads; the printed values and Fig. 1 read
// from them and checked against the committed copies; the whole simulation study (24 scenarios x 3
// contamination rates x 1,000 replicates at n = 1500 and n = 500, a second run with other seeds, and the
// hypothesis variants of the contamination rule and the fitted model); every printed cell of Tables 1-3 and
// A1-A3; Fig. 1 drawn on the published picture and scored; the claims of the text; the fits against statsmodels
// and an independent maximizer; the package check; results.json; the results page; and the check of the fresh
// run against the committed outputs.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.jobs = 0

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.paper = "${projectDir}/.."

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process PUBLISHED_VALUES {
    publishDir "${params.outdir}/figure-reproduction/output", mode: 'copy'
    input:
    path downloads
    output:
    path 'published_values.json'
    script:
    """
    ${params.python} ${params.pipe}/extract_published.py ${downloads}/PMC4079617.1.xml ${downloads}/1471-2288-14-82-S1.pdf \
        ${downloads}/1471-2288-14-82-S2.pdf published_values.json --check ${params.committed}/published_values.json
    """
}

process PUBLISHED_FIGURE {
    input:
    path downloads
    output:
    path 'fig1_published.png'
    script:
    """
    ${params.python} ${params.pipe}/published_figure.py ${downloads}/PMC4079617.1.pdf fig1_published.png --check ${projectDir}/published/fig1.png
    """
}

process SIMULATE {
    publishDir "${params.outdir}/figure-reproduction/output", mode: 'copy'
    output:
    path 'simulation.json'
    script:
    """
    ${params.python} ${params.pipe}/simulate.py simulation.json ${params.jobs ? '--jobs ' + params.jobs : ''}
    """
}

process COMPARE {
    publishDir "${params.outdir}/figure-reproduction/output", mode: 'copy'
    input:
    path published
    path sim
    output:
    path 'comparison.json'
    path 'tables.csv'
    script:
    """
    ${params.python} ${params.pipe}/compare.py ${published} ${sim} comparison.json --csv tables.csv
    """
}

process CLAIMS {
    publishDir "${params.outdir}/figure-reproduction/output", mode: 'copy'
    input:
    path published
    path sim
    output:
    path 'claims.json'
    script:
    """
    ${params.python} ${params.pipe}/claims.py ${published} ${sim} claims.json
    """
}

process FIGURE {
    publishDir "${params.outdir}/figure-reproduction/output", mode: 'copy'
    input:
    path fig1
    path published
    path sim
    output:
    path 'fig'
    script:
    """
    ${params.python} ${params.pipe}/figure.py ${fig1} ${sim} ${published} fig
    """
}

process CROSSCHECK {
    publishDir "${params.outdir}/figure-reproduction/output", mode: 'copy'
    output:
    path 'crosscheck.json'
    script:
    """
    ${params.python} ${params.pipe}/crosscheck.py crosscheck.json
    """
}

process PACKAGE {
    publishDir "${params.outdir}/figure-reproduction/output", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${params.pipe}/check_package.py ${params.paper}/package --json package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path published
    path sim
    path comparison
    path tables
    path claims
    path fig
    path cross
    path pkg
    path fig1
    output:
    path 'results.json'
    path 'site'
    path 'report.md'
    path 'check.json'
    path 'results_check.json'
    script:
    """
    out=run/figure-reproduction/output
    mkdir -p \$out
    cp ${published} ${sim} ${comparison} ${tables} ${claims} ${cross} ${pkg} \$out/
    cp ${fig}/* \$out/
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py \$out results.json --environment env.json
    cp results.json run/results.json
    ${params.python} ${params.pipe}/make_results_check.py \$out results_check.json
    cp results_check.json run/results_check.json
    ${params.python} ${params.pipe}/build_page.py run/results.json \$out ${fig1} site
    cp -r site run/site
    ${params.python} ${params.pipe}/check_reproduction.py run ${params.paper} check.json report.md || true
    """
}

process CHECK {
    input:
    path check
    script:
    """
    ${params.python} -c "import json, sys; c = json.load(open('${check}')); print('passed' if c['passed'] else 'FAILED: ' + ', '.join(k for k, v in c.items() if isinstance(v, dict) and not v['passed'])); sys.exit(0 if c['passed'] else 1)"
    """
}

workflow {
    downloads = FETCH()
    published = PUBLISHED_VALUES(downloads)
    fig1 = PUBLISHED_FIGURE(downloads)
    sim = SIMULATE()
    (comparison, tables) = COMPARE(published, sim)
    claims = CLAIMS(published, sim)
    fig = FIGURE(fig1, published, sim)
    cross = CROSSCHECK()
    pkg = PACKAGE()
    (results, site, report, check, rcheck) = RESULTS(published, sim, comparison, tables, claims, fig, cross, pkg, fig1)
    CHECK(check)
}
