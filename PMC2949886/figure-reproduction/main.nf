// Reproduce PMC2949886 (van Iterson, Boer and Menezes 2010, "Filtering, FDR and power").
// The authors' R scripts are lost; the method is the R package PMC2949886/package (filterfdr),
// rebuilt from the paper and its Additional File 1 (see README.md).
//
// Run from the repository root:
//   nextflow run PMC2949886/figure-reproduction/main.nf --outdir results [--full]
//
// Default (CI, about 15 minutes): read the published vector figures, rerun the first 50 of the
// 1000 simulated data sets and check them against the committed chunk sums (output/sim), form the
// means from the committed chunks, rerun the single-data-set analyses (Figs 2, 6 and S4, 1000
// permutations each), Fig. 1, and the leukemia analysis (Figs 7 and S5), draw and score every
// figure, check the package, and compare the run with the committed outputs.
// --full: simulate all 1000 data sets again for both noise readings, and 100 with pi0 = 0.7
//   (about 40 CPU minutes; -profile skyriver runs every chunk as its own Slurm job).

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

process INSTALL_PACKAGE {
    output:
    path 'rlib'
    script:
    """
    mkdir rlib && cp -r ${params.pkg} pkgsrc
    R CMD INSTALL --library=rlib pkgsrc > install.log 2>&1 || { cat install.log; exit 1; }
    """
}

process READ_PUBLISHED {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'published_values.json'
    script:
    """
    ${params.python} ${params.pipe}/published.py ${downloads} published_values.json
    """
}

// one chunk of simulated data sets: [variant, noise SD, pi0, first, last]
process SIM_CHUNK {
    cpus 1
    input:
    tuple val(variant), val(sd), val(pi0), val(first), val(last)
    path rlib
    output:
    tuple val(variant), path("${variant}_chunk*")
    script:
    def c = String.format('%02d', ((first as int) - 1).intdiv((last as int) - (first as int) + 1))
    """
    R_LIBS=\$PWD/${rlib}:\${R_LIBS:-} ${params.rscript} ${params.pipe}/simulate.R ${first} ${last} ${sd} ${variant}_chunk${c} ${pi0}
    """
}

process COLLECT_SIM {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path chunks
    output:
    path 'sim'
    script:
    """
    mkdir -p sim/sd0.1 sim/sd0.01 sim/pi0.7
    for f in ${chunks}; do v=\${f%%_chunk*}; cp \$f sim/\$v/\${f#*_}; done
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

// CI: data sets 1-50 again, against the committed chunk00
process SIM_CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path rlib
    output:
    path 'sim_check.json'
    script:
    """
    R_LIBS=\$PWD/${rlib}:\${R_LIBS:-} ${params.rscript} ${params.pipe}/simulate.R 1 50 0.1 chunk00
    ${params.python} ${params.pipe}/sim_check.py chunk00 ${params.committed}/sim/sd0.1/chunk00 sim_check.json
    """
}

process SUMMARIZE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path sim
    output:
    path 'sim_*.json'
    script:
    """
    for v in sd0.1 sd0.01 pi0.7; do ${params.python} ${params.pipe}/summarize.py ${sim}/\$v sim_\$v.json; done
    """
}

process ONE_DATASET {
    publishDir "${params.outdir}", mode: 'copy'
    cpus 1
    input:
    val sd
    path rlib
    output:
    path "one_sd${sd}.json"
    script:
    """
    R_LIBS=\$PWD/${rlib}:\${R_LIBS:-} ${params.rscript} ${params.pipe}/one_dataset.R 1 ${sd} 1000 one_sd${sd}.json
    """
}

process FIG1 {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path rlib
    output:
    path 'fig1.json'
    script:
    """
    R_LIBS=\$PWD/${rlib}:\${R_LIBS:-} ${params.rscript} ${params.pipe}/fig1.R fig1.json
    """
}

process LEUKEMIA {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path rlib
    output:
    path 'leukemia.json'
    script:
    """
    R_LIBS=\$PWD/${rlib}:\${R_LIBS:-} ${params.rscript} ${params.pipe}/leukemia.R ${downloads}/GSE13425_series_matrix.txt.gz 20 leukemia.json
    """
}

process COMPARE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path published
    path runs
    output:
    path 'figures'
    path 'comparison.json'
    script:
    """
    mkdir -p runs_in && cp ${runs} runs_in/
    mkdir figures
    ${params.python} ${params.pipe}/compare.py ${downloads} ${published} runs_in figures
    mv figures/comparison.json .
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    bash ${params.pipe}/check_package.sh ${params.pkg} package.json || true
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path everything
    output:
    path 'results.json'
    path 'report.md'
    path 'site'
    script:
    """
    mkdir run && cp -r ${everything} run/
    ${params.python} ${params.pipe}/build_results.py run results.json
    ${params.python} ${params.pipe}/check_reproduction.py results.json run ${params.committed} report.md ${params.full ? '--full' : ''}
    ${params.python} ${params.pipe}/build_page.py results.json run site/index.html
    """
}

workflow {
    dl = FETCH()
    lib = INSTALL_PACKAGE()
    pub = READ_PUBLISHED(dl)
    if (params.full) {
        def tasks = []
        (0..19).each { c -> tasks << ['sd0.1', '0.1', '0.8', 50 * c + 1, 50 * c + 50] }
        (0..19).each { c -> tasks << ['sd0.01', '0.01', '0.8', 50 * c + 1, 50 * c + 50] }
        (0..3).each { c -> tasks << ['pi0.7', '0.1', '0.7', 25 * c + 1, 25 * c + 25] }
        ch = SIM_CHUNK(channel.fromList(tasks), lib)
        sim = COLLECT_SIM(ch.map { it[1] }.flatten().collect())
        check = channel.empty()
    } else {
        sim = SIM_COMMITTED()
        check = SIM_CHECK(lib)
    }
    sums = SUMMARIZE(sim)
    one = ONE_DATASET(channel.of('0.1', '0.01', '0'), lib)
    f1 = FIG1(lib)
    leuk = LEUKEMIA(dl, lib)
    runs = sums.flatten().mix(one, f1, leuk).collect()
    cmp = COMPARE(dl, pub, runs)
    pk = PACKAGE()
    RESULTS(pub.mix(runs.flatten(), cmp[0], cmp[1], pk, check, sim).collect())
}
