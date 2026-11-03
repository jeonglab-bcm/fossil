# The files analysed are the ones named in the README, and the installed GABi is the CRAN 0.1 code.
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "common.R"))

check("01.1", unname(tools::sha256sum(TARBALL)) == SHA256[["tarball"]], "GABi_0.1.tar.gz sha256 matches")
check("01.2", unname(tools::sha256sum(S1_FILE)) == SHA256[["s1"]], "Additional file 1 (S1) sha256 matches")

tmp <- tempfile("gabi-src-")
dir.create(tmp)
untar(TARBALL, exdir = tmp)
src <- new.env()
for (f in list.files(file.path(tmp, "GABi", "R"), full.names = TRUE)) sys.source(f, envir = src)
ns <- asNamespace("GABi")
same <- vapply(ls(src), function(n) identical(deparse(get(n, src)), deparse(get(n, ns))), logical(1))
check("01.3", as.character(packageVersion("GABi")) == "0.1" && all(same) &&
        setequal(ls(src), ls(ns)),
      "installed GABi 0.1 has exactly the tarball's functions, unchanged",
      paste(length(same), "functions"))

s1 <- load_s1()
check("01.4", setequal(ls(s1), c("block.fitness", "block.selection", "cor.fitness", "cor.selection",
                                 "highvar.fitness", "highvar.selection", "getFitnesses",
                                 "featureSelection.dysregSurv")),
      "S1 defines the 8 fitness/selection functions for the 4 models")
unlink(tmp, recursive = TRUE)
done()
