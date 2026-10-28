# Fig. 5 data: the clinical rows of Table S3 (validation cohort) and the logrank tests of p. 12.
# Usage: Rscript make_fig5_data.R <Table S3> <out clinical .csv> <out tests .json>
suppressMessages({library(survival); library(jsonlite)})
a <- commandArgs(trailingOnly = TRUE)

s3 <- read.delim(a[1], row.names = 1, check.names = FALSE, nrows = 4)
cl <- data.frame(sample = colnames(s3), group = sub("[.].*", "", colnames(s3)),
                 PFS = as.numeric(s3["PFS", ]), progression = as.numeric(s3["Event.1.Progression", ]),
                 OS = as.numeric(s3["OS", ]), death = as.numeric(s3["Event.1.Death", ]))
write.csv(cl, a[2], row.names = FALSE)

test <- function(f) {
  s <- survdiff(f, data = cl)
  list(n = as.integer(s$n), events = as.integer(s$obs), chisq = s$chisq,
       p = pchisq(s$chisq, 1, lower.tail = FALSE))
}
km <- summary(survfit(Surv(PFS, progression) ~ group, data = cl))$table
write_json(list(pfs = test(Surv(PFS, progression) ~ group), os = test(Surv(OS, death) ~ group),
                pfs_median = setNames(as.list(km[, "median"]), c("Group1", "Group2")),
                paper = list(os_p = 0.1, pfs_p = 0.15)),
           a[3], auto_unbox = TRUE, digits = NA, pretty = TRUE)
