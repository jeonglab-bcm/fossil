# The simulation design of the paper: the three two-locus disease models of Marchini, Donnelly and
# Cardon (2005), each disease locus observed through a marker in LD (r^2) with it, plus null
# markers with minor allele frequency drawn from U(0, 0.5).
#
# Marchini's tables give the odds of disease for each two-locus genotype (rows: copies of the
# disease allele at locus A, columns: at locus B):
#   model 1  alpha (1 + theta)^(i + j)
#   model 2  alpha for i = 0 or j = 0, else alpha (1 + theta)^(i * j): 1+t, (1+t)^2, (1+t)^4;
#            epiMODE's Table 1 (the same group) has (1 + theta)^(i + j): (1+t)^2, (1+t)^3, (1+t)^4
#   model 3  alpha for i = 0 or j = 0, else alpha (1 + theta)
# alpha and theta are solved from the prevalence and the marginal effect lambda, defined (Zhang
# and Liu 2007; epiMODE Text S1) as the odds ratio of the marginal penetrances of the
# heterozygote and the wild-type homozygote at locus A, minus 1.

#' Disease model of the simulation study
#'
#' @param model 1, 2 or 3 (Marchini et al. 2005).
#' @param lambda Marginal effect of each locus (paper: 0.3, 0.5 and 1.0 for models 1-3).
#' @param maf Minor (disease) allele frequency of both disease loci.
#' @param prevalence Disease prevalence (paper: 0.1).
#' @param scale "odds" (Marchini's tables of odds) or "risk" (the same table read as relative
#'   risks, as in epiMODE's Text S1).
#' @param table "epimode" or "marchini" (model 2 only). epiMODE's Table 1 (Tang, Wu, Jiang and Li
#'   2009, the same group) prints (1+f)^2, (1+f)^3 and (1+f)^4 for two, three and four disease
#'   alleles; Marchini et al. print 1+f, (1+f)^2 and (1+f)^4. The epiMODE table gives the
#'   paper's chi-squared powers (see the reproduction's README), so it is the default.
#' @return A list with the 3 x 3 \code{penetrance} table, \code{alpha}, \code{theta}, and the
#'   achieved \code{prevalence} and \code{lambda}.
#' @export
disease_model <- function(model, lambda, maf, prevalence = 0.1, scale = c("odds", "risk"),
                          table = c("epimode", "marchini")) {
  scale <- match.arg(scale)
  table <- match.arg(table)
  pattern <- function(theta) {
    i <- matrix(0:2, 3, 3)
    j <- t(i)
    switch(as.character(model),
      "1" = (1 + theta)^(i + j),
      "2" = if (table == "marchini") ifelse(i == 0 | j == 0, 1, (1 + theta)^(i * j))
            else ifelse(i == 0 | j == 0, 1, (1 + theta)^(i + j)),
      "3" = ifelse(i == 0 | j == 0, 1, 1 + theta),
      stop("model must be 1, 2 or 3"))
  }
  hw <- c((1 - maf)^2, 2 * maf * (1 - maf), maf^2)
  w <- outer(hw, hw)
  pen <- function(base, theta) {
    r <- base * pattern(theta)
    if (scale == "odds") r / (1 + r) else r
  }
  # base parameter giving the prevalence for a given theta
  base_for <- function(theta) {
    f <- function(lb) sum(w * pen(exp(lb), theta)) - prevalence
    hi <- if (scale == "odds") 20 else log(1 / max(pattern(theta)))
    if (f(hi) < 0) return(NA_real_)
    exp(stats::uniroot(f, c(-30, hi), tol = 1e-13)$root)
  }
  marg_lambda <- function(theta) {
    b <- base_for(theta)
    if (is.na(b)) return(NA_real_)
    P <- pen(b, theta)
    m <- as.vector(P %*% hw)            # marginal penetrance by genotype at locus A
    odds <- m / (1 - m)
    odds[2] / odds[1] - 1
  }
  g <- function(lt) {
    v <- marg_lambda(exp(lt))
    if (is.na(v)) return(1e6)
    v - lambda
  }
  root <- stats::uniroot(g, c(-20, 8), tol = 1e-12)$root
  theta <- exp(root)
  b <- base_for(theta)
  if (is.na(b)) stop("no model with these parameters (a penetrance would exceed 1)")
  P <- pen(b, theta)
  if (any(P > 1) || abs(marg_lambda(theta) - lambda) > 1e-6)
    stop("no model with these parameters (a penetrance would exceed 1)")
  dimnames(P) <- list(A = 0:2, B = 0:2)
  list(penetrance = P, alpha = b, theta = theta, prevalence = sum(w * P),
       lambda = marg_lambda(theta), model = model, maf = maf, scale = scale, table = table)
}

