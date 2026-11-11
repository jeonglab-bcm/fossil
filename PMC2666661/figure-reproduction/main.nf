// Reproduce PMC2666661 (Meng, Yu, Cupples, Farrer and Lunetta 2009, "Performance of random forest
// when SNPs are in linkage disequilibrium"). The authors' revised Random Forests program is lost;
// the method is the package PMC2666661/package (rfld), a port of Breiman and Cutler's Random
// Forests 5.1 with the paper's RF1 and IM1 (see README.md).
//
// Run from the repository root:
//   nextflow run PMC2666661/figure-reproduction/main.nf --outdir results [--full] [--port_check]
//
// Default (CI, a few minutes): read the published figures, recompute Table 1, rerun a few
// replicates of each simulation study from scratch and check them against the committed
// per-replicate statistics (output/sim), recompute every figure, comparison and claim from those
// statistics, check the package, and compare the run with the committed outputs.
// --full: simulate every replicate again (H4M4 SNP study, 13 LD models x 100; its independent-data
//   variant; the other six genetic models, 5 LD models x 100; the haplotype study, 2 frequency rules
//   x 11 r^2 x 100), about 150 CPU hours: run it on a cluster (-profile skyriver).
// --port_check: also download Breiman and Cutler's Fortran prog.f, build it with gfortran and check
//   the port against it, and check the haplotype EM against haplo.stats (needs R with haplo.stats;
//   --rscript). Otherwise the committed checks (output/checks) are used.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.full = false
params.port_check = false
params.rscript = 'Rscript'

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.pkgsrc = "${projectDir}/../package/src"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''} ${params.port_check ? '--port-check' : ''}
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
    ${params.python} ${params.pipe}/read_published.py ${downloads} published_values.json
    """
}

process TABLE1 {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'table1.json'
    script:
    """
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/table1.py table1.json
    """
}

// --full: the simulation studies, one task per chunk of replicates
process SNP_CHUNK {
    cpus 1
    input:
    tuple val(model), val(ld), val(reps), val(lddata)
    output:
    path "snp_${model}_${lddata}_${ld}_${reps}"
    script:
    def rs = model == 'H4M4' ? '--R 0.5 0.02' : '--R 0.5'
    """
    mkdir -p out
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/snp_study.py run out --model ${model} --ld-model ${ld} --reps ${reps} --ld-data ${lddata} ${rs}
    mv out snp_${model}_${lddata}_${ld}_${reps}
    """
}

process HAP_CHUNK {
    cpus 1
    input:
    tuple val(rule), val(r2), val(reps)
    output:
    path "hap_${rule}_${r2}_${reps}"
    script:
    """
    mkdir -p out
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/hap_study.py run out --r2 ${r2} --reps ${reps} --rule ${rule}
    mv out hap_${rule}_${r2}_${reps}
    """
}

process REDUCE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path chunks
    output:
    path 'sim'
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/reduce_chunks.py . sim
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
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/sim_check.py ${sim} sim_check.json || true
    """
}

process SUMMARY {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path sim
    path published
    output:
    path 'summary.json', emit: summary
    path 'comparison.json', emit: comparison
    path 'figures', emit: figures
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/summarize.py aggregate ${sim}/snp.json ${sim}/hap.json ${sim}/other ${sim}/snp_independent.json summary.json
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/compare.py ${published} summary.json comparison.json
    mkdir -p downloads && cp ${projectDir}/published/figure-*.jpg downloads/
    for n in 1 2 3 4 5 6; do cp downloads/figure-\$n.jpg downloads/1471-2105-10-78-\$n.jpg; done
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/render.py downloads ${published} summary.json figures
    """
}

process CHECKS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'checks'
    script:
    if (params.port_check)
        """
        mkdir checks
        PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/port_check.py ${downloads}/prog.f checks/port_check.json --workdir pc
        PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/haplo_check.py ${params.rscript} checks/haplo_check.json --reps 3
        PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/fortran_expected.py ${downloads}/prog.f ${projectDir}/../package/src/rfld/data/h4m4_r1.csv checks/h4m4_r1_expected.csv --workdir fe
        PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/rf1_variants.py checks/rf1_variants.json --reps 30
        PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/hap_variants.py checks/hap_variants.json --reps 30
        """
    else
        """
        mkdir checks && cp ${params.committed}/checks/* checks/
        """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${params.pipe}/check_package.py ${projectDir}/../package --json package.json || true
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path published
    path table1
    path summary
    path comparison
    path figures
    path sim_check
    path checks
    path package_json
    output:
    path 'results.json', emit: results
    path 'report.md', emit: report
    path 'site', emit: site
    script:
    """
    mkdir run && cp -r ${published} ${table1} ${summary} ${comparison} ${figures} ${sim_check} ${checks} ${package_json} run/
    cp ${checks}/port_check.json ${checks}/haplo_check.json run/
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/build_results.py run results.json
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/check_reproduction.py results.json run ${params.committed} report.md ${params.full ? '--full' : ''}
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/build_page.py results.json run ${projectDir}/published site/index.html
    """
}

workflow {
    dl = FETCH()
    pub = READ_PUBLISHED(dl)
    t1 = TABLE1()
    if (params.full) {
        def snpTasks = []
        ['n0', 'n1', 'n2', 'n3', 'n4', 'r1', 'r2', 'r3', 'r4', 'r1n1', 'r2n2', 'r3n3', 'r4n4'].each { ld ->
            (0..9).each { c -> ['incremental', 'independent'].each { d -> snpTasks << ['H4M4', ld, "${10 * c}-${10 * c + 9}", d] } }
        }
        ['H1M1', 'H2M3', 'H3M3', 'H3M4', 'H9M2', 'H8M4'].each { m ->
            ['n0', 'r1', 'r2', 'r3', 'r4'].each { ld -> (0..4).each { c -> snpTasks << [m, ld, "${20 * c}-${20 * c + 19}", 'incremental'] } }
        }
        def hapTasks = []
        ['empirical_ratio', 'equal_snp_freq'].each { rule ->
            (0..10).each { i -> (0..9).each { c -> hapTasks << [rule, String.format('%.1f', 0.1 * i), "${10 * c}-${10 * c + 9}"] } }
        }
        snp = SNP_CHUNK(channel.fromList(snpTasks))
        hap = HAP_CHUNK(channel.fromList(hapTasks))
        sim = REDUCE(snp.mix(hap).collect())
    } else {
        sim = SIM_COMMITTED()
    }
    sc = SIM_CHECK(sim)
    s = SUMMARY(sim, pub)
    ck = CHECKS(dl)
    pk = PACKAGE()
    RESULTS(pub, t1, s.summary, s.comparison, s.figures, sc, ck, pk)
}
