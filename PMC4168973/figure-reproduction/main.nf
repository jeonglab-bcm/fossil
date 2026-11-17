// Reproduce PMC4168973 (Huang, Yee, Ching, Yu and Garmire 2014, "A novel model to combine clinical
// and pathway-based transcriptomic information for the prognosis prediction of breast cancer").
// The authors' code is lost; the method is the R package PMC4168973/package (pdscox), rebuilt
// from the paper's text.
//
// Run from the repository root (R with the packages of pipeline/install_r.sh, Python with
// requirements.txt):
//   nextflow run PMC4168973/figure-reproduction/main.nf --outdir results [--full] [--sources DIR] [--cpus N]
//
// Default (CI, about 15 minutes on 4 cores): download the inputs and check their SHA-256; install
// pdscox; prepare the four data sets; rerun the pathway deregulation scores of 4 of the 403
// pathways in each data set and the first 2 cross-validation runs of every model, which must equal
// the committed ones (output/pds, output/models/lambdas.json); fit every model from the committed
// scores and penalties; Table 1, Fig. 1, Tables 2 and 3, Figs 3 to 6 and S1 to S4; score the
// figure panels; check the package; write results.json and the results page; check the run
// against the committed outputs.
// --full: score all 403 pathways in each data set (about 2 hours on 4 cores) and run every
//   cross-validation run (about 2 hours more), then build everything from the fresh run.

params.outdir = 'results'
params.python = 'python3'
params.rscript = 'Rscript'
params.sources = null
params.full = false
params.cpus = 4
params.pds_check = '1,101,201,301'

params.pipe = "${projectDir}/pipeline"
params.published = "${projectDir}/published"
params.committed = "${projectDir}/output"
params.notes = "${projectDir}/results_notes.json"
params.pkg = "${projectDir}/../package"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process INSTALL {
    output:
    path 'rlib'
    script:
    """
    mkdir rlib
    R CMD INSTALL --no-test-load --library=rlib ${params.pkg} > install.log 2>&1 || { cat install.log; exit 1; }
    """
}

process PREPARE {
    publishDir "${params.outdir}", mode: 'copy', pattern: '*.json'
    input:
    path downloads
    path rlib
    output:
    path 'data', emit: data
    path 'datasets.json'
    script:
    """
    R_LIBS=rlib ${params.rscript} ${params.pipe}/prepare_data.R ${downloads} data > /dev/null
    cp data/datasets.json .
    """
}

// Default: 4 pathways per data set are rerun and checked; the committed scores are used.
// --full: every pathway is scored.
process PDS {
    cpus params.cpus
    input:
    path data
    path rlib
    output:
    path 'pds', emit: pds
    path 'pds_rerun', emit: rerun
    script:
    def which = params.full ? '' : params.pds_check
    """
    mkdir pds_rerun
    for s in miller pawitan ivshina desmedt; do
      R_LIBS=rlib ${params.rscript} ${params.pipe}/pds.R ${data} \$s pds_rerun/\$s.csv ${task.cpus} "${which}" > pds_\$s.log 2>&1
    done
    if [ "${params.full}" = "true" ]; then cp -r pds_rerun pds; else cp -r ${params.committed}/pds pds; fi
    """
}

process CLINICAL {
    input:
    path data
    path rlib
    output:
    path 'clin'
    script:
    """
    R_LIBS=rlib ${params.rscript} ${params.pipe}/clinical.R ${data} clin
    """
}

process MODELS {
    cpus params.cpus
    input:
    path data
    path pds
    path rlib
    output:
    path 'mod'
    script:
    def mode = params.full ? 'full' : 'check'
    """
    R_LIBS=rlib ${params.rscript} ${params.pipe}/models.R ${data} ${pds} mod ${task.cpus} ${mode} ${params.committed} \
        ${data}/sig.gene70.rda
    """
}

process TABLE3 {
    input:
    path data
    path rlib
    output:
    path 'table3.json'
    script:
    """
    R_LIBS=rlib ${params.rscript} ${params.pipe}/table3.R ${data} .
    """
}

process RERUN_CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path rerun
    path mod
    output:
    path 'rerun_check.json'
    script:
    if (params.full)
        """
        echo '{"passed": true, "full": true}' > rerun_check.json
        """
    else
        """
        ${params.python} ${params.pipe}/check_rerun.py ${rerun} ${params.committed} ${mod}/lambda_check.json rerun_check.json
        """
}

// Score the panels, and gather every output into one folder (the layout of the committed output/)
process COMPARE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path clin
    path mod
    path t3
    path pds
    path datasets
    output:
    path 'output', emit: out
    script:
    """
    mkdir -p output/curves output/models
    cp -r ${clin}/* ${mod}/* output/
    cp ${t3} ${datasets} output/
    cp -r ${pds} output/pds
    ${params.python} ${params.pipe}/score_figures.py ${params.pipe}/panels.json output/curves ${params.published} output/fig
    mv output/fig/*.png output/ && mv output/fig/pixel_scores.json output/ && rmdir output/fig
    ${params.python} ${params.pipe}/compare.py ${params.pipe}/paper_values.json output
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    bash ${params.pipe}/check_r_package.sh ${params.pkg} package.json
    test -s package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path out
    path pkg
    path rlib
    output:
    path 'results.json'
    script:
    """
    R_LIBS=rlib ${params.rscript} ${params.pipe}/env_versions.R env.json
    ${params.python} ${params.pipe}/env_versions_py.py env.json
    ${params.python} ${params.pipe}/build_results.py ${params.notes} ${out}/comparison.json results.json \
        --package ${pkg} --inputs ${params.pipe}/fetch_inputs.sh --env env.json --date \$(date -u +%F)
    ${params.python} ${params.pipe}/check_results.py results.json --write --root ${projectDir}/..
    """
}

process PAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path out
    output:
    path 'site', emit: site
    path 'report.md'
    script:
    """
    ${params.python} ${params.pipe}/build_page.py ${results} ${out} ${params.published} site
    ${params.python} ${params.pipe}/check_results.py ${results} --markdown --root ${projectDir}/.. > report.md || true
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path out
    path rerun
    output:
    path 'check.json'
    script:
    """
    mkdir fresh && cp -r ${out}/* fresh/ && cp ${results} fresh/
    ${params.python} ${params.pipe}/check_reproduction.py fresh ${params.committed} ${projectDir}/.. check.json ${rerun}
    """
}

workflow {
    dl = FETCH()
    lib = INSTALL()
    prep = PREPARE(dl, lib)
    pds = PDS(prep.data, lib)
    clin = CLINICAL(prep.data, lib)
    mod = MODELS(prep.data, pds.pds, lib)
    t3 = TABLE3(prep.data, lib)
    rc = RERUN_CHECK(pds.rerun, mod)
    cmp = COMPARE(clin, mod, t3, pds.pds, prep[1])
    pk = PACKAGE()
    res = RESULTS(cmp.out, pk, lib)
    PAGE(res, cmp.out)
    CHECK(res, cmp.out, rc)
}
