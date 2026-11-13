// Reproduce PMC2853684 (Navlakha and Kingsford 2010, "The power of protein interaction networks for
// associating genes with diseases"). The authors released their predictions but not their code; the
// methods are the package PMC2853684/package (diseasenet), rebuilt from the paper, plus MCL 14-137 and
// Weka 3.6.6 for the consensus Random Forest (see README.md).
//
// Run from the repository root:
//   nextflow run PMC2853684/figure-reproduction/main.nf --outdir results [--sources DIR]
// About 6 minutes on 4 cores: downloads (35 MB), the methods rerun on HPRD and OPHID and on every
// gene-disease pair without linkage intervals, the consensus forest, the comparison with every value
// the paper prints or draws, the renders, the package check and the check against the committed outputs.

params.outdir = 'results'
params.python = 'python3'
params.java = 'java'
params.mcl = 'mcl'
params.sources = null

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.published = "${projectDir}/published"
params.pkgsrc = "${projectDir}/../package/src"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process READ_PUBLISHED {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'published_values.json'
    script:
    """
    ${params.python} ${params.pipe}/read_published.py ${downloads}/paper/PMC2853684.1.pdf ${downloads}/paper/btq076_1.pdf published_values.json
    """
}

process MCL {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'mcl'
    script:
    """
    bash ${params.pipe}/run_mcl.sh ${downloads}/data mcl ${params.mcl}
    """
}

process CONSENSUS {
    publishDir "${params.outdir}", mode: 'copy'
    cpus 2
    input:
    path downloads
    output:
    path 'consensus.json'
    script:
    """
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/consensus.py ${downloads}/data ${downloads}/weka.jar consensus.json --java ${params.java}
    """
}

process ANALYSIS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path mcl
    path consensus
    output:
    path 'analysis.json'
    script:
    """
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/analysis.py ${downloads}/data ${mcl} analysis.json --consensus ${consensus}
    """
}

process COMPARE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path analysis
    path published
    output:
    path 'comparison.json', emit: comparison
    path 'figures', emit: figures
    script:
    """
    ${params.python} ${params.pipe}/compare.py ${analysis} ${published} comparison.json
    MPLBACKEND=Agg ${params.python} ${params.pipe}/render.py ${analysis} ${published} ${params.published} figures
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${params.pipe}/check_package.py ${projectDir}/../package --json package.json || true
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path published
    path mcl
    path consensus
    path analysis
    path comparison
    path figures
    path package_json
    output:
    path 'results.json', emit: results
    path 'report.md', emit: report
    path 'site', emit: site
    script:
    """
    mkdir run && cp -r ${published} ${mcl} ${consensus} ${analysis} ${comparison} ${figures} ${package_json} run/
    ${params.python} ${params.pipe}/build_results.py run results.json
    ${params.python} ${params.pipe}/check_reproduction.py results.json run ${params.committed} report.md
    ${params.python} ${params.pipe}/build_page.py results.json run ${params.published} site/index.html
    """
}

workflow {
    dl = FETCH()
    pub = READ_PUBLISHED(dl)
    mc = MCL(dl)
    cons = CONSENSUS(dl)
    an = ANALYSIS(dl, mc, cons)
    cmp = COMPARE(an, pub)
    pk = PACKAGE()
    RESULTS(pub, mc, cons, an, cmp.comparison, cmp.figures, pk)
}
