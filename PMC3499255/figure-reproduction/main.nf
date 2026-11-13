// Reproduce PMC3499255 (Morelli et al. 2012, "A Bayesian inference framework to
// reconstruct transmission trees using epidemiological and genetic data"). The
// authors' R MCMC was never released; the method is the package PMC3499255/package
// (transtree), reimplemented from the paper and Text S1. See README.md.
//
// Run from the repository root:
//   nextflow run PMC3499255/figure-reproduction/main.nf --outdir results [--full]
//
// Default (CI): reconstruct the 2007 and 2001 outbreaks from the datasets
// (deterministic, fixed seed), render Figs 3 and 4, run the pseudo-likelihood and
// arithmetic checks, check the package, build results.json and the page, and
// compare the fresh run with the committed outputs. The simulated Fig. 2 and the
// Table 1 / Table S1 simulation series are read from the committed outputs.
// --full: also rerun Fig. 2 (one 20-premise simulation) and the simulation series
//   (scaled down from the paper's 100 x 5e5; counts recorded as deviations).

nextflow.enable.dsl = 2

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.full = false

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.pkgsrc = "${projectDir}/../package/src"
params.published = "${projectDir}/published"

// real-data committed iteration counts (deterministic, reproduced exactly in CI)
params.iters_real = 30000

def PY = "PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python}"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process ANALYZE {
    tag "${name}"
    input:
    tuple val(name), val(iters), val(seed)
    path downloads
    output:
    tuple val(name), path("${name}.json")
    script:
    """
    ${PY} ${params.pipe}/analyze.py ${name} --sources ${downloads} --iters ${iters} --seed ${seed} --out ${name}.json
    """
}

process ANALYZE_TEST {
    output:
    path 'test.json'
    script:
    if (params.full)
        """
        ${PY} ${params.pipe}/analyze.py test --iters 15000 --seed 1 --sim-seed 0 --n 20 --out test.json
        """
    else
        """
        cp ${params.committed}/test.json test.json
        """
}

process SERIES {
    input:
    path downloads
    output:
    path 'series.json'
    script:
    if (params.full)
        """
        ${PY} ${params.pipe}/series.py --sources ${downloads} --medians ${params.committed}/medians.json \
            --n-sims 12 --iters 3000 --out series.json
        """
    else
        """
        cp ${params.committed}/series.json series.json
        """
}

process TEXTCLAIMS {
    input:
    path a07
    path a01
    output:
    path 'textclaims.json'
    script:
    "${PY} ${params.pipe}/textclaims.py ${a07} ${a01} --out textclaims.json"
}

process CHECKS {
    input:
    path downloads
    output:
    path 'pseudolik_check.json'
    path 'arithmetic_check.json'
    script:
    """
    ${PY} ${params.pipe}/checks.py pseudolik --out pseudolik_check.json
    ${PY} ${params.pipe}/checks.py arithmetic --sources ${downloads} --out arithmetic_check.json
    """
}

process PACKAGE {
    output:
    path 'package.json'
    script:
    "${params.python} ${params.pipe}/check_package.py ${projectDir}/../package --json package.json || true"
}

process RENDER {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path a07
    path a01
    path tst
    output:
    path 'fig*_ours.png'
    path 'fig*_overlay.png'
    script:
    """
    ${PY} ${params.pipe}/render.py ${a07} --published ${params.published}/figure-3.jpg --ours fig3_ours.png --overlay fig3_overlay.png --title "Fig 3: 2007 UK outbreak (reproduced)"
    ${PY} ${params.pipe}/render.py ${a01} --published ${params.published}/figure-4.jpg --ours fig4_ours.png --overlay fig4_overlay.png --title "Fig 4: 2001 Darlington cluster (reproduced)"
    ${PY} ${params.pipe}/render.py ${tst} --published ${params.published}/figure-2.jpg --ours fig2_ours.png --overlay fig2_overlay.png --title "Fig 2: simulated outbreak (reproduced)"
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path jsons        // all *.json outputs
    path figs         // all fig png outputs
    output:
    path 'run', emit: run
    path 'results.json', emit: results
    path 'report.md', emit: report
    script:
    """
    mkdir run
    cp ${jsons} run/ 2>/dev/null || true
    cp ${figs} run/ 2>/dev/null || true
    ${PY} ${params.pipe}/build_results.py run ${projectDir}/results_notes.json results.json \
        --check-results ${params.pipe}/check_results.py --root run
    cp results.json run/results.json
    ${PY} ${params.pipe}/check_reproduction.py results.json run ${params.committed} report.md ${params.full ? '--full' : ''}
    """
}

process BUILD_PAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path run
    output:
    path 'site'
    script:
    """
    ${PY} ${params.pipe}/build_page.py ${run}/results.json ${run} ${params.published} site/index.html
    """
}

workflow {
    dl = FETCH().first()
    reals = ANALYZE(channel.of(['y2007', params.iters_real, 1], ['y2001', params.iters_real, 1]), dl)
    a07 = reals.filter { it[0] == 'y2007' }.map { it[1] }
    a01 = reals.filter { it[0] == 'y2001' }.map { it[1] }
    tst = ANALYZE_TEST()
    ser = SERIES(dl)
    txt = TEXTCLAIMS(a07, a01)
    (pseudo, arith) = CHECKS(dl)
    pkg = PACKAGE()
    (ours, overlays) = RENDER(a07, a01, tst)
    jsons = a07.mix(a01, tst, ser, txt, pseudo, arith, pkg).collect()
    figs = ours.mix(overlays).collect()
    r = RESULTS(jsons, figs)
    BUILD_PAGE(r.run)
}
