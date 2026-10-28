x <- c(2,3,1); p <- c(.2,.3,.5); N <- sum(x)
v1 <- function(psi) -(lgamma(1/psi+N) - lgamma(1/psi)) + sum(lgamma(p/psi + x) - lgamma(p/psi))
v2 <- function(psi) { a <- p/psi; lgamma(sum(a)) - lgamma(sum(a)+N) + sum(lgamma(a+x)) - sum(lgamma(a)) }
v3 <- function(psi) { A <- 1/psi; a <- p*A; lgamma(A) - lgamma(A+N) + sum(lgamma(a+x) - lgamma(a)) }
grids <- list()
for (L in c(50,91,100,150,181,200,250,300,301,400,451,500,901,1000)) grids[[paste0("len",L)]] <- seq(1e-11, 1e-10, length.out=L)
for (s in c(1e-13,2e-13,2.5e-13,3e-13,4e-13,5e-13,1e-12)) grids[[paste0("by",s)]] <- seq(1e-11, 1e-10, by=s)
grids[["i1e-13"]] <- (100:1000)*1e-13
grids[["i2e-13"]] <- (50:500)*2e-13
grids[["i5e-13"]] <- (20:200)*5e-13
grids[["i1e-12"]] <- (10:100)*1e-12
rows <- list()
for (g in names(grids)) for (psi in grids[[g]]) rows[[length(rows)+1]] <- sprintf("%s,%.17g,%.17g,%.17g,%.17g", g, psi, v1(psi), v2(psi), v3(psi))
writeLines(c("grid,psi,v1,v2,v3", unlist(rows)), "eq6_grids.csv")
cat(length(rows), "rows\n")
