<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [great_tables and reactable parity with sdvplotR](#great_tables-and-reactable-parity-with-sdvplotr)
  - [Wave A: marks and team identity](#wave-a-marks-and-team-identity)
  - [Wave B: table themes](#wave-b-table-themes)

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

## Wave B: table themes

| R function | gt feature | great_tables equivalent | decision |
| --- | --- | --- | --- |
| `gt_theme_almanac` | `opt_row_striping()`, `row.striping.background_color`, `stripe = NA` | `opt_row_striping()`, `row_striping_background_color`, `stripe=None` | ported |
| `gt_theme_athletic` | `cells_body(columns = c(-names(data)[1]))`, dotted `cell_borders()`, `cols_align()` | `loc.body(columns=<all but the first data column>)`, `style.borders(style="dotted")`, `cols_align()` | ported |
| `gt_theme_booktabs` | three rules (`column_labels.border.top`, `.bottom`, `table_body.border.bottom`) | the same `tab_options` | ported |
| `gt_theme_broadsheet` | `.gt_row_group_first td` padding in `opt_css()` | great_tables has no `gt_row_group_first` class: `.gt_group_heading_row + tr td` | table_additional_css (equivalent selector); ported |
| `gt_theme_broadsheet` | `paper` = `"white"`, `"salmon"` or any color | the presets, or a hex color (anything else raises `ValueError`) | ported (stricter) |
| `gt_theme_brutalist` | four 3px table borders, black `column_labels.background.color` | the same `tab_options` | ported |
| `gt_theme_drench` | `gt::adjust_luminance()` | `_adjust_luminance()`, a port of grDevices' Luv / `hcl()` math (R's D65 white 0.3137, 0.3291); 426 of 432 sampled colors match R exactly, the other 6 are pure white, where R returns NA and the port white | ported |
| `gt_theme_drench` | `.theme_on_color()`, `.theme_secondary_on()` | `_contrast.on_color()`, `_secondary_on()` (lowercase hex) | ported |
| `gt_theme_gtutils` | `cells_body(rows = 1:(nrow(data) - 1))` row rules | `loc.body(rows=range(n - 1))`; a one-row table gets no rule (R's `1:0` ruled its only row) | ported (R's one-row rule not ported) |
| `gt_theme_kenpom` | `cells_body(rows = seq(1, n, 2))` / `seq(2, n, 2)` banding | `loc.body(rows=range(0, n, 2))` / `range(1, n, 2)`; R errors on a one-row table, the port bands it | ported |
| `gt_theme_kenpom` | hidden `tab_spanner("toss_out_spanner_dev")` + `#toss_out_spanner_dev {display: none;}` | great_tables gives a stacked spanner no element id, so the label is `<span class="sdvplot-hidden-spanner">` and the CSS is `th:has(.sdvplot-hidden-spanner)`; a second application reuses the spanner | html + table_additional_css; ported |
| `gt_theme_midnight` | dark ground on every part (`heading`, `column_labels`, `row_group`, `stub`, `source_notes` backgrounds) | the same `tab_options` | ported |
| `pal_midnight` | an exported character vector of five hex colors (a rank palette for dark grounds) | a tuple of the same five hex strings, exported from `sdvplot.great_tables` beside `gt_theme_midnight` | ported |
| `gt_theme_ncaa` | hidden spanner (as kenpom), `opt_row_striping()`, `.gt_row` padding | as kenpom; `opt_row_striping()`; `opt_css()` | ported |
| `gt_theme_pl` | `cells_body(rows = 1)` top rule, row rules (as gtutils) | `loc.body(rows=[0])`, skipped on an empty table | ported |
| `gt_theme_savant` | `opt_row_striping()`, centered heading | the same | ported |
| `gt_theme_scoreboard` | `.theme_on_color(accent)` for the labels | `_contrast.on_color()` | ported |
| `gt_theme_sofa` | `style`: `"light"` or anything else (dark) | `"light"` or `"dark"`, else `ValueError` | ported (stricter) |
| `gt_theme_swiss` | padding as the separator, one accent rule | the same `tab_options` | ported |
| `gt_theme_terminal` | monospaced readout, rule on every row | the same `tab_options` | ported |
| `gt_theme_tier` | `style`: `"dark"` or anything else (light); row rules (as gtutils) | `"light"` or `"dark"`, else `ValueError`; as gtutils | ported (stricter) |
| `gt_theme_tufte` | one hairline, italic labels | the same `tab_options` and `style.text(style="italic")` | ported |
| `gt_theme_preview` | lays the panels out with `gt_grid()` (`ncol`, `file`, `...`) and returns the grid | returns `dict[str, GT]` keyed by theme name; `ncol`, `file` and `...` not ported (layout is wave D's `gt_grid`); `gt_theme_sdv_team` is shown with `league="nfl"` and no team, as R shows it | ported (dict instead of a grid) |
| all 18 themes | `opt_table_font(font = list(google_font(x), default_fonts()))` | `opt_table_font(font=<gt 1.3.0's default_fonts()>)` then `opt_table_font(font=google_font(x))`; the import asks for every weight (great_tables' own import loads only 400, so 600/700 would be synthesized) | ported |
| all 18 themes | `cell_text(weight = 650)` | `style.text(weight=650)` (renders; great_tables types `weight` as keywords) | ported |
| all 18 themes | `cells_column_spanners()` | `loc.spanner_labels(ids=<every spanner id>)` (great_tables raises without ids); skipped on a table without spanners | ported |
| all 18 themes | `tab_options(footnotes.border.bottom.style = "none")` | no such option; great_tables' `.gt_footnotes` is already `border-bottom-style: none` | dropped (no-op) |
| all 18 themes | `.theme_scale_output()` (density rescales a finished table: `_styles` text sizes and the size/padding options, gt's defaults included) | `_scale_output()` walks `GT._styles` and `GT._options` the same way; sizes match R on athletic, gtutils, kenpom, ncaa, pl, savant, sofa, tier at "compact" and "social" | ported |
| all 18 themes | `.table_id()` (reads or sets `table_id`) | `GT._options.table_id`, else `GT.with_id(random_id())` | ported |
| all 18 themes | colors are passed to CSS unchecked | `hex6()`: a non-hex color raises `ValueError` naming the argument | ported (stricter) |
| all 18 themes | `...` to `tab_options()`, last | `**options` to `tab_options()`, last (great_tables' snake_case names) | ported |
