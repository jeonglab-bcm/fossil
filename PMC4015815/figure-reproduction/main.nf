// Reproduce PMC4015815 (Liu, Xu, Zou, Xu, Wang and Chen 2014, "Using distances between Top-n-gram
// and residue pairs for protein remote homology detection"): Table 1 (SVM-DR and SVM-DT rows),
// Figures 3, 4 and 5, the claims in the text, results.json and the comparison page.
//
// Run: nextflow run main.nf --outdir results [--python python3] [--sources DIR]
//        [--dmax 0,10,20,40,50,60,80,100,150,200] [--profiles] [--workers N]
//
// --dmax      the dMAX values to train at (Figure 3's grid, read from the figure). Table 1 and
//             Figures 4-5 use 150. Without 0 in the list the dMAX = 0 points are read from the
//             committed sweep (output/sweep_*.csv): Gist's coordinate ascent needs tens of
//             thousands of passes on the composition-only kernel (hours of CPU).
// --profiles  regenerate the PSI-BLAST profiles (nrdb90 of 2016, 3 iterations, E = 0.001; about
//             4 CPU hours) instead of reading the committed Top-1-gram sequences
//             (pipeline/inputs/top1_nrdb90_i3.fasta.gz, written by this step).
// --sources   a folder with local copies of the downloads (see pipeline/fetch_inputs.sh).

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.dmax = '0,10,20,40,50,60,80,100,150,200'
params.profiles = false
params.workers = 4
params.seed = 1

