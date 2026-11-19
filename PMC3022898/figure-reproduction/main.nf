// Reproduce PMC3022898 (Reichmann, Gagnon, Horsburgh and Losina 2011, "Evaluation of exposure-specific
// risks from two independent samples: a simulation study"). The authors' SAS 9.2 programs are lost;
// the method is the package PMC3022898/package (esrisk), implemented from the paper's text.
//
// Run from the repository root, with the pinned requirements and the package installed:
//   pip install -r PMC3022898/figure-reproduction/requirements.txt ./PMC3022898/package
//   nextflow run PMC3022898/figure-reproduction/main.nf --outdir results [--extract] [--sources DIR]
//
// Every step runs every time (about a minute): the whole simulation (119 settings x 1,000 pairs of
// samples, with its hypothesis variants and a second run), the comparison with every printed cell of
// Tables 2-4 and S1-S7, the figures, Table 5, the claims, the package check, results.json, the results
// page and the check against the committed outputs.
// --extract: read the printed tables again from the article XML and Additional file 1 (needs
//   LibreOffice, --soffice) and check them against the committed output/published_values.json.
// --sources DIR: use local copies of the downloads.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.extract = false
params.soffice = 'soffice'

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
        ${params.python} ${params.pipe}/extract_published.py ${downloads}/PMC3022898.1.xml ${downloads}/1471-2288-11-1-S1.DOC published_values.json --soffice ${params.soffice}
        """
    else
        """
        cp ${params.committed}/published_values.json published_values.json
        """
}

process READ_FIGURES {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path downloads
    output:
    path 'figure_values.json'
    script:
    """
    ${params.python} ${params.pipe}/read_published.py ${downloads} figure_values.json
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
    path figvals
    path sim
    output:
    path 'comparison.json'
    script:
    """
    ${params.python} ${params.pipe}/compare.py ${published} ${figvals} ${sim} comparison.json
    """
}

process FIGURES {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path downloads
    path figvals
    path sim
    output:
    path 'fig*.png'
    path 'figures.json'
    script:
    """
    ${params.python} ${params.pipe}/figures.py ${downloads} ${figvals} ${sim} .
    """
}

process TABLE5 {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path published
    output:
    path 'table5.json'
    script:
    """
    ${params.python} ${params.pipe}/table5.py ${published} table5.json
    """
}

process CLAIMS {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path published
    path figvals
    path sim
    path t5
    output:
    path 'claims.json'
    script:
    """
    ${params.python} ${params.pipe}/claims.py ${published} ${figvals} ${sim} ${t5} claims.json
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
    path figvals
    path sim
    path comparison
    path figures
    path figjson
    path t5
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
    cp ${published} ${figvals} ${sim} ${comparison} ${figures} ${figjson} ${t5} ${claims} ${pkg} run/output/
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
    figvals = READ_FIGURES(downloads)
    sim = SIMULATE()
    comparison = COMPARE(published, figvals, sim)
    (figures, figjson) = FIGURES(downloads, figvals, sim)
    t5 = TABLE5(published)
    claims = CLAIMS(published, figvals, sim, t5)
    pkg = PACKAGE()
    (results, site, report, check, rcheck) = RESULTS(published, figvals, sim, comparison, figures, figjson, t5, claims, pkg)
    CHECK(check)
}
