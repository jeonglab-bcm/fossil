// Reproduce PMC2430201 (Friedrich, Adhikari and Beyene 2008, "The ratio of means method as an alternative
// to mean differences for analyzing continuous outcome variables in meta-analysis: a simulation study").
// The authors' SAS 8.2 programs are lost; the method is the package PMC2430201/package (rommeta),
// implemented from the paper's text.
//
// Run from the repository root, with the pinned requirements and the package installed:
//   pip install -r PMC2430201/figure-reproduction/requirements.txt ./PMC2430201/package
//   nextflow run PMC2430201/figure-reproduction/main.nf --outdir results [--extract] [--metafor] [--sources DIR]
//
// Every step runs every time (about 3 minutes): the whole simulation study (216 scenarios x 10,000
// meta-analyses, a second run and the hypothesis variants), the comparison with every printed cell of
// Tables 3-8, the claims of the text, the check of rommeta's pooling against metafor's committed results,
// the package check, results.json, the results page and the check against the committed outputs.
// --extract: read the printed tables again from the article XML and check them against the committed
//   output/published_values.json.
// --metafor: rerun R's metafor (needs R and metafor, --rscript) and check it gives reference/metafor_replicates.csv.
// --sources DIR: use a local copy of the download.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.extract = false
params.metafor = false
params.rscript = 'Rscript'

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
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path downloads
    output:
    path 'published_values.json'
    script:
    if (params.extract)
        """
        ${params.python} ${params.pipe}/extract_published.py ${downloads}/PMC2430201.1.xml published_values.json --check ${params.committed}/published_values.json
        """
    else
        """
        cp ${params.committed}/published_values.json published_values.json
        """
}

process SIMULATE {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path published
    output:
    path 'simulation.json'
    script:
    """
    ${params.python} ${params.pipe}/simulate.py ${published} simulation.json
    """
}

process COMPARE {
    publishDir "${params.outdir}/output", mode: 'copy'
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
    publishDir "${params.outdir}/output", mode: 'copy'
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

process CROSSCHECK {
    publishDir "${params.outdir}/output", mode: 'copy'
    output:
    path 'crosscheck.json'
    script:
    """
    ${params.python} ${params.pipe}/crosscheck.py ${projectDir}/reference/metafor_replicates.csv crosscheck.json ${params.metafor ? '--metafor --rscript ' + params.rscript : ''}
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
    path comparison
    path tables
    path claims
    path cross
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
    cp ${published} ${sim} ${comparison} ${tables} ${claims} ${cross} ${pkg} run/output/
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py run/output results.json --environment env.json
    cp results.json run/results.json
    ${params.python} ${params.pipe}/make_results_check.py run/output results_check.json
    cp results_check.json run/results_check.json
    ${params.python} ${params.pipe}/build_page.py results.json run/output site
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
    sim = SIMULATE(published)
    (comparison, tables) = COMPARE(published, sim)
    claims = CLAIMS(published, sim)
    cross = CROSSCHECK()
    pkg = PACKAGE()
    (results, site, report, check, rcheck) = RESULTS(published, sim, comparison, tables, claims, cross, pkg)
    CHECK(check)
}
