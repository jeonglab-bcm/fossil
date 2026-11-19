// Reproduce PMC3196500 (Thorlund et al. 2011, "The number of patients and events required to limit the
// risk of overestimation of intervention effects in meta-analysis: a simulation study"). The authors'
// simulation code was never released; the method is the package PMC3196500/package (oisim), implemented
// from the paper's text and Appendices S1 and S2.
//
// Run from the repository root, with the pinned requirements and the package installed:
//   pip install -r PMC3196500/figure-reproduction/requirements.txt ./PMC3196500/package
//   nextflow run PMC3196500/figure-reproduction/main.nf --outdir results [--extract] [--sources DIR]
//
// Every step runs every time (about 4 minutes on 4 cores): the downloads and their SHA-256, the check that
// the committed published figures are the downloaded ones, all 36 scenarios (20,000 meta-analyses of 100
// trials each) with a second run and two hypothesis variants, every printed cell of Tables 1-4, S3 and S4,
// every panel of Fig. 2 and Figs S1-S12 with its controls, the claims, the package check, results.json, the
// results page and the check against the committed outputs.
// --extract: read the printed tables again from the article XML and the supplement's Word files (needs
//   LibreOffice, --soffice) instead of the committed output/published_values.json.
// --sources DIR: use local copies of the downloads.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.extract = false
params.soffice = 'soffice'
params.workers = 4

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.published = "${projectDir}/published"
params.paper = "${projectDir}/.."

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    ${params.python} ${params.pipe}/verify_published.py downloads ${params.published}
    """
}

process PUBLISHED_VALUES {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path downloads
    output:
    path 'published_values.json'
    script:
    if (params.extract)
        """
        ${params.python} ${params.pipe}/extract_published.py ${downloads}/PMC3196500.1.xml ${downloads}/pone.0025491.s016.doc ${downloads}/pone.0025491.s017.doc published_values.json --soffice ${params.soffice}
        cmp published_values.json ${params.committed}/published_values.json
        """
    else
        """
        cp ${params.committed}/published_values.json published_values.json
        """
}

process SIMULATE {
    publishDir "${params.outdir}/output", mode: 'copy'
    cpus params.workers
    output:
    path 'simulation.json'
    script:
    """
    ${params.python} ${params.pipe}/simulate.py simulation.json --workers ${params.workers}
    """
}

process TABLES {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path published
    path sim
    output:
    path 'tables.json'
    script:
    """
    ${params.python} ${params.pipe}/tables.py ${published} ${sim} tables.json
    """
}

process FIGURES {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path sim
    output:
    path 'fig*.png'
    path 'figures.json'
    script:
    """
    ${params.python} ${params.pipe}/figures.py ${params.published} ${sim} .
    """
}

process CLAIMS {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path published
    path tables
    path sim
    output:
    path 'claims.json'
    script:
    """
    ${params.python} ${params.pipe}/claims.py ${published} ${tables} ${sim} claims.json
    """
}

process PACKAGE {
    publishDir "${params.outdir}/output", mode: 'copy'
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
    path tables
    path figures
    path figjson
    path claims
    path pkg
    output:
    path 'results.json'
    path 'site'
    path 'report.md'
    path 'check.json'
    path 'results_check.json'
    script:
    """
    mkdir -p run/output
    cp ${published} ${sim} ${tables} ${figures} ${figjson} ${claims} ${pkg} run/output/
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py run/output results.json --environment env.json
    cp results.json run/results.json
    ${params.python} ${params.pipe}/make_results_check.py run/output results_check.json
    cp results_check.json run/results_check.json
    ${params.python} ${params.pipe}/build_page.py results.json run/output ${params.published} site
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
    sim = SIMULATE()
    tables = TABLES(published, sim)
    (figures, figjson) = FIGURES(sim)
    claims = CLAIMS(published, tables, sim)
    pkg = PACKAGE()
    (results, site, report, check, rcheck) = RESULTS(published, sim, tables, figures, figjson, claims, pkg)
    CHECK(check)
}
