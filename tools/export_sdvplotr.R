# Export sdvplotR's team matching for sdvplot (Ruling R43): its clean_team_abbrs() table (abbr_mapping) and
# resolve_historical_abbr() table (historical_team_mappings) become data-raw/sdvplotr_*.csv, which
# tools/build_index.py turns into `sdvplotr` alias rows; logo_history becomes the parity-test fixture.
# Base R only. From the sdvplot root, with the sdvplotR checkout beside it (or its path as the argument):
#   R_ENVIRON_USER=/dev/null Rscript tools/export_sdvplotr.R [/path/to/sdvplotR]
args <- commandArgs(trailingOnly = TRUE)
src <- if (length(args)) args[[1]] else file.path("..", "sdvplotR")

e <- new.env()
load(file.path(src, "R", "sysdata.rda"), envir = e)
sys.source(file.path(src, "R", "historical_teams.R"), envir = e) # defines historical_team_mappings

# a named list of named character vectors (sport -> key -> canonical abbr) as one long table
long <- function(m) {
  d <- do.call(rbind, lapply(names(m), function(s) {
    data.frame(sport = s, key = enc2utf8(names(m[[s]])), canon = enc2utf8(unname(m[[s]])))
  }))
  d[order(d$sport, d$key, method = "radix"), ]
}
write <- function(d, path) {
  write.csv(d, path, row.names = FALSE, fileEncoding = "UTF-8", na = "")
  message(path, ": ", nrow(d), " rows")
}

# historical_team_mappings carries no season ranges: a key maps to the franchise's current abbreviation
write(long(e$abbr_mapping), file.path("data-raw", "sdvplotr_abbr_mapping.csv"))
write(long(e$historical_team_mappings), file.path("data-raw", "sdvplotr_historical.csv"))
lh <- e$logo_history
write(lh[order(lh$sport, lh$key, lh$season_from, lh$variant, method = "radix"), ],
      file.path("tests", "fixtures", "sdvplotr_logo_history.csv"))

commit <- system2("git", c("-C", src, "rev-parse", "HEAD"), stdout = TRUE)
dirty <- length(system2("git", c("-C", src, "status", "--porcelain", "--", "R", "data-raw"), stdout = TRUE)) > 0
writeLines(c(
  "sdvplotR commit the sdvplotr_*.csv snapshots and tests/fixtures/sdvplotr_logo_history.csv were exported from",
  "(tools/export_sdvplotr.R):",
  paste0(commit, if (dirty) " (with uncommitted changes)" else "")
), file.path("data-raw", "sdvplotr_commit.txt"))
