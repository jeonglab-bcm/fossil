// Reproduce PMC4457112 (Cohen, Smalheiser, McDonagh, Yu, Adams, Davis and Yu 2015, "Automated confidence
// ranked classification of randomized controlled trial articles"). The RCT Tagger's code and model were
// never released and its web service is gone; the method is the package PMC4457112/package (rctconf),
// rebuilt from the paper's text.
//
// Run from the repository root, with the pinned requirements and the package installed:
//   pip install -r PMC4457112/figure-reproduction/requirements.txt ./PMC4457112/package
//   nextflow run PMC4457112/figure-reproduction/main.nf --outdir results [--full] [--extract]
//
// Every run (minutes): the mini reproduction (three baseline files downloaded and SHA-256 checked, then
//   every step of the full run on them: extraction, dataset, features, forward selection, the eight
//   models, scoring) checked against the committed output/mini; the comparison of the committed full
//   run with Tables 1-3 and the claims; the package check; results.json; the results page; the check
//   against the committed outputs.
// --full: the whole run instead of the committed full outputs: the 1,334 files of the 2026 PubMed
//   baseline (about 52 GB, streamed), 6.3 million citations, forward selection and every model.
//   About 4 hours on 4 cores with 16 GB of memory and 20 GB of disk.
// --extract: read Tables 1-3 again from the paper's PMC XML and check them against the committed
//   output/published_values.json.

params.outdir = 'results'
params.python = 'python3'
params.full = false
params.extract = false
params.workers = 4
params.sources = null

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.paper = "${projectDir}/.."
params.mini_files = '0676,0680,0712'

process PUBLISHED_VALUES {
    publishDir "${params.outdir}/output", mode: 'copy'
    output:
    path 'published_values.json'
    script:
    if (params.extract)
        """
        curl -sS --retry 5 --retry-all-errors -o PMC4457112.xml 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=4457112&rettype=xml'
        ${params.python} ${params.pipe}/extract_published.py PMC4457112.xml published_values.json
        cmp published_values.json ${params.committed}/published_values.json
        """
    else
        """
        cp ${params.committed}/published_values.json published_values.json
        """
}

process MINI {
    publishDir "${params.outdir}/output", mode: 'copy'
    output:
    path 'mini'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.mini_files} ${params.sources ? '--sources ' + params.sources : ''}
    PYTHON=${params.python} bash ${params.pipe}/run_mini.sh downloads ${params.mini_files} mini ${params.workers}
    """
}

process FULL {
    publishDir "${params.outdir}/output", mode: 'copy'
    output:
    path 'full/*'
    script:
    if (params.full)
        """
        mkdir -p full data
        ${params.python} ${params.pipe}/extract_medline.py --out medline --files 1-1334 --workers ${params.workers} ${params.sources ? '--local ' + params.sources : ''}
        ${params.python} ${params.pipe}/manifest.py medline/manifest.json full/baseline_manifest.json
        ${params.python} ${params.pipe}/build_dataset.py medline data --extra-fractions 0.05 0.1
        cp data/dataset.json full/
        ${params.python} ${params.pipe}/featurize.py data --workers ${params.workers}
        ${params.python} ${params.pipe}/models.py data full --workers 2
        ${params.python} ${params.pipe}/variants.py data full
        ${params.python} ${params.pipe}/selection_rule.py data full --workers 3
        ${params.python} ${params.pipe}/score_all.py medline data full --workers ${params.workers}
        ${params.python} ${params.pipe}/topic.py ${params.committed}/cholecystitis_pmids.txt data full/topic.json
        ${params.python} ${params.pipe}/single_feature.py data full/single_feature.json
        ${params.python} ${params.pipe}/fraction.py data full/fraction.json --workers ${params.workers}
        """
    else
        """
        mkdir -p full
        for f in dataset selection models variants disagreements topic single_feature fraction baseline_manifest; do
            cp ${params.committed}/\$f.json full/
        done
        cp ${params.committed}/disagreements_pmids.tsv full/
        """
}

process PACKAGE {
    publishDir "${params.outdir}/output", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${params.pipe}/check_package.py ${params.paper}/package --json package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path published
    path mini
    path full
    path pkg
    output:
    path 'results.json'
    path 'site'
    path 'report.md'
    path 'check.json'
    path 'results_check.json'
    path 'output/comparison.json'
    script:
    """
    mkdir -p run/output
    cp -r ${published} ${mini} ${pkg} run/output/
    cp ${full} run/output/
    cp ${params.committed}/cholecystitis_pmids.txt run/output/
    ${params.python} ${params.pipe}/compare.py run/output
    mkdir -p output && cp run/output/comparison.json output/
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py run/output results.json --environment env.json
    cp results.json run/results.json
    ${params.python} ${params.pipe}/make_results_check.py run/output results_check.json
    cp results_check.json run/results_check.json
    ${params.python} ${params.pipe}/build_page.py results.json run/output site
    cp -r site run/site
    ${params.python} ${params.pipe}/check_reproduction.py run ${params.paper} check.json report.md || true
    """
}

process CHECK {
    input:
    path check
    script:
    """
    ${params.python} -c "import json, sys; c = json.load(open('${check}')); print('passed' if c['passed'] else 'FAILED: ' + ', '.join(k for k, v in c.items() if isinstance(v, dict) and not v['passed'])); sys.exit(0 if c['passed'] else 1)"
    """
}

workflow {
    published = PUBLISHED_VALUES()
    mini = MINI()
    full = FULL()
    pkg = PACKAGE()
    (results, site, report, check, rcheck, comparison) = RESULTS(published, mini, full, pkg)
    CHECK(check)
}
