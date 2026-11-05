// Reproduce PMC4426843 (Bleazard, Lamb and Griffiths-Jones 2015, "Bias in microRNA functional
// enrichment analysis"): Figure 1, Tables 1 and 2, the Supplementary Table S1/S3/S5 checks, and
// the comparison page that site/PMC4426843/index.html is copied from.
//
// Run: nextflow run main.nf --outdir results [--python python3] [--rscript Rscript]
//        [--sources DIR] [--full] [--rerun all|Human:39,Mouse:1,...]
//
// --full      regenerate the miRanda predictions: cut the Ensembl 75 3' UTRs and run miRanda 3.3a
//             on all human and mouse miRBase 20 mature miRNAs (about 45 CPU hours; use the
//             skyriver profile). Without it the committed gene-level site tables are used
//             (pipeline/inputs/sites_{hsa,mmu}.txt.xz, written by a --full run).
// --rerun     which empirical nulls to sample (species:list size). 'all' (default) samples all
//             22; otherwise the others are read from the committed counts (output/empirical;
//             only the human 39-miRNA null, which Table 1 and Fig. 1 use, is committed in full).
// --sources   a folder with local copies of the downloads (see pipeline/fetch_inputs.sh).

params.outdir = 'results'
params.python = 'python3'
params.rscript = 'Rscript'
params.miranda = 'miranda'
params.sources = null
params.full = false
params.rerun = 'all'
params.iterations = 999999


