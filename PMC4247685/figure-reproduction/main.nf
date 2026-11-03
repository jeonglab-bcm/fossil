// Reproduce PMC4247685 (Curry 2014, GABi): Figs 2-5, the comparison page and a check report.
// Run: nextflow run main.nf --outdir results [--python python3] [--sources DIR] [--rerun_ga] [--cores N]
// The two genetic-algorithm runs (Fig. 2 benchmark, TCGA bicluster) take about an hour each on
// 6 cores; by default the pipeline reads their committed outputs from data/ and --rerun_ga
// recomputes them.

process FETCH {
    output:
    path 'S1.txt', emit: s1
    path 'S2.txt', emit: s2
    path 'S3.txt', emit: s3
    path 'HumanMethylation27.gz', emit: hm27
    path 'OV_clinicalMatrix', emit: clinical
    path 'OV_survival.txt', emit: survival
    script:
    """
    bash ${projectDir}/pipeline/fetch_inputs.sh ${params.sources ?: ''}
    """
}

process PAPER_MEASURE {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path published
    output:
    path 'paper_measure.json', emit: base
    path 'fig2_published_boxes.json', emit: fig2
    script:
    """
    ${params.python} ${projectDir}/pipeline/paper_measure.py . paper_measure.json
    ${params.python} ${projectDir}/pipeline/fig2_measure.py figure-2.jpg fig2_published_boxes.json
    """
}

process FIG5_DATA {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path s3
    output:
    path 'fig5_clinical.csv', emit: clinical
    path 'fig5_tests.json', emit: tests
    script:
    """
    Rscript ${projectDir}/pipeline/make_fig5_data.R ${s3} fig5_clinical.csv fig5_tests.json
    """
}

process TCGA_PREPARE {
    publishDir "${params.outdir}/data", mode: 'copy', pattern: '*.csv'
    input:
    path hm27
    path clinical
    path survival
    path s3
    output:
    path 'tcga_x.rds', emit: matrix
    path 'tcga_samples.csv', emit: samples
    script:
    """
    Rscript ${projectDir}/pipeline/tcga_prepare.R ${hm27} ${clinical} ${survival} ${s3} tcga_x.rds tcga_samples.csv
    """
}

process S2_S3_CHECK {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path s2
    path s3
    path hm27
    output:
    path 's2_s3_check.json'
    script:
    """
    Rscript ${projectDir}/pipeline/s2_s3_check.R ${s2} ${s3} ${hm27} s2_s3_check.json
    """
}

process TCGA_GABI {
    publishDir "${params.outdir}/data", mode: 'copy'
    cpus params.cores
    input:
    path s1
    path matrix
    path samples
    output:
    path 'tcga_bicluster_seed1.json'
    script:
    """
    Rscript ${projectDir}/pipeline/tcga_gabi.R ${s1} ${matrix} ${samples} tcga_bicluster_seed1.json 1 ${task.cpus} floor
    """
}

process FIG34_DATA {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path matrix
    path samples
    path bicluster
    path s2
    output:
    path 'fig3_density.csv', emit: fig3
    path 'fig4_groups.csv', emit: fig4
    path 'fig34_summary.json', emit: summary
    script:
    """
    Rscript ${projectDir}/pipeline/make_fig34_data.R ${matrix} ${samples} ${bicluster} ${s2} fig3_density.csv fig4_groups.csv fig34_summary.json
    """
}

process FIG2_BENCHMARK {
    publishDir "${params.outdir}/data", mode: 'copy'
    cpus params.cores
    input:
    path s1
    output:
    path 'fig2_scores.csv'
    script:
    """
    Rscript ${projectDir}/pipeline/fig2_benchmark.R ${s1} fig2_scores.csv ${task.cpus} 40
    """
}

process FIG2_BLOCK_CHECK {
    publishDir "${params.outdir}/data", mode: 'copy'
    cpus params.cores
    input:
    path s1
    path scores
    output:
    path 'fig2_block_check.json'
    script:
    """
    Rscript ${projectDir}/pipeline/fig2_block_check.R ${s1} ${scores} fig2_block_check.json ${task.cpus}
    """
}

