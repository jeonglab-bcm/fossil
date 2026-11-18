// Reproduce PMC3446288 (Weischenfeldt et al. 2012, "Mammalian tissues defective in nonsense-mediated
// mRNA decay display highly aberrant splicing patterns"). The authors' RAINMAN pipeline is lost; the
// method is the Python package PMC3446288/package (nmdsplice), rebuilt from the paper's text.
//
// Run from the repository root, in the environment of environment.yml:
//   nextflow run PMC3446288/figure-reproduction/main.nf --outdir results [--full] [--sources DIR] [--cpus N]
//
// Default (CI, about 15 minutes on 4 cores): download the UCSC mm9 annotation and genome and the
// paper's supplementary files and check their SHA-256; read the junction counts and gene counts of
// the four samples from the committed mapping (output/mapping); call PTCs, regulation and splice
// classes; count RefSeq stops and genome trinucleotides; read the phastCons profiles from the
// committed output/conservation.json; draw and score every figure; check the package; compare with
// the paper; write results.json and the results page; check the run against the committed outputs.
// --full: also download the reads (SRA), the Bowtie index, the GEO TopHat alignments and phastCons
//   (about 9 GB), build the junction database, map the four samples (about 6 hours on 4 cores),
//   rebuild the junction table and the phastCons profiles, and use those instead of the committed ones.

params.outdir = 'results'
params.python = 'python3'
params.rscript = 'Rscript'
params.sources = null
params.full = false
params.cpus = 4

params.pipe = "${projectDir}/pipeline"
params.published = "${projectDir}/published"
params.committed = "${projectDir}/output"
params.notes = "${projectDir}/results_notes.json"
params.pkg = "${projectDir}/../package"

def SAMPLES = [['BMM_WT', 'SRR094621', 'GSM653000_BMM_WT'], ['BMM_KO', 'SRR094622', 'GSM653001_BMM_KO'],
               ['Liver_WT', 'SRR094623', 'GSM653002_Liver_WT'], ['Liver_KO', 'SRR094624', 'GSM653003_Liver_KO']]

process FETCH {
    output:
    path 'inputs'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh inputs ${params.full ? '--full' : ''} ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process JUNCTION_DB {
    publishDir "${params.outdir}/mapping", mode: 'copy', pattern: '*.json'
    input:
    path inputs
    output:
    path 'jdb', emit: jdb
    path 'jdb_stats.json'
    script:
    """
    mkdir jdb
    PYTHONPATH=${params.pkg}/src ${params.python} ${params.pipe}/build_junction_db.py ${inputs}/annot ${inputs}/genome/mm9.fa jdb/junctions.fa jdb_stats.json
    bowtie-build -q jdb/junctions.fa jdb/junctions && rm jdb/junctions.fa
    """
}

process MAP {
    cpus params.cpus
    publishDir "${params.outdir}/mapping", mode: 'copy', pattern: '*_mapping_stats.json'
    input:
    tuple val(sample), val(run), val(gsm), path(inputs), path(jdb)
    output:
    tuple val(sample), path("${sample}"), emit: mapped
    path "${sample}_mapping_stats.json"
    script:
    """
    fasterq-dump -e ${task.cpus} -O fq ${inputs}/sra/${run}.sra && gzip -1 fq/${run}.fastq
    BOWTIE=bowtie ${params.python} ${params.pipe}/map_sample.py fq/${run}.fastq.gz ${inputs}/genome/genome ${jdb}/junctions ${sample} --threads ${task.cpus}
    rm -rf fq
    cp ${sample}/mapping_stats.json ${sample}_mapping_stats.json
    """
}

process SUMMARIZE {
    publishDir "${params.outdir}/mapping", mode: 'copy'
    input:
    tuple val(sample), path(mapdir), val(gsm), path(inputs)
    output:
    path "${sample}_*"
    path "${sample}.db.tsv", emit: db
    path "${sample}.tophat.tsv", emit: tophat
    script:
    """
    PYTHONPATH=${params.pkg}/src ${params.python} ${params.pipe}/summarize_mapping.py ${mapdir} ${inputs}/annot ${inputs}/genome/mm9.fa.fai ${sample} .
    cp ${mapdir}/junction_counts.tsv ${sample}.db.tsv
    tar -xOf ${inputs}/geo/GSE26561_RAW.tar ${gsm}_aligned.SAM.gz | zcat | bash ${params.pipe}/tophat_junctions.sh | sort -k1,1 -k2,2n -k3,3n > ${sample}.tophat.tsv
    """
}

process JUNCTION_TABLE {
    publishDir "${params.outdir}/mapping", mode: 'copy'
    input:
    path db
    path tophat
    output:
    path 'junctions.tsv.gz'
    script:
    def args = SAMPLES.collect { "--db ${it[0]} ${it[0]}.db.tsv --tophat ${it[0]} ${it[0]}.tophat.tsv" }.join(' ')
    """
    ${params.python} ${params.pipe}/build_junction_table.py junctions.tsv.gz ${args}
    """
}

process COMMITTED_MAPPING {
    output:
    path 'mapping'
    script:
    """
    cp -r ${params.committed}/mapping mapping
    """
}

process GATHER_MAPPING {
    input:
    path files
    output:
    path 'mapping'
    script:
    """
    mkdir mapping && cp ${files} mapping/
    """
}

process REFSEQ_STOPS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path inputs
    output:
    path 'refseq_stops.json'
    script:
    """
    PYTHONPATH=${params.pkg}/src ${params.python} ${params.pipe}/refseq_stops.py ${inputs}/annot ${inputs}/genome/mm9.fa refseq_stops.json 2> /dev/null
    """
}

