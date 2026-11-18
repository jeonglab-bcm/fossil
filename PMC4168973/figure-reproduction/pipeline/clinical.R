# Table 1, the Fig. 1 tests and curves, and the univariate Cox p-values of Table 2's clinical model.
#   Rscript clinical.R DATA_DIR OUT_DIR
# Writes OUT_DIR/clinical.json and OUT_DIR/curves/fig1_<panel>.csv (Kaplan-Meier steps per group).
suppressPackageStartupMessages({library(pdscox); library(survival); library(jsonlite)})
invisible(Sys.setlocale("LC_COLLATE", "C"))  # group order ("LN+" before "LN-") must not depend on the locale
a <- commandArgs(TRUE)
dd <- a[1]; out <- a[2]
dir.create(file.path(out, "curves"), recursive = TRUE, showWarnings = FALSE)
sets <- lapply(c(miller = "miller", pawitan = "pawitan", ivshina = "ivshina", desmedt = "desmedt"),
               function(s) readRDS(file.path(dd, paste0(s, ".rds")))$clin)

fmt3 <- function(x) sprintf("%.3f", x)
fmt2 <- function(x) sprintf("%.2f", x)
pct <- function(k, n) sprintf("%d (%d%%)", k, round(100 * k / n))
cnt <- function(v, val, n) if (is.na(val)) pct(sum(is.na(v)), n) else pct(sum(v == val, na.rm = TRUE), n)

# Table 1. Size categories: <10, 10-20, 20-50 and >50 mm with 20 in "20-50"; a tumour of exactly
# 50 mm falls in neither of the last two (the paper's Miller counts add up to 233 of 236).
size_counts <- function(s, n) c(
  "size <10" = pct(sum(s < 10, na.rm = TRUE), n), "size 10-20" = pct(sum(s >= 10 & s < 20, na.rm = TRUE), n),
  "size 20-50" = pct(sum(s >= 20 & s < 50, na.rm = TRUE), n), "size >50" = pct(sum(s > 50, na.rm = TRUE), n))
t1 <- list()
for (s in names(sets)) {
  c <- sets[[s]]; n <- nrow(c)
  # Mean RFS over all patients; two Miller patients without a time count as 0 (see results_notes)
  tm <- ifelse(is.na(c$time), 0, c$time)
  v <- c(patients = as.character(n), relapse = pct(sum(c$event == 1), n),
         "non-relapse" = pct(sum(c$event == 0), n), "mean RFS" = fmt3(mean(tm)))
  if (!is.null(c$age)) v <- c(v, "mean age" = fmt2(mean(c$age)))
  if (!is.null(c$er)) v <- c(v, "ER positive" = cnt(c$er, 1, n), "ER negative" = cnt(c$er, 0, n), "ER NA" = cnt(c$er, NA, n))
  if (!is.null(c$pgr)) v <- c(v, "PG positive" = cnt(c$pgr, 1, n), "PG negative" = cnt(c$pgr, 0, n), "PG NA" = cnt(c$pgr, NA, n))
  if (!is.null(c$size_mm)) v <- c(v, size_counts(c$size_mm, n))
  v <- c(v, "grade 1" = cnt(c$grade, 1, n), "grade 2" = cnt(c$grade, 2, n), "grade 3" = cnt(c$grade, 3, n),
         "grade NA" = cnt(c$grade, NA, n))
  if (!is.null(c$node)) {
    if (s != "desmedt") v <- c(v, "LN positive" = cnt(c$node, 1, n))
    v <- c(v, "LN negative" = cnt(c$node, 0, n))
    if (s != "desmedt") v <- c(v, "LN NA" = cnt(c$node, NA, n))
  }
  if (!is.null(c$p53)) {
    # A tumour without p53 status counts as wild type (Table 1: no NA for Miller).
    p <- if (s == "miller") ifelse(is.na(c$p53), 0, c$p53) else c$p53
    v <- c(v, "p53 mutated" = cnt(p, 1, n), "p53 wild type" = cnt(p, 0, n), "p53 NA" = cnt(p, NA, n))
  }
  t1[[s]] <- as.list(v)
}
# Variants that test the causes
pw <- sets$pawitan
t1_variants <- list(
  pawitan_mean_rfs_relapse_time_only = fmt3(mean(pw$time_relapse)),
  miller_mean_rfs_known_times_only = fmt3(mean(sets$miller$time, na.rm = TRUE)),
  miller_mean_rfs_truncated = sprintf("%.3f", floor(mean(ifelse(is.na(sets$miller$time), 0, sets$miller$time)) * 1000) / 1000),
  miller_size_50_in_20_50 = pct(sum(sets$miller$size_mm >= 20 & sets$miller$size_mm <= 50), nrow(sets$miller)),
  miller_p53_na = sum(is.na(sets$miller$p53)))

