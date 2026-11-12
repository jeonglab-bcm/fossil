// Reproduce PMC1274252 (Adie, Adams, Evans, Porteous and Pickard 2005, "Speeding disease gene
// discovery by sequence based candidate prioritization"). PROSPECTR's Perl scorer and its web site
// are gone; its training and test sets, its download page (with the Weka recipe) and a genome-wide
// score dump survive in the Wayback Machine. The method is the package PMC1274252/package
// (prospectr_adtree): a port of Weka 3.4's ADTree and the paper's Figure 2 tree as a scorer.
//
// Run from the repository root:
//   nextflow run PMC1274252/figure-reproduction/main.nf --outdir results [--quick] [--weka_versions]
//
// FETCH      download the archived sets, dump.tab, Additional File 1 and Weka 3.4.3; check SHA-256
// PREPARE    the same sets restricted to Table 1's features (CDS length added)
// WEKA       Weka 3.4.3's ADTree, as the download page gives it, on both feature sets (needs a JDK)
// REPRODUCE  everything else through the package: the port checked against WEKA, Table 3 from the
//            published tree and from the retrained tree, Figure 2 rule by rule, Table 4, Table 2,
//            Figure 1, the claims (--quick skips the 10- and 20-rule cross-validations)
// FIGURES    renders, overlays and pixel scores on the authors' original figure files
// PACKAGE    check_package.py: wheel, fresh install, tests, tutorial rerun
// RESULTS    results.json, the check against the committed outputs (report.md) and the results page
// --weka_versions: also run Weka 3.4.1, 3.4.2 and 3.4.4 and compare (otherwise the committed check)

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.quick = false
params.weka_versions = false

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.published = "${projectDir}/published"
params.pkg = "${projectDir}/../package"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''} ${params.weka_versions ? '--weka-versions' : ''}
    """
}

process PREPARE {
    input:
    path downloads
    output:
    path 't1'
    script:
    """
    PYTHONPATH=${params.pkg}/src ${params.python} ${params.pipe}/prepare.py ${downloads} t1
    """
}

process WEKA {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path t1
    output:
    path 'weka'
    script:
    """
    bash ${params.pipe}/run_weka.sh ${downloads} ${t1} weka
    """
}

process WEKA_VERSIONS {
    input:
    path downloads
    path weka
    output:
    path 'checks'
    script:
    if (params.weka_versions)
        """
        mkdir -p checks v
        for v in 3-4-1 3-4-2 3-4-4; do bash ${params.pipe}/run_weka.sh ${downloads} - v/\$v ${downloads}/weka-\$v.zip; done
        ${params.python} ${params.pipe}/weka_versions.py checks/weka_versions.json ${weka}/main 3.4.1=v/3-4-1/main 3.4.2=v/3-4-2/main 3.4.4=v/3-4-4/main
        """
    else
        """
        mkdir -p checks && cp ${params.committed}/checks/weka_versions.json checks/
        """
}

process REPRODUCE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path t1
    path weka
    output:
    path 'analysis.json'
    script:
    """
    PYTHONPATH=${params.pkg}/src ${params.python} ${params.pipe}/reproduce.py ${downloads} ${t1} ${weka} ${params.published}/published_values.json analysis.json ${params.quick ? '--quick' : ''}
    """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path analysis
    output:
    path 'figures.json', emit: json
    path 'figures', emit: figures
    script:
    """
    PYTHONPATH=${params.pkg}/src ${params.python} ${params.pipe}/figures.py ${params.published} ${analysis} .
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${params.pipe}/check_package.py ${params.pkg} --json package.json || true
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path analysis
    path figures_json
    path figures
    path checks
    path weka
    path package_json
    output:
    path 'results.json', emit: results
    path 'report.md', emit: report
    path 'site', emit: site
    script:
    """
    mkdir run && cp -r ${analysis} ${figures_json} ${figures} ${checks} ${weka} ${package_json} run/
    ${params.python} ${params.pipe}/build_results.py run results.json
    ${params.python} ${params.pipe}/check_reproduction.py results.json run ${params.committed} report.md ${params.quick ? '--quick' : ''}
    ${params.python} ${params.pipe}/build_page.py results.json run ${params.published} site/index.html
    """
}

workflow {
    dl = FETCH()
    t1 = PREPARE(dl)
    wk = WEKA(dl, t1)
    ck = WEKA_VERSIONS(dl, wk)
    an = REPRODUCE(dl, t1, wk)
    fg = FIGURES(an)
    pk = PACKAGE()
    RESULTS(an, fg.json, fg.figures, ck, wk, pk)
}
