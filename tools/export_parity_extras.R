# Export the R oracle for sdvplot's parity extras, computed on the committed real shot rows
# (tests/fixtures/nba_shotchartdetail_2023.csv):
#   tests/fixtures/sdvplotr_court_coords.csv  sdvplotR's sdv_court_coords() output (court_x, court_y) per row
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
