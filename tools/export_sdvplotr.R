# Export sdvplotR's team matching for sdvplot (Ruling R43): its clean_team_abbrs() table (abbr_mapping) and
# resolve_historical_abbr() table (historical_team_mappings) become data-raw/sdvplotr_*.csv, which
# tools/build_index.py turns into `sdvplotr` alias rows, and its conference and league rows (sdvplotr_conferences.csv); logo_history and logo_ref's team colours (with their
# color_source, sdvplotR #63) become the parity-test fixtures under tests/fixtures/sdvplotr_*.csv.
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
# a binary connection, so Windows writes LF too (the repo keeps every text file LF; tests/test_repo_files.py)
lf <- function(path, lines) {
  con <- file(path, open = "wb")
  on.exit(close(con))
  writeLines(enc2utf8(lines), con, useBytes = TRUE)
}
write <- function(d, path) {
  txt <- capture.output(write.csv(d, row.names = FALSE, na = ""))
  lf(path, txt)
  message(path, ": ", nrow(d), " rows")
}

# historical_team_mappings carries no season ranges: a key maps to the franchise's current abbreviation
write(long(e$abbr_mapping), file.path("data-raw", "sdvplotr_abbr_mapping.csv"))
write(long(e$historical_team_mappings), file.path("data-raw", "sdvplotr_historical.csv"))
lh <- e$logo_history
write(lh[order(lh$sport, lh$key, lh$season_from, lh$variant, method = "radix"), ],
      file.path("tests", "fixtures", "sdvplotr_logo_history.csv"))
# logo_ref's teams (not conferences) with both colours and where each came from (color_source)
lr <- e$logo_ref[e$logo_ref$type == "team", c("sport", "espn_team_id", "team_abbr", "color1", "color2", "color_source")]
write(lr[order(lr$sport, as.integer(lr$espn_team_id), method = "radix"), ],
      file.path("tests", "fixtures", "sdvplotr_team_colors.csv"))
# logo_ref's conference and league rows (type "conference" / "league": the college conferences, AFC, NFC and the NFL),
# which tools/build_index.py adds to the index as its opt-in conference rows (teams(include_conferences=True)). The
# key is team_abbr (R's espn_team_id is NA for them); logo URLs are kept so the marks the archive still lacks are listed
conf <- e$logo_ref[e$logo_ref$type != "team", c("sport", "team_abbr", "team_name", "team_short_name", "logo_url",
                                                "logo_dark_url", "color1", "color2", "color_source", "conference",
                                                "division", "type")]
write(conf[order(conf$sport, conf$team_abbr, method = "radix"), ], file.path("data-raw", "sdvplotr_conferences.csv"))

commit <- system2("git", c("-C", src, "rev-parse", "HEAD"), stdout = TRUE)
dirty <- length(system2("git", c("-C", src, "status", "--porcelain", "--", "R", "data-raw"), stdout = TRUE)) > 0
lf(file.path("data-raw", "sdvplotr_commit.txt"), c(
  "sdvplotR commit the data-raw/sdvplotr_*.csv snapshots and the tests/fixtures/sdvplotr_logo_history.csv and",
  "sdvplotr_team_colors.csv fixtures were exported from",
  "(tools/export_sdvplotr.R):",
  paste0(commit, if (dirty) " (with uncommitted changes)" else "")
))
