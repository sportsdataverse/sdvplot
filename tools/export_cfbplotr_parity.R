# Export the R oracle for sdvplot's ports of the cfbplotR-era sdvplotR functions: sdv_teams(division =),
# sdv_aliases(), sdv_clean_names(), sdv_team_factor(), the scales' alt_colors and sdv_add_athlete_id(). Writes, under
# tests/fixtures/:
#   sdvplotr_cfbplotr_meta.csv     the sdvplotR commit and the index version the answers come from
#   sdvplotr_divisions.csv         sdv_teams(league, division = d)$team_id for every division of every college league
#   sdvplotr_aliases_digest.csv    per league: sdv_aliases(league)'s rows and an md5 of them, sorted and tab-joined
#   sdvplotr_clean_names.csv       sdv_clean_names() on real alias values (and misses), every column, both keep modes
#   sdvplotr_team_factor.csv       sdv_team_factor(): each value (NA as "") and the factor's levels in order
#   sdvplotr_alt_colors.csv        the colour the scales give each value, with and without alt_colors
#   sdvplotr_athlete_ids.csv       sdv_add_athlete_id() on real player names, with the roster rows it read in
#   sdvplotr_athlete_rosters.csv   (every roster row whose name is one of the inputs: the match needs no other row)
# The index answers come from sdvplotR's bundled snapshot (options(sdvplotR.offline = TRUE)), the index sdvplot
# bundles at the same version; the rosters are read over the network (cfbfastR-data). From the sdvplot root:
#   R_ENVIRON_USER=/dev/null Rscript tools/export_cfbplotr_parity.R [/path/to/sdvplotR]
args <- commandArgs(trailingOnly = TRUE)
src <- if (length(args)) args[[1]] else file.path("..", "sdvplotR")
fixtures <- file.path("tests", "fixtures")
options(sdvplotR.offline = TRUE, warn = 1)
suppressMessages(pkgload::load_all(src, export_all = TRUE, quiet = TRUE))

