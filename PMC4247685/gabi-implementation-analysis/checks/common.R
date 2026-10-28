# Shared helpers for the checks. Each check is run as `Rscript checks/NN_name.R`.
#
# GABi comes from the installed library (GABi 0.1 from CRAN). The S1 code (Additional file 1) is
# sourced from PMC4247685/sources/ (local, not in git), or from $GABI_SOURCES if set.

suppressPackageStartupMessages({
  library(GABi)
  library(survival) # S1 calls survdiff() unqualified
})

.this_file <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])
CHECKS_DIR <- dirname(normalizePath(.this_file))
ANALYSIS_DIR <- dirname(CHECKS_DIR)
SOURCES_DIR <- Sys.getenv("GABI_SOURCES",
                          normalizePath(file.path(ANALYSIS_DIR, "..", "sources"), mustWork = FALSE))
S1_FILE <- file.path(SOURCES_DIR, "12859_2014_355_MOESM1_ESM.txt")
TARBALL <- file.path(SOURCES_DIR, "GABi_0.1.tar.gz")
SHA256 <- c(tarball = "ae9655fc16e48a5e7da46d4e09bdef835ef65e46da8409d38f37cbd01656b1fe",
            s1 = "f91e4234ae7c76ca7ebf4a852b95373012f82cc0206ceb07d4bf94552d73e1f7")

.n_pass <- 0L
.n_fail <- 0L

# Print one PASS/FAIL line. `cond` must be a single TRUE/FALSE.
check <- function(id, cond, text, detail = NULL) {
  ok <- isTRUE(cond)
  if (ok) .n_pass <<- .n_pass + 1L else .n_fail <<- .n_fail + 1L
  cat(sprintf("%s  %s  %s%s\n", if (ok) "PASS" else "FAIL", id, text,
              if (is.null(detail)) "" else paste0("  [", detail, "]")))
  invisible(ok)
}

note <- function(...) cat("      ", sprintf(...), "\n", sep = "")

done <- function() {
  cat(sprintf("SUMMARY %s: %d pass, %d fail\n", basename(.this_file), .n_pass, .n_fail))
  quit(save = "no", status = if (.n_fail > 0) 1 else 0)
}

# S1 functions, loaded into their own environment.
load_s1 <- function() {
  if (!file.exists(S1_FILE)) stop("S1 not found at ", S1_FILE, " (see README: Getting the sources)")
  if (unname(tools::sha256sum(S1_FILE)) != SHA256[["s1"]]) stop("S1 sha256 mismatch")
  e <- new.env(parent = globalenv())
  sys.source(S1_FILE, envir = e)
  e
}

# GABi's row filter (GABi.R:7-18), reimplemented to build the environment the S1 functions expect.
# 03_row_filter.R checks that this matches what GABi passes to the fitness function.
gabi_diffRows <- function(x, diffThreshold = 0.9) {
  mn <- apply(x, 1, min, na.rm = TRUE)
  mx <- apply(x, 1, max, na.rm = TRUE)
  inv <- which(mn == mx)
  d <- setdiff(seq_len(nrow(x)), inv)
  s <- (rowMeans(x[d, , drop = FALSE], na.rm = TRUE) - mn[d]) / (mx[d] - mn[d])
  setdiff(seq_len(nrow(x)), c(d[s < 1 - diffThreshold], d[s > diffThreshold], inv))
}

# Give an S1 (or GABi) function the free variables it reads from GABi's frame
# (GABi.R:31-32 sets environment(fitnessFun) <- environment()).
bind <- function(f, x, fitnessArgs, diffRows = gabi_diffRows(x)) {
  e <- new.env(parent = globalenv())
  e$x <- x
  e$diffRows <- diffRows
  e$row.mins <- apply(x, 1, min, na.rm = TRUE)
  e$row.maxes <- apply(x, 1, max, na.rm = TRUE)
  e$fitnessArgs <- fitnessArgs
  environment(f) <- e
  f
}

# Same function, but returns all its local variables instead of its last expression.
# Used to read intermediate values of the authors' code without copying it.
instrument <- function(f) {
  b <- body(f)
  b[[length(b)]] <- quote(as.list(environment()))
  body(f) <- b
  f
}

# Replace one exact fragment of a function's deparsed source. Fails unless it occurs exactly once.
patch <- function(f, from, to) {
  src <- deparse(f, width.cutoff = 500L)
  hits <- sum(lengths(regmatches(src, gregexpr(from, src, fixed = TRUE))))
  if (hits != 1) stop("patch: '", from, "' found ", hits, " times")
  g <- eval(parse(text = gsub(from, to, src, fixed = TRUE)))
  environment(g) <- environment(f)
  g
}

# First sub-call of `expr` whose deparsed text starts with `prefix`.
find_call <- function(expr, prefix) {
  txt <- paste(deparse(expr, width.cutoff = 500L), collapse = "\n")
  if (startsWith(txt, prefix)) return(expr)
  if (is.call(expr)) for (a in as.list(expr)[-1]) {
    if (!missing(a) && !is.null(a)) {
      r <- find_call(a, prefix)
      if (!is.null(r)) return(r)
    }
  }
  NULL
}

# Run an expression (usually a GABi call, which prints progress with cat()) and keep its value,
# printed output and warnings.
quiet <- function(expr) {
  warns <- character()
  log <- withCallingHandlers(
    capture.output(value <- expr),
    warning = function(w) {
      warns <<- c(warns, conditionMessage(w))
      invokeRestart("muffleWarning")
    })
  list(value = value, log = log, warnings = warns)
}

# trace()/untrace() a GABi namespace function without the console messages.
trace_ns <- function(name, tracer, exit = NULL) {
  args <- list(name, tracer = tracer, where = asNamespace("GABi"), print = FALSE)
  if (!is.null(exit)) args$exit <- exit
  invisible(suppressMessages(capture.output(do.call(trace, args, quote = TRUE))))
}
untrace_ns <- function(name) invisible(suppressMessages(capture.output(untrace(name, where = asNamespace("GABi")))))