process FIG2_COMPARE {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path scores
    path boxes
    output:
    path 'fig2_boxes.csv', emit: table
    path 'fig2_tests.json', emit: tests
    script:
    """
    Rscript ${projectDir}/pipeline/fig2_compare.R ${scores} ${boxes} fig2_boxes.csv fig2_tests.json
    """
}

process RENDER {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    tuple val(fig), path(data), path(published)
    output:
    tuple val(fig), path("${fig}_ours.png"), path("${fig}.json")
    script:
    def mode = fig == 'fig2' ? 'grid' : 'base'
    def render = fig == 'fig2' ?
        "Rscript ${projectDir}/pipeline/plot_fig2.R ${data} ${fig}_render.png" :
        "Rscript ${projectDir}/pipeline/plot_base.R ${fig} ${data} ${fig}_render.png"
    """
    ${render}
    ${params.python} ${projectDir}/pipeline/align.py ${fig}_render.png ${published} ${fig}_ours.png ${fig}.json ${mode}
    """
}

process BUILD_PAGE {
    publishDir "${params.outdir}/site", mode: 'copy'
    input:
    path inputs
    output:
    path 'index.html'
    script:
    """
    ${params.python} ${projectDir}/pipeline/build_page.py . index.html
    """
}

process CHECK {
    publishDir params.outdir, mode: 'copy'
    input:
    path inputs
    output:
    path 'report.md'
    script:
    """
    ${params.python} ${projectDir}/pipeline/check_reproduction.py . > report.md
    """
}

workflow {
    pub = "${projectDir}/published"
    inputs = FETCH()
    measure = PAPER_MEASURE(Channel.fromPath("${pub}/*").collect())
    fig5 = FIG5_DATA(inputs.s3)
    tcga = TCGA_PREPARE(inputs.hm27, inputs.clinical, inputs.survival, inputs.s3)
    s2s3 = S2_S3_CHECK(inputs.s2, inputs.s3, inputs.hm27)

    // Figs 3-4 need the TCGA bicluster; until a run has committed it, they are skipped.
    def committed = file("${projectDir}/data/tcga_bicluster_seed1.json")
    bicluster = params.rerun_ga ?
        TCGA_GABI(inputs.s1, tcga.matrix, tcga.samples) :
        (committed.exists() ? Channel.fromPath(committed) : Channel.empty())
    fig34 = FIG34_DATA(tcga.matrix, tcga.samples, bicluster, inputs.s2)

    scores = params.rerun_ga ? FIG2_BENCHMARK(inputs.s1) : Channel.fromPath("${projectDir}/data/fig2_scores.csv")
    fig2 = FIG2_COMPARE(scores, measure.fig2)
    block = params.rerun_ga ? FIG2_BLOCK_CHECK(inputs.s1, scores) : Channel.fromPath("${projectDir}/data/fig2_block_check.json")

    jobs = Channel.of(['fig2', "${pub}/figure-2.jpg"], ['fig3', "${pub}/figure-3.png"],
                      ['fig4', "${pub}/figure-4.png"], ['fig5', "${pub}/figure-5.png"])
        .join(scores.map { ['fig2', it] }
              .mix(fig34.fig3.map { ['fig3', it] }, fig34.fig4.map { ['fig4', it] },
                   fig5.clinical.map { ['fig5', it] }))
        .map { fig, published, data -> tuple(fig, data, file(published)) }
    renders = RENDER(jobs)

    everything = renders.flatMap { fig, png, json -> [png, json] }
        .mix(fig5.tests, fig5.clinical, fig34.summary, fig2.table, fig2.tests, measure.base, tcga.samples, scores, s2s3, block)
        .mix(Channel.fromPath("${pub}/*"))
        .collect()
    BUILD_PAGE(everything)
    CHECK(everything)
}
