// Reproduce PMC4232638 (Martelotto et al. 2014, "Benchmarking mutation effect prediction algorithms using
// functionally validated cancer-related missense mutations", Genome Biology 15:484). The authors' code
// was never released; the method is the package PMC4232638/package (mutbench), rebuilt from the text.
//
// Run from the repository root, with the pinned requirements, poppler-utils and the package installed:
//   pip install -r PMC4232638/figure-reproduction/requirements.txt ./PMC4232638/package
//   nextflow run PMC4232638/figure-reproduction/main.nf --outdir results [--sources DIR]
//
// Every step runs every time (about 3 minutes on 4 cores): the downloads and their SHA-256, the printed
// values read from the article XML and the supplement PDFs, the plotted values read from the vector
// figures, the whole analysis (performance with bootstrap intervals, kappa, clustering, low-confidence
// calls, gene classes, all 11,253 combinations over 1,000 random splits, twice), the comparison, the
// claims, the figures, the package check, results.json, the results page and the check against the
// committed outputs.
// --sources DIR: copy the inputs from a local folder (paper.pdf, PMC4232638.xml, supp/) instead.

params.outdir = 'results'
params.python = 'python3'
params.sources = null

params.pipe = "${projectDir}/pipeline"
params.published = "${projectDir}/published"
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
    publishDir "${params.outdir}/output", mode: 'copy', pattern: 'published_values.json'
    input:
    path downloads
    output:
    path 'published_values.json', emit: values
    path 'published_combinations.json.gz', emit: combinations
    script:
    """
    ${params.python} ${params.pipe}/extract_published.py ${downloads} published_values.json published_combinations.json.gz
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
    ${params.python} ${params.pipe}/read_figures.py ${downloads}/paper.pdf figure_values.json ${downloads}/supp
    """
}

process ANALYZE {
    publishDir "${params.outdir}/output", mode: 'copy', pattern: 'analysis.json'
    input:
    path downloads
    output:
    path 'analysis.json', emit: analysis
    path 'combinations.npz', emit: combinations
    script:
    """
    ${params.python} ${params.pipe}/analyze.py ${downloads}/supp/13059_2014_484_MOESM2_ESM.xlsx analysis.json combinations.npz
    """
}

process COMPARE {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path published
    path pub_comb
    path figvals
    path analysis
    path combinations
    output:
    path 'comparison.json', emit: comparison
    path 'claims.json', emit: claims
    script:
    """
    ${params.python} ${params.pipe}/compare.py ${published} ${figvals} ${params.published}/fig1_reading.json ${analysis} ${combinations} ${pub_comb} comparison.json
    ${params.python} ${params.pipe}/claims.py ${published} ${pub_comb} ${analysis} ${figvals} ${combinations} claims.json
    """
}

process FIGURES {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path downloads
    path figvals
    path analysis
    path combinations
    output:
    path 'fig*.png', emit: pngs
    path 'figures.json', emit: json
    script:
    """
    ${params.python} ${params.pipe}/figures.py ${params.published} ${figvals} ${analysis} ${combinations} ${params.published}/fig1_reading.json ${downloads}/supp/13059_2014_484_MOESM2_ESM.xlsx .
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
    path analysis
    path comparison
    path claims
    path pngs
    path figjson
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
    cp ${published} ${figvals} ${analysis} ${comparison} ${claims} ${pngs} ${figjson} ${pkg} run/output/
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
    pub = PUBLISHED_VALUES(downloads)
    figvals = READ_FIGURES(downloads)
    an = ANALYZE(downloads)
    cmp = COMPARE(pub.values, pub.combinations, figvals, an.analysis, an.combinations)
    figs = FIGURES(downloads, figvals, an.analysis, an.combinations)
    pkg = PACKAGE()
    (results, site, report, check, rcheck) = RESULTS(pub.values, figvals, an.analysis, cmp.comparison, cmp.claims, figs.pngs, figs.json, pkg)
    CHECK(check)
}
