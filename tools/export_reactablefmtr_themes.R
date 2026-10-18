# Export reactablefmtr's 27 table themes to src/sdvplot/data/reactablefmtr_themes.json, which
# sdvplot.reactable.reactable_sdv_theme() reads. Each theme function is called with a sentinel "@<arg>@" for every
# argument but `centered`, so the JSON holds reactablefmtr's own values plus where each argument lands; the Python side
# swaps the sentinels for the caller's values or the R defaults (also exported). `centered = TRUE` only changes
# cellStyle (checked here), exported as centered_cell_style.
# Needs reactablefmtr (2.1.0) and jsonlite. From the sdvplot root:
#   R_ENVIRON_USER=/dev/null Rscript tools/export_reactablefmtr_themes.R
themes <- c("cerulean", "clean", "cosmo", "cyborg", "dark", "darkly", "default", "espn", "fivethirtyeight", "flatly",
            "hoverdark", "hoverlight", "journal", "lux", "midnight", "midnightblue", "minty", "no_lines", "nytimes",
            "pff", "sandstone", "sanfran", "slate", "spacelab", "sunrise", "superhero", "void")
# A style list that names a property twice (espn's groupHeaderStyle has two fontSize) reaches the browser as
# "fontSize" and "fontSize.1" (jsonlite renames the repeat, in reactable's widget JSON too), and the renamed one is not a
# CSS property, so only the first counts: keep the first, as the R table renders.
first_names <- function(x) {
  if (!is.list(x)) return(x)
  if (!is.null(names(x))) x <- x[!duplicated(names(x))]
  lapply(x, first_names)
}
out <- list()
for (t in themes) {
  f <- get(t, envir = asNamespace("reactablefmtr"))
  fm <- formals(f)
  params <- setdiff(names(fm), "centered")
  defaults <- setNames(lapply(params, function(p) { v <- eval(fm[[p]]); if (is.null(v)) NA else v }), params)
  sent <- setNames(lapply(params, function(p) paste0("@", p, "@")), params)
  a <- first_names(unclass(do.call(f, c(sent, list(centered = FALSE)))))
  b <- first_names(unclass(do.call(f, c(sent, list(centered = TRUE)))))
  differ <- union(setdiff(names(a), names(b)), setdiff(names(b), names(a)))
  for (k in intersect(names(a), names(b))) if (!identical(a[[k]], b[[k]])) differ <- c(differ, k)
  if (!all(differ %in% "cellStyle")) stop(t, ": centered = TRUE changes ", paste(differ, collapse = ", "))
  out[[t]] <- list(defaults = defaults, theme = a, centered_cell_style = b$cellStyle)
}
json <- jsonlite::toJSON(list(reactablefmtr = as.character(utils::packageVersion("reactablefmtr")), themes = out),
                         auto_unbox = TRUE, null = "null", na = "null", pretty = TRUE, digits = NA)
path <- file.path("src", "sdvplot", "data", "reactablefmtr_themes.json")
con <- file(path, "wb")  # binary: LF line endings on Windows too
writeLines(json, con)
close(con)
message(path, ": ", length(out), " themes")
