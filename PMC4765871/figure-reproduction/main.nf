// Reproduce PMC4765871 (Ocone, Haghverdi, Mueller and Theis 2015, "Reconstructing gene regulatory
// dynamics from high-dimensional single-cell snapshot data"). The authors' code is lost; every step
// is rebuilt from the paper and its supplement (see README.md).
//
// Run from the repository root:
//   nextflow run PMC4765871/figure-reproduction/main.nf --outdir results [--full] [--sources DIR]
//
// Without --full the MCMC samplers are not rerun: their outputs are read from the committed
// output/run (ffl_fits.json, haem_fits.json, toggle_fits.json) and everything else (simulations,
// diffusion maps, Wanderlust, GENIE3, emulators, figures, scores, results.json) is recomputed and
// compared with the committed outputs. --full reruns the samplers too (about 1 h on 48 cores; use
// -profile skyriver); chains on another CPU differ, so a --full run is checked against results.json
// but not byte for byte against the committed fits.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.full = false
params.cpus = 4

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${projectDir}/pipeline/fetch_inputs.sh downloads ${params.sources ?: ''}
    """
}

process PUBLISHED {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'published', emit: figures
    path 'published_data.json', emit: data
    script:
    """
    ${params.python} ${projectDir}/pipeline/published.py ${downloads}/PMC4765871.1.pdf published
    ${params.python} ${projectDir}/pipeline/extract_published.py ${downloads}/PMC4765871.1.pdf published_data.json
    """
}

process FFL {
    cpus params.cpus
    publishDir "${params.outdir}/run", mode: 'copy'
    output:
    path '*'
    script:
    def from = params.full ? '' : "--mcmc-from ${projectDir}/output/run"
    """
    ${params.python} ${projectDir}/pipeline/ffl.py . ${from} --cpus ${task.cpus}
    """
}

process TOGGLE {
    cpus params.cpus
    publishDir "${params.outdir}/run", mode: 'copy'
    output:
    path '*'
    script:
    def from = params.full ? '' : "--mcmc-from ${projectDir}/output/run"
    """
    ${params.python} ${projectDir}/pipeline/toggle.py . ${from} --cpus ${task.cpus}
    """
}

process HAEM {
    cpus params.cpus
    publishDir "${params.outdir}/run", mode: 'copy'
    input:
    path downloads
    output:
    path '*'
    script:
    def from = params.full ? '' : "--mcmc-from ${projectDir}/output/run"
    """
    ${params.python} ${projectDir}/pipeline/haem.py ${downloads}/moignard2013_s3.xlsx . ${from} --cpus ${task.cpus}
    """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path ffl
    path toggle
    path haem
    path published
    path published_data
    output:
    path 'figures'
    script:
    """
    mkdir run && cp ${ffl} ${toggle} ${haem} run/
    ${params.python} ${projectDir}/pipeline/figures.py run ${published} ${published_data} figures
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path ffl
    path toggle
    path haem
    path figures
    path published_data
    output:
    path 'results.json', emit: results
    path 'report.md', emit: report
    path 'site', emit: site
    script:
    """
    mkdir run && cp ${ffl} ${toggle} ${haem} run/
    ${params.python} ${projectDir}/pipeline/build_results.py run ${figures} ${published_data} results.json
    ${params.python} ${projectDir}/pipeline/check_reproduction.py results.json run ${figures} ${published_data} ${projectDir}/output report.md ${params.full ? '--full' : ''}
    ${params.python} ${projectDir}/pipeline/build_page.py results.json ${figures} ${projectDir}/published site/index.html
    """
}

workflow {
    dl = FETCH()
    pub = PUBLISHED(dl)
    f = FFL()
    t = TOGGLE()
    h = HAEM(dl)
    figs = FIGURES(f.collect(), t.collect(), h.collect(), pub.figures, pub.data)
    RESULTS(f.collect(), t.collect(), h.collect(), figs, pub.data)
}
