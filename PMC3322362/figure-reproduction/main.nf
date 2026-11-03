// Reproduce PMC3322362 (Muppirala et al. 2011, RPISeq): Table 1, Fig. 1 and the hub checks of Fig. 2.
// Run: nextflow run main.nf --outdir results [--python python3] [--java java] [--javac javac] [--sources DIR]
// --sources reuses local copies of the inputs (file names as in pipeline/fetch_inputs.sh).

process FETCH {
    output:
    path 'S3.txt', emit: s3
    path '*.rpi', emit: rpi2241
    path 'ipminer369*', emit: ipminer
    path '*.jar', emit: jars
    script:
    """
    bash ${projectDir}/pipeline/fetch_inputs.sh ${params.sources ?: ''}
    """
}

process ENCODE {
    input:
    path s3
    path rpi2241
    path ipminer
    output:
    path '*.arff', emit: arff
    path 'neg369_s*.rpi', emit: neg369
    script:
    """
    P=${projectDir}/pipeline
    ${params.python} \$P/encode.py arff rpi2241.arff pos2241.rpi neg2241.rpi
    for s in \$(seq 1 ${params.seeds}); do
      ${params.python} \$P/negatives369.py pos2241.rpi ${s3} \$s neg369_s\$s.rpi
      ${params.python} \$P/encode.py arff rpi369_s\$s.arff pos2241.rpi neg369_s\$s.rpi --rpi369 ${s3}
    done
    ${params.python} \$P/encode.py arff-pairs rpi369_ipminer.arff ipminer369.tsv ipminer369_protein.fa ipminer369_rna.fa
    ${params.python} \$P/encode.py arff-unlabelled hubs.arff \$P/inputs/fig2c_hubs.tsv
    """
}

process COMPILE {
    input:
    path jars
    output:
    path 'classes'
    script:
    """
    mkdir classes
    ${params.javac} -nowarn -cp weka.jar:pentaho-package-manager.jar -d classes ${projectDir}/pipeline/RpiWeka.java
    """
}

process CV {
    tag "${name} ${clf}"
    publishDir "${params.outdir}/cv", mode: 'copy'
    input:
    tuple val(name), val(clf), path(arff)
    path jars
    path classes
    output:
    path "${name}_${clf}.*"
    script:
    """
    ${params.java} -Xmx4g -cp weka.jar:pentaho-package-manager.jar:classes RpiWeka cv ${clf} ${arff} 10 1 ${name}_${clf}
    """
}

process HUBS {
    tag "${train} ${clf}"
    publishDir "${params.outdir}/hubs", mode: 'copy'
    input:
    tuple val(train), val(clf), path(arff), path(hubs)
    path jars
    path classes
    output:
    path "hubs_${train}_${clf}.csv"
    script:
    """
    ${params.java} -Xmx4g -cp weka.jar:pentaho-package-manager.jar:classes RpiWeka train ${clf} ${arff} ${hubs} hubs_${train}_${clf}.csv
    """
}

process FIG1 {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path cv
    output:
    path 'output/*'
    script:
    """
    P=${projectDir}/pipeline
    mkdir -p output
    curves="rpi2241_rf.predictions.csv rpi2241_svm.predictions.csv rpi369_s1_rf.predictions.csv rpi369_s1_svm.predictions.csv"
    ${params.python} \$P/fig1.py \$P/params/fig1.json output/fig1_ours \$curves
    ${params.python} \$P/compare_fig1.py \$P/params/fig1.json ${projectDir}/published/figure-1.jpg output/fig1_curves.json \$curves
    ${params.python} \$P/compare_figure.py --published ${projectDir}/published/figure-1.jpg --render output/fig1_ours.png \
      --out output/fig1_compare --published-grey 255 --render-grey 255 --regions \$P/params/fig1_regions.json --window 12
    """
}

process TABLES {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path cv
    path hubs
    path fig1
    output:
    path 'tables.json'
    script:
    """
    mkdir -p cvdir hubdir
    mv *.summary.json cvdir/
    mv hubs_*.csv hubdir/
    ${params.python} ${projectDir}/pipeline/make_tables.py cvdir ${projectDir}/pipeline/inputs/fig2c_hubs.tsv hubdir \
      fig1_ours.roc.json fig1_curves.json tables.json
    """
}

process CHECK {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path tables
    output:
    path 'report.md'
    script:
    """
    ${params.python} ${projectDir}/pipeline/check_reproduction.py ${tables} > report.md || { cat report.md; exit 1; }
    """
}

workflow {
    inputs = FETCH()
    enc = ENCODE(inputs.s3, inputs.rpi2241, inputs.ipminer)
    classes = COMPILE(inputs.jars)
    arffs = enc.arff.flatten().map { f -> [f.baseName, f] }
    clfs = Channel.of('rf', 'svm')
    jobs = arffs.filter { it[0] != 'hubs' }.combine(clfs).map { name, f, clf -> [name, clf, f] }
    cv = CV(jobs, inputs.jars, classes)
    hubs_arff = arffs.filter { it[0] == 'hubs' }.map { it[1] }
    train = arffs.filter { it[0] in ['rpi2241', 'rpi369_s1'] }
        .map { name, f -> [name == 'rpi2241' ? '2241' : '369', f] }
        .combine(clfs).combine(hubs_arff)
        .map { t, f, clf, h -> [t, clf, f, h] }
    hubs = HUBS(train, inputs.jars, classes)
    all_cv = cv.flatten().collect()
    fig1 = FIG1(all_cv)
    fig1_json = fig1.flatten().filter { it.name in ['fig1_ours.roc.json', 'fig1_curves.json'] }.collect()
    tables = TABLES(all_cv, hubs.collect(), fig1_json)
    CHECK(tables)
}
