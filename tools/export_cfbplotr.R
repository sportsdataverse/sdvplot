# Export cfbplotR's name lookup for sdvplot: team_name_mapping (alternate -> school, what clean_school_names() reads)
# joined to logo_ref (the school's type and the ESPN id in its ESPN logo URL, where it has one) becomes
# data-raw/cfbplotr_names.csv, which tools/build_index.py turns into "name" aliases (cfbplotr_aliases) and conference
# keys. A school logo_ref lacks keeps an empty type and id.
# Base R only. From the sdvplot root, with the cfbplotR checkout beside it (or its path as the argument):
#   R_ENVIRON_USER=/dev/null Rscript tools/export_cfbplotr.R [/path/to/cfbplotR]
args <- commandArgs(trailingOnly = TRUE)
src <- if (length(args)) args[[1]] else file.path("..", "cfbplotR")

e <- new.env()
load(file.path(src, "data", "team_name_mapping.rda"), envir = e)
load(file.path(src, "data", "logo_ref.rda"), envir = e)

m <- data.frame(alternate = enc2utf8(names(e$team_name_mapping)), school = enc2utf8(unname(e$team_name_mapping)))
lr <- as.data.frame(e$logo_ref)[, c("school", "type", "logo")]
lr$espn_id <- ifelse(grepl("/ncaa/500/[0-9]+\\.png$", lr$logo), sub(".*/ncaa/500/([0-9]+)\\.png$", "\\1", lr$logo), NA)
d <- merge(m, lr[, c("school", "type", "espn_id")], by = "school", all.x = TRUE, sort = FALSE)
d <- d[order(d$school, d$alternate, method = "radix"), c("alternate", "school", "type", "espn_id")]

# a binary connection, so Windows writes LF too (the repo keeps every text file LF; tests/test_repo_files.py)
lf <- function(path, lines) {
  con <- file(path, open = "wb")
  on.exit(close(con))
  writeLines(enc2utf8(lines), con, useBytes = TRUE)
}
lf(file.path("data-raw", "cfbplotr_names.csv"), capture.output(write.csv(d, row.names = FALSE, na = "")))
message("data-raw/cfbplotr_names.csv: ", nrow(d), " rows")
commit <- system2("git", c("-C", shQuote(src), "rev-parse", "HEAD"), stdout = TRUE)
dirty <- length(system2("git", c("-C", shQuote(src), "status", "--porcelain", "--", "data"), stdout = TRUE)) > 0
lf(file.path("data-raw", "cfbplotr_commit.txt"), c(
  "cfbplotR commit data-raw/cfbplotr_names.csv (its data/team_name_mapping.rda and data/logo_ref.rda) was exported from",
  "(tools/export_cfbplotr.R):",
  paste0(commit, if (dirty) " (with uncommitted changes)" else "")
))
