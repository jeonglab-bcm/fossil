// Reproduce PMC2648748 (Jiang, Tang, Wu and Fu 2009, "A random forest approach to the detection of
// epistatic interactions in case-control studies"). The authors' program (epiForest) is lost; the
// method is the R package PMC2648748/package (epiforest), rebuilt from the paper.
//
// Run from the repository root:
//   nextflow run PMC2648748/figure-reproduction/main.nf --outdir results [--full] [--variants]
//
// Default (CI, about 10 minutes): read the published Figs 2 and 3, rerun three simulated data sets
// from scratch and check them against the committed per-data-set records (output/sim), recompute
// the power of every method and Fig. 3 from those records, draw and score both figures with their
// negative controls, rerun the disease-model and B-statistic checks, check the package, and
// compare the run with the committed outputs.
// --full: simulate and analyse all 2,400 data sets again (3 models x 4 MAFs x 2 r^2 x 100), about
//   28 CPU hours (7 hours on 4 cores); one task per 25 data sets.
// --variants: also rerun the SWSFS hypothesis tests (ntree, mtry, stopping rule; about 2 CPU hours).

params.outdir = 'results'
params.python = 'python3'
params.rscript = 'Rscript'
params.sources = null
params.full = false
params.variants = false

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.published = "${projectDir}/published"
params.pkg = "${projectDir}/../package"

process FETCH {
    publishDir "${params.outdir}", mode: 'copy', pattern: 'fetch.json'
    output:
    path 'downloads', emit: dir
    path 'fetch.json', emit: json
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    cp downloads/fetch.json fetch.json
    """
}

process READ_PUBLISHED {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'published_values.json'
    script:
    """
    ${params.python} ${params.pipe}/read_published.py ${params.published}/figure-2.png ${params.published}/figure-3.png published_values.json
    """
}

process INSTALL_PACKAGE {
    output:
    path 'rlib'
    script:
    """
    mkdir rlib
    R CMD INSTALL --no-docs -l rlib ${params.pkg} > install.log 2>&1 || (cat install.log; exit 1)
    """
}

// --full: the simulation study, one task per 25 data sets of a setting
process SIM_CHUNK {
    cpus 1
    input:
    path rlib
    tuple val(model), val(maf), val(r2), val(first)
    output:
    path "sim_${model}_${maf}_${r2}_${first}.jsonl"
    script:
    """
    R_LIBS=${rlib} ${params.rscript} ${params.pipe}/sim_study.R ${model} ${maf} ${r2} ${first} ${first + 24} sim_${model}_${maf}_${r2}_${first}.jsonl
    """
}

process REDUCE {
    input:
    path chunks
    output:
    path 'sim'
    script:
    """
    mkdir chunks && mv *.jsonl chunks/
    ${params.python} ${params.pipe}/summarize.py reduce chunks sim
    """
}

process SIM_COMMITTED {
    output:
    path 'sim'
    script:
    """
    mkdir sim && cp ${params.committed}/sim/*.json sim/
    """
}

process SIM_CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path rlib
    path sim
    output:
    path 'sim_check.json'
    script:
    """
    R_LIBS=${rlib} ${params.python} ${params.pipe}/sim_check.py ${sim} sim_check.json --rscript ${params.rscript}
    """
}

process SUMMARY {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path sim
    path published
    output:
    path 'sim', emit: sim
    path 'summary.json', emit: summary
    path 'comparison.json', emit: comparison
    path 'fig*_*.png', emit: figures
    path 'controls', emit: controls
    script:
    """
    ${params.python} ${params.pipe}/summarize.py aggregate ${sim} summary.json
    ${params.rscript} ${params.pipe}/render.R summary.json .
    mkdir pub && cp ${params.published}/figure-2.png ${params.published}/figure-3.png pub/
    ${params.python} ${params.pipe}/compare.py ${published} summary.json . pub comparison.json
    """
}

process CHECKS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path rlib
    path published
    output:
    path 'checks'
    script:
    """
    mkdir checks
    R_LIBS=${rlib} ${params.rscript} ${params.pipe}/model_variants.R ${published} checks/model_variants.json
    R_LIBS=${rlib} ${params.rscript} ${params.pipe}/bstat_null.R checks/bstat_null.json
    if ${params.variants}; then
      mkdir sv
      for job in "1 0.05 0.7" "3 0.2 1.0"; do
        for v in ntree500 mtry31 ntree2000; do
          set -- \$job
          R_LIBS=${rlib} ${params.rscript} ${params.pipe}/swsfs_variants.R sv/\${v}_\$1_\$2_\$3.json \$1 \$2 \$3 1:3 --variant \$v
        done
      done
      ${params.python} ${params.pipe}/swsfs_summary.py sv checks/swsfs_variants.json
    else
      cp ${params.committed}/checks/swsfs_variants.json checks/
    fi
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    bash ${params.pipe}/check_package.sh ${params.pkg} package.json > package.log 2>&1 || (cat package.log; true)
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path published
    path fetch
    path summary
    path comparison
    path figures
    path controls
    path sim_check
    path checks
    path package_json
    output:
    path 'results.json', emit: results
    path 'report.md', emit: report
    path 'site', emit: site
    script:
    """
    mkdir run && cp -r ${published} ${fetch} ${summary} ${comparison} ${figures} ${controls} ${sim_check} ${checks} ${package_json} run/
    ${params.python} ${params.pipe}/build_results.py run results.json
    ${params.python} ${params.pipe}/check_reproduction.py results.json run ${params.committed} report.md ${params.full ? '--full' : ''}
    ${params.python} ${params.pipe}/build_page.py results.json run ${params.published} site/index.html
    """
}

workflow {
    fetched = FETCH()
    pub = READ_PUBLISHED()
    rlib = INSTALL_PACKAGE()
    if (params.full) {
        def tasks = []
        [1, 2, 3].each { m -> ['0.05', '0.1', '0.2', '0.5'].each { q -> ['0.7', '1.0'].each { r ->
            [1, 26, 51, 76].each { f -> tasks << [m, q, r, f] } } } }
        chunks = SIM_CHUNK(rlib, channel.fromList(tasks))
        sim = REDUCE(chunks.collect())
    } else {
        sim = SIM_COMMITTED()
    }
    sc = SIM_CHECK(rlib, sim)
    s = SUMMARY(sim, pub)
    ck = CHECKS(rlib, pub)
    pk = PACKAGE()
    RESULTS(pub, fetched.json, s.summary, s.comparison, s.figures, s.controls, sc, ck, pk)
}
