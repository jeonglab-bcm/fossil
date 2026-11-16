# Hypothesis test only (not part of the pipeline): GSE2034 re-normalized from its CEL files.
#   curl -O https://ftp.ncbi.nlm.nih.gov/geo/series/GSE2nnn/GSE2034/suppl/GSE2034_RAW.tar   (1 GB)
#   mkdir cel && tar xf GSE2034_RAW.tar -C cel
#   Rscript usa_cel_normalize.R          # writes gse2034_rma.tsv.gz and gse2034_mas5.tsv.gz
# Ran on Skyriver with a conda R 4.3 (bioconda affy 1.80, hgu133acdf) and preprocessCore built with
# --disable-threading (its threaded build fails there with "pthread_create() is 22").
# Then: python usa_cel_check.py gse2034_rma.tsv.gz,gse2034_mas5.tsv.gz SOURCES ANNOTATION usa_cel.json
library(affy)
files <- list.files("cel", pattern = "CEL.gz$", full.names = TRUE)
ab <- ReadAffy(filenames = files)
e <- exprs(rma(ab))
colnames(e) <- sub(".CEL.gz", "", basename(files))
write.table(e, gzfile("gse2034_rma.tsv.gz"), sep = "\t", quote = FALSE, col.names = NA)
m <- exprs(mas5(ab))
colnames(m) <- colnames(e)
write.table(m, gzfile("gse2034_mas5.tsv.gz"), sep = "\t", quote = FALSE, col.names = NA)
