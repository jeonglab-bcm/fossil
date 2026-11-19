# Read the two downloaded supplements into tidy CSV files.
#   Rscript prepare_data.R DOWNLOADS_DIR OUT_DIR
# breast.csv: Szabo et al.'s Additional data file 1 (80 tumours x 6 genes; PUM named PUM1 as in
#   the paper). vandesompele.csv: Vandesompele et al.'s Additional data file 1 (85 samples x 10
#   genes) with the tissue type taken from the sample name. Values are not changed.
args <- commandArgs(TRUE)
dl <- args[1]; out <- args[2]
dir.create(out, showWarnings = FALSE, recursive = TRUE)
x <- as.data.frame(readxl::read_excel(file.path(dl, "gb-2004-5-8-r59-s1.xls"), sheet = "Relative copy numbers"))
stopifnot(identical(names(x), c("Sample", "MRPL19", "PSMC4", "SF3A1", "PUM", "GAPD", "ACTB")), nrow(x) == 80)
names(x)[names(x) == "PUM"] <- "PUM1"; names(x)[1] <- "sample"
x$sample <- paste0("T", x$sample)
write.csv(x, file.path(out, "breast.csv"), row.names = FALSE)
r <- utils::read.delim(file.path(dl, "gb-2002-3-7-research0034-s1.TXT"), skip = 2, check.names = FALSE,
                       strip.white = TRUE, stringsAsFactors = FALSE)
names(r)[1] <- "sample"
r <- r[!is.na(suppressWarnings(as.numeric(r$ACTB))), ]
r$tissue <- sub("^(BM|FIB|LEU|NB|POOL).*", "\\1", r$sample)
r <- r[c("sample", "tissue", setdiff(names(r), c("sample", "tissue")))]
stopifnot(nrow(r) == 85, identical(as.vector(table(r$tissue)), c(9L, 20L, 13L, 34L, 9L)))
write.csv(r, file.path(out, "vandesompele.csv"), row.names = FALSE)
cat("breast", dim(x), "vandesompele", dim(r), "\n")
