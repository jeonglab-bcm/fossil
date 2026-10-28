// Reproduce PMC4081639 (Yu & Shaw 2014): figure data, Table 1, figure renders, comparison page and a check report.
// Run: nextflow run main.nf --outdir results [--python python3]

process PAPER_MEASURE {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path published
    output:
    path 'paper_traces.json', emit: traces
    path 'fig5_scale.json', emit: fig5_scale
    path 'fig6_paper.json', emit: fig6_paper
    script:
    """
    ${params.python} ${projectDir}/pipeline/paper_measure.py .
    """
}

process EQ6_GRIDS {
    output:
    path 'eq6_grids.csv'
    script:
    """
    Rscript ${projectDir}/pipeline/eq6_grids.R
    """
}

process SCORE_EQ6 {
    publishDir "${params.outdir}/logs", mode: 'copy'
    input:
    path grids
    path traces
    output:
    path 'score_eq6.txt'
    script:
    """
    ${params.python} ${projectDir}/pipeline/score_eq6.py > score_eq6.txt
    """
}

process FIG2_DATA {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path grids
    output:
    path 'fig2_data.csv', emit: data
    path 'fig2_data_native.csv', emit: native_r
    path 'fig2_summary.json', emit: summary
    script:
    """
    ${params.python} ${projectDir}/pipeline/make_fig2_data.py
    """
}

process FIG4_DATA {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path fig2
    path psi_grid
    path mesh_values
    output:
    path 'fig4_data.csv'
    script:
    """
    ${params.python} ${projectDir}/pipeline/make_fig4_data.py
    """
}

process FIG5_ERRORS {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path lib_values
    output:
    path 'fig5_errs.json'
    script:
    """
    ${params.python} ${projectDir}/pipeline/fig5_score2.py
    """
}

process FIG5_VGAM {
    publishDir "${params.outdir}/data", mode: 'copy'
    output:
    path 'fig5_vgam_best.json'
    script:
    """
    ${params.python} ${projectDir}/pipeline/fig5_vgam_variants.py > fig5_vgam_variants.log
    """
}

process FIG5_DATA {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path best
    path errs
    output:
    path 'fig5_data.csv'
    script:
    """
    ${params.python} ${projectDir}/pipeline/make_fig5_data.py
    """
}

process TABLE1 {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path source
    path counts
    output:
    path 'table1_result.json'
    script:
    """
    ext=\$( [ "\$(uname)" = Darwin ] && echo dylib || echo so )
    cc -O2 -shared -fPIC ${source} -o libmesh.\$ext -lm
    FOSSIL_HMP=. ${params.python} ${projectDir}/pipeline/table1_native.py
    """
}

// Timing runs after the long Fig. 5 jobs (inputs used only for ordering), so other tasks disturb it less.
process TIMING_MESH {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path source
    path after
    output:
    path 'fig6_mesh_native.csv'
    script:
    """
    cc -O2 -o mesh_native ${source} -lm
    ./mesh_native > fig6_mesh_native.csv
    """
}

process TIMING_VGAM {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path rscript
    path after
    output:
    path 'fig6_vgam.csv'
    script:
    """
    Rscript ${rscript}
    """
}

process FIG6_DATA {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path mesh
    path vgam
    path paper
    output:
    path 'fig6_data.csv', emit: data
    path 'fig6_data_scaled.csv', emit: scaled
    path 'fig6_scale.json', emit: scale
    script:
    """
    ${params.python} ${projectDir}/pipeline/make_fig6_data.py
    """
}

process RENDER {
    tag "fig${fig}"
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    tuple val(fig), path(prm, stageAs: 'render_params.json')
    path data
    path published
    output:
    path "fig${fig}*", emit: files
    script:
    """
    FOSSIL_PUBLISHED=. FOSSIL_DATA=. ${params.python} ${projectDir}/pipeline/final.py ${fig} ${prm} .
    """
}

process SITE {
    publishDir "${params.outdir}/site/PMC4081639", mode: 'copy'
    input:
    path renders
    path published
    path table1
    output:
    path 'index.html'
    script:
    """
    FOSSIL_PUBLISHED=. FOSSIL_OUTPUT=. FOSSIL_DATA=. ${params.python} ${projectDir}/pipeline/build_page.py index.html
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path files
    output:
    path 'report.md'
    script:
    """
    ${params.python} ${projectDir}/pipeline/check_reproduction.py . > report.md || { cat report.md; exit 1; }
    cat report.md
    """
}

workflow {
    pipe = "${projectDir}/pipeline"
    published = channel.fromPath("${projectDir}/published/figure-*.jpg").collect()

    PAPER_MEASURE(published)
    EQ6_GRIDS()
    SCORE_EQ6(EQ6_GRIDS.out, PAPER_MEASURE.out.traces)
    FIG2_DATA(EQ6_GRIDS.out)
    FIG4_DATA(FIG2_DATA.out.data, file("${pipe}/fig4_in.txt"), file("${pipe}/fig4_mesh.txt"))
    FIG5_ERRORS(file("${pipe}/fig5_lib.txt"))
    FIG5_VGAM()
    FIG5_DATA(FIG5_VGAM.out, FIG5_ERRORS.out)
    TABLE1(file("${pipe}/mesh_lib.c"), channel.fromPath("${projectDir}/hmp-data/*.csv").collect())

    TIMING_MESH(file("${pipe}/mesh_native.c"), FIG5_DATA.out)
    TIMING_VGAM(file("${pipe}/fig6_vgam.R"), TIMING_MESH.out)
    FIG6_DATA(TIMING_MESH.out, TIMING_VGAM.out, PAPER_MEASURE.out.fig6_paper)

    data = FIG2_DATA.out.data
        .mix(FIG4_DATA.out, FIG5_DATA.out, FIG6_DATA.out.data, FIG6_DATA.out.scaled)
        .collect()
    figs = channel.of('2', '4', '5', '5_own', '6', '6_measured')
        .map { t -> tuple(t, file("${pipe}/params/fig${t}.json")) }
    RENDER(figs, data, published)

    renders = RENDER.out.files.flatten().collect()
    SITE(renders, published, TABLE1.out)

    CHECK(renders
        .mix(FIG2_DATA.out.data, FIG2_DATA.out.summary, FIG4_DATA.out, FIG5_DATA.out, FIG6_DATA.out.scale, TABLE1.out)
        .flatten()
        .collect())
}
