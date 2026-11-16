// Reproduce PMC407845 (Gao, Foat and Bussemaker 2004, "Defining transcriptional networks through
// integrative modeling of mRNA expression and transcription factor binding data"). The authors'
// MA-Networker code was never released; the method is the package PMC407845/package (manetworker),
// implemented from the paper's Methods.
//
// Run from the repository root:
//   nextflow run PMC407845/figure-reproduction/main.nf --outdir results [--sources DIR]
//
// Steps: download the inputs (Lee 2002 and Simon 2001 ChIP, 15 SGD expression archives, GO 2004-03,
// the S288C genome, the vector Fig. 2) and check their SHA-256; run MA-Networker (backward selection,
// activity profiles, coupling, Table 1 and its variants); the validation analyses (GO, deletion
// response, motifs, divergent promoters, Simon overlap); draw and score the figures; compare with the
// paper; check the package; write results.json and the results page; check the run against the
// committed outputs. About 3 minutes on 4 cores, most of it the package check.

params.outdir = 'results'
params.python = 'python3'
params.sources = null

params.pipe = "${projectDir}/pipeline"
params.published = "${projectDir}/published"
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

process NETWORKER {
    publishDir "${params.outdir}", mode: 'copy', pattern: '*.{json,tsv}'
    input:
    path downloads
    output:
    path 'run', emit: run
    path '*.{json,tsv}'
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/networker.py ${downloads} run
    cp run/*.json run/*.tsv .
    """
}

process VALIDATE {
    publishDir "${params.outdir}", mode: 'copy', pattern: '*.json'
    input:
    path downloads
    path run
    output:
    path 'run2', emit: run
    path '*.json'
    script:
    """
    cp -r ${run} run2
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/validate.py ${downloads} run2 run2
    cp run2/go.json run2/deletion.json run2/motifs.json run2/divergent.json run2/simon.json .
    """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path run
    output:
    path 'fig*'
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/figures.py ${params.published} ${run} ${downloads} .
    """
}

process COMPARE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path run
    path figs
    output:
    path 'comparison.json'
    script:
    """
    mkdir -p r && cp ${run}/*.json ${run}/*.tsv r/ && cp figures.json r/
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/compare.py r comparison.json
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
    path comparison
    path pkg
    output:
    path 'results.json'
    script:
    """
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py ${params.notes} ${comparison} results.json \
        --package ${pkg} --inputs ${params.pipe}/fetch_inputs.sh --env env.json --date \$(date -u +%F)
    ${params.python} ${params.pipe}/check_results.py results.json --write --root ${projectDir}/..
    """
}

process PAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path 'f/*'
    output:
    path 'site', emit: site
    path 'report.md'
    script:
    """
    ${params.python} ${params.pipe}/build_page.py ${results} f ${params.published} site
    ${params.python} ${params.pipe}/check_results.py ${results} --markdown --root ${projectDir}/.. > report.md || true
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path comparison
    path site
    path 'f/*'
    output:
    path 'check.json'
    script:
    """
    mkdir -p fresh && cp f/* fresh/ && cp ${comparison} ${results} fresh/
    ${params.python} ${params.pipe}/check_reproduction.py fresh ${params.committed} ${projectDir}/.. check.json
    """
}

workflow {
    dl = FETCH()
    nw = NETWORKER(dl)
    va = VALIDATE(dl, nw.run)
    fg = FIGURES(dl, va.run)
    cmp = COMPARE(va.run, fg.collect())
    pk = PACKAGE()
    res = RESULTS(cmp, pk)
    pg = PAGE(res, fg.collect())
    CHECK(res, cmp, pg.site, fg.mix(nw[1], va[1]).flatten().collect())
}