#' Marker-given-locus allele probabilities for a given r^2
#'
#' The marker has the same minor allele frequency p as the disease locus (epiMODE Text S1), and
#' the two minor alleles are in positive LD with correlation r = sqrt(r2).
#'
#' @param maf Minor allele frequency of the locus and the marker.
#' @param r2 Squared correlation between them.
#' @return \code{c(q_minor, q_major)}: probability that a marker allele is minor given that the
#'   locus allele on the same haplotype is minor or major.
#' @export
ld_transition <- function(maf, r2) {
  r <- sqrt(r2)
  c(q_minor = maf + r * (1 - maf), q_major = maf * (1 - r))
}

#' Simulate one case-control data set
#'
#' @param model,lambda,maf,prevalence,scale,table See \code{\link{disease_model}}.
#' @param r2 LD between each disease locus and its marker (paper: 0.7 or 1).
#' @param n_markers Total markers (paper: 1000), including the two disease markers.
#' @param n_cases,n_controls Sample sizes (paper: 1000 each).
#' @param positions Columns of the two disease markers; random if NULL.
#' @return A list: \code{geno} (integer matrix, cases first), \code{status}, \code{disease}
#'   (columns of the two disease markers), \code{maf} (of every marker), \code{model}.
#' @export
simulate_dataset <- function(model, lambda, maf, r2, prevalence = 0.1, n_markers = 1000,
                             n_cases = 1000, n_controls = 1000, positions = NULL,
                             scale = "odds", table = "epimode") {
  dm <- disease_model(model, lambda, maf, prevalence, scale = scale, table = table)
  hw <- c((1 - maf)^2, 2 * maf * (1 - maf), maf^2)
  w <- as.vector(outer(hw, hw))                  # first locus fastest
  P <- as.vector(dm$penetrance)
  draw <- function(n, prob) {
    cell <- sample.int(9L, n, replace = TRUE, prob = prob) - 1L
    cbind(cell %% 3L, cell %/% 3L)
  }
  loci <- rbind(draw(n_cases, w * P), draw(n_controls, w * (1 - P)))
  q <- ld_transition(maf, r2)
  marker <- function(g) stats::rbinom(length(g), g, q[1]) + stats::rbinom(length(g), 2L - g, q[2])
  n <- n_cases + n_controls
  null_maf <- stats::runif(n_markers - 2, 0, 0.5)
  if (is.null(positions)) positions <- sort(sample.int(n_markers, 2))
  geno <- matrix(0L, n, n_markers)
  others <- setdiff(seq_len(n_markers), positions)
  geno[, others] <- matrix(stats::rbinom(n * length(others), 2L, rep(null_maf, each = n)), n)
  geno[, positions[1]] <- marker(loci[, 1])
  geno[, positions[2]] <- marker(loci[, 2])
  storage.mode(geno) <- "integer"
  colnames(geno) <- paste0("snp", seq_len(n_markers))
  mafs <- numeric(n_markers)
  mafs[others] <- null_maf
  mafs[positions] <- maf
  list(geno = geno, status = rep(1:0, c(n_cases, n_controls)), disease = positions, maf = mafs,
       model = dm)
}
