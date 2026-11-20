// Reproduce PMC2824146 (Marshall, Altman, Royston and Holder 2010, "Comparison of techniques for
// handling missing covariate data within prognostic modelling studies: a simulation study").
// The simulation code was never released; the method is rebuilt from the paper's text as the R
// package PMC2824146/package (misscox), which the pipeline calls for every step.
//
// Run from the repository root:
//   nextflow run PMC2824146/figure-reproduction/main.nf --outdir results [--full]
//
// Default (CI, about 15 minutes): download the paper's open-access PDF and figures, read every
// plotted value out of the vector figures, recompute Table 1, the text's data description, the
// linear predictor, Figure 1 and Table 3 from GBSG2, rerun replicate 1 of the MAR and MNAR studies
// and the first 200 true-value cohorts from scratch and check them against the committed
// per-replicate results (output/sim), summarise those results, test the true-value hypotheses,
// compare every figure point and text claim, draw the figures, check the package, and compare
// the run with the committed outputs.
// --full: simulate every replicate again (MAR and MNAR 200 replicates, MCAR and combined 100,
//   20,000 true-value cohorts), about 24 CPU hours, in 64 tasks.

params.outdir = 'results'
params.python = 'python3'
params.rscript = 'Rscript'
params.sources = null
params.full = false

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.pkg = "${projectDir}/../package"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process EXTRACT {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'published_values.json'
    script:
    """
    ${params.python} ${params.pipe}/extract_published.py ${downloads}/PMC2824146.1.pdf published_values.json
    """
}

process TARGETS {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'targets.json'
    script:
    """
    ${params.rscript} ${params.pipe}/gbsg_targets.R targets.json
    """
}

// --full: one task per chunk of replicates
process SIM_CHUNK {
    cpus 1
    input:
    tuple val(kind), val(first), val(last), val(mech)
    output:
    path "chunk_*"
    script:
    def f = String.format('%03d', first as int)
    def l = String.format('%03d', last as int)
    if (kind == 'truth')
        """
        mkdir -p chunk_truth/truth
        ${params.rscript} ${params.pipe}/run_sim.R truth ${first} ${last} chunk_truth/truth/truth_${first}-${last}.csv.gz
        """
    else
        """
        mkdir -p chunk_${mech}_${f}/${mech}
        ${params.rscript} ${params.pipe}/run_sim.R sim ${first} ${last} ${mech} chunk_${mech}_${f}/${mech}/reps_${f}-${l}.csv.gz
        """
}

process GATHER {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path chunks
    output:
    path 'sim'
    script:
    """
    mkdir -p sim
    for c in chunk_*; do cp -r \$c/* sim/; done
    """
}

process SIM_COMMITTED {
    output:
    path 'sim'
    script:
    """
    mkdir sim && cp -r ${params.committed}/sim/. sim/
    """
}

process SIM_CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path sim
    output:
    path 'sim_check.json'
    script:
    """
    ${params.rscript} ${params.pipe}/sim_check.R ${sim} sim_check.json 1
    """
}

process SUMMARY {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path sim
    output:
    path 'summary.json'
    script:
    """
    ${params.rscript} ${params.pipe}/summarise_sim.R ${sim} summary.json
    """
}

process TRUTH_VARIANTS {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'truth_variants.json'
    script:
    """
    ${params.rscript} ${params.pipe}/truth_variants.R truth_variants.json 2000
    """
}

process HYPOTHESES {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'hypotheses.json'
    script:
    """
    ${params.rscript} ${params.pipe}/hypotheses.R hypotheses.json 10 200
    """
}

process COMPARE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path published
    path targets
    path summary
    output:
    path 'comparison.json', emit: comparison
    path 'figures', emit: figures
    script:
    """
    ${params.python} ${params.pipe}/compare.py ${published} ${targets} ${summary} comparison.json
    ${params.python} ${params.pipe}/render.py ${downloads}/PMC2824146.1.pdf ${published} ${summary} ${targets} figures
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    bash ${params.pipe}/check_package_r.sh ${params.pkg} package.json || true
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path published
    path targets
    path summary
    path comparison
    path figures
    path sim_check
    path truth_variants
    path hypotheses
    path package_json
    output:
    path 'results.json', emit: results
    path 'report.md', emit: report
    path 'site', emit: site
    script:
    """
    mkdir run && cp -r ${published} ${targets} ${summary} ${comparison} ${figures} ${sim_check} ${truth_variants} ${hypotheses} ${package_json} run/
    ${params.python} ${params.pipe}/build_results.py run results.json
    ${params.python} ${params.pipe}/check_reproduction.py results.json run ${params.committed} report.md ${params.full ? '--full' : ''}
    ${params.python} ${params.pipe}/build_page.py results.json run ${projectDir}/published site/index.html
    """
}

workflow {
    dl = FETCH()
    pub = EXTRACT(dl)
    tg = TARGETS()
    if (params.full) {
        def tasks = []
        (0..3).each { c -> tasks << ['truth', 5000 * c + 1, 5000 * (c + 1), 'none'] }
        ['MAR', 'MNAR'].each { m -> (0..19).each { c -> tasks << ['sim', 10 * c + 1, 10 * (c + 1), m] } }
        ['MCAR', 'COMBINED'].each { m -> (0..9).each { c -> tasks << ['sim', 10 * c + 1, 10 * (c + 1), m] } }
        sim = GATHER(SIM_CHUNK(channel.fromList(tasks)).collect())
    } else {
        sim = SIM_COMMITTED()
    }
    sc = SIM_CHECK(sim)
    s = SUMMARY(sim)
    tv = TRUTH_VARIANTS()
    hy = HYPOTHESES()
    cmp = COMPARE(dl, pub, tg, s)
    pk = PACKAGE()
    RESULTS(pub, tg, s, cmp.comparison, cmp.figures, sc, tv, hy, pk)
}
