// Reproduce PMC3098087 (Blagus and Lusa 2010, "Class prediction for high-dimensional
// class-imbalanced data"). The authors released no code; the method is the R package
// PMC3098087/package (multds), written from the paper's text.
//
// Run from the repository root, with R, the R packages of the package's DESCRIPTION and the pinned
// Python requirements installed:
//   R CMD INSTALL PMC3098087/package
//   pip install -r PMC3098087/figure-reproduction/requirements.txt
//   nextflow run PMC3098087/figure-reproduction/main.nf --outdir results [--full] [--sources DIR]
//
// By default the first --check_reps (3) replicates of every simulation setting and every breast
// cancer design are rerun from their seeds and must equal the committed ones
// (output/replicates_check.csv); the comparisons, figures, claims and page are then built from the
// committed summary of all replicates (output/summary.csv). --full reruns every replicate (about
// 4 hours on 4 cores) and builds everything from the fresh summary.

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.paper = "${projectDir}/.."

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process EXTRACT {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path downloads
    output:
    path 'published_values.json'
    script:
    """
    ${params.python} ${params.pipe}/extract_published.py ${downloads} published_values.json
    """
}

process READ_DATA {
    publishDir "${params.outdir}/output", mode: 'copy', pattern: '*.json'
    input:
    path downloads
    output:
    path 'sotiriou.rds', emit: rds
    path 'data_counts.json', emit: counts
    script:
    """
    Rscript ${params.pipe}/read_sotiriou.R ${downloads}/sotiriou/Sotiriou-Breast-PNAS-2003-Project sotiriou.rds
    Rscript -e 'd <- readRDS("sotiriou.rds"); writeLines(jsonlite::toJSON(list(arrays = d\$arrays, probes = d\$probes, er_neg = sum(d\$er == 0), er_pos = sum(d\$er == 1), grade12 = sum(d\$grade <= 2), grade3 = sum(d\$grade == 3), missing_set_to_zero = d\$missing), auto_unbox = TRUE, pretty = TRUE), "data_counts.json")'
    """
}

process PORT_CHECK {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path downloads
    output:
    path 'port_check.json'
    script:
    """
    Rscript ${params.pipe}/port_check.R ${downloads}/sma_0.5.15.tar.gz port_check.json
    """
}

process SIMULATE {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path rds
    output:
    path 'summary.csv', emit: summary
    path 'replicates_check.csv', emit: check
    script:
    def reps = params.full ? '1:1000' : "1:${params.check_reps}"
    """
    Rscript ${params.pipe}/simulate.R sim --reps ${reps} --cores ${params.cores}
    Rscript ${params.pipe}/er.R ${rds} er --reps ${params.full ? '1:500' : reps} --cores ${params.cores}
    Rscript ${params.pipe}/summarize.R sim er --out fresh_summary.csv --check replicates_check.csv --check-reps ${params.check_reps}
    if [ "${params.full}" = "true" ]; then mv fresh_summary.csv summary.csv; else cp ${params.committed}/summary.csv summary.csv; fi
    """
}

process HYPOTHESES {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path rds
    output:
    path 'hypotheses.json'
    script:
    """
    Rscript ${params.pipe}/hypotheses.R ${rds} hypotheses.json --reps 200
    """
}

process COMPARE {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path published
    path summary
    output:
    path 'comparison.json'
    script:
    """
    ${params.python} ${params.pipe}/compare.py ${published} ${summary} comparison.json
    """
}

process FIGURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path published
    path summary
    output:
    path 'output/*'
    path 'published/*'
    script:
    """
    ${params.python} ${params.pipe}/figures.py ${downloads} ${published} ${summary} output published
    """
}

process CLAIMS {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path published
    path summary
    path counts
    output:
    path 'claims.json'
    script:
    """
    ${params.python} ${params.pipe}/claims.py ${published} ${summary} ${counts} claims.json
    """
}

process PACKAGE {
    publishDir "${params.outdir}/output", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    bash ${params.pipe}/check_package.sh ${params.paper}/package package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path published
    path counts
    path port
    path summary
    path rcheck
    path comparison
    path figs
    path pubfigs
    path claims
    path pkg
    path hyp
    output:
    path 'results.json'
    path 'site'
    path 'report.md'
    path 'check.json'
    path 'results_check.json'
    script:
    """
    mkdir -p run/output run/published
    cp ${published} ${counts} ${port} ${summary} ${rcheck} ${comparison} ${figs} ${claims} ${pkg} ${hyp} run/output/
    cp ${pubfigs} run/published/
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py run/output results.json --environment env.json
    cp results.json run/results.json
    ${params.python} ${params.pipe}/make_results_check.py run/output results_check.json
    cp results_check.json run/results_check.json
    ${params.python} ${params.pipe}/build_page.py results.json run/output run/published site
    cp -r site run/site
    ${params.python} ${params.pipe}/check_reproduction.py run ${params.paper} check.json report.md ${params.full ? '--full' : ''} || true
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
    downloads = FETCH()
    published = EXTRACT(downloads)
    data = READ_DATA(downloads)
    port = PORT_CHECK(downloads)
    sim = SIMULATE(data.rds)
    comparison = COMPARE(published, sim.summary)
    (figs, pubfigs) = FIGURES(downloads, published, sim.summary)
    claims = CLAIMS(published, sim.summary, data.counts)
    pkg = PACKAGE()
    hyp = HYPOTHESES(data.rds)
    (results, site, report, check, rcheck) = RESULTS(published, data.counts, port, sim.summary, sim.check, comparison, figs, pubfigs, claims, pkg, hyp)
    CHECK(check)
}
