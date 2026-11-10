#!/bin/bash
# PSI-BLAST profiles for the reproduction, on the Skyriver cluster (about 60 CPU hours in all).
# Writes output/profiles/pdb_profiles.npz (the 2,458 chains of Additional file 1 plus the two
# human proteins of Figs 8 and 9) and output/profiles/human_profiles.npz (the proteome sample).
#
# Submit from the repository root:  sbatch PMC1800866/figure-reproduction/run_profiles.sbatch
# It runs the setup here (debugq), then submits the PSI-BLAST arrays and a collecting job.
#
# Database: UniRef100 release 2010_01 (9,808,438 clusters), the oldest UniRef archive; the 2005
# NCBI nr the paper used is not archived. BLAST+ 2.17.0 from NCBI.
#SBATCH --job-name=pmc1800866-profiles
#SBATCH --partition=debugq
#SBATCH --time=06:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --output=pmc1800866-profiles-%j.out
set -euo pipefail
ROOT=$PWD/PMC1800866
W=$ROOT/work            # git-ignored; compute nodes must see it (not /tmp)
PY=${PY:-$ROOT/.venv/bin/python}
P=$ROOT/figure-reproduction/pipeline
mkdir -p "$W/db" "$W/logs"
cd "$W/db"
[ -x ncbi-blast-2.17.0+/bin/psiblast ] || {
  curl -sS --retry 5 -O https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.17.0/ncbi-blast-2.17.0+-x64-linux.tar.gz
  tar xzf ncbi-blast-2.17.0+-x64-linux.tar.gz; }
[ -s uniref100_2010_01.pin ] || [ -s uniref100_2010_01.00.pin ] || {
  curl -sS --retry 5 -C - -O https://ftp.uniprot.org/pub/databases/uniprot/previous_releases/release-2010_01/uniref/uniref2010_01.tar.gz
  echo "37a9d0a3c12dcc01c8a7513c0a0ff350b966366ba1311a9f65fa98b82e9173ce  uniref2010_01.tar.gz" | sha256sum -c
  tar xzf uniref2010_01.tar.gz uniref100.tar && tar xf uniref100.tar uniref100.xml.gz
  "$PY" "$P/uniref_xml_to_fasta.py" uniref100.xml.gz > uniref100_2010_01.fasta && rm uniref100.xml.gz uniref100.tar
  ncbi-blast-2.17.0+/bin/makeblastdb -in uniref100_2010_01.fasta -dbtype prot -out uniref100_2010_01 -parse_seqids -max_file_sz 4GB; }
cd "$W"
# Queries: SEQRES of the supplement's chains (output/struct/chains.tsv) and the sampled human proteins.
awk -F'\t' 'NR>1{print ">"$1"\n"$4}' "$ROOT/figure-reproduction/output/struct/chains.tsv" > queries.fa
awk 'NR>1' "$ROOT/figure-reproduction/output/proteome/proteome_sample.fa" >/dev/null 2>&1 || true
cp "$ROOT/figure-reproduction/output/proteome/proteome_sample.fa" proteome_sample.fa
grep -A1 -E '^>(NP_060357.1|XP_374396.2)$' proteome_sample.fa | grep -v -- '--' >> queries.fa
run() {  # name fasta outdir tasks
  sbatch --parsable --job-name="$1" --partition=debugq --time=08:00:00 --cpus-per-task=4 --mem=8G \
    --array=0-$(($4 - 1)) --output="logs/$1-%A_%a.out" \
    --wrap="PSIBLAST=$W/db/ncbi-blast-2.17.0+/bin/psiblast bash $P/run_psiblast.sh $2 $W/db/uniref100_2010_01 $3 4 \$SLURM_ARRAY_TASK_ID $4"
}
a=$(run p19psi queries.fa pssm 60)
b=$(run p19hum proteome_sample.fa pssm_human 20)
sbatch --dependency=afterok:$a:$b --partition=debugq --time=01:00:00 --mem=8G --output=logs/collect-%j.out \
  --wrap="$PY $P/collect_profiles.py $W/pssm $ROOT/figure-reproduction/output/profiles/pdb_profiles.npz && \
          $PY $P/collect_profiles.py $W/pssm_human $ROOT/figure-reproduction/output/profiles/human_profiles.npz"
