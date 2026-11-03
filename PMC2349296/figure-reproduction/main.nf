// Reproduce PMC2349296 (Pyysalo et al. 2008, "Comparative analysis of five protein-protein
// interaction corpora"): Tables 2-4, Figs 1-2 and the summary claims, plus the comparison page
// that site/PMC2349296/index.html is copied from.
// Run: nextflow run main.nf --outdir results [--python python3] [--rscript Rscript] [--sources DIR]
// --sources DIR reuses local copies of the downloads (see pipeline/fetch_inputs.sh).

params.outdir = 'results'
params.python = 'python3'
params.rscript = 'Rscript'
params.java = 'java'
params.sources = null


process FETCH {
    output:
    path 'corpora', emit: corpora
    path 'medpost', emit: medpost
    path 'stanford-parser', emit: parser
    path 'relex_page.html', emit: relex_page
    script:
    """
    bash ${projectDir}/pipeline/fetch_inputs.sh ${params.sources ?: ''}
    """
}

// Co-occurrence baseline (Tables 2 and 4) and corpus statistics (Table 3).
process COOCCURRENCE {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path corpora
    output:
    path 'co/cooccurrence.csv', emit: cooc
    path 'co/table3.csv', emit: table3
    path 'co/corpus_counts.csv', emit: counts
    script:
    """
    ${params.python} ${projectDir}/pipeline/cooccurrence.py ${corpora} co
    """
}

// MedPost: build, tokenize and tag (Penn tags); token alignment; parser input.
process MEDPOST {
    publishDir "${params.outdir}/data", mode: 'copy', pattern: 'pre/tokens_medpost.csv'
    input:
    path corpora
    path medpost
    output:
    path 'pre', emit: pre
    script:
    """
    bash ${projectDir}/pipeline/build_medpost.sh ${medpost}
    ${params.python} ${projectDir}/pipeline/preprocess.py medpost-input ${corpora} mp
    for c in AIMed BioInfer HPRD50 IEPA LLL; do
      for v in orig split; do
        ${medpost}/medpost -idtext -id -penn -nosegment < mp/\$c.\$v.mp_in > mp/\$c.\$v.mp_out
      done
    done
    ${params.python} ${projectDir}/pipeline/preprocess.py align ${corpora} mp pre
    """
}

// Stanford Lexicalized Parser 1.5.1, englishPCFG, MedPost tags, collapsed typed dependencies.
// 1.5.1 picks a pair's relation by iterating a HashSet of relation objects hashed by identity
// (GrammaticalStructure.getGrammaticalRelation), so its output depends on the JVM build: Java 11
// and Java 24 give different relations for some pairs. -XX:hashCode=2 makes every identity hash
// equal, so the sets iterate in insertion order and the output is the same on every JVM.
process PARSE {
    tag "${corpus}"
    cpus 1
    memory '6 GB'
    input:
    tuple val(corpus), path(pre)
    path parser
    output:
    path "${corpus}.parse.xml"
    script:
    """
    ${params.java} -XX:+UnlockExperimentalVMOptions -XX:hashCode=2 -mx5g -cp ${parser}/stanford-parser.jar edu.stanford.nlp.parser.lexparser.LexicalizedParser \\
      -tokenized -tagSeparator / -sentences newline \\
      -outputFormat 'wordsAndTags,typedDependenciesCollapsed' -outputFormatOptions xml \\
      ${parser}/englishPCFG.ser.gz ${pre}/${corpus}.parse_in > ${corpus}.parse.xml 2> ${corpus}.parse.log
    grep -q 'Parsed file' ${corpus}.parse.log
    """
}

process RELEX {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path pre
    path parses
    path relex_page
    output:
    path 'relex/relex.csv'
    script:
    """
    mkdir parses && cp ${parses} parses/
    ${params.python} ${projectDir}/pipeline/extract_terms.py ${relex_page} relex_terms.txt
    ${params.python} ${projectDir}/pipeline/relex.py ${pre} parses relex_terms.txt relex
    """
}

process CLAIMS {
    publishDir "${params.outdir}/data", mode: 'copy'
    input:
    path cooc
    path relex
    path table3
    output:
    path 'claims.csv', emit: claims
    path 'figure_values.csv', emit: values
    script:
    """
    ${params.rscript} ${projectDir}/pipeline/claims.R ${projectDir}/pipeline/published_values.csv ${cooc} ${relex} ${table3} claims.csv figure_values.csv
    """
}

// Figs 1 and 2 drawn with base R from our values and, as a drawing check, from the published
// values; each compared with the published image.
process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path values
    output:
    path 'figures/*', emit: figures
    path 'compare', emit: compare
    script:
    """
    mkdir figures
    ${params.rscript} ${projectDir}/pipeline/figures.R ${values} ${projectDir}/pipeline/params/figure_params.R figures/ours
    ${params.rscript} ${projectDir}/pipeline/figures.R ${projectDir}/pipeline/published_values.csv ${projectDir}/pipeline/params/figure_params.R figures/published-values
    for i in 1 2; do
      for k in ours published-values; do
        ${params.python} ${projectDir}/pipeline/compare_figures.py ${projectDir}/published/figure-\$i.jpg figures/\$k-figure-\$i.png \\
          ${projectDir}/pipeline/params/regions-figure-\$i.json compare/figure-\$i-\$k
      done
    done
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path cooc
    path table3
    path counts
    path pre
    path relex
    path claims
    path compare
    output:
    path 'report.md', emit: report
    path 'results_table.csv', emit: table
    script:
    """
    mkdir run
    cp ${cooc} ${table3} ${counts} ${relex} ${claims} run/
    cp ${pre}/tokens_medpost.csv run/
    cp -r ${compare} run/compare
    ${params.python} ${projectDir}/pipeline/check_reproduction.py run ${projectDir}/output ${projectDir}/pipeline/published_tables.csv .
    """
}

process PAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path report
    path table
    path claims
    path figures
    path compare
    path counts
    output:
    path 'site/index.html'
    script:
    """
    mkdir figs && cp ${figures} figs/
    ${params.python} ${projectDir}/pipeline/build_page.py ${table} ${claims} figs ${compare} ${counts} ${projectDir}/published site/index.html
    """
}

workflow {
    f = FETCH()
    co = COOCCURRENCE(f.corpora)
    mp = MEDPOST(f.corpora, f.medpost)
    corpora = Channel.of('AIMed', 'BioInfer', 'HPRD50', 'IEPA', 'LLL')
    parses = PARSE(corpora.combine(mp.pre), f.parser)
    rx = RELEX(mp.pre, parses.collect(), f.relex_page)
    cl = CLAIMS(co.cooc, rx, co.table3)
    fig = FIGURES(cl.values)
    ck = CHECK(co.cooc, co.table3, co.counts, mp.pre, rx, cl.claims, fig.compare)
    PAGE(ck.report, ck.table, cl.claims, fig.figures, fig.compare, co.counts)
}
