// Reproduce PMC3392844 (Liu, Wu, Chen, Sun, Zhao, Chen, Matheny and Xu 2012, "Large-scale prediction of
// adverse drug reactions using chemical, biological, and phenotypic properties of drugs"). The authors' code
// was never released; the method is the package PMC3392844/package (adrfusion), rebuilt from the paper's
// text, run on the authors' own training file and folds (recovered in Zhang et al. 2015's supplement).
//
// Run from the repository root, with the pinned requirements and the package installed:
//   pip install -r PMC3392844/figure-reproduction/requirements.txt ./PMC3392844/package
//   nextflow run PMC3392844/figure-reproduction/main.nf --outdir results [--full] [--extract] [--sources DIR]
//
// Every model of Tables 2 and 3 runs on every ADR and fold each time (about 15 minutes on 4 cores).
// --full: also rerun SVM seeds 1-3 (seed_spread.json) and the hypothesis variants (hypotheses.json),
//   about 25 minutes more; without it the committed copies of those two files are used.
// --extract: download the paper's PDF and XML, read its tables, curves and figure crops again
//   (extract_published.py, needs poppler-utils) and check they equal the committed copies.
// --sources DIR: use local copies of the downloads.

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.paper = "${projectDir}/.."

process FETCH {
    output:
    path 'data'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh data ${params.extract ? '--paper' : ''} ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process PUBLISHED {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path data
    output:
    path 'published_values.json'
    path 'published_curves.json'
    script:
    if (params.extract)
        """
        ${params.python} ${params.pipe}/extract_published.py ${data}/PMC3392844.1.xml ${data}/PMC3392844.1.pdf fresh
        cp fresh/published_values.json fresh/published_curves.json .
        for f in fig2 fig3 fig4 fig5; do ${params.python} -c "
import sys, numpy as np
from PIL import Image
a = np.array(Image.open('fresh/\$f.png')); b = np.array(Image.open('${projectDir}/published/\$f.png'))
sys.exit(0 if a.shape == b.shape and (a == b).all() else 1)" || { echo "fresh \$f.png differs from published/"; exit 1; }; done
        ${params.python} -c "
import json, sys
a, b = json.load(open('fresh/published_values.json')), json.load(open('${params.committed}/published_values.json'))
c, d = json.load(open('fresh/published_curves.json')), json.load(open('${params.committed}/published_curves.json'))
sys.exit(0 if a == b and c == d else 1)"
        """
    else
        """
        cp ${params.committed}/published_values.json ${params.committed}/published_curves.json .
        """
}

process RUN_SVM {
    cpus params.cpus
    input:
    path data
    output:
    path 'scores_svm'
    script:
    """
    ${params.python} ${params.pipe}/run_models.py ${data} scores_svm --jobs ${task.cpus} \
        svm:chem svm:bio svm:pheno svm:chem+bio svm:chem+pheno svm:chem+bio+pheno svm:chem+indication svm:chem+bio+pheno:paper
    """
}

process RUN_METHODS {
    cpus params.cpus
    input:
    path data
    output:
    path 'scores_methods'
    script:
    """
    ${params.python} ${params.pipe}/run_models.py ${data} scores_methods --jobs ${task.cpus} \
        knn:chem+bio+pheno lr:chem+bio+pheno nb:chem+bio+pheno rf:chem+bio+pheno rf:chem+bio+pheno:paper
    """
}

process EVALUATE {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path data
    path scores_svm
    path scores_methods
    path pubvals
    output:
    path 'metrics.json'
    path 'rocs.json'
    path 'per_adr_auc.json'
    path 'comparison.json'
    script:
    """
    mkdir -p scores && cp ${scores_svm}/*.npy ${scores_methods}/*.npy scores/
    ${params.python} ${params.pipe}/evaluate.py ${data} scores ${pubvals} .
    """
}

process TABLE4 {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path data
    path pubvals
    output:
    path 'table4.json'
    script:
    """
    PYTHONPATH=${params.pipe} ${params.python} ${params.pipe}/table4.py ${data} ${pubvals} table4.json
    """
}

process FIGURES {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path curves
    path rocs
    output:
    path 'fig*.png'
    path 'figures.json'
    script:
    """
    ${params.python} ${params.pipe}/figures.py ${projectDir}/published ${curves} ${rocs} .
    """
}

process CLAIMS {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path pubvals
    path metrics
    path comparison
    path t4
    output:
    path 'claims.json'
    script:
    """
    ${params.python} ${params.pipe}/claims.py ${pubvals} ${metrics} ${comparison} ${t4} claims.json
    """
}

process SEEDS {
    publishDir "${params.outdir}/output", mode: 'copy'
    cpus params.cpus
    input:
    path data
    path scores_svm
    path pubvals
    output:
    path 'seed_spread.json'
    script:
    if (params.full)
        """
        for s in 1 2 3; do
          ${params.python} ${params.pipe}/run_models.py ${data} seed\$s --seed \$s --jobs ${task.cpus} \
              svm:chem svm:bio svm:pheno svm:chem+bio svm:chem+pheno svm:chem+bio+pheno
        done
        PYTHONPATH=${params.pipe} ${params.python} ${params.pipe}/seed_spread.py ${data} ${pubvals} seed_spread.json ${scores_svm} seed1 seed2 seed3
        """
    else
        """
        cp ${params.committed}/seed_spread.json .
        """
}

process HYPOTHESES {
    publishDir "${params.outdir}/output", mode: 'copy'
    cpus params.cpus
    input:
    path data
    path scores_methods
    output:
    path 'hypotheses.json'
    script:
    if (params.full)
        """
        PYTHONPATH=${params.pipe} ${params.python} ${params.pipe}/hypotheses.py ${data} ${scores_methods} hypotheses.json --jobs ${task.cpus}
        """
    else
        """
        cp ${params.committed}/hypotheses.json .
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
    path outputs
    output:
    path 'results.json'
    path 'site'
    path 'report.md'
    path 'check.json'
    path 'results_check.json'
    script:
    """
    mkdir -p run/output
    cp ${outputs} run/output/
    cp ${params.committed}/offline_checks.json run/output/
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py run/output results.json --environment env.json
    cp results.json run/results.json
    ${params.python} ${params.pipe}/make_results_check.py run/output results_check.json
    cp results_check.json run/results_check.json
    ${params.python} ${params.pipe}/build_page.py results.json run/output ${projectDir}/published site
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
    data = FETCH()
    (pubvals, curves) = PUBLISHED(data)
    svm = RUN_SVM(data)
    methods = RUN_METHODS(data)
    (metrics, rocs, peradr, comparison) = EVALUATE(data, svm, methods, pubvals)
    t4 = TABLE4(data, pubvals)
    (figpngs, figjson) = FIGURES(curves, rocs)
    claims = CLAIMS(pubvals, metrics, comparison, t4)
    seeds = SEEDS(data, svm, pubvals)
    hyp = HYPOTHESES(data, methods)
    pkg = PACKAGE()
    all = pubvals.mix(curves, metrics, rocs, peradr, comparison, t4, figpngs.flatten(), figjson, claims, seeds, hyp, pkg).collect()
    (results, site, report, check, rcheck) = RESULTS(all)
    CHECK(check)
}
