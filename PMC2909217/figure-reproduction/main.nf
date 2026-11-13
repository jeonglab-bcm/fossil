// Reproduce PMC2909217 (You, Yin, Han, Huang and Zhou 2010, "A semi-supervised learning approach to
// predict synthetic genetic interactions by combining functional and topological properties of
// functional gene network"). The authors' program (GeneticInterPred) is lost; the method is the
// package PMC2909217/package (fgnssl), rebuilt from the paper (see README.md).
//
// Run from the repository root:
//   nextflow run PMC2909217/figure-reproduction/main.nf --outdir results [--sources DIR] [--jobs 4] [--update]
//
// --update: write the report but do not fail when the run differs from the committed outputs (to
//   refresh them after an intended change: copy results/ into output/ and results.json up).
//
// FETCH downloads the inputs from SGD's archive on AWS S3 and checks their SHA-256; PREPARE builds
// the gold standard, the networks' edges and the expression matrix; FEATURES builds the weighted FGN
// and the binary network and the 18 features of every pair; EXPERIMENTS reruns the cross-validation
// behind Figs 2-5; KS recomputes Table 1 and the densities of Fig. 6; HYPOTHESES tests one change at
// a time; FIGURES draws and scores Figs 2-6 on the published pixel grids; CLAIMS computes the claims
// in the text; PACKAGE checks the package from a fresh install; RESULTS writes results.json, checks
// the run against the committed outputs (report.md) and builds the results page.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.jobs = 4
params.update = false

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.pkgsrc = "${projectDir}/../package/src"
params.paper = "${projectDir}/.."

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process PREPARE {
    publishDir "${params.outdir}", mode: 'copy', pattern: 'counts.json'
    input:
    path downloads
    output:
    path 'inputs', emit: inputs
    path 'counts.json', emit: counts
    script:
    """
    ${params.python} ${params.pipe}/prepare_inputs.py ${downloads} inputs
    cp inputs/counts.json counts.json
    """
}

process FEATURES {
    publishDir "${params.outdir}", mode: 'copy', pattern: 'network.json'
    input:
    path inputs
    output:
    path 'features', emit: features
    path 'network.json', emit: network
    script:
    """
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/features.py ${inputs} features
    cp features/network.json network.json
    """
}

process EXPERIMENTS {
    cpus params.jobs
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path features
    output:
    path 'roc.json'
    script:
    """
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/experiments.py ${features}/features.npz roc.json --jobs ${params.jobs}
    """
}

process KS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path features
    output:
    path 'table1.json', emit: table
    path 'densities.json', emit: densities
    script:
    """
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/ks_tests.py ${features}/features.npz .
    """
}

process HYPOTHESES {
    cpus params.jobs
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path inputs
    path features
    output:
    path 'hypotheses.json'
    script:
    """
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/hypotheses.py ${inputs} ${features}/features.npz hypotheses.json ${params.jobs}
    """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path roc
    path densities
    output:
    path 'comparison.json', emit: comparison
    path 'figures', emit: figures
    script:
    """
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/figures.py ${projectDir}/published ${params.pipe}/calibration.json ${roc} ${densities} .
    """
}

process CLAIMS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path roc
    path table
    path inputs
    path features
    output:
    path 'claims.json'
    script:
    """
    ${params.python} ${params.pipe}/claims.py ${roc} ${table} ${inputs}/counts.json ${features}/network.json ${params.pipe}/published_values.json claims.json
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${params.pipe}/check_package.py ${params.paper}/package --json package.json || true
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path inputs
    path features
    path roc
    path table
    path densities
    path hypotheses
    path comparison
    path figures
    path claims
    path package_json
    output:
    path 'results.json', emit: results
    path 'page.json'
    path 'report.md', emit: report
    path 'site', emit: site
    script:
    """
    mkdir run
    cp ${inputs}/counts.json ${features}/network.json ${roc} ${table} ${densities} ${hypotheses} ${comparison} ${claims} ${package_json} run/
    cp -r ${figures} run/figures
    ${params.python} ${params.pipe}/build_results.py run ${projectDir}/results_notes.json results.json
    cp run/page.json page.json
    ${params.python} ${params.pipe}/check_reproduction.py results.json run ${params.committed} ${params.paper}/results.json report.md ${params.update ? '|| true' : ''}
    ${params.python} ${params.pipe}/build_page.py results.json run ${projectDir}/published site/index.html
    """
}

workflow {
    dl = FETCH()
    pr = PREPARE(dl)
    inp = pr.inputs
    ft = FEATURES(inp).features
    roc = EXPERIMENTS(ft)
    ks = KS(ft)
    hy = HYPOTHESES(inp, ft)
    fg = FIGURES(roc, ks.densities)
    cl = CLAIMS(roc, ks.table, inp, ft)
    pk = PACKAGE()
    RESULTS(inp, ft, roc, ks.table, ks.densities, hy, fg.comparison, fg.figures, cl, pk)
}
