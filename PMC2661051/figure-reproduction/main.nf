// Reproduce PMC2661051 (Ackermann and Strimmer 2009, "A general modular framework for gene set
// enrichment analysis"). The authors' R code is lost; the method is the R package
// PMC2661051/package (gseamod), rebuilt from the paper's text.
//
// Run from the repository root (R with the packages of pipeline/install_r.sh, Python with
// requirements.txt):
//   nextflow run PMC2661051/figure-reproduction/main.nf --outdir results [--full] [--sources DIR] [--cpus N]
//
// Default (CI, about 10 minutes on 4 cores): download the p53 and Hedenfalk inputs and check their
// SHA-256; install gseamod from the repository; rerun replicates 1-3 of the simulation study and
// 6 p53 and 6 Hedenfalk gene sets from scratch and check them against the committed p-values
// (output/sim, output/real); build Tables 2-7 and Figs 2-4 from the committed p-values; compare
// with the paper; check the package; write results.json and the results page; check the run
// against the committed outputs.
// --full: rerun all 100 replicates (Tables 2-6) and every p53 and Hedenfalk gene set (Figs 2 and
//   4, Table 7), about 6 hours of CPU (1.5 h on 4 cores), and build everything from the fresh run.

params.outdir = 'results'
params.python = 'python3'
params.rscript = 'Rscript'
params.sources = null
params.full = false
params.cpus = 4
params.check_reps = '1 3'
params.check_sets_p53 = '1,58,116,174,232,290'
params.check_sets_hed = '1,17,34,51,68,84'

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

process SIMULATE {
    cpus params.cpus
    input:
    path rlib
    output:
    path 'sim'
    script:
    def reps = params.full ? '1 100' : params.check_reps
    """
    R_LIBS=rlib ${params.rscript} ${params.pipe}/simulate_tables.R sim ${reps} ${task.cpus}
    """
}

process REAL {
    cpus params.cpus
    input:
    path data
    path rlib
    output:
    path 'real'
    script:
    def sp = params.full ? '' : params.check_sets_p53
    def sh = params.full ? '' : params.check_sets_hed
    """
    mkdir real
    R_LIBS=rlib ${params.rscript} ${params.pipe}/real_data.R ${data}/p53.rds real/p53.csv ${task.cpus} ${sp}
    R_LIBS=rlib ${params.rscript} ${params.pipe}/real_data.R ${data}/hedenfalk.rds real/hedenfalk.csv ${task.cpus} ${sh}
    """
}

// Default: the reruns must equal the committed p-values, which the rest of the pipeline then uses.
// --full: the fresh p-values are used as they are.
process RERUN_CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path sim
    path real
    output:
    path 'sim_all', emit: sim
    path 'real_all', emit: real
    path 'rerun_check.json'
    script:
    if (params.full)
        """
        cp -r ${sim} sim_all && cp -r ${real} real_all
        echo '{"passed": true, "full": true}' > rerun_check.json
        """
    else
        """
        ${params.python} ${params.pipe}/check_rerun.py ${sim} ${params.committed}/sim ${real} ${params.committed}/real rerun_check.json
        cp -r ${params.committed}/sim sim_all && cp -r ${params.committed}/real real_all
        """
}

// Variants that test causes (stronger correlation in the simulation, set 3 false positives on 400
// more data sets, other Hedenfalk preprocessing): rerun with --full, read from output/ otherwise.
process VARIANTS {
    publishDir "${params.outdir}", mode: 'copy'
    cpus params.cpus
    input:
    path downloads
    path rlib
    output:
    path 'variants.json'
    script:
    if (params.full)
        """
        R_LIBS=rlib ${params.rscript} ${params.pipe}/variants.R ${downloads} variants.json ${task.cpus}
        """
    else
        """
        cp ${params.committed}/variants.json .
        """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path data
    path real
    path rlib
    output:
    path 'fig*'
    script:
    """
    R_LIBS=rlib ${params.rscript} ${params.pipe}/figures.R ${data}/p53.rds ${real}/p53.csv ${real}/hedenfalk.csv .
    ${params.python} ${params.pipe}/overlay.py ${params.published} . .
    """
}

process READ_PUBLISHED {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'published_values.json'
    script:
    """
    ${params.python} ${params.pipe}/read_published.py ${params.published} published_values.json
    """
}

process COMPARE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path sim
    path real
    path datasets
    path figs
    path pubvals
    path variants
    output:
    path 'comparison.json', emit: comparison
    path 'tables.json', emit: tables
    script:
    """
    mkdir r && cp ${real}/*.csv ${datasets} figures.json fig3_variants.json ${variants} r/
    ${params.python} ${params.pipe}/compare.py ${sim} r ${pubvals} ${params.pipe}/paper_values.json .
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
    path comparison
    path pkg
    path rlib
    output:
    path 'results.json'
    script:
    """
    R_LIBS=rlib ${params.rscript} ${params.pipe}/env_versions.R env.json
    ${params.python} ${params.pipe}/env_versions_py.py env.json
    ${params.python} ${params.pipe}/build_results.py ${params.notes} ${comparison} results.json \
        --package ${pkg} --inputs ${params.pipe}/fetch_inputs.sh --env env.json --date \$(date -u +%F)
    ${params.python} ${params.pipe}/check_results.py results.json --write --root ${projectDir}/..
    """
}

process PAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path tables
    path 'f/*'
    output:
    path 'site', emit: site
    path 'report.md'
    script:
    """
    ${params.python} ${params.pipe}/build_page.py ${results} ${tables} f ${params.published} site
    ${params.python} ${params.pipe}/check_results.py ${results} --markdown --root ${projectDir}/.. > report.md || true
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path comparison
    path tables
    path datasets
    path pubvals
    path variants
    path sim
    path real
    path rerun
    path 'f/*'
    output:
    path 'check.json'
    script:
    """
    mkdir -p fresh && cp f/* ${comparison} ${tables} ${datasets} ${pubvals} ${variants} ${results} fresh/
    cp -r ${sim} fresh/sim && cp -r ${real} fresh/real
    ${params.python} ${params.pipe}/check_reproduction.py fresh ${params.committed} ${projectDir}/.. check.json ${rerun}
    """
}

workflow {
    dl = FETCH()
    lib = INSTALL()
    prep = PREPARE(dl, lib)
    sim = SIMULATE(lib)
    real = REAL(prep.data, lib)
    rc = RERUN_CHECK(sim, real)
    figs = FIGURES(prep.data, rc.real, lib)
    pv = READ_PUBLISHED()
    va = VARIANTS(dl, lib)
    cmp = COMPARE(rc.sim, rc.real, prep[1], figs.collect(), pv, va)
    pk = PACKAGE()
    res = RESULTS(cmp.comparison, pk, lib)
    pg = PAGE(res, cmp.tables, figs.collect())
    CHECK(res, cmp.comparison, cmp.tables, prep[1], pv, va, rc.sim, rc.real, rc[2], figs.collect())
}
