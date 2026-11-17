# Make the example data of multds and its expected output.
#   Rscript scripts/make_example_data.R SMA_TARBALL inst/extdata
# The input is synthetic, drawn as in the paper's alternative case (independent N(0, 1) variables,
# mean 0.8 in Class 2 for the first 20 of 300), with an imbalanced training set (8 against 32) and
# a balanced test set (10 and 10). The expected output does not come from multds:
# - expected_selected.csv: the 40 variables with the largest |t| from stats::t.test(var.equal = TRUE)
#   on the sample-centred training set;
# - expected_predictions.csv: the classes that sma::stat.diag.da (sma 0.5.15, the function the paper
#   used for DLDA and DQDA) predicts for the test samples with those 40 variables.
args <- commandArgs(trailingOnly = TRUE)
out <- args[2]
set.seed(523)
p <- 300
gen <- function(n1, n2) {
  x <- matrix(rnorm((n1 + n2) * p), n1 + n2, p)
  x[n1 + seq_len(n2), 1:20] <- x[n1 + seq_len(n2), 1:20] + 0.8
  data.frame(class = c(rep(1L, n1), rep(2L, n2)), round(x, 4))
}
train <- gen(8, 32)
test <- gen(10, 10)
names(train)[-1] <- names(test)[-1] <- sprintf("v%03d", 1:p)
write.csv(train, file.path(out, "train.csv"), row.names = FALSE)
write.csv(test, file.path(out, "test.csv"), row.names = FALSE)

xtr <- as.matrix(train[, -1]); xtr <- xtr - rowMeans(xtr)
xte <- as.matrix(test[, -1]); xte <- xte - rowMeans(xte)
tt <- apply(xtr, 2, function(v) t.test(v[train$class == 1], v[train$class == 2], var.equal = TRUE)$statistic)
sel <- order(-abs(tt))[1:40]
write.csv(data.frame(rank = 1:40, variable = colnames(xtr)[sel], t = round(unname(tt[sel]), 6)),
          file.path(out, "expected_selected.csv"), row.names = FALSE)

tmp <- tempfile(); dir.create(tmp)
utils::untar(args[1], files = c("sma/R/Rdisc.R", "sma/R/Rna.R"), exdir = tmp)
sma <- new.env()
sys.source(file.path(tmp, "sma/R/Rna.R"), envir = sma)
sys.source(file.path(tmp, "sma/R/Rdisc.R"), envir = sma)
pred <- data.frame(sample = seq_len(nrow(test)), class = test$class,
                   DLDA = sma$stat.diag.da(xtr[, sel], train$class, xte[, sel], pool = 1)$pred,
                   DQDA = sma$stat.diag.da(xtr[, sel], train$class, xte[, sel], pool = 0)$pred)
write.csv(pred, file.path(out, "expected_predictions.csv"), row.names = FALSE)