write <- function(d, name) {
  path <- file.path(fixtures, name)
  chr <- vapply(d, is.character, TRUE)
  d[chr] <- lapply(d[chr], enc2utf8)
  lines <- utils::capture.output(write.csv(d, row.names = FALSE, na = ""))
  con <- file(path, "wb") # bytes, not text: UTF-8 in any locale, LF line endings on Windows too
  on.exit(close(con))
  writeBin(charToRaw(enc2utf8(paste0(paste(lines, collapse = "
"), "
"))), con)
  message(path, ": ", nrow(d), " rows")
}

index_version <- sdv_versions()$index_version
# an exported tree (git archive) has no .git: name its commit in SDVPLOTR_COMMIT
commit <- Sys.getenv("SDVPLOTR_COMMIT", suppressWarnings(system2("git", c("-C", src, "rev-parse", "HEAD"), stdout = TRUE))[1])
write(data.frame(sdvplotr_commit = commit, index_version = index_version), "sdvplotr_cfbplotr_meta.csv")

# sdv_teams(division =): every division alone, and the cfbplotR pairs, in each college league
college <- c("cfb", "mbb", "wbb", "ncaa_baseball", "ncaa_softball", "ncaa_mhockey", "ncaa_whockey")
college <- intersect(college, sdv_leagues())
div_cases <- list()
for (lg in college) {
  divs <- c(if (lg == "cfb") c("FBS", "FCS", "DII", "DIII", "P4", "P5", "G5") else c("DI", "DII", "DIII"), "Conference")
  sets <- c(as.list(divs), if (lg == "cfb") list(c("P4", "FCS"), c("G5", "DII")) else list(c("DI", "DII")))
  for (d in sets) {
    # an index with no divisions for the league is an error: written as "<error>", which Python must raise for too
    ids <- tryCatch(suppressWarnings(sdv_teams(lg, division = d)$team_id), error = function(e) "<error>")
    div_cases[[length(div_cases) + 1L]] <- data.frame(
      league = lg, division = paste(d, collapse = "+"), team_id = if (length(ids)) ids else NA_character_
    )
  }
}
write(do.call(rbind, div_cases), "sdvplotr_divisions.csv")

# sdv_aliases(): per league, the rows sorted (C locale) and tab-joined, NA as "", md5 of the UTF-8 bytes
a <- sdv_aliases()
digest <- do.call(rbind, lapply(sort(unique(a$league), method = "radix"), function(lg) {
  x <- a[a$league == lg, , drop = FALSE]
  cells <- lapply(x, function(v) ifelse(is.na(v), "", as.character(v)))
  lines <- sort(do.call(paste, c(cells, sep = "\t")), method = "radix")
  f <- tempfile()
  con <- file(f, "wb")
  writeBin(charToRaw(enc2utf8(paste(lines, collapse = "\n"))), con)
  close(con)
  data.frame(league = lg, rows = nrow(x), md5 = unname(tools::md5sum(f)))
}))
write(digest, "sdvplotr_aliases_digest.csv")

# sdv_clean_names(): 30 real alias values per id system (resolve's own systems) in four leagues, plus misses
set.seed(20261125)
clean_in <- do.call(rbind, lapply(c("cfb", "nfl", "mbb", "nba"), function(lg) {
  x <- a[a$league == lg & a$id_system %in% resolve_priority, , drop = FALSE]
  pick <- unlist(lapply(split(seq_len(nrow(x)), x$id_system), function(i) i[sample.int(length(i), min(30L, length(i)))]))
  data.frame(league = lg, value = c(x$value[sort(pick)], "Miami", "not a team", "  utah  ", "SAN JOSÉ STATE", "12.0"))
}))
clean_in <- clean_in[!duplicated(clean_in), , drop = FALSE]
clean_out <- do.call(rbind, lapply(c("location", "short_name", "name", "abbr", "team_id"), function(col) {
  do.call(rbind, lapply(split(clean_in, clean_in$league), function(d) {
    lg <- d$league[1]
    data.frame(
      league = lg, value = d$value, numeric = FALSE, column = col,
      keep = sdv_clean_names(d$value, lg, column = col),
      drop = suppressWarnings(sdv_clean_names(d$value, lg, keep_non_matches = FALSE, column = col))
    )
  }))
}))
# numbers in: ids that went through a float, a miss, a fraction and NA (kept as id_chr() writes them)
num <- c(13, 12, 4000000, 1.5, NA)
clean_num <- data.frame(
  league = "nfl", value = format(num, scientific = FALSE, drop0trailing = TRUE, trim = TRUE), numeric = TRUE,
  column = "abbr", keep = sdv_clean_names(num, "nfl", column = "abbr"),
  drop = suppressWarnings(sdv_clean_names(num, "nfl", keep_non_matches = FALSE, column = "abbr"))
)
clean_num$value[is.na(num)] <- NA
write(rbind(clean_out, clean_num), "sdvplotr_clean_names.csv")

# sdv_team_factor()
factor_cases <- list(
  list("nfl", c("KC", "BUF", "invalid", "Kansas City Chiefs", "SF", "KC", NA)),
  list("cfb", c("Utah", "Alabama", "Georgia", "Ohio State", "Miami", "Texas A&M", "BYU")),
  list("nba", c("LAL", "BOS", "Golden State Warriors", "1610612747", "nope")),
  list("nba", c(1610612747, 1610612738, 1610612747, 99)) # numbers in: the factor's values are id_chr() text
)
team_factor <- do.call(rbind, lapply(seq_along(factor_cases), function(k) {
  lg <- factor_cases[[k]][[1]]
  v <- factor_cases[[k]][[2]]
  f <- suppressWarnings(sdv_team_factor(v, lg))
  rbind(
    data.frame(case = k, league = lg, kind = if (is.numeric(v)) "number" else "input", pos = seq_along(v), value = id_chr(v)),
    data.frame(case = k, league = lg, kind = "value", pos = seq_along(v), value = as.character(f)),
    data.frame(case = k, league = lg, kind = "level", pos = seq_along(levels(f)), value = levels(f))
  )
}))
write(team_factor, "sdvplotr_team_factor.csv")

# alt_colors: the colour get_team_colors() (every scale_*_sdv) gives each value
alt_cases <- list(
  list("cfb", c("Alabama", "Utah", "Georgia", "Oregon", "Florida State", "BYU", "Ohio State"), c("Alabama", "Utah")),
  list("nfl", c("KC", "BUF", "SF", "Green Bay Packers", "LV", "DAL"), c("KC", "Green Bay Packers")),
  list("mbb", c("Duke", "UNC", "Kentucky", "Kansas"), "Duke")
)
alt <- do.call(rbind, lapply(seq_along(alt_cases), function(k) {
  lg <- alt_cases[[k]][[1]]
  v <- alt_cases[[k]][[2]]
  alts <- alt_cases[[k]][[3]]
  do.call(rbind, lapply(c("primary", "secondary"), function(w) {
    plain <- get_team_colors(lg, w)
    swapped <- get_team_colors(lg, w, alt_colors = alts)
    data.frame(
      case = k, league = lg, which = w, alt_colors = paste(alts, collapse = "|"), value = v,
      color = unname(plain[v]), alt_color = unname(swapped[v])
    )
  }))
}))
write(alt, "sdvplotr_alt_colors.csv")

# sdv_add_athlete_id(): the rosters need the network, the index stays the bundled one (loaded above)
invisible(sdv_teams())
options(sdvplotR.offline = FALSE)
stopifnot(identical(sdv_versions()$index_version, index_version))
players <- data.frame(
  player_name = c(
    "Britain Covey", "JT Daniels", "Bryce Young", "Caleb Williams", "C.J. Stroud", "Michael Penix Jr.",
    "Bo Nix", "Jayden Daniels", "Michael Smith", "Chris Johnson", "Josh Allen", "Nobody Atall", NA, "  bryce YOUNG "
  ),
  team = c(
    "Utah", "Georgia", "Alabama", "USC", "Ohio State", "Washington", "Oregon", "LSU", NA, "", "Wyoming",
    "Utah", "Utah", "ALA"
  ),
  season = c(2021, 2021, 2022, 2023, 2022, 2023, 2023, 2023, 2021, 2021, 2017, 2021, 2021, 2022)
)
withTeam <- sdv_add_athlete_id(players, player_name, team, season, headshot_urls = TRUE)
nameOnly <- suppressWarnings(sdv_add_athlete_id(players["player_name"], player_name))
withSeason <- suppressWarnings(sdv_add_athlete_id(players[c("player_name", "season")], player_name))
latest <- latest_roster_season()
write(data.frame(
  players,
  athlete_id = withTeam$athlete_id, headshot_url = withTeam$headshot_url,
  athlete_id_name_only = nameOnly$athlete_id, athlete_id_name_season = withSeason$athlete_id,
  latest_season = latest
), "sdvplotr_athlete_ids.csv")
# the raw roster rows (the files' own columns), so Python reads them as it reads a downloaded roster
seasons <- sort(unique(c(players$season, latest)))
keys <- norm_value(players$player_name)
ro <- do.call(rbind, lapply(seasons, function(s) {
  r <- as.data.frame(read_rds_url(roster_url("cfb", s)))[c("athlete_id", "first_name", "last_name", "team", "headshot_url")]
  r <- r[norm_value(paste(r$first_name, r$last_name)) %in% keys, , drop = FALSE]
  cbind(season = rep(as.integer(s), nrow(r)), r)
}))
write(ro, "sdvplotr_athlete_rosters.csv")
