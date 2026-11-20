// Reproduce PMC1955447 (Moineddin, Matheson and Glazier 2007, "A simulation study of sample size for multilevel
// logistic regression models"). The authors' SAS 9.1 programs (PROC NLMIXED) are lost; the method is the Python
// package PMC1955447/package (mlagq), implemented from the paper's text.
//
// Run from the repository root, with the pinned requirements and the package installed:
//   pip install -r PMC1955447/figure-reproduction/requirements.txt ./PMC1955447/package
//   nextflow run PMC1955447/figure-reproduction/main.nf --outdir results [--full] [--extract] [--sources DIR]
//
// Default (CI, about 10 minutes on 4 cores): rerun the first 3 replicates of every cell of Tables 1-5 from
// scratch and check them against the committed per-replicate records (output/records), summarize those records
// into every printed quantity, compare every printed cell and claim, check mlagq's likelihood against direct
// numerical integration, check the package, write results.json and the results page, and compare the run with
// the committed outputs.
// --full: rerun the whole simulation study (Tables 1-3: 27 cells x 1,000; Table 4: 27 x 1,000; Table 5:
//   72 x 100), a second run of Tables 1-3 with other seeds and the hypothesis variants (replicates 0-199 of the
//   main grid, refitted six other ways): about 6 CPU hours (2.5 hours on 4 cores).
// --extract: read the printed tables again from the article XML and check them against output/published_values.json.
// --sources DIR: use a local copy of the article XML.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.full = false
params.extract = false
params.check_reps = 3
params.jobs = 4

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

process PUBLISHED_VALUES {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path downloads
    output:
    path 'published_values.json'
    script:
    if (params.extract)
        """
        ${params.python} ${params.pipe}/extract_published.py ${downloads}/PMC1955447.1.xml published_values.json --check ${params.committed}/published_values.json
        """
    else
        """
        cp ${params.committed}/published_values.json published_values.json
        """
}

// --full: the whole simulation study and its variants
process SIMULATE {
    cpus params.jobs
    output:
    path 'records'
    script:
    """
    mkdir records
    S="${params.python} ${params.pipe}/simulate.py"
    \$S main records/main.csv.gz --jobs ${params.jobs}
    \$S prevalence records/prevalence.csv.gz --jobs ${params.jobs}
    \$S robustness records/robustness.csv.gz --jobs ${params.jobs}
    \$S main records/main_run2.csv.gz --base 19554472 --jobs ${params.jobs}
    \$S main records/var_nocov.csv.gz --reps 0:200 --nocov --jobs ${params.jobs}
    \$S main records/var_qfirst.csv.gz --reps 0:200 --qpick first --jobs ${params.jobs}
    \$S main records/var_noabsx.csv.gz --reps 0:200 --absxconv none --jobs ${params.jobs}
    \$S main records/var_maxfunc2000.csv.gz --reps 0:200 --maxfunc 2000 --jobs ${params.jobs}
    \$S main records/var_q1.csv.gz --reps 0:200 --qpoints 1 --jobs ${params.jobs}
    \$S main records/var_q3.csv.gz --reps 0:200 --qpoints 3 --jobs ${params.jobs}
    """
}

process RECORDS_COMMITTED {
    output:
    path 'records'
    script:
    """
    mkdir records
    cp ${params.committed}/records/main.csv.gz ${params.committed}/records/prevalence.csv.gz ${params.committed}/records/robustness.csv.gz ${params.committed}/records/extra.json records/
    """
}

// Default: the first replicates of every cell from scratch, against the committed records
process SIM_CHECK {
    cpus params.jobs
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path records
    output:
    path 'sim_check.json'
    script:
    """
    ${params.python} ${params.pipe}/sim_check.py ${records} sim_check.json --reps ${params.check_reps} --jobs ${params.jobs}
    """
}

process SUMMARIZE {
    publishDir "${params.outdir}/output", mode: 'copy', pattern: 'simulation.json'
    publishDir "${params.outdir}/output/records", mode: 'copy', pattern: 'records_out/*', saveAs: { it.split('/')[-1] }
    input:
    path records
    output:
    path 'simulation.json', emit: sim
    path 'records_out/*', emit: kept
    script:
    """
    mkdir records_out
    if [ -f ${records}/main_run2.csv.gz ]; then
      ${params.python} ${params.pipe}/summarize.py ${records} simulation.json --extra records_out/extra.json
    else
      cp ${records}/extra.json records_out/extra.json
      ${params.python} ${params.pipe}/summarize.py ${records} simulation.json --extra ${records}/extra.json
    fi
    cp ${records}/main.csv.gz ${records}/prevalence.csv.gz ${records}/robustness.csv.gz records_out/
    """
}

process RECORD_TESTS {
    cpus params.jobs
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path records
    output:
    path 'record_tests.json'
    script:
    """
    ${params.python} ${params.pipe}/record_tests.py ${records} record_tests.json --jobs ${params.jobs}
    """
}

process COMPARE {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path published
    path sim
    output:
    path 'comparison.json'
    path 'tables.csv'
    script:
    """
    ${params.python} ${params.pipe}/compare.py ${published} ${sim} comparison.json --csv tables.csv
    """
}

process CLAIMS {
    publishDir "${params.outdir}/output", mode: 'copy'
    input:
    path published
    path sim
    path tests
    output:
    path 'claims.json'
    script:
    """
    ${params.python} ${params.pipe}/claims.py ${published} ${sim} ${tests} claims.json
    """
}

process CROSSCHECK {
    publishDir "${params.outdir}/output", mode: 'copy'
    output:
    path 'crosscheck.json'
    script:
    """
    ${params.python} ${params.pipe}/crosscheck.py crosscheck.json
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
    path sim
    path comparison
    path tables
    path claims
    path tests
    path cross
    path pkg
    path kept
    path simcheck
    output:
    path 'results.json'
    path 'site'
    path 'report.md'
    path 'check.json'
    path 'results_check.json'
    script:
    """
    mkdir -p run/output/records
    cp ${published} ${sim} ${comparison} ${tables} ${claims} ${tests} ${cross} ${pkg} run/output/
    cp ${kept} run/output/records/
    cp ${simcheck} run/output/ 2>/dev/null || true
    ${params.python} ${params.pipe}/env_versions.py env.json
    ${params.python} ${params.pipe}/build_results.py run/output results.json --environment env.json
    cp results.json run/results.json
    ${params.python} ${params.pipe}/make_results_check.py run/output results_check.json
    cp results_check.json run/results_check.json
    ${params.python} ${params.pipe}/build_page.py results.json run/output site
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
    published = PUBLISHED_VALUES(downloads)
    records = params.full ? SIMULATE() : RECORDS_COMMITTED()
    simcheck = params.full ? Channel.value(file("${params.committed}/sim_check.json")) : SIM_CHECK(records)
    summ = SUMMARIZE(records)
    tests = RECORD_TESTS(records)
    (comparison, tables) = COMPARE(published, summ.sim)
    claims = CLAIMS(published, summ.sim, tests)
    cross = CROSSCHECK()
    pkg = PACKAGE()
    (results, site, report, check, rcheck) = RESULTS(published, summ.sim, comparison, tables, claims, tests, cross, pkg, summ.kept.collect(), simcheck)
    CHECK(check)
}
