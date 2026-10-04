<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [great_tables and reactable parity with sdvplotR](#great_tables-and-reactable-parity-with-sdvplotr)
  - [Wave A: marks and team identity](#wave-a-marks-and-team-identity)
  - [Wave C1: cell styling and formatting](#wave-c1-cell-styling-and-formatting)

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

## Wave C1: cell styling and formatting

All 17 functions are ported, in `sdvplot.great_tables` (`_cells.py`). Throughout the wave: the table argument is
`gt`; rows are great_tables row selections (0-based positions, a polars expression, or a callable for pandas data)
instead of R's data-masked expressions and 1-based indices; positions in other arguments are 0-based; palettes are
lists of hex colors (paletteer's `"pkg::palette"` strings are not supported); warnings are `SdvplotWarning`; and a
table that is not a `GT` raises `TypeError`.

| R function | gt feature | great_tables equivalent | decision |
| --- | --- | --- | --- |
| `gt_538_caption` | `tab_footnote()` on the column labels, `opt_css()` on `.gt_footnote` and `.gt_sourcenote` | great_tables renders source notes above footnotes | approximated: both captions are source notes, the rule and size inline on the top one (the rule spans the cell's content, inside its 5px padding); R's unused `...` dropped |
| `gt_bold_rows` | `tab_style(cells_body(rows = <expr>))` | `tab_style(loc.body(rows=))` | ported; the deprecated `row` and `filter_statement` arguments are not ported |
| `gt_border_bars_bottom` | `tab_source_note(html())`, `opt_css()`, `google_font()` | the same | ported; no Google Fonts import when the source notes have no font (R imports a family named `inherit`) |
| `gt_border_bars_top` | `tab_caption()` | none (`tab_header(preheader=)` is stored, never rendered) | approximated: the bars open the heading, inside the table's top border, with the existing title re-wrapped under them; call it after `tab_header` |
| `gt_border_grid` | `gtExtras::gt_add_divider(columns = -last_col())`, `opt_css()` | `tab_style(style.borders(sides="right"), loc.body / loc.column_labels)` | ported; "every column but the last" counts visible body columns (R: data columns, so a stub or hidden last column shifted it) |
| `gt_color_pills` | `scales::col_numeric()` (CIELAB), `text_transform()` through `.fmt_rows()`, `...` to `col_numeric` | `_contrast.mix` sRGB ramp, `fmt()` per distinct HTML string | approximated colors (sRGB, as great_tables' `data_color`; scales interpolates in CIELAB); `...` not ported; out-of-domain values grey `#808080` with one warning (scales' NA color); records `_sdvplot_scale` |
| `gt_color_ranks` | `data_color(rows =)`, paletteer | `data_color(rows=)` | ported; hex palettes only; records `_sdvplot_scale` |
| `gt_color_results` | `tab_style()` per result | the same | ported; `result_type` is validated; `"binary"` compares numbers (R also matches the strings `"1"`/`"0"`) |
| `gt_column_subheaders` | `cols_label(html())` per column, `...` of lists | one `cols_label(cases=)` | ported; per-column `**subheaders` dicts; a name that is not a column raises (R ignores it); the deprecated `gt_table` argument is not ported |
| `gt_cutline` | `tab_style(cell_borders())`, `opt_css()` with an inline SVG label | `tab_style(style.borders())`, `opt_css()` | ported; the SVG label is byte-identical to R's |
| `gt_delta` | `cols_add()`, `vec_fmt_number()` / `vec_fmt_percent()` | no `cols_add` in great_tables 1.0; `vals.fmt_number` / `vals.fmt_percent` | implemented through GT internals (`_tbl_data`, `_body`, `_boxhead`; pinned by a test); `from` is `from_` (a Python keyword); `after` positions are 0-based |
| `gt_fmt_rank` | `text_transform()` | `text_transform()` | ported |
| `gt_fmt_tally` | `.fmt_rows()` (`fmt()` with a vectorized constant), `cols_hide()`, `vec_fmt_percent()` | `fmt()` per distinct string, `cols_hide()`, `vals.fmt_percent` | ported; `share_of` is 0-based (default `0`, R's `1`) |
| `gt_group_stripes` | `_row_groups`, `_stub_df` | `GT._stub.group_rows` (render order) | ported |
| `gt_highlight_cells` | an rlang formula or function per column, or a logical matrix | a callable on each column's pandas/polars Series, or a DataFrame or 2-D sequence mask | ported |
| `gt_highlight_na` | `tab_style()` + `text_transform()` for `missing_text` | `tab_style()` + `fmt()` (`text_transform` skips null cells) | ported; `columns=None` means every column (R: `everything()`) |
| `gt_indicator_boxes` | `text_transform()` with a vectorized rule over the rendered text | `fmt()` per data value; the rule is called per value (and column name) | approximated: a rule that needs the whole column (`x > mean(x)`) must be computed beforehand; `show_only` is validated |
