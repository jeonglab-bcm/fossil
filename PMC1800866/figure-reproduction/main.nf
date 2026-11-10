// Reproduce PMC1800866 (Passerini, Andreini, Menchetti, Rosato and Frasconi 2007, "Predicting zinc
// binding at the proteome level"). The authors' predictor is lost; the method is the package
// PMC1800866/package (spsvm), implemented from the paper's text (see README.md).
//
// Run from the repository root:
//   nextflow run PMC1800866/figure-reproduction/main.nf --outdir results [--full] [--sources DIR]
//
// Default (CI): reads the committed PSI-BLAST profiles (output/profiles), the parsed PDB chains
// (output/struct) and the leave-one-out predictions (output/predictions/loo_*.tsv); recomputes the site
// analysis, Figs 1 and 2, the five-fold CV of both models, Figs 3-6, the proteome sample scan, the
// package check and results.json, and compares the run with the committed outputs.
// --full also downloads the 2,314 PDB entries (about 1 GB) and parses them again. Two slow steps run
// outside this pipeline, on the cluster: the PSI-BLAST profiles (run_profiles.sbatch, about 60 CPU
// hours) and the leave-one-out (run_loo.sbatch, 3,843 SVM fits, about 30 CPU hours), whose outputs
// are committed in output/profiles and output/predictions.

params.outdir = 'results'
params.python = 'python3'
params.sources = null
params.full = false

def pipe = "${projectDir}/pipeline"
def committed = "${projectDir}/output"

process FETCH {
    output:
    path 'downloads'
    script:
    """
    bash ${pipe}/fetch_inputs.sh downloads ${params.sources ?: ''} ${params.full ? '--full' : ''}
    """
}

process PUBLISHED {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'published', emit: figures
    path 'published_curves.json', emit: curves
    script:
    """
    ${params.python} ${pipe}/published.py ${downloads} published
    ${params.python} ${pipe}/extract_published_curves.py ${downloads}/PMC1800866.1.pdf published_curves.json
    """
}

process STRUCTURES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    output:
    path 'struct'
    script:
    if (params.full)
        """
        ${params.python} ${pipe}/parse_structures.py ${downloads}/s1/SVM_evaluation_data ${downloads}/cif struct
        """
    else
        """
        mkdir struct && cp ${committed}/struct/* struct/
        """
}

process SITES {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path struct
    output:
    path 'sites'
    script:
    """
    ${params.python} ${pipe}/analyze_sites.py ${downloads}/s1/SVM_evaluation_data ${struct} sites
    ${params.python} ${pipe}/text_arithmetic.py ${pipe}/params/published_tables.json ${downloads}/s1/SVM_evaluation_data ${downloads}/1471-2105-8-39-S3.TXT sites
    """
}

process FIGURES_1_2 {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path sites
    output:
    path 'figures12'
    script:
    """
    ${params.python} ${pipe}/figure1.py ${downloads}/1471-2105-8-39-1.jpg ${sites}/fig1.tsv figures12
    ${params.python} ${pipe}/figure2.py ${downloads}/1471-2105-8-39-2.jpg ${sites}/tables.json figures12
    """
}

process PREPARE {
    input:
    path downloads
    path struct
    output:
    path 'svm'
    script:
    """
    ${params.python} ${pipe}/run_svm.py prepare ${downloads}/s1/SVM_evaluation_data ${struct}/chains.tsv ${committed}/profiles/pdb_profiles.npz svm
    """
}

process CV {
    cpus 1
    input:
    path svm
    each variant
    output:
    path "cv_${variant}.tsv"
    script:
    """
    ${params.python} ${pipe}/run_svm.py cv ${variant} ${svm}
    cp ${svm}/cv_${variant}.tsv .
    """
}

process LOO_COMMITTED {
    output:
    path 'loo_*.tsv'
    script:
    """
    cp ${committed}/predictions/loo_CH.tsv ${committed}/predictions/loo_CHDE.tsv .
    """
}

process EVALUATE {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path svm
    path cv
    path loo
    path sites
    path published_curves
    output:
    path 'evaluation', emit: figures
    path 'predictions', emit: predictions
    script:
    """
    mkdir predictions && cp ${svm}/candidates.tsv ${svm}/mapping.json ${cv} ${loo} predictions/
    ${params.python} ${pipe}/evaluate.py predictions ${sites}/sites.tsv ${published_curves} ${downloads}/PMC1800866.1.pdf evaluation
    """
}

process PROTEOME {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path downloads
    path svm
    output:
    path 'proteome'
    script:
    """
    ${params.python} ${pipe}/scan_proteome.py ${svm} ${committed}/profiles/human_profiles.npz ${committed}/proteome/proteome_sample.tsv ${downloads} proteome
    """
}

process PACKAGE {
    publishDir "${params.outdir}", mode: 'copy'
    output:
    path 'package.json'
    script:
    """
    ${params.python} ${pipe}/check_package.py ${projectDir}/../package --json package.json
    """
}

process RESULTS {
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path published
    path published_curves
    path struct
    path sites
    path figures12
    path evaluation
    path predictions
    path proteome
    path package_json
    output:
    path 'results.json', emit: results
    path 'report.md', emit: report
    path 'site', emit: site
    script:
    """
    mkdir run && cp -r ${struct} ${sites} ${figures12} ${evaluation} ${predictions} ${proteome} run/ && cp ${published_curves} ${package_json} run/
    ${params.python} ${pipe}/build_results.py run results.json
    ${params.python} ${pipe}/check_reproduction.py results.json run ${committed} report.md ${params.full ? '--full' : ''}
    ${params.python} ${pipe}/build_page.py results.json run ${published} site/index.html
    """
}

workflow {
    dl = FETCH()
    pub = PUBLISHED(dl)
    st = STRUCTURES(dl)
    si = SITES(dl, st)
    f12 = FIGURES_1_2(dl, si)
    sv = PREPARE(dl, st)
    variants = Channel.of('CH', 'CHDE')
    cv = CV(sv, variants)
    loo = LOO_COMMITTED()
    ev = EVALUATE(dl, sv, cv.collect(), loo, si, pub.curves)
    pr = PROTEOME(dl, sv)
    pk = PACKAGE()
    RESULTS(pub.figures, pub.curves, st, si, f12, ev.figures, ev.predictions, pr, pk)
}
