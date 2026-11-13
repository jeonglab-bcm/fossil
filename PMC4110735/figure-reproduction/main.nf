// Reproduce PMC4110735 (Roy, Bhattacharyya and Kalita 2014, "Reconstruction of gene co-expression
// network from microarray data using local expression patterns"). The authors' GeCON program is lost;
// the method is the package PMC4110735/package (gecon), implemented from the paper's equations.
//
// Run from the repository root:
//   nextflow run PMC4110735/figure-reproduction/main.nf --outdir results [--timing] [--sources DIR]
//
// Default: download and check the inputs, simulate D1-D8 with the GNW port (one task per network),
// score GeCON and minet's ARACNE, CLR and MRNET on all 13 datasets (Table 2), read Fig. 4's bars,
// redraw and score Figs 2, 3 and 7, build the real-data modules and their GO enrichment (Tables 3-5),
// check the GNW port against the DREAM4 release, check the package, recompute the text's claims,
// and compare the run with the committed outputs. Fig. 5 uses the committed run times.
// --timing: measure the Fig. 5 run times again (about 10 minutes; they depend on the machine and are
//   reported, not compared).

params.pipe = "${projectDir}/pipeline"
params.committed = "${projectDir}/output"
params.pkgsrc = "${projectDir}/../package/src"



process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${params.pipe}/fetch_inputs.sh downloads --go ${params.sources ? '--sources ' + params.sources : ''}
    """
}

process DREAM_DATA {
    tag "${ds}"
    cpus 1
    input:
    tuple val(ds), path(downloads)
    output:
    path "part_${ds}"
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/dream_data.py ${downloads} part_${ds} --only ${ds}
    """
}

process MERGE_DATA {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path parts
    output:
    path 'dream', emit: dream
    path 'datasets.json', emit: meta
    script:
    """
    mkdir dream
    ${params.python} - <<'PY'
import glob, json, os, shutil
meta = {}
for d in sorted(glob.glob("part_D*")):
    for f in os.listdir(d):
        if f == "datasets.json":
            meta.update(json.load(open(os.path.join(d, f))))
        else:
            shutil.copy(os.path.join(d, f), os.path.join("dream", f))
order = sorted(meta, key=lambda k: int(k[1:]))
meta = {k: meta[k] for k in order}
json.dump(meta, open("dream/datasets.json", "w"), indent=1)
json.dump(meta, open("datasets.json", "w"), indent=1)
PY
    """
}

process DREAM_EVAL {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path dream
    output:
    path 'dream.json'
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/dream_eval.py ${dream} dream.json --rscript ${params.rscript}
    """
}

process PROFILES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'profiles.json', emit: json
    path 'figures/*', emit: figures
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/profile_figures.py ${downloads} ${projectDir}/published .
    """
}

process FIG4 {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path dream_json
    output:
    path 'fig4.json', emit: json
    path 'figures/*', emit: figures
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/fig4_bars.py ${projectDir}/published ${projectDir}/paper_values.json ${dream_json} .
    """
}

process TIMING {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'timing.json'
    script:
    if (params.timing)
        """
        PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/timing.py timing.json --reps 3 --rscript ${params.rscript}
        """
    else
        """
        cp ${params.committed}/timing.json timing.json
        """
}

process FIG5 {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path timing
    output:
    path 'fig5.json', emit: json
    path 'figures/*', emit: figures
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/fig5_plot.py ${projectDir}/published ${timing} .
    """
}

process REAL_DATA {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'enrich.json', emit: enrich
    path 'table3.json', emit: table3
    path 'normalisation.json', emit: norm
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/enrichment.py ${downloads} ${projectDir}/paper_values.json enrich.json
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/real_data.py ${downloads} .
    """
}

process PORT_CHECK {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'port_check.json'
    script:
    """
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/gnw_check.py ${downloads} port_check.json
    """
}

process CLAIMS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path dream_json
    path profiles
    path enrich
    path timing
    output:
    path 'claims.json'
    script:
    """
    ${params.python} ${params.pipe}/claims.py ${projectDir}/paper_values.json ${dream_json} ${profiles} ${enrich} ${timing} claims.json
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
    path files
    output:
    path 'results.json', emit: results
    path 'report.md', emit: report
    path 'site', emit: site
    script:
    """
    mkdir -p run/figures run/dream
    for f in ${files}; do
      case "\$f" in
        *.png) cp "\$f" run/figures/ ;;
        dream) cp -r dream/. run/dream/ ;;
        *) cp -r "\$f" run/ ;;
      esac
    done
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/build_results.py run ${projectDir}/results_notes.json ${projectDir}/paper_values.json results.json --inputs ${projectDir}/inputs.json
    ${params.python} ${params.pipe}/check_results.py results.json --write --skip-files > /dev/null || true
    cp results.json run/results.json
    ${params.python} ${params.pipe}/check_reproduction.py results.json run ${params.committed} report.md ${params.timing ? '--timing' : ''}
    PYTHONPATH=${params.pkgsrc}:${params.pipe} ${params.python} ${params.pipe}/build_page.py results.json run ${projectDir}/published site/index.html
    """
}

workflow {
    dl = FETCH()
    parts = DREAM_DATA(channel.of(1..13).map { "D${it}" }.combine(dl))
    data = MERGE_DATA(parts.collect())
    ev = DREAM_EVAL(data.dream)
    pr = PROFILES(dl)
    f4 = FIG4(ev)
    tm = TIMING()
    f5 = FIG5(tm)
    rd = REAL_DATA(dl)
    pc = PORT_CHECK(dl)
    cl = CLAIMS(ev, pr.json, rd.enrich, tm)
    pk = PACKAGE()
    all = data.dream.mix(data.meta, ev, pr.json, pr.figures.flatten(), f4.json, f4.figures.flatten(), tm, f5.json,
                         f5.figures.flatten(), rd.enrich, rd.table3, rd.norm, pc, cl, pk).collect()
    RESULTS(all)
}
