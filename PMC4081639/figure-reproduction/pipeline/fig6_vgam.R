library(microbenchmark)
vgam_ll <- function(x, p, psi) {
  rho <- psi / (1 + psi)
  s <- 0
  for (k in seq_along(x)) s <- s + sum(log(p[k] * (1 - rho) + (0:(x[k] - 1)) * rho))
  s - sum(log((1 - rho) + (0:(sum(x) - 1)) * rho))
}
p <- c(1/6, 1/3, 1/2); psi <- 1/60
out <- NULL
for (n in 10^(2:5)) {
  x <- n * c(1, 2, 3)
  mb <- microbenchmark(vgam_ll(x, p, psi), times = 100)
  out <- rbind(out, data.frame(n = n, method = "VGAM", runtime_us = mb$time / 1000))
}
write.csv(out, "fig6_vgam.csv", row.names = FALSE)
print(aggregate(runtime_us ~ n, out, median))