process ANALYZE {
    publishDir "${params.outdir}", mode: 'copy', pattern: '{analysis.json,events.tsv.gz,figure_data.json}'
    input:
    path inputs
    path mapping
    output:
    path 'analysis.json', emit: analysis
    path 'figure_data.json', emit: figdata
    path 'events.tsv.gz', emit: events
    path 'junctions_annotated.tsv.gz', emit: junctions
    path 'junction_matrix_for_edger.tsv.gz', emit: matrix
    script:
    """
    PYTHONPATH=${params.pkg}/src ${params.python} ${params.pipe}/analyze.py ${mapping}/junctions.tsv.gz ${mapping} ${mapping} ${inputs}/annot ${inputs}/genome/mm9.fa .
    """
}

process CONSERVATION {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path inputs
    path events
    path figdata
    path junctions
    output:
    path 'conservation.json'
    script:
    if (params.full)
        """
        PYTHONPATH=${params.pkg}/src ${params.python} ${params.pipe}/conservation.py ${events} ${figdata} ${junctions} ${inputs}/annot ${inputs}/phastcons conservation.json
        """
    else
        """
        cp ${params.committed}/conservation.json .
        """
}

process PORT_CHECKS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path inputs
    path matrix
    output:
    path 'port_checks.json'
    script:
    """
    PYTHONPATH=${params.pkg}/src ${params.python} ${params.pipe}/port_checks.py ${inputs}/supp ${inputs}/annot ${inputs}/genome/mm9.fa ${matrix} ${params.pipe}/paper_values.json port_checks.json --rscript ${params.rscript} > /dev/null
    """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path analysis
    path figdata
    path conservation
    path stops
    output:
    path 'figs/*'
    script:
    """
    cd ${params.pipe} && PYTHONPATH=${params.pkg}/src ${params.python} figures.py \$OLDPWD/${analysis} \$OLDPWD/${figdata} \$OLDPWD/${conservation} \$OLDPWD/${stops} ${params.published} \$OLDPWD/figs
    """
}

process COMPARE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path analysis
    path figs
    path conservation
    path stops
    path mapping
    path port
    output:
    path 'comparison.json'
    script:
    """
    ${params.python} ${params.pipe}/compare.py ${params.pipe}/paper_values.json ${analysis} figures.json ${conservation} ${stops} ${mapping}/jdb_stats.json ${port} comparison.json
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${params.pipe}/check_package.py ${params.pkg} --json package.json > package.log 2>&1 || { cat package.log; exit 1; }
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path comparison
    path pkg
    output:
    path 'results.json'
    script:
    """
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py ${params.notes} ${comparison} results.json \
        --package ${pkg} --inputs ${params.pipe}/fetch_inputs.sh --env env.json
    ${params.python} ${params.pipe}/check_results.py results.json --write --root ${projectDir}/..
    """
}

process PAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path figs
    output:
    path 'site'
    path 'report.md'
    script:
    """
    mkdir f && cp ${figs} f/
    ${params.python} ${params.pipe}/build_page.py ${results} f ${params.published} site
    ${params.python} ${params.pipe}/check_results.py ${results} --markdown --root ${projectDir}/.. > report.md || true
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path comparison
    path analysis
    path figdata
    path events
    path conservation
    path stops
    path port
    path pkg
    path figs
    output:
    path 'check.json'
    script:
    """
    mkdir fresh && cp ${results} ${comparison} ${analysis} ${figdata} ${events} ${conservation} ${stops} ${port} ${pkg} fresh/
    mkdir fresh/figs && cp ${figs} fresh/figs/
    ${params.python} ${params.pipe}/check_reproduction.py fresh ${params.committed} ${projectDir}/.. check.json
    """
}

workflow {
    inputs = FETCH()
    if (params.full) {
        jdb = JUNCTION_DB(inputs)
        samples = Channel.fromList(SAMPLES)
        mapped = MAP(samples.combine(inputs).combine(jdb.jdb).map { s, r, g, i, j -> tuple(s, r, g, i, j) })
        gsm = Channel.fromList(SAMPLES).map { s, r, g -> tuple(s, g) }
        sm = SUMMARIZE(mapped.mapped.join(gsm).combine(inputs))
        jt = JUNCTION_TABLE(sm.db.collect(), sm.tophat.collect())
        mapping = GATHER_MAPPING(sm[0].flatten().mix(jt, jdb[1], mapped[1]).collect())
    } else {
        mapping = COMMITTED_MAPPING()
    }
    st = REFSEQ_STOPS(inputs)
    an = ANALYZE(inputs, mapping)
    cons = CONSERVATION(inputs, an.events, an.figdata, an.junctions)
    port = PORT_CHECKS(inputs, an.matrix)
    figs = FIGURES(an.analysis, an.figdata, cons, st)
    cmp = COMPARE(an.analysis, figs.collect(), cons, st, mapping, port)
    pk = PACKAGE()
    res = RESULTS(cmp, pk)
    PAGE(res, figs.collect())
    CHECK(res, cmp, an.analysis, an.figdata, an.events, cons, st, port, pk, figs.collect())
}
