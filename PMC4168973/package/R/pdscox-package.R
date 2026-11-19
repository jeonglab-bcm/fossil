#' pdscox: pathway deregulation scores with Cox-LASSO for relapse prognosis
#'
#' Rebuilds the prognosis model of Huang S, Yee C, Ching T, Yu H, Garmire LX (2014). A novel
#' model to combine clinical and pathway-based transcriptomic information for the prognosis
#' prediction of breast cancer. PLoS Comput Biol 10(9):e1003851. doi:10.1371/journal.pcbi.1003851.
#'
#' Gene expression becomes pathway deregulation scores (\code{\link{pathway_scores}}), a Cox
#' model with an L1 penalty selects pathways (\code{\link{cox_lasso}}), the prognostic index
#' (\code{\link{prognostic_index}}) splits samples into higher and lower risk
#' (\code{\link{share_cutoff}}, \code{\link{risk_groups}}), and the split is judged by the
#' log-rank test and the ROC AUC (\code{\link{evaluate_model}}). The authors' code is lost;
#' this package was rebuilt from the paper's text and checked against its printed values in the
#' fossil reproduction (\url{https://github.com/jeonglab-bcm/fossil/tree/main/PMC4168973}).
#' @keywords internal
"_PACKAGE"
