// Reproduce PMC2813257 (Neher and Leitner 2010, "Recombination rate and selection strength in HIV
// intra-patient evolution"). The authors' scripts were never released; the method is the package
// PMC2813257/package (hivrecomb), written from the paper's text (see README.md).
//
// Run from the repository root:
//   nextflow run PMC2813257/figure-reproduction/main.nf --outdir results [--studies] [--sources DIR]
//
// Default (CI, about 10 minutes): download the 1,753 GenBank clones and LANL's clinical file,
// build MUSCLE 3.6 from its source, align each patient, run both analyses, draw the four panels
// and their controls, score them against the published figures, build results.json, check the
// package, and compare the run with the committed outputs.
// --studies: also run the hypothesis tests behind the causes in results.json (the 2005 MUSCLE
//   binary needs --alt-muscle, the other tests take about 15 minutes more).
// --sources DIR: reuse a local copy of the downloads instead of fetching them.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.studies = false
params.boot = 500
params.seed = 0

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.published = "${projectDir}/published"
params.pkgsrc = "${projectDir}/../package/src"
params.pkg = "${projectDir}/../package"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ?: ''}
    """
}

process ALIGN {
    publishDir "${params.outdir}", mode: 'copy', pattern: 'alignments/samples.tsv'
    input:
    path downloads
    output:
    path 'alignments'
    script:
    """
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/prepare_data.py \\
        ${downloads}/genbank/env.gb ${downloads}/lanl/set1_clinical_data.txt \\
        ${downloads}/muscle/muscle alignments
    """
}

process ANALYZE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path alignments
    output:
    path 'analysis.json'
    path 'bootstrap.npy'
    path 'rates_*.npy'
    script:
    """
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/analyze.py ${alignments} . \\
        --boot ${params.boot} --seed ${params.seed}
    """
}

process READ_PUBLISHED {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'published_values.json'
    path 'published'
    script:
    """
    ${params.python} ${params.pipe}/read_published.py ${params.published} .
    """
}

process RENDER {
    input:
    path analysis
    path bootstrap
    output:
    path 'figures'
    script:
    """
    ${params.python} ${params.pipe}/render.py ${analysis} ${params.published} figures
    """
}

process COMPARE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path figures
    path published
    path published_values
    output:
    path 'comparison.json'
    path 'figures'
    script:
    """
    ${params.python} ${params.pipe}/compare.py .
    """
}

process STUDIES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path alignments
    path downloads
    output:
    path 'studies.json'
    script:
    """
    PYTHONPATH=${params.pkgsrc} ${params.python} ${params.pipe}/studies.py ${alignments} studies.json \\
        --shriner ${downloads}/lanl/set1_Shriner.fasta --genbank ${downloads}/genbank/env.gb \\
        --clinical ${downloads}/lanl/set1_clinical_data.txt --muscle ${downloads}/muscle/muscle
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${params.pipe}/check_package.py ${params.pkg} --json package.json || true
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path analysis
    path published_values
    path comparison
    path package_json
    output:
    path 'results.json'
    script:
    """
    ${params.python} ${params.pipe}/build_results.py ${projectDir}/results_notes.json \\
        ${analysis} ${published_values} ${comparison} ${package_json} results.json
    ${params.python} ${params.pipe}/check_results.py results.json --write --root ${projectDir}/..
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path figures
    path comparison
    path analysis
    path published_values
    path package_json
    output:
    path 'report.md'
    script:
    """
    mkdir -p run/figures
    cp ${results} ${comparison} ${analysis} ${published_values} ${package_json} run/
    cp figures/* run/figures/
    ${params.python} ${params.pipe}/check_reproduction.py ${results} run ${params.committed} report.md ${projectDir}/..
    """
}

process BUILD_PAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path figures
    path published
    output:
    path 'site'
    script:
    """
    mkdir -p site
    ${params.python} ${params.pipe}/build_page.py ${results} figures ${published} site/index.html
    """
}

workflow {
    downloads = FETCH()
    alignments = ALIGN(downloads)
    (analysis, bootstrap, rates) = ANALYZE(alignments)
    (published_values, published) = READ_PUBLISHED()
    figures = RENDER(analysis, bootstrap)
    (comparison, scored) = COMPARE(figures, published, published_values)
    package_json = PACKAGE()
    results = RESULTS(analysis, published_values, comparison, package_json)
    CHECK(results, scored, comparison, analysis, published_values, package_json)
    BUILD_PAGE(results, scored, published)
    if (params.studies) {
        STUDIES(alignments, downloads)
    }
}
