// Reproduce PMC3730102 (Lee et al. 2013, "Proteome-wide discovery of mislocated proteins in cancer").
// The authors' CoLP server is gone and no code was released; the method is the package
// PMC3730102/package (condloc), implemented from this paper and from Lee et al. 2008 (DC-kNN).
//
// Run from the repository root:
//   nextflow run PMC3730102/figure-reproduction/main.nf --outdir results [--sources DIR]
//
// Steps: download the inputs (GEO, GO 2007-01, Pathway Commons 2011, Ramani 2005, UniProt, the paper's
// figures) and check their SHA-256; build the gold standard, network and expression (Table 1); train
// DC-kNN with leave-two-out selection (Fig. 2); compute the conditional location maps, mislocations and
// the named proteins (Figs 3 to 6); draw every attempted panel and its overlay; check the package; write
// results.json and the results page; check the run against the committed outputs. About 15 minutes on
// 4 cores.

params.outdir = 'results'
params.python = 'python3'
params.sources = null

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.notes = "${projectDir}/results_notes.json"
params.pkg = "${projectDir}/../package"
params.pkgsrc = "${projectDir}/../package/src"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process PREPARE {
    publishDir "${params.outdir}", mode: 'copy', pattern: 'prepare.json'
    input:
    path downloads
    output:
    path 'run', emit: run
    path 'prepare.json'
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/prepare.py ${downloads} run
    cp run/prepare.json .
    """
}

process TRAIN {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path run
    output:
    path 'fig2.json', emit: fig2
    path 'model.json', emit: model
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/train.py ${run} .
    """
}

process CONDITIONAL {
    publishDir "${params.outdir}", mode: 'copy', pattern: 'clm.json'
    input:
    path run
    path 'model.json'
    output:
    path 'run2', emit: run
    path 'clm.json', emit: clm
    script:
    """
    cp -r ${run} run2
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/conditional.py run2 .
    """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path run
    path 'fig2.json'
    path 'clm.json'
    output:
    path 'fig*'
    path 'published', emit: published
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/figures.py ${downloads}/paper . ${run} .
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${params.pipe}/check_package.py ${params.pkg} --json package.json || true
    test -s package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path 'prepare.json'
    path 'fig2.json'
    path 'clm.json'
    path pkg
    output:
    path 'results.json'
    script:
    """
    mkdir -p o && cp prepare.json fig2.json clm.json o/
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py ${params.notes} o results.json \
        --package ${pkg} --inputs ${params.pipe}/fetch_inputs.sh --env env.json --date \$(date -u +%F) \
        --uniprot ${downloads}/uniprot
    ${params.python} ${params.pipe}/check_results.py results.json --write --root ${projectDir}/..
    """
}

process PAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path 'f/*'
    path published
    output:
    path 'site', emit: site
    path 'report.md'
    script:
    """
    ${params.python} ${params.pipe}/build_page.py ${results} f ${published} site
    ${params.python} ${params.pipe}/check_results.py ${results} --markdown --root ${projectDir}/.. > report.md || true
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path 'f/*'
    output:
    path 'check.json'
    script:
    """
    mkdir -p fresh && cp f/* fresh/ && cp ${results} fresh/
    ${params.python} ${params.pipe}/check_reproduction.py fresh ${params.committed} ${projectDir}/.. check.json
    """
}

workflow {
    dl = FETCH()
    pr = PREPARE(dl)
    tr = TRAIN(pr.run)
    cd = CONDITIONAL(pr.run, tr.model)
    fg = FIGURES(dl, cd.run, tr.fig2, cd.clm)
    pk = PACKAGE()
    res = RESULTS(dl, pr[1], tr.fig2, cd.clm, pk)
    pg = PAGE(res, fg[0].collect(), fg.published)
    CHECK(res, fg[0].mix(pr[1], tr.fig2, tr.model, cd.clm).collect())
}
