# Haplotype frequencies and phase posteriors from haplo.stats::haplo.em, for haplo_check.py.
#   Rscript haplo_check.R GENO.csv OUT.csv
# GENO.csv: columns g1, g2 (counted-allele counts 0, 1, 2 at SNP 1 and SNP 2), one row per person.
# OUT.csv: one row per haplotype (a1, a2 = counted-allele indicators) with its frequency, and the
# posterior probability, for the first double heterozygote, of the phase carrying (1,1)+(0,0).
args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages(library(haplo.stats))
g <- read.csv(args[1])
al <- function(x) cbind(ifelse(x >= 1, 2, 1), ifelse(x >= 2, 2, 1))  # allele 2 = counted
geno <- cbind(al(g$g1), al(g$g2))
set.seed(1)
em <- haplo.em(geno, locus.label = c("s1", "s2"), control = haplo.em.control(min.posterior = 1e-12))
hap <- em$haplotype
out <- data.frame(a1 = as.integer(hap[, 1]) - 1, a2 = as.integer(hap[, 2]) - 1, freq = em$hap.prob)
dh <- which(g$g1 == 1 & g$g2 == 1)[1]
post <- NA
if (!is.na(dh)) {
  sel <- em$subj.id == dh
  h1 <- em$hap1code[sel]; h2 <- em$hap2code[sel]; p <- em$post[sel]
  key <- function(i) paste(out$a1[i], out$a2[i])
  for (k in seq_along(p)) {
    pair <- sort(c(key(h1[k]), key(h2[k])))
    if (identical(pair, sort(c("0 0", "1 1")))) post <- p[k]
  }
}
out$post_00_11 <- post
write.csv(out, args[2], row.names = FALSE)
cat(as.character(packageVersion("haplo.stats")), "\n")
