// Reproduce PMC1523355 (Hayward, Kent, Vijan and Hofer 2006, "Multivariable risk prediction can greatly
// enhance the statistical power of clinical trial subgroup analysis"). The authors' simulation code is
// lost; the method is the package PMC1523355/package (stratpower), implemented from the paper's text.
//
// Run from the repository root, with the pinned requirements and the package installed:
//   pip install -r PMC1523355/figure-reproduction/requirements.txt ./PMC1523355/package
//   nextflow run PMC1523355/figure-reproduction/main.nf --outdir results [--extract] [--sources DIR]
//
// Every step runs every time (a few minutes): every simulated setting of Tables 1-5 and Fig. 1B at
// 20,000 trials, a second run, the hypothesis variants and the finite-population runs; the comparison
// with every printed value; Fig. 1A drawn on the published axes and scored; the claims; the package check;
// results.json, the results page and the check against the committed outputs.
// --extract: read the printed tables again from the article XML and check them against the committed
//   output/published_values.json.
// --sources DIR: use local copies of the downloads.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.extract = false

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
        ${params.python} ${params.pipe}/extract_published.py ${downloads}/PMC1523355.1.xml published_values.json --check ${params.committed}/published_values.json
        """
    else
        """
        cp ${params.committed}/published_values.json published_values.json
        """
}

process SIMULATE {
    publishDir "${params.outdir}/output", mode: 'copy'
    output:
    path 'simulation.json'
    script:
    """
    ${params.python} ${params.pipe}/simulate.py simulation.json
    """
}

process COMPARE {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path published
    path sim
    output:
    path 'comparison.json'
    script:
    """
    ${params.python} ${params.pipe}/compare.py ${published} ${sim} comparison.json
    """
}

process FIGURES {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path downloads
    path sim
    output:
    path 'fig*.png'
    path 'figures.json'
    script:
    """
    ${params.python} ${params.pipe}/figures.py ${downloads}/1471-2288-6-18-1.jpg ${sim} .
    """
}

process CLAIMS {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path published
    path sim
    path comparison
    output:
    path 'claims.json'
    script:
    """
    ${params.python} ${params.pipe}/claims.py ${published} ${sim} ${comparison} claims.json
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
    cp ${published} ${sim} ${comparison} ${figures} ${figjson} ${claims} ${pkg} run/output/
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py run/output results.json --environment env.json
    cp results.json run/results.json
    ${params.python} ${params.pipe}/make_results_check.py run/output results_check.json
    cp results_check.json run/results_check.json
    ${params.python} ${params.pipe}/build_page.py results.json run/output ${projectDir}/published site
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
    comparison = COMPARE(published, sim)
    (figures, figjson) = FIGURES(downloads, sim)
    claims = CLAIMS(published, sim, comparison)
    pkg = PACKAGE()
    (results, site, report, check, rcheck) = RESULTS(published, sim, comparison, figures, figjson, claims, pkg)
    CHECK(check)
}
