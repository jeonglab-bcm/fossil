// Reproduce PMC2563693 (Lee, Chuang, Kim, Ideker and Lee 2008, "Inferring pathway activity toward
// precise disease classification", PLoS Comput Biol 4:e1000217). The authors' software is lost;
// the method is the package PMC2563693/package (pacorg), written from the paper's Methods.
//
// Run from the repository root:
//   nextflow run PMC2563693/figure-reproduction/main.nf --outdir results [--full]
//
// Default (CI, about 15 minutes on 4 cores): download and check the inputs, build the seven
// datasets, recompute Fig. 2, Figs S1 and S5, the CORGs of Table 1 and Table S2 and the Fig. 4
// activities from scratch; rerun the first two repeats of every cross-validation experiment
// and check them against the committed results of the full run (output/cv); summarize and
// compare everything from those committed results; check the package; compare the run with the
// committed outputs.
// --full: rerun all 100 repeats of 5-fold cross-validation for the 7 datasets and 4 dataset
//   pairs (Figs 3, S2, S3, Tables 1 and S2 frequencies), about 3.3 CPU hours: run it on a
//   cluster (-profile skyriver) or a large machine, then commit results/cv as output/cv.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.full = false
params.check_repeats = 2

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.annotation = "${projectDir}/annotation"
params.pkgsrc = "${projectDir}/../package/src"

def py = { -> "PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} -W ignore" }

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process PREPARE {
    publishDir "${params.outdir}", mode: 'copy', pattern: 'datasets.json'
    input:
    path downloads
    output:
    path 'data', emit: data
    path 'datasets.json', emit: record
    script:
    """
    ${py()} ${params.pipe}/export_bioc.py ${downloads}/bioc/seventyGeneData/data/vanDeVijver.rda ${downloads}/bioc/stjudem/data/stjude.rda ${downloads}/bioc_export
    ${py()} ${params.pipe}/prepare_data.py ${downloads} ${params.annotation} data
    cp data/datasets.json datasets.json
    """
}

process MARKERS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path data
    path downloads
    output:
    path 'markers'
    script:
    """
    mkdir markers
    ${py()} ${params.pipe}/markers.py ${data} ${downloads} ${params.annotation} markers
    ${py()} ${params.pipe}/fig2.py ${data} markers/fig2.json
    """
}

process ROBUSTNESS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path data
    output:
    path 'robustness.json'
    script:
    """
    ${py()} ${params.pipe}/robustness.py ${data} robustness.json 100
    """
}

process HYPOTHESES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path data
    path downloads
    output:
    path 'hypotheses.json'
    script:
    """
    ${py()} ${params.pipe}/hypotheses.py ${data} ${downloads} ${params.annotation} ${projectDir}/variants hypotheses.json > /dev/null
    """
}

process CV_CHUNK {
    cpus 1
    input:
    tuple val(args), path(data)
    output:
    path 'cv'
    script:
    """
    ${py()} ${params.pipe}/cv.py ${data} cv ${args}
    """
}

process CV_PACK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path chunks, stageAs: 'chunk*' 
    output:
    path 'cv'
    script:
    """
    mkdir -p all/within all/cross
    for c in chunk*; do cp -r \$c/. all/; done
    ${py()} ${params.pipe}/pack_cv.py pack all cv
    """
}

process CV_COMMITTED {
    output:
    path 'cv'
    script:
    """
    mkdir cv && cp -r ${params.committed}/cv/. cv/
    """
}

process CV_CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path chunks, stageAs: 'chunk*' 
    path packs
    output:
    path 'cv_check.json'
    script:
    """
    mkdir -p fresh/within fresh/cross
    for c in chunk*; do cp -r \$c/. fresh/; done
    ${py()} ${params.pipe}/pack_cv.py check fresh ${packs} cv_check.json
    """
}

process COMPARE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path packs
    path markers
    path robustness
    path record
    path hypotheses
    path downloads
    output:
    path 'run', emit: run
    path 'figures', emit: figures
    script:
    """
    mkdir run
    cp -r ${markers}/. run/
    cp ${robustness} ${record} ${hypotheses} run/
    ${py()} ${params.pipe}/reduce_cv.py ${packs} run/cv_summary.json
    ${py()} ${params.pipe}/read_published.py ${downloads}/paper/supp run/published_vector.json > /dev/null
    ${py()} ${params.pipe}/digitize.py ${projectDir}/published run/digitized.json > /dev/null
    ${py()} ${params.pipe}/compare.py run run/comparison.json
    ${py()} ${params.pipe}/render.py run ${projectDir}/published ${downloads}/paper/supp figures
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
    path run
    path figures
    path cv_check
    path package_json
    output:
    path 'results.json'
    path 'report.md'
    path 'site'
    path 'output'
    script:
    """
    cp ${cv_check} ${package_json} ${run}/
    ${py()} ${params.pipe}/build_results.py ${run} results.json
    mkdir -p output && cp -r ${run}/. output/ && rm -rf output/figures && cp -r ${figures} output/figures
    ${py()} ${params.pipe}/check_reproduction.py results.json output ${params.committed} report.md
    ${py()} ${params.pipe}/build_page.py results.json output ${projectDir}/published site/index.html
    """
}

workflow {
    dl = FETCH()
    prep = PREPARE(dl)
    mk = MARKERS(prep.data, dl)
    rb = ROBUSTNESS(prep.data)
    hy = HYPOTHESES(prep.data, dl)
    def names = ['nfkb', 'leukemia', 'prostate', 'breast_netherlands', 'breast_usa', 'lung_michigan', 'lung_boston']
    def pairs = [['breast_netherlands', 'breast_usa'], ['breast_usa', 'breast_netherlands'],
                 ['lung_michigan', 'lung_boston'], ['lung_boston', 'lung_michigan']]
    def tasks = []
    if (params.full) {
        names.each { n -> (0..9).each { c -> tasks << "within ${n} ${10 * c} ${10 * c + 10}" } }
        pairs.each { p -> (0..9).each { c -> tasks << "cross ${p[0]} ${p[1]} ${10 * c} ${10 * c + 10}" } }
    } else {
        names.each { n -> tasks << "within ${n} 0 ${params.check_repeats}" }
        pairs.each { p -> tasks << "cross ${p[0]} ${p[1]} 0 ${params.check_repeats}" }
    }
    chunks = CV_CHUNK(channel.fromList(tasks).combine(prep.data)).collect()
    packs = params.full ? CV_PACK(chunks) : CV_COMMITTED()
    ck = CV_CHECK(chunks, packs)
    cmp = COMPARE(packs, mk, rb, prep.record, hy, dl)
    pk = PACKAGE()
    RESULTS(cmp.run, cmp.figures, ck, pk)
}
