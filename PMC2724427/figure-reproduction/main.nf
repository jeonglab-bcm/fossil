// Reproduce PMC2724427 (Nemes, Jonasson, Genell and Steineck 2009, "Bias in odds ratios by
// logistic regression modelling and sample size"). The authors released no code; the method is
// the R package PMC2724427/package (logitbias): the population lines of Additional file 1, and
// the study written from the paper's text.
//
// Run from the repository root:
//   nextflow run PMC2724427/figure-reproduction/main.nf --outdir results [--full] [--sources DIR]
//
// Steps: download Additional file 1 and the published figures and check their SHA-256; run the
// study (281 sample sizes from 100 to 1500, 1,000 samples each, one population of 100,000, seed
// 2724427); the port and kernel checks; the seed spread and the hypothesis run; calibrate the
// published axes; redraw Figs 1-3 on the published pixel grid with their negative controls;
// compare with Table 1, the text and the figures; check the package; write results.json and the
// results page; check the run against the committed outputs.
//
// Without --full, the seed spread (20 more populations) and the hypothesis run (x with SD 1)
// are taken from the committed output/seeds, except seed 1, which is rerun and must equal its
// committed copy. With --full all 21 extra studies run (about 50 minutes on 4 cores).

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.full = false
params.jobs = 4
params.seed = 2724427

params.pipe = "${projectDir}/pipeline"
params.published = "${projectDir}/published"
params.committed = "${projectDir}/output"
params.notes = "${projectDir}/results_notes.json"
params.pkg = "${projectDir}/../package"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    for f in figure-1.jpg figure-2.jpg figure-3.jpg; do cmp downloads/\$f ${params.published}/\$f; done
    """
}

process SIMULATE {
    publishDir "${params.outdir}", mode: 'copy'
    cpus params.jobs
    input:
    path downloads
    output:
    path 'run/per_n.csv', emit: per_n
    path 'run/samples_fig.csv', emit: samples
    path 'run/fit.json', emit: fit
    path 'run/checks.json', emit: checks
    script:
    """
    Rscript ${params.pipe}/simulate.R run --seed ${params.seed} --cores ${params.jobs}
    Rscript ${params.pipe}/checks.R run/per_n.csv run/fit.json run/checks.json
    """
}

process SEEDS {
    publishDir "${params.outdir}", mode: 'copy'
    cpus params.jobs
    input:
    path downloads
    output:
    path 'seeds'
    script:
    if (params.full)
        """
        for s in \$(seq 1 20); do Rscript ${params.pipe}/simulate.R seeds --seed \$s --light --cores ${params.jobs}; done
        Rscript ${params.pipe}/simulate.R seeds/xsd1 --seed ${params.seed} --x-sd 1 --cores ${params.jobs}
        """
    else
        """
        mkdir -p seeds && cp -r ${params.committed}/seeds/. seeds/
        rm seeds/seed_1.json
        Rscript ${params.pipe}/simulate.R seeds --seed 1 --light --cores ${params.jobs}
        """
}

process FIGURES {
    publishDir "${params.outdir}/figs", mode: 'copy', pattern: 'ours/*', saveAs: { f -> file(f).name }
    input:
    path per_n
    path samples
    path seeds
    output:
    path 'figs', emit: figs
    path 'ours/*', emit: ours
    path 'calib.json', emit: calib
    script:
    """
    ${params.python} ${params.pipe}/calibrate.py ${params.published} calib.json
    Rscript ${params.pipe}/figures.R calib.csv ${per_n} ${samples} figs ${seeds}/xsd1/per_n.csv ${seeds}/xsd1/samples_fig.csv
    mkdir -p ours && cp figs/fig*_ours.png ours/
    """
}

process COMPARE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path per_n
    path samples
    path fit
    path checks
    path figs
    path calib
    path seeds
    output:
    path 'cmp/comparison.json', emit: comparison
    path 'cmp/tables.json', emit: tables
    path 'cmp/fig*_overlay.png', emit: overlays
    script:
    """
    mkdir -p r && cp ${per_n} ${samples} ${fit} ${checks} r/
    ${params.python} ${params.pipe}/compare.py ${params.published} ${calib} r ${figs} ${seeds} cmp
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path pkg  // the package folder, staged as a copy, so a change to it reruns this step
    output:
    path 'package.json'
    script:
    """
    bash ${params.pipe}/check_package_r.sh ${pkg} package.json || true
    test -s package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path comparison
    path pkg
    path notes  // results_notes.json, so an edit to it reruns this step
    output:
    path 'results.json'
    script:
    """
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py ${notes} ${comparison} results.json \
        --package ${pkg} --inputs ${params.pipe}/fetch_inputs.sh --env env.json --date \$(date -u +%F)
    ${params.python} ${params.pipe}/check_results.py results.json --write --root ${projectDir}/..
    """
}

process PAGE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path tables
    path figs
    path overlays
    path notes
    output:
    path 'site', emit: site
    path 'report.md'
    script:
    """
    ${params.python} ${params.pipe}/build_page.py ${results} ${figs} ${params.published} site ${tables}
    ${params.python} ${params.pipe}/check_results.py ${results} --markdown --root ${projectDir}/.. > report.md || true
    """
}

process CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path results
    path site
    path 'r/*'
    path 'c/*'
    path figs
    path pkgjson
    path seeds
    output:
    path 'check.json'
    script:
    """
    mkdir -p fresh/run fresh/figs fresh/cmp
    cp r/* fresh/run/ && cp c/* fresh/cmp/ && cp ${figs}/fig*_ours.png fresh/figs/ && cp -r ${seeds} fresh/seeds
    cp ${pkgjson} ${results} fresh/
    ${params.python} ${params.pipe}/check_reproduction.py fresh ${params.committed} ${projectDir}/.. check.json
    """
}

workflow {
    dl = FETCH()
    sim = SIMULATE(dl)
    sd = SEEDS(dl)
    fg = FIGURES(sim.per_n, sim.samples, sd)
    cmp = COMPARE(sim.per_n, sim.samples, sim.fit, sim.checks, fg.figs, fg.calib, sd)
    pk = PACKAGE(Channel.fromPath(params.pkg, type: 'dir'))
    notes = Channel.fromPath(params.notes)
    res = RESULTS(cmp.comparison, pk, notes)
    pg = PAGE(res, cmp.tables, fg.figs, cmp.overlays, Channel.fromPath(params.notes))
    CHECK(res, pg.site, sim.per_n.mix(sim.samples, sim.fit, sim.checks).collect(),
          cmp.comparison.mix(cmp.tables, cmp.overlays.flatten()).collect(), fg.figs, pk, sd)
}
