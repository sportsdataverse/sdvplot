# Export the R oracle for sdvplot's parity extras, computed on the committed real shot rows
# (tests/fixtures/nba_shotchartdetail_2023.csv):
#   tests/fixtures/sdvplotr_court_coords.csv  sdvplotR's sdv_court_coords() output (court_x, court_y) per row
#   tests/fixtures/sdvplotr_court_coords_euroleague.csv  the same with provider = "euroleague" on the real Euroleague
#                                             shot rows (tests/fixtures/euroleague_points_E2025_1.csv; -1,-1 -> NA)
#   tests/fixtures/sdvplotr_pitch_coords.csv  sdvplotR's sdv_pitch_coords() output on a landmark grid of every provider
#   tests/fixtures/ggpath_ref_lines.csv       ggpath's geom_mean_lines() / geom_median_lines() per facet panel
# Needs ggplot2 and ggpath. From the sdvplot root, with the sdvplotR checkout's path as the argument:
#   R_ENVIRON_USER=/dev/null Rscript tools/export_parity_extras.R [/path/to/sdvplotR]
suppressPackageStartupMessages({
  library(ggplot2)
  library(ggpath)
})
pdf(NULL)  # ggplotGrob() below needs a device: draw to none rather than Rplots.pdf
args <- commandArgs(trailingOnly = TRUE)
src <- if (length(args)) args[[1]] else file.path("..", "sdvplotR")
fixtures <- file.path("tests", "fixtures")
shots <- read.csv(file.path(fixtures, "nba_shotchartdetail_2023.csv"), colClasses = c(game_id = "character"),
                  encoding = "UTF-8")
write <- function(d, name) {  # doubles at 17 significant digits, so they read back bit for bit
  path <- file.path(fixtures, name)
  num <- vapply(d, is.double, TRUE)
  d[num] <- lapply(d[num], sprintf, fmt = "%.17g")
  con <- file(path, "wb")  # binary: LF line endings on Windows too (the repo's text files are LF)
  on.exit(close(con))
  write.csv(d, con, row.names = FALSE, na = "", quote = which(!num))
  message(path, ": ", nrow(d), " rows")
}

e <- new.env()
sys.source(file.path(src, "R", "court_coords.R"), envir = e)
cc <- e$sdv_court_coords(shots, "loc_x", "loc_y")
write(cc[c("game_id", "game_event_id", "court_x", "court_y")], "sdvplotr_court_coords.csv")
euro <- read.csv(file.path(fixtures, "euroleague_points_E2025_1.csv"), encoding = "UTF-8")
ec <- e$sdv_court_coords(euro, "coord_x", "coord_y", provider = "euroleague")
write(ec[c("num_anot", "coord_x", "coord_y", "court_x", "court_y")], "sdvplotr_court_coords_euroleague.csv")

# sdvplotR's sdv_pitch_coords() on landmarks, midpoints and 5%-off-pitch points of every provider, alternate rows
# flipped. Sourced like sdv_court_coords() above, so this needs no installed sdvplotR: its system.file() is pointed
# at the checkout's inst/.
pc <- new.env()
pc$system.file <- function(..., package, mustWork = FALSE) file.path(src, "inst", ...)
for (f in c("court_coords.R", "pitch_coords.R")) sys.source(file.path(src, "R", f), envir = pc)
pitch_grid <- function(marks) {
  mid <- function(v) { v <- sort(v); (head(v, -1) + tail(v, -1)) / 2 }
  pad <- function(v) c(min(v) - diff(range(v)) / 20, max(v) + diff(range(v)) / 20)
  g <- expand.grid(x = sort(unique(c(marks$x, mid(marks$x), pad(marks$x)))),
                   y = sort(unique(c(marks$y, mid(marks$y), pad(marks$y)))))
  g$flip <- seq_len(nrow(g)) %% 2 == 0
  g
}
cases <- c(
  lapply(c("opta", "wyscout", "statsbomb", "uefa", "impect"), function(p) list(p, pc$pitch_landmarks(p), NULL, NULL)),
  list(list("espn", list(x = c(0, 0.05, 0.115, 0.23, 0.34, 0.5, 1), y = c(0, 0.106, 0.316, 0.452, 0.5, 0.548, 0.684,
                                                                         0.894, 1)), NULL, NULL)),
  lapply(list(c("tracab", 105, 68), c("tracab", 100, 64), c("skillcorner", 105, 68), c("secondspectrum", 100, 64),
              c("metrica", 105, 68)), function(a) {
    len <- as.numeric(a[[2]]); wid <- as.numeric(a[[3]])
    list(a[[1]], pc$physical_landmarks(a[[1]], len, wid), len, wid)
  })
)
pitch <- do.call(rbind, lapply(cases, function(k) {
  g <- pitch_grid(k[[2]])
  out <- pc$sdv_pitch_coords(g, k[[1]], x_column = "x", y_column = "y", flip = "flip",
                             pitch_length = k[[3]], pitch_width = k[[4]])
  data.frame(provider = k[[1]], x = g$x, y = g$y, flip = tolower(g$flip),
             pitch_length = k[[3]] %||% NA_real_, pitch_width = k[[4]] %||% NA_real_,
             pitch_x = out$pitch_x, pitch_y = out$pitch_y)
}))
write(pitch, "sdvplotr_pitch_coords.csv")

# ggpath's own GeomRefLines draw_panel, recording each panel's reference value and checking it against the line
# ggpath actually drew (the segment grob's npc position mapped back through the panel's range).
from_npc <- function(u, range) range[1] + as.numeric(u) * diff(range)
recorder <- function(env) {
  ggproto("RecordRefLines", ggpath:::GeomRefLines,
    draw_panel = function(self, data, panel_params, coord, ref_function, na.rm = FALSE) {
      grob <- ggproto_parent(ggpath:::GeomRefLines, self)$draw_panel(data, panel_params, coord, ref_function, na.rm)
      x <- ref_function(data$x0, na.rm = na.rm)
      y <- ref_function(data$y0, na.rm = na.rm)
      h <- grob[[1]]  # gList(hline, vline): one segments grob each
      v <- grob[[2]]
      stopifnot(isTRUE(all.equal(unique(from_npc(v$x0, panel_params$x$continuous_range)), x)))
      stopifnot(isTRUE(all.equal(unique(from_npc(h$y0, panel_params$y$continuous_range)), y)))
      env$rows <- rbind(env$rows, data.frame(PANEL = data$PANEL[1], x0 = x, y0 = y))
      grob
    })
}
lines <- do.call(rbind, lapply(c("mean", "median"), function(ref) {
  env <- new.env()
  fun <- if (ref == "mean") base::mean else stats::median
  p <- ggplot(shots, aes(loc_x, loc_y, x0 = loc_x, y0 = loc_y)) + geom_point() + facet_wrap(~shot_zone_basic) +
    layer(geom = recorder(env), stat = "identity", position = "identity", params = list(ref_function = fun))
  invisible(ggplotGrob(p))
  layout <- ggplot_build(p)$layout$layout
  out <- merge(env$rows, layout[c("PANEL", "shot_zone_basic")], by = "PANEL")
  data.frame(shot_zone_basic = out$shot_zone_basic, ref = ref, x0 = out$x0, y0 = out$y0)
}))
write(lines[order(lines$ref, lines$shot_zone_basic, method = "radix"), ], "ggpath_ref_lines.csv")
message("ggplot2 ", packageVersion("ggplot2"), ", ggpath ", packageVersion("ggpath"), ", sdvplotR ",
        system2("git", c("-C", src, "rev-parse", "--short", "HEAD"), stdout = TRUE))
