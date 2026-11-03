# Reference implementation of the bicluster models as printed in Curry (2014), BMC Bioinformatics
# 15:355, written from the paper only (Eqs 14-16, 17-23, 24-29, 31-35, 45 and Algorithm 2).
#
# Convention, as in Algorithm 1: chr is a 0/1 vector over the columns of x (samples, J = which(chr == 1));
# rows of x are features (X). Where an equation is undefined or, as printed, contradicts the text, the
# function has a switch and the default is the printed form.

# Eqs 14-16. delta_i = 1 if mean_J(a_ij) >= theta; g = |J| * sum(delta).
paper_block <- function(chr, x, theta) {
  J <- which(chr == 1)
  I <- which(rowMeans(x[, J, drop = FALSE]) >= theta)
  list(score = length(J) * length(I), features = I)
}

# Eq 20-21. Seed row i* = argmax_x |cor(a_xJ, b)|, b = first PC rotation of A_XJ (length |J|).
# A_XJ has features as observations and the |J| columns as variables (prcomp defaults: centred, unscaled).
paper_cor_seed <- function(chr, x) {
  J <- which(chr == 1)
  b <- prcomp(x[, J, drop = FALSE])$rotation[, 1]
  r <- suppressWarnings(apply(x[, J, drop = FALSE], 1, cor, y = b)) # Pearson, as in Eq 20
  which.max(abs(r))
}

# Eqs 17-23. c_ii* is Pearson (Eq 17). p_i = 2*Phi(sqrt((|J|-3)/1.06) * atanh(c_ii*)) as printed (Eq 19, 22).
# sign = "printed": exactly that, which exceeds 1 for every positive correlation.
# sign = "two-sided": 2*Phi(-|z|), the usual Fisher-z p-value that the text implies.
# floor: lower bound on p_i. The paper gives none; with floor = 0 the seed row (c = 1) has p = 0 and
# the two-sided score is +Inf for every J.
paper_cor <- function(chr, x, alpha, sign = c("printed", "two-sided"), floor = 0) {
  sign <- match.arg(sign)
  J <- which(chr == 1)
  n <- length(J)
  seed <- paper_cor_seed(chr, x)
  cc <- suppressWarnings(apply(x[, J, drop = FALSE], 1, cor, y = x[seed, J]))
  z <- if (n > 3) sqrt((n - 3) / 1.06) * atanh(cc) else rep(0, length(cc))
  p <- if (sign == "printed") 2 * pnorm(z) else 2 * pnorm(-abs(z))
  p[is.na(p)] <- 1
  p <- pmax(p, floor)
  delta <- p < alpha
  list(score = -n * sum(log(p[delta])), features = which(delta), seed = seed, p = p)
}

# Eqs 24-29. ratio = var_J / var_J'; p_i = F_chi2(ratio; |J| - 1).
# tail = "printed": the CDF, as printed in Eq 25 (small when the J variance is small).
# tail = "upper": 1 - CDF, which is what the text ("variance ... significantly greater") describes.
paper_highvar <- function(chr, x, alpha, tail = c("printed", "upper"), floor = 0) {
  tail <- match.arg(tail)
  J <- which(chr == 1)
  ratio <- apply(x, 1, function(y) var(y[J]) / var(y[-J]))
  p <- pchisq(ratio, df = length(J) - 1, lower.tail = (tail == "printed"))
  p <- pmax(p, floor)
  delta <- p < alpha
  list(score = -length(J) * sum(log(p[delta])), features = which(delta), p = p)
}

# Not in the paper: an F-test version of Eq 25, the calibrated test for a ratio of two sample variances.
ftest_highvar <- function(chr, x, alpha, floor = 2e-16) {
  J <- which(chr == 1)
  ratio <- apply(x, 1, function(y) var(y[J]) / var(y[-J]))
  p <- pmax(pf(ratio, length(J) - 1, ncol(x) - length(J) - 1, lower.tail = FALSE), floor)
  delta <- p < alpha
  list(score = -length(J) * sum(log(p[delta])), features = which(delta), p = p)
}

# Eqs 31-35. Logrank z = sum_t (O_Jt - E_Jt) / sqrt(sum_t V_t) over distinct event times.
# Returns z and h as printed (-log(2*Phi(z))) and two-sided (-log(2*Phi(-|z|))).
paper_logrank <- function(time, event, inJ) {
  ev <- sort(unique(time[event == 1]))
  OJ <- EJ <- V <- 0
  for (t in ev) {
    atrisk <- time >= t
    Nt <- sum(atrisk); NJt <- sum(atrisk & inJ)
    Ot <- sum(time == t & event == 1); OJt <- sum(time == t & event == 1 & inJ)
    OJ <- OJ + OJt
    EJ <- EJ + Ot / Nt * NJt
    if (Nt > 1) V <- V + Ot * (NJt / Nt) * (1 - NJt / Nt) * (Nt - Ot) / (Nt - 1)
  }
  z <- (OJ - EJ) / sqrt(V)
  c(z = z, h_printed = -log(2 * pnorm(z)), h_two_sided = -log(2 * pnorm(-abs(z))))
}

# Eq 45. F-measure of two index sets.
fmeasure <- function(A, B) {
  k <- length(intersect(A, B))
  if (k == 0) return(0)
  2 * (k / length(A)) * (k / length(B)) / (k / length(A) + k / length(B))
}

# Algorithm 2 with the p10 offsets. Returns the matrix and the implanted rows I and columns J.
alg2 <- function(model = c("block", "cor", "highvar"), n = 100, m = 20,
                 p = sample(100, 1), q = sample(2:18, 1), zeta = runif(1)) {
  model <- match.arg(model)
  A <- matrix(runif(n * m), n, m)
  I <- sample(n, p)
  J <- sample(m, q)
  A[I, J] <- A[I, J] + switch(model,
    block = rnorm(1),
    cor = matrix(rnorm(q), p, q, byrow = TRUE),
    highvar = matrix(rnorm(p * q), p, q))
  A <- A + matrix(rnorm(n * m, 0, zeta), n, m)
  A <- t(apply(A, 1, function(r) (r - min(r)) / (max(r) - min(r))))
  list(x = A, I = sort(I), J = sort(J), p = p, q = q, zeta = zeta)
}
