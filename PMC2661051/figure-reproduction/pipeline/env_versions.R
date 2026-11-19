# R runtime and package versions of the run, for results.json (Python's are added by
# env_versions_py.py: calling Python from R can fail where R resets LD_LIBRARY_PATH).
args <- commandArgs(TRUE)
pk <- c("gseamod", "limma", "fdrtool", "corpcor", "globaltest", "jsonlite")
v <- c(list(R = paste(R.version$major, R.version$minor, sep = ".")),
       setNames(lapply(pk, function(p) tryCatch(as.character(packageVersion(p)), error = function(e) NA)), pk))
jsonlite::write_json(v, args[1], auto_unbox = TRUE, pretty = TRUE)
