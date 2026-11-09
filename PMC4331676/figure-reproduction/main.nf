// Reproduce PMC4331676 (Xu, Zhou, Wang, He, Wang and Liu 2015, "Identifying DNA-binding proteins
// by combining support vector machine and PSSM distance transformation"). No code was released and
// the web server is gone; the method is rebuilt from the paper as the pssmdt package (../package).
//
// Run from the repository root:
//   nextflow run PMC4331676/figure-reproduction/main.nf --outdir results [--sources DIR]
//
// The PSSMs come from PSI-BLAST against UniRef100 release 2014_01 (22 GB of downloads, about
// 40 CPU hours); they are committed packed in output/pssm/. Without --blastdb the pipeline starts
// from them. On a cluster, --blastdb DB --blast BIN_DIR reruns PSI-BLAST and blastp first
// (-profile skyriver; see README.md). Everything after the PSSMs (about 15 CPU minutes) is rerun
// every time, the sensitivity variants included.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.blastdb = null
params.blast = null
params.chunks = 40
params.cpus = 4

def PIPE = "${projectDir}/pipeline"
def OUT = "${projectDir}/output"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${PIPE}/fetch_inputs.sh downloads ${params.sources ?: ''}
    """
}

process PREPARE {
    publishDir "${params.outdir}/run", mode: 'copy', pattern: '*.json'
    input:
    path downloads
    output:
    path 'data', emit: data
    path 'published', emit: published
    path 'datasets.json'
    path 'lou.json', emit: lou
    path 'published_values.json', emit: pubvals
    path 'akh.json', emit: akh
    path 'arithmetic.json', emit: arith
    script:
    """
    ${params.python} ${PIPE}/parse_datasets.py ${downloads}/1752-0509-9-S1-S10-S1.pdf ${downloads}/pone.0086703.s002.txt data
    cp data/datasets.json .
    mkdir published
    for k in 1 2 3 4 5 6; do
      ${params.python} -c "from PIL import Image; Image.open('${downloads}/1752-0509-9-S1-S10-\$k.jpg').save('published/fig\$k.png')"
    done
    ${params.python} ${PIPE}/read_published.py published published_values.json
    ${params.python} ${PIPE}/lou_comparators.py ${downloads}/pone.0086703.s003.txt lou.json
    ${params.python} ${PIPE}/akh_occurrences.py ${downloads}/1AKH.cif akh.json
    ${params.python} ${PIPE}/paper_arithmetic.py lou.json arithmetic.json
    """
}

process PSIBLAST {
    cpus 4
    input:
    path data
    each chunk
    output:
    path 'pssm/*'
    script:
    """
    PSIBLAST=${params.blast}/psiblast bash ${PIPE}/run_psiblast.sh ${data} ${params.blastdb} pssm ${chunk} ${params.chunks} ${task.cpus}
    """
}

process PACK {
    publishDir "${params.outdir}/pssm", mode: 'copy'
    input:
    path data
    path 'pssm/*'
    output:
    path 'pssm_uniref100_2014_01.npz'
    script:
    """
    ${params.python} ${PIPE}/pack_pssms.py ${data} pssm pssm_uniref100_2014_01.npz
    """
}

process HOMOLOGY {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path data
    output:
    path 'homology_removed.tsv', emit: removed
    path 'blastp_bench_vs_pdb186.tsv', emit: blastp
    script:
    if (params.blast)
        """
        MAKEBLASTDB=${params.blast}/makeblastdb BLASTP=${params.blast}/blastp bash ${PIPE}/run_blastp.sh ${data} blastp_bench_vs_pdb186.tsv
        ${params.python} ${PIPE}/homology_filter.py ${data} blastp_bench_vs_pdb186.tsv homology_removed.tsv
        """
    else
        """
        cp ${OUT}/blastp_bench_vs_pdb186.tsv .
        ${params.python} ${PIPE}/homology_filter.py ${data} blastp_bench_vs_pdb186.tsv homology_removed.tsv
        """
}

process BENCHMARK {
    cpus params.cpus
    publishDir "${params.outdir}/run", mode: 'copy'
    input:
    path pssms
    output:
    path 'benchmark.json', emit: bench
    path 'benchmark_decisions.json', emit: dec
    script:
    """
    ${params.python} ${PIPE}/experiments.py benchmark ${pssms} . --jobs ${task.cpus}
    """
}

process LG_SWEEP {
    cpus params.cpus
    publishDir "${params.outdir}/run", mode: 'copy'
    input:
    path pssms
    output:
    path 'lg_sweep.json'
    script:
    """
    ${params.python} ${PIPE}/experiments.py lg ${pssms} . --jobs ${task.cpus}
    """
}

process INDEPENDENT {
    publishDir "${params.outdir}/run", mode: 'copy'
    input:
    path pssms
    path removed
    path bench
    output:
    path 'independent.json'
    path 'pdb186_decisions.json'
    script:
    """
    ${params.python} ${PIPE}/experiments.py independent ${pssms} ${removed} ${bench} .
    """
}

process WEIGHTS {
    publishDir "${params.outdir}/run", mode: 'copy'
    input:
    path pssms
    path bench
    output:
    path 'weights.json'
    script:
    """
    ${params.python} ${PIPE}/experiments.py weights ${pssms} ${bench} .
    """
}

process DEFINITION {
    publishDir "${params.outdir}/run", mode: 'copy'
    input:
    path pssms
    output:
    path 'definition_check.json'
    script:
    """
    ${params.python} ${PIPE}/bioseq_definition.py ${pssms} definition_check.json
    """
}

process SENSITIVITY {
    cpus params.cpus
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path pssms
    path blastp
    output:
    path 'sensitivity.json'
    script:
    """
    ${params.python} ${PIPE}/sensitivity.py ${pssms} ${OUT}/pssm ${blastp} sensitivity.json --jobs ${task.cpus}
    """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path published
    path 'run/*'
    output:
    path 'figures'
    script:
    """
    ${params.python} ${PIPE}/figures.py ${published} run run/lou.json run/published_values.json figures
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${PIPE}/check_package.py ${projectDir}/../package --json package.json || true
    test -s package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path 'run/*'
    path figures
    path sensitivity
    path removed
    path package_json
    path published
    output:
    path 'results.json'
    path 'report.md'
    path 'site'
    script:
    """
    ${params.python} ${PIPE}/build_results.py run ${figures} ${sensitivity} ${removed} ${package_json} ${projectDir}/results_notes.json results.json
    ${params.python} ${PIPE}/check_reproduction.py results.json run ${figures} ${sensitivity} ${removed} ${OUT} report.md
    ${params.python} ${PIPE}/build_page.py results.json run ${figures} ${published} site/index.html
    """
}

workflow {
    dl = FETCH()
    prep = PREPARE(dl)
    if (params.blastdb) {
        pssm = PACK(prep.data, PSIBLAST(prep.data, Channel.of(0..<params.chunks)).collect())
    } else {
        pssm = Channel.value(file("${OUT}/pssm/pssm_uniref100_2014_01.npz"))
    }
    hom = HOMOLOGY(prep.data)
    removed = hom.removed
    b = BENCHMARK(pssm)
    lg = LG_SWEEP(pssm)
    ind = INDEPENDENT(pssm, removed, b.bench)
    w = WEIGHTS(pssm, b.bench)
    defn = DEFINITION(pssm)
    sens = SENSITIVITY(pssm, hom.blastp)
    run = b.bench.mix(b.dec, lg, ind[0], ind[1], w, defn, prep.lou, prep.pubvals, prep.akh, prep.arith, prep[2]).collect()
    figs = FIGURES(prep.published, run)
    pkg = PACKAGE()
    RESULTS(run, figs, sens, removed, pkg, prep.published)
}
