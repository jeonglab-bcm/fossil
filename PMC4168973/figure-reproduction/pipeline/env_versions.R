# R runtime and package versions of the run, for results.json.
args <- commandArgs(TRUE)
pk <- c("pdscox", "pathifier", "princurve", "penalized", "survival", "limma", "jsonlite")
v <- c(list(R = paste(R.version$major, R.version$minor, sep = ".")),
       setNames(lapply(pk, function(p) tryCatch(as.character(packageVersion(p)), error = function(e) NA)), pk))
jsonlite::write_json(v, args[1], auto_unbox = TRUE, pretty = TRUE)
