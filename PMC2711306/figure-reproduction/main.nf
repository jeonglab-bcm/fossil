// Reproduce PMC2711306 (Kuchaiev, Rasajski, Higham and Przulj 2009, "Geometric de-noising of
// protein-protein interaction networks"): Figs 1-5, Figs S1-S3, Tables S1-S6 and the claims in
// the text. The method is the package PMC2711306/package (geodenoise).
//
// Run from the repository root:
//   nextflow run PMC2711306/figure-reproduction/main.nf --outdir results [--full] [--octave_check] [--sources DIR]
//
// Without --full the Yhigh networks come from the committed pipeline/inputs (the Collins scores
// are on the Wayback Machine, which is too unreliable for CI) and the validation against
// BioGRID 2.0.50, HPRD, GO and KEGG is read from the committed output/validate.json; HumanBG is
// rebuilt from BioGRID 2.0.35 and must equal the committed copy. --full downloads everything and
// recomputes both. --octave_check also runs the authors' Matlab embedding under GNU Octave (port check;
// otherwise output/port_check.json is read). The package check needs network access.

params.outdir = 'results'
params.python = 'python3'
params.octave = 'octave-cli'
params.sources = null
params.full = false
params.octave_check = false
params.seeds = 20
params.cpus = 4

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${projectDir}/pipeline/fetch_inputs.sh downloads ${params.full || params.octave_check ? 'full' : 'light'} ${params.sources ?: ''}
    """
}

process SUPPLEMENT {
    input:
    path downloads
    output:
    path 'supplement.json'
    script:
    """
    ${params.python} ${projectDir}/pipeline/parse_supplement.py ${downloads} supplement.json
    """
}

process NETWORKS {
    publishDir "${params.outdir}/run", mode: 'copy', pattern: 'network_counts.json'
    input:
    path downloads
    output:
    path 'net', emit: net
    path 'network_counts.json', emit: counts
    script:
    def collins = params.full ? "${downloads}/combined_scores.txt" : "${projectDir}/pipeline/inputs"
    """
    ${params.python} ${projectDir}/pipeline/networks.py ${downloads} ${collins} ${projectDir}/pipeline/params/physical_systems.txt net
    cp net/network_counts.json .
    # the committed inputs must be what the builder writes
    for f in humanbg.tsv yhigh.tsv yhigh_low.tsv yhigh_wrong_truth.tsv yhigh_biogrid.tsv network_counts.json; do
      cmp net/\$f ${projectDir}/pipeline/inputs/\$f
    done
    """
}

process YEAST {
    cpus params.cpus
    publishDir "${params.outdir}/run", mode: 'copy'
    input:
    path net
    output:
    path 'yeast.json', emit: json
    path 'roc_dense.csv', emit: dense
    script:
    """
    export OMP_NUM_THREADS=${task.cpus} OPENBLAS_NUM_THREADS=${task.cpus}
    ${params.python} ${projectDir}/pipeline/yeast.py ${net}/yhigh.tsv ${net}/yhigh_low.tsv . --wrong-truth ${net}/yhigh_wrong_truth.tsv
    """
}

process HUMAN {
    cpus params.cpus
    memory '8 GB'
    publishDir "${params.outdir}/run", mode: 'copy'
    input:
    path net
    path supplement
    output:
    path 'human.json', emit: json
    path 'predictions.tsv', emit: predictions
    path 'false_positive_candidates.tsv', emit: fp
    script:
    """
    export OMP_NUM_THREADS=${task.cpus} OPENBLAS_NUM_THREADS=${task.cpus}
    ${params.python} ${projectDir}/pipeline/human.py ${net}/humanbg.tsv ${supplement} . --seeds ${params.seeds}
    """
}

process VALIDATE {
    memory '8 GB'
    publishDir "${params.outdir}/run", mode: 'copy'
    input:
    path net
    path predictions
    path fp
    path supplement
    path downloads
    output:
    path 'validate.json'
    script:
    if (params.full)
        """
        ${params.python} ${projectDir}/pipeline/validate.py ${net}/humanbg.tsv ${predictions} ${fp} ${supplement} ${downloads} validate.json
        """
    else
        """
        cp ${projectDir}/output/run/validate.json .
        """
}

process PORT_CHECK {
    publishDir "${params.outdir}/run", mode: 'copy'
    input:
    path net
    path downloads
    output:
    path 'port_check.json'
    script:
    if (params.octave_check)
        """
        ${params.python} ${projectDir}/pipeline/port_check.py --export ${net}/yhigh.tsv numbered.txt
        ${params.octave} --no-gui ${projectDir}/pipeline/port_check.m ${downloads}/authors ${projectDir}/pipeline/octave_shims numbered.txt yhigh 2 3 4 5 6 7
        ${params.python} ${projectDir}/pipeline/port_check.py ${net}/yhigh.tsv ${net}/yhigh_low.tsv yhigh port_check.json 2 3 4 5 6 7
        """
    else
        """
        cp ${projectDir}/output/run/port_check.json .
        """
}

process ARITHMETIC {
    publishDir "${params.outdir}/run", mode: 'copy'
    output:
    path 'arithmetic.json'
    script:
    """
    ${params.python} ${projectDir}/pipeline/arithmetic.py arithmetic.json
    """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path yeast
    path human
    output:
    path 'figures'
    script:
    """
    ${params.python} ${projectDir}/pipeline/figures.py ${yeast} ${human} ${projectDir}/published figures
    """
}

process PACKAGE {
    publishDir "${params.outdir}/run", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${projectDir}/pipeline/check_package.py ${projectDir}/../package --json package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path run_files
    path figures
    output:
    path 'results.json', emit: results
    path 'report.md', emit: report
    path 'site', emit: site
    script:
    """
    mkdir run && cp ${run_files} run/ && cp ${figures}/figures.json run/
    cp ${projectDir}/output/run/fig2_label_hypotheses.json run/
    ${params.python} ${projectDir}/pipeline/make_results.py run ${projectDir}/results_notes.json ${projectDir}/pipeline/params/inputs.json results.json
    ${params.python} ${projectDir}/pipeline/check_reproduction.py results.json run ${figures} ${projectDir}/output report.md ${params.full ? '--full' : ''}
    ${params.python} ${projectDir}/pipeline/build_page.py results.json ${figures} ${projectDir}/published site/index.html
    """
}

workflow {
    dl = FETCH()
    supp = SUPPLEMENT(dl)
    nets = NETWORKS(dl)
    y = YEAST(nets.net)
    h = HUMAN(nets.net, supp)
    v = VALIDATE(nets.net, h.predictions, h.fp, supp, dl)
    p = PORT_CHECK(nets.net, dl)
    a = ARITHMETIC()
    f = FIGURES(y.json, h.json)
    k = PACKAGE()
    run_files = nets.counts.mix(y.json, y.dense, h.json, h.predictions, h.fp, v, p, a, k).collect()
    RESULTS(run_files, f)
}
