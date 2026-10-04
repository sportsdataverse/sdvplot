<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [great_tables and reactable parity with sdvplotR](#great_tables-and-reactable-parity-with-sdvplotr)
  - [Wave A: marks and team identity](#wave-a-marks-and-team-identity)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# great_tables and reactable parity with sdvplotR

How each of sdvplotR's `gt_*` and `reactable_sdv_*` functions maps to `sdvplot.great_tables` and `sdvplot.reactable`.
A contributor reference, not a docs-site page. A function counts as ported only when its row says so. Each table wave
adds its own section.

Rules for every wave: the Python function keeps the R name. R argument names that mean a core concept take the
core's keyword: `sport` becomes `league`, `id_type` becomes `id_system`, and the image `type` becomes `mark_type`
(the color `type` becomes `which`). Image heights are pixels. Tests assert on the rendered HTML/CSS, not on R's
HTML bytes.

## Wave A: marks and team identity

| R function | gt feature | great_tables equivalent | decision |
| --- | --- | --- | --- |
| `gt_sdv_logos` | `text_transform(cells_body())` building `<img>` per cell | `GT.text_transform(loc.body(columns))`. Values are resolved when the function is called, from one render of the cell text (public API), and looked up at render | ported. Unknown values keep their text and warn once, when called. great_tables passes escaped text (`A&amp;M`), so it is unescaped before resolving, as in R |
| `gt_sdv_wordmarks` | same | same | ported. Adds `season=` (R has none) |
| `gt_sdv_headshots` | `text_transform()` + `web_image()` | same as logos | ported. `id_system="espn"` by default for every league (R reads NFL ids as GSIS by default) |
| `gt_sdv_cols_label` | `cols_label_with(fn)` returning `html()` | `cols_label_with()` reads the selection; `cols_label(cases={col: html(...)})` sets the images (great_tables escapes a text transform's output in labels) | ported. The column *names* are resolved, not labels set earlier. Columns that do not resolve keep their labels and warn |
| `gt_merge_stack_team_color` | `fmt()` per data row, `cols_hide()` | `GT.fmt(fn, columns, rows=[i])` per data row, `cols_hide()`; rows read from `GT._tbl_data` (pinned by a test) | ported. Column arguments are strings (R takes bare names). The bottom line is in the team color, as in R |
| `gt_theme_sdv` | `opt_table_font(google_font())`, `tab_style(cell_text())`, `tab_options()`, `opt_css()`, `.theme_scale_output()` | `opt_table_font(font=google_font("Lato"))`, `tab_style(style.text())`, `tab_options()`, `opt_css()` scoped to the table id (`with_id()`) | ported. Spanners are styled by CSS (`.gt_column_spanner`), because great_tables 1.0's `loc.spanner_labels()` needs explicit ids. great_tables 1.0 has no footnotes border or padding option. `density` scales the theme's own sizes and great_tables' default paddings; R also rescales px sizes set before the theme |
| `gt_theme_sdv_team` | same; colors from `sdv_team_colors()` | same; colors from `team_colors()`, ink and blending from `sdvplot._contrast` | ported. `league=` is required (R defaults `sport = "nfl"`). An unknown team raises `UnresolvedTeamError` |
| `reactable_sdv_logos` | `colDef(cell = function(value, index))` | `reactable.Column(cell=fn(CellInfo), html=True)` | ported. Returns the `Column` (R returns the cell function); `id=` and other `Column` arguments are keywords. Adds `season=` and `include_name=`. `variant` takes sdvplot's variants (`"default"`, `"dark"`, named) |
| `reactable_sdv_wordmarks` | same | same | ported, as logos |
| `reactable_sdv_headshots` | same | same | ported. `id_system=` for `id_type=`; height 40 px as in R |
| `reactable_sdv_cols_label` | a named list of `colDef(header = "<img>")` | `list[Column(id=name, name="", header="<img>", html=True)]` | ported. Column names that do not resolve are left out with one warning (R drops them silently) |
| `reactable_sdv_team_color_bar` | `colDef(style = function(value, index, name))` returning CSS text | `Column(style=fn(CellInfo) -> dict)` | ported. `which=` for `type=`; `na_color` defaults to `#b3b3b3` (R's `grey70`) |
| `reactable_sdv_team_color_bg` | same, with `scales::alpha()` | same; the fill is `#rrggbbaa` | ported. `na_color` must be a hex color |
