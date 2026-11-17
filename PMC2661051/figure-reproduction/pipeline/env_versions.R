# Runtime and package versions of the run, for results.json.
args <- commandArgs(TRUE)
pk <- c("gseamod", "limma", "fdrtool", "corpcor", "globaltest", "jsonlite")
v <- c(list(R = paste(R.version$major, R.version$minor, sep = ".")),
       setNames(lapply(pk, function(p) tryCatch(as.character(packageVersion(p)), error = function(e) NA)), pk))
py <- tryCatch(system2(args[2], c("-c", shQuote("import sys,PIL,numpy;print(sys.version.split()[0],PIL.__version__,numpy.__version__)")), stdout = TRUE), error = function(e) "")
if (length(py) && nzchar(py[1])) { p <- strsplit(py[1], " ")[[1]]; v$python <- p[1]; v$pillow <- p[2]; v$numpy <- p[3] }
jsonlite::write_json(v, args[1], auto_unbox = TRUE, pretty = TRUE)