process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${projectDir}/pipeline/fetch_inputs.sh downloads ${params.full ? 'full' : 'light'} ${params.sources ?: ''}
    """
}

// Supplementary Tables S1-S5 as TSV (the committed copies in pipeline/inputs come from here).
process SUPPLEMENT {
    publishDir "${params.outdir}/supplement", mode: 'copy'
    input:
    path downloads
    output:
    path 'supp/*'
    script:
    """
    ${params.python} ${projectDir}/pipeline/parse_supplement.py ${downloads} supp
    """
}

// Gene -> biological-process GO terms from the Ensembl 75 BioMart dumps.
process GO {
    publishDir "${params.outdir}", mode: 'copy', pattern: '*.json'
    input:
    path downloads
    output:
    path 'hsa_go_bp.tsv', emit: hsa
    path 'mmu_go_bp.tsv', emit: mmu
    path 'go_universe.json', emit: summary
    script:
    """
    ${params.python} ${projectDir}/pipeline/build_go.py ${downloads} hsapiens hsa_go_bp.tsv
    ${params.python} ${projectDir}/pipeline/build_go.py ${downloads} mmusculus mmu_go_bp.tsv
    ${params.python} ${projectDir}/pipeline/go_universe.py ${projectDir}/pipeline/inputs/s1_terms.tsv hsa_go_bp.tsv mmu_go_bp.tsv go_universe.json
    """
}

// --full: 3' UTRs of all Ensembl 75 transcripts, identical sequences collapsed.
process UTRS {
    tag "${sp}"
    cpus 1
    memory '16 GB'
    input:
    tuple val(sp), val(gtf), val(genome), val(core)
    path downloads
    output:
    tuple val(sp), path("${sp}.unique.fa"), path("${sp}.map.tsv")
    script:
    """
    ${params.python} ${projectDir}/pipeline/extract_utrs.py ${downloads}/${gtf} ${downloads}/${genome} ${sp}.utr.fa ${downloads}/${core}
    ${params.python} ${projectDir}/pipeline/dedup_utrs.py ${sp}.utr.fa ${sp}.unique.fa ${sp}.map.tsv
    """
}

// --full: miRanda 3.3a, default settings, 50 mature miRNAs per task.
process MIRANDA {
    tag "${sp} ${chunk}"
    cpus 1
    memory '2 GB'
    time '4h'
    input:
    tuple val(sp), path(utrs), path(map), val(chunk), path(downloads)
    output:
    tuple val(sp), path("${sp}.c${chunk}.pairs.tsv")
    script:
    """
    awk -v i=${chunk} 'BEGIN{n=0} /^>/{p=0} /^>${sp}-/{p=1; n++} p && int((n-1)/50)+1==i' ${downloads}/mature.fa > mirs.fa
    bash ${projectDir}/pipeline/run_miranda.sh mirs.fa ${utrs} ${sp}.c${chunk}.pairs.tsv ${params.miranda}
    """
}

process SITES_FULL {
    tag "${sp}"
    publishDir "${params.outdir}/sites", mode: 'copy', pattern: '*.xz'
    memory '8 GB'
    input:
    tuple val(sp), path(pairs), path(map)
    output:
    tuple val(sp), path("${sp}.tsv"), emit: sites
    path "sites_${sp}.txt.xz"
    script:
    """
    ${params.python} ${projectDir}/pipeline/gene_sites.py ${map} ${sp}.tsv ${pairs}
    ${params.python} ${projectDir}/pipeline/sites_codec.py pack ${sp}.tsv sites_${sp}.txt.xz
    """
}

process SITES_COMMITTED {
    tag "${sp}"
    input:
    val sp
    output:
    tuple val(sp), path("${sp}.tsv")
    script:
    """
    ${params.python} ${projectDir}/pipeline/sites_codec.py unpack ${projectDir}/pipeline/inputs/sites_${sp}.txt.xz ${sp}.tsv
    """
}

// Per-study target sets against Supplementary Table S3.
process TARGETS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path hsa_sites
    path hsa_go
    path mmu_sites
    path mmu_go
    output:
    path 'targets_vs_s3.csv'
    script:
    """
    ${params.python} ${projectDir}/pipeline/compare_targets.py ${projectDir}/pipeline/inputs/s3_mirna_lists.tsv ${projectDir}/pipeline/inputs/s3_targets.tsv \\
      targets_vs_s3.csv ${hsa_sites} ${hsa_go} ${mmu_sites} ${mmu_go}
    """
}

// The Supplementary Table S5 positive control: the 8 miRNAs that target 'regulation of
// axonogenesis' most, as a list of its own.
process AXON_SELECT {
    input:
    path hsa_sites
    path hsa_go
    output:
    path 'lists.tsv'
    script:
    """
    ${params.python} ${projectDir}/pipeline/axonogenesis.py select ${hsa_sites} ${hsa_go} ${projectDir}/pipeline/inputs/s5_axonogenesis.tsv axon.tsv
    cat ${projectDir}/pipeline/inputs/s3_mirna_lists.tsv > lists.tsv
    tail -n +2 axon.tsv >> lists.tsv
    """
}

// One empirical null per (species, list size), shared by every list of that size.
process EMPIRICAL {
    tag "${species} ${size}"
    publishDir "${params.outdir}/empirical", mode: 'copy', pattern: '{*.gz,*.hist_*.tsv}'
    cpus 4
    memory '6 GB'
    time '6h'
    input:
    tuple val(species), val(sp), val(size), path(sites), path(go), path(lists)
    output:
    path "${sp}_${size}.counts.tsv.gz", emit: counts
    path "${sp}_${size}.null.tsv.gz", optional: true, emit: nulls
    path "${sp}_${size}.hist*.tsv", optional: true, emit: hist
    script:
    def rerun = params.rerun == 'all' || params.rerun.tokenize(',').contains("${species}:${size}".toString())
    def seed = species == 'Mouse' ? 1000 + size : size
    def hist = (species == 'Human' && size == 39) ? '--hist GO:0006811' : ''
    if (rerun)
        """
        export OMP_NUM_THREADS=${task.cpus} OPENBLAS_NUM_THREADS=${task.cpus}
        ${params.python} ${projectDir}/pipeline/empirical.py --sites ${sites} --go ${go} --lists ${lists} --species ${species} \\
          --size ${size} --iterations ${params.iterations} --seed ${seed} --out ${sp}_${size} ${hist}
        gzip -n ${sp}_${size}.counts.tsv ${sp}_${size}.null.tsv
        """
    else
        """
        cp ${projectDir}/output/empirical/${sp}_${size}.counts.tsv.gz .
        if [ -f ${projectDir}/output/empirical/${sp}_${size}.null.tsv.gz ]; then cp ${projectDir}/output/empirical/${sp}_${size}.null.tsv.gz .; fi
        if [ -n "${hist}" ]; then cp ${projectDir}/output/empirical/${sp}_${size}.hist_GO0006811.tsv .; fi
        """
}

process TABLE2 {
    publishDir "${params.outdir}", mode: 'copy', pattern: '{table2.csv,axonogenesis.json}'
    input:
    path counts
    output:
    path 'table2.csv', emit: table
    path 'axonogenesis.json', emit: axon
    path 'pvalues', emit: pvalues
    script:
    """
    for f in ${counts}; do gunzip -c \$f > \${f%.gz}; done
    ${params.python} ${projectDir}/pipeline/table2.py ${projectDir}/pipeline/params/published_table2.csv . *.counts.tsv
    ${params.python} ${projectDir}/pipeline/axonogenesis.py compare ${projectDir}/pipeline/inputs/s5_axonogenesis.tsv pvalues/Axonogenesis.tsv axonogenesis.json
    """
}

process TABLE1 {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path null39
    output:
    path 'table1.csv', emit: table
    path 's1_check.json', emit: check
    script:
    """
    gunzip -c ${null39} > null39.tsv
    ${params.python} ${projectDir}/pipeline/table1.py ${projectDir}/pipeline/params/published_table1.csv ${projectDir}/pipeline/inputs/s1_terms.tsv null39.tsv .
    """
}

// Figure 1 drawn with base R from our null and, as a drawing check, from the empirical bar heights
// read off the published figure; each compared with the published image.
process FIGURE1 {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path hist
    output:
    path 'figures/*', emit: figures
    path 'compare', emit: compare
    script:
    """
    mkdir figures canvas
    ${params.rscript} ${projectDir}/pipeline/figure1.R ${hist} ${projectDir}/pipeline/params/figure1_params.R canvas/ours
    ${params.rscript} ${projectDir}/pipeline/figure1.R ${projectDir}/pipeline/params/published_empirical_bins.tsv ${projectDir}/pipeline/params/figure1_params.R canvas/published-values
    for k in ours published-values; do
      ${params.python} ${projectDir}/pipeline/compare_figure1.py ${projectDir}/published/figure-1.jpg canvas/\$k.png \\
        ${projectDir}/pipeline/params/regions-figure-1.json compare/figure-1-\$k --crop 0 40 764 690
      cp compare/figure-1-\$k/aligned.png figures/\$k-figure-1.png
      cp canvas/\$k.pdf figures/\$k-figure-1.pdf
      cp canvas/\${k}_bins.csv figures/\$k-figure-1-bins.csv
    done
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path go_summary
    path targets
    path table1
    path s1_check
    path table2
    path axon
    path compare
    path figures
    output:
    path 'report.md', emit: report
    path 'results_table.csv', emit: table
    script:
    """
    mkdir run
    cp ${go_summary} ${targets} ${table1} ${s1_check} ${table2} ${axon} run/
    cp -r ${compare} run/compare
    mkdir run/figures && cp ${figures} run/figures/
    ${params.python} ${projectDir}/pipeline/check_reproduction.py run ${projectDir}/output .
    """
}

process PAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path figures
    path compare
    output:
    path 'site/index.html'
    script:
    """
    mkdir run figs
    cp ${results} run/
    cp ${figures} figs/
    ${params.python} ${projectDir}/pipeline/build_page.py run figs ${compare} ${projectDir}/published site/index.html
    """
}

workflow {
    dl = FETCH()
    SUPPLEMENT(dl)
    go = GO(dl)
    if (params.full) {
        genomes = Channel.of(
            ['hsa', 'Homo_sapiens.GRCh37.75.gtf.gz', 'Homo_sapiens.GRCh37.75.dna.toplevel.fa.gz', 'homo_sapiens_core_75_37'],
            ['mmu', 'Mus_musculus.GRCm38.75.gtf.gz', 'Mus_musculus.GRCm38.75.dna.toplevel.fa.gz', 'mus_musculus_core_75_38'])
        utrs = UTRS(genomes, dl)
        chunks = utrs.flatMap { sp, fa, map -> (1..(sp == 'hsa' ? 52 : 39)).collect { [sp, fa, map, it] } }
        pairs = MIRANDA(chunks.combine(dl))
        grouped = pairs.groupTuple().join(utrs.map { sp, fa, map -> [sp, map] })
        sites = SITES_FULL(grouped).sites
    } else {
        sites = SITES_COMMITTED(Channel.of('hsa', 'mmu'))
    }
    hsa = sites.filter { it[0] == 'hsa' }.map { it[1] }
    mmu = sites.filter { it[0] == 'mmu' }.map { it[1] }
    targets = TARGETS(hsa, go.hsa, mmu, go.mmu)
    lists = AXON_SELECT(hsa, go.hsa)
    sizes = Channel.of(
        ['Human', 'hsa', 1], ['Human', 'hsa', 2], ['Human', 'hsa', 3], ['Human', 'hsa', 5],
        ['Human', 'hsa', 8], ['Human', 'hsa', 9], ['Human', 'hsa', 10], ['Human', 'hsa', 11],
        ['Human', 'hsa', 15], ['Human', 'hsa', 18], ['Human', 'hsa', 25], ['Human', 'hsa', 26],
        ['Human', 'hsa', 39], ['Human', 'hsa', 46], ['Human', 'hsa', 130], ['Human', 'hsa', 176],
        ['Mouse', 'mmu', 1], ['Mouse', 'mmu', 8], ['Mouse', 'mmu', 10], ['Mouse', 'mmu', 12],
        ['Mouse', 'mmu', 27], ['Mouse', 'mmu', 37])
    gos = go.hsa.map { ['hsa', it] }.mix(go.mmu.map { ['mmu', it] })
    inputs = sizes.map { species, sp, size -> [sp, species, size] }
        .combine(sites, by: 0)
        .combine(gos, by: 0)
        .map { sp, species, size, s, g -> [species, sp, size, s, g] }
        .combine(lists)
    emp = EMPIRICAL(inputs)
    t2 = TABLE2(emp.counts.collect())
    null39 = emp.nulls.filter { it.name == 'hsa_39.null.tsv.gz' }
    t1 = TABLE1(null39)
    fig = FIGURE1(emp.hist.flatten().filter { it.name.startsWith('hsa_39.hist') })
    ck = CHECK(go.summary, targets, t1.table, t1.check, t2.table, t2.axon, fig.compare, fig.figures)
    PAGE(ck.table.mix(go.summary, targets, t1.table, t1.check, t2.table, t2.axon).collect(), fig.figures, fig.compare)
}