def P = "${projectDir}/pipeline"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${P}/fetch_inputs.sh downloads ${params.profiles ? 'full' : 'light'} ${params.sources ?: ''}
    """
}

// The committed published/figure-*.png are the PNGs embedded in the PMC open-access PDF.
process FIGURES_CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'figures_check.json'
    script:
    """
    ${params.python} ${P}/extract_figures.py ${downloads}/PMC4015815.1.pdf ${projectDir}/published figures_check.json
    """
}

// The Gist port against Gist's own sample run (doc/sample.weights).
process PORT_CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'port_check.json'
    script:
    """
    ${params.python} ${P}/port_check.py ${downloads}/gist/gist-2.3/doc port_check.json
    """
}

process PROFILES {
    publishDir "${params.outdir}/profiles", mode: 'copy', pattern: '{top1_nrdb90_i3.fasta.gz,top1_stats.json}'
    cpus params.workers
    input:
    path downloads
    output:
    path 'top1_nrdb90_i3.fasta.gz', emit: top1
    path 'top1_stats.json'
    script:
    """
    PSIBLAST=\$PWD/${downloads}/blast/ncbi-blast-2.17.0+/bin/psiblast \\
      bash ${P}/run_psiblast.sh ${downloads}/scop.1.53.1e-25.fasta \\
      \$PWD/${downloads}/psein1/Pse-in-One-2.0/psiblast/nrdb90/nrdb90 psiblast ${task.cpus} 3 0.001
    ${params.python} ${P}/top1.py ${downloads}/scop.1.53.1e-25.fasta psiblast/pssm top1.fasta top1_stats.json
    gzip -n -9 top1.fasta && mv top1.fasta.gz top1_nrdb90_i3.fasta.gz
    """
}

process SWEEP {
    publishDir "${params.outdir}", mode: 'copy'
    cpus params.workers
    input:
    tuple val(method), path(downloads), path(top1)
    output:
    tuple val(method), path("sweep_${method}.csv")
    script:
    def seqs = method == 'dr' ? 'residues' : "top1:top1.fasta"
    """
    ${method == 'dt' ? "gunzip -c ${top1} > top1.fasta" : ''}
    ${params.python} ${P}/run_sweep.py --fasta ${downloads}/scop.1.53.1e-25.fasta \\
      --membership ${downloads}/all_seq_fam_membership.txt --sequences ${seqs} \\
      --dmax ${params.dmax} --seed ${params.seed} --workers ${task.cpus} --out fresh.csv
    ${params.python} ${P}/merge_sweep.py fresh.csv ${projectDir}/output/sweep_${method}.csv sweep_${method}.csv
    """
}

// Figures 4 and 5: discriminant weights of family 2.5.1.3 at dMAX = 150 (and 2.5.1.1 as a control).
process WEIGHTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    tuple val(method), val(family), path(downloads), path(top1)
    output:
    path "weights_${method}_${family}.json"
    script:
    def seqs = method == 'dr' ? 'residues' : "top1:top1.fasta"
    """
    ${method == 'dt' ? "gunzip -c ${top1} > top1.fasta" : ''}
    ${params.python} ${P}/discriminant_weights.py --fasta ${downloads}/scop.1.53.1e-25.fasta \\
      --membership ${downloads}/all_seq_fam_membership.txt --sequences ${seqs} \\
      --family ${family} --dmax 150 --seed ${params.seed} --out weights_${method}_${family}.json
    """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path sweeps
    path weights
    output:
    path '{fig*.png,fig*.json,tables.json,fig3_published.json,fig5_published.json}', emit: all
    path 'compare', emit: compare
    script:
    """
    PUB=${projectDir}/published
    ${params.python} ${P}/figure3_axes.py \$PUB/figure-3.png fig3_published.json
    ${params.python} ${P}/figure3.py \$PUB/figure-3.png fig3_published.json sweep_dr.csv sweep_dt.csv .
    ${params.python} ${P}/figure4.py \$PUB/figure-4.png weights_dt_2.5.1.3.json weights_dr_2.5.1.3.json . \\
      weights_dr_2.5.1.1.json weights_dt_2.5.1.1.json
    ${params.python} ${P}/figure5_read.py \$PUB/figure-5.png fig5_published.json
    ${params.python} ${P}/figure5.py \$PUB/figure-5.png fig5_published.json weights_dt_2.5.1.3.json weights_dr_2.5.1.3.json .
    ${params.python} ${P}/tables.py sweep_dr.csv sweep_dt.csv weights_dr_2.5.1.3.json weights_dt_2.5.1.3.json tables.json
    for f in 3 4 5; do
      ${params.python} ${P}/compare_figure.py --published \$PUB/figure-\$f.png --render fig\${f}_ours.png \\
        --out compare/figure-\$f --published-grey 255 --render-grey 255
    done
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path outputs
    output:
    path 'results.json'
    script:
    """
    mkdir run && cp ${outputs} run/
    ${params.python} ${P}/build_results.py run ${projectDir}/results_notes.json results.json
    ${params.python} ${P}/check_results.py results.json --write --skip-files
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path outputs
    path compare
    output:
    path 'report.md'
    script:
    """
    mkdir run && cp ${outputs} run/ && cp -r ${compare} run/compare
    ${params.python} ${P}/check_reproduction.py run ${projectDir}/output report.md
    """
}

process PAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path outputs
    output:
    path 'site/index.html'
    script:
    """
    mkdir run && cp ${outputs} run/
    ${params.python} ${P}/build_page.py run ${projectDir}/published site/index.html
    """
}

workflow {
    dl = FETCH()
    figs_ok = FIGURES_CHECK(dl)
    port = PORT_CHECK(dl)
    top1 = params.profiles ? PROFILES(dl).top1 : Channel.value(file("${P}/inputs/top1_nrdb90_i3.fasta.gz"))
    sweeps = SWEEP(Channel.of('dr', 'dt').combine(dl).combine(top1))
    jobs = Channel.of(['dr', '2.5.1.3'], ['dt', '2.5.1.3'], ['dr', '2.5.1.1'], ['dt', '2.5.1.1'])
    w = WEIGHTS(jobs.combine(dl).combine(top1))
    figs = FIGURES(sweeps.map { it[1] }.collect(), w.collect())
    outputs = figs.all.flatten().mix(figs_ok, port).collect()
    res = RESULTS(outputs)
    all = outputs.mix(res).collect()
    CHECK(all, figs.compare)
    PAGE(all)
}