# Fig. 1, Miller. Missing times are 0, missing p53 is wild type (both found by matching the paper).
m <- sets$miller
m$t0 <- ifelse(is.na(m$time), 0, m$time)
m$p53w <- ifelse(is.na(m$p53), 0, m$p53)
m$size3 <- cut(m$size_mm, c(-Inf, 21, 35, Inf), right = FALSE, labels = c("<21", "21-35", ">=35"))
m$size3_legend <- cut(m$size_mm, c(-Inf, 21, 42, Inf), right = FALSE, labels = c("<21", "21-42", ">=42"))
chi <- function(v) chisq.test(table(v, m$event))$p.value
fig1_chisq <- list(ER = chi(m$er), PG = chi(m$pgr), p53 = chi(m$p53w), grade = chi(m$grade), LN = chi(m$node))
lr <- function(g, time = m$t0, rho = 0) logrank_p(time, m$event, g, rho = rho)
fig1_logrank <- list(p53 = lr(m$p53w), grade = lr(m$grade), size = lr(m$size3), LN = lr(m$node),
                     ER = lr(m$er), PG = lr(m$pgr))
fig1_variants <- list(
  size_legend_cuts_21_42 = lr(m$size3_legend),
  missing_times_dropped = lapply(list(p53 = m$p53w, grade = m$grade, size = m$size3, LN = m$node, ER = m$er, PG = m$pgr),
                                 function(g) logrank_p(m$time, m$event, g)),
  peto_wilcoxon_rho1 = lapply(list(p53 = m$p53w, grade = m$grade, size = m$size3, LN = m$node, ER = m$er, PG = m$pgr),
                              function(g) lr(g, rho = 1)),
  chisq_without_yates = list(ER = chisq.test(table(m$er, m$event), correct = FALSE)$p.value,
                             LN = chisq.test(table(m$node, m$event), correct = FALSE)$p.value),
  p53_chisq_missing_dropped = chisq.test(table(m$p53, m$event))$p.value)

km_steps <- function(time, event, group, file) {
  ok <- !is.na(group)
  f <- survfit(Surv(time[ok], event[ok]) ~ group[ok])
  st <- if (is.null(f$strata)) rep("all", length(f$time)) else rep(sub("^[^=]*=", "", names(f$strata)), f$strata)
  write.csv(data.frame(group = st, time = f$time, surv = f$surv, n_censor = f$n.censor, n_event = f$n.event),
            file, row.names = FALSE)
}
km_steps(m$t0, m$event, factor(ifelse(m$node == 1, "LN+", "LN-")), file.path(out, "curves", "fig1_B.csv"))
km_steps(m$t0, m$event, factor(paste0("grade=", m$grade)), file.path(out, "curves", "fig1_C.csv"))
km_steps(m$t0, m$event, factor(ifelse(m$p53w == 1, "P53+", "P53-")), file.path(out, "curves", "fig1_D.csv"))
km_steps(m$t0, m$event, m$size3, file.path(out, "curves", "fig1_E.csv"))
km_steps(m$t0, m$event, m$size3_legend, file.path(out, "curves", "fig1_E_legendcuts.csv"))
# Wrong-input controls: the same panel drawn from another clinical factor
km_steps(m$t0, m$event, factor(ifelse(m$er == 1, "LN+", "LN-")), file.path(out, "curves", "fig1_B_wrong.csv"))
km_steps(m$t0, m$event, factor(paste0("grade=", ifelse(m$size3 == "<21", 1, ifelse(m$size3 == "21-35", 2, 3)))),
         file.path(out, "curves", "fig1_C_wrong.csv"))
km_steps(m$t0, m$event, factor(ifelse(m$pgr == 1, "P53-", "P53+")), file.path(out, "curves", "fig1_D_wrong.csv"))
km_steps(m$t0, m$event, factor(c("<21", "21-35", ">=35")[pmin(m$grade, 3)], levels = c("<21", "21-35", ">=35")),
         file.path(out, "curves", "fig1_E_wrong.csv"))

# Table 2, clinical model: univariate Cox (Wald) p-values on Miller; size in mm as a number.
uc <- univariate_cox(cbind(LN = m$node, size = m$size_mm, grade = m$grade, p53 = m$p53w), m$t0, m$event)
t2_univariate <- setNames(as.list(uc$p), uc$feature)

write_json(list(table1 = t1, table1_variants = t1_variants, fig1_chisq = fig1_chisq,
                fig1_logrank = fig1_logrank, fig1_variants = fig1_variants,
                table2_clinical_univariate = t2_univariate),
           file.path(out, "clinical.json"), auto_unbox = TRUE, pretty = TRUE, digits = NA)
