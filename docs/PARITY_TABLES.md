<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [great_tables and reactable parity with sdvplotR](#great_tables-and-reactable-parity-with-sdvplotr)
  - [Wave A: marks and team identity](#wave-a-marks-and-team-identity)
  - [Wave B: table themes](#wave-b-table-themes)
  - [Wave C1: cell styling and formatting](#wave-c1-cell-styling-and-formatting)
  - [Wave D: image export and composition](#wave-d-image-export-and-composition)
  - [Wave C2: legends, layout and annotation (`sdvplot.great_tables._layout`)](#wave-c2-legends-layout-and-annotation-sdvplotgreat_tables_layout)

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
| `gt_sdv_logos` | `text_transform(cells_body())` building `<img>` per cell | `GT.text_transform(loc.body(columns))`. Values are resolved when the function is called, from one render of the cell text (public API), and looked up at render | ported. Unknown values keep their text and warn once, when called. great_tables passes escaped text (`A&amp;M`), so it is unescaped before resolving, as in R. `locations` takes `loc.body()`, `loc.stub()` and `loc.row_groups()`; R also takes `cells_column_labels()`, but great_tables' `text_transform` escapes column labels, so any other location is a `ValueError` (column labels: `gt_sdv_cols_label`). The same holds for `gt_sdv_wordmarks` and `gt_sdv_headshots` |
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
| `gt_theme_preview` | lays the panels out with `gt_grid()` (`ncol`, `file`, `...`) and returns the grid | returns `dict[str, GT]` keyed by theme name; `ncol`, `file` and `...` not ported (layout is wave D's `gt_grid`); `gt_theme_sdv_team` is shown with `league="nfl"` and no team, as R shows it; `n` must be a positive whole number (R's `head(data, n)` takes any `n`: 0 shows no rows, -1 drops the last) | ported (dict instead of a grid; stricter `n`) |
| all 18 themes | `opt_table_font(font = list(google_font(x), default_fonts()))` | `opt_table_font(font=<gt 1.3.0's default_fonts()>)` then `opt_table_font(font=google_font(x))`; the import asks for every weight (great_tables' own import loads only 400, so 600/700 would be synthesized) | ported |
| all 18 themes | `cell_text(weight = 650)` | `style.text(weight=650)` (renders; great_tables types `weight` as keywords) | ported |
| all 18 themes | `cells_column_spanners()` | `loc.spanner_labels(ids=<every spanner id>)` (great_tables raises without ids); skipped on a table without spanners | ported |
| all 18 themes | `tab_options(footnotes.border.bottom.style = "none")` | no such option; great_tables' `.gt_footnotes` is already `border-bottom-style: none` | dropped (no-op) |
| all 18 themes | `.theme_scale_output()` (density rescales a finished table: `_styles` text sizes and the size/padding options, gt's defaults included) | `_scale_output()` walks `GT._styles` and `GT._options` the same way; sizes match R on athletic, gtutils, kenpom, ncaa, pl, savant, sofa, tier at "compact" and "social" | ported |
| all 18 themes | `.table_id()` (reads or sets `table_id`) | `GT._options.table_id`, else `GT.with_id(random_id())`; an empty id gets a random one too (R keeps `""`, which scopes nothing). Every wave shares this one helper (`_marks._table_id`) | ported (stricter) |
| all 18 themes | colors are passed to CSS unchecked | `hex6()`: a non-hex color raises `ValueError` naming the argument | ported (stricter) |
| all 18 themes | `...` to `tab_options()`, last | `**options` to `tab_options()`, last (great_tables' snake_case names) | ported |

## Wave C1: cell styling and formatting

All 17 functions are ported, in `sdvplot.great_tables` (`_cells.py`). Throughout the wave: the table argument is
`gt`; rows are great_tables row selections (0-based positions, a polars expression, or a callable for pandas data)
instead of R's data-masked expressions and 1-based indices; positions in other arguments are 0-based; palettes are
lists of hex colors (paletteer's `"pkg::palette"` strings are not supported); warnings are `SdvplotWarning`; and a
table that is not a `GT` raises `TypeError`.

| R function | gt feature | great_tables equivalent | decision |
| --- | --- | --- | --- |
| `gt_538_caption` | `tab_footnote()` on the column labels, `opt_css()` on `.gt_footnote` and `.gt_sourcenote` | great_tables renders source notes above footnotes | approximated: both captions are source notes, the rule and size inline on the top one (the rule spans the cell's content, inside its 5px padding); R's unused `...` dropped; `align` must be left, center or right (R pastes any string into CSS); the auto rule color skips `background-color` and `border-*-color` (R's `(?<=color:\s)` lookbehind also matches them) |
| `gt_bold_rows` | `tab_style(cells_body(rows = <expr>))` | `tab_style(loc.body(rows=))` | ported; the deprecated `row` and `filter_statement` arguments are not ported |
| `gt_border_bars_bottom` | `tab_source_note(html())`, `opt_css()`, `google_font()` | the same | ported; no Google Fonts import when the source notes have no font (R imports a family named `inherit`); `bar_align`, `img_align` and `text_align` are validated (R falls back to center, and pastes e.g. an invalid `padding-center`) |
| `gt_border_bars_top` | `tab_caption()` | none (`tab_header(preheader=)` is stored, never rendered) | approximated: the bars open the heading, inside the table's top border, with the existing title re-wrapped under them; call it after `tab_header`; the alignments are validated as in `gt_border_bars_bottom` |
| `gt_border_grid` | `gtExtras::gt_add_divider(columns = -last_col())`, `opt_css()` | `tab_style(style.borders(sides="right"), loc.body / loc.column_labels)` | ported; "every column but the last" counts visible body columns (R: data columns, so a stub or hidden last column shifted it) |
| `gt_color_pills` | `scales::col_numeric()` (CIELAB), `text_transform()` through `.fmt_rows()`, `...` to `col_numeric` | `_contrast.mix` sRGB ramp, `fmt()` per distinct HTML string | approximated colors (sRGB, as great_tables' `data_color`; scales interpolates in CIELAB); `...` not ported; out-of-domain values grey `#808080` with one warning (scales' NA color); records `_sdvplot_scale` |
| `gt_color_ranks` | `data_color(rows =)`, paletteer | `data_color(rows=)` | ported; hex palettes only; records `_sdvplot_scale` |
| `gt_color_results` | `tab_style()` per result | the same | ported; `result_type` is validated; `"binary"` compares numbers (R also matches the strings `"1"`/`"0"`) |
| `gt_column_subheaders` | `cols_label(html())` per column, `...` of lists | one `cols_label(cases=)` | ported; per-column `**subheaders` dicts; a name that is not a column raises (R ignores it); the deprecated `gt_table` argument is not ported; `font` is written as `&quot;<font>&quot;` (R's `'<font>'` ends the single-quoted style attribute early, so the font and anything after it are lost) |
| `gt_cutline` | `tab_style(cell_borders())`, `opt_css()` with an inline SVG label | `tab_style(style.borders())`, `opt_css()` | ported; the SVG label is byte-identical to R's; `style` must be dashed, solid or dotted; `after` must be whole numbers (numpy integers accepted; R has no whole-number check) |
| `gt_delta` | `cols_add()`, `vec_fmt_number()` / `vec_fmt_percent()` | no `cols_add` in great_tables 1.0; `vals.fmt_number` / `vals.fmt_percent` | implemented through GT internals (`_tbl_data`, `_body`, `_boxhead`; pinned by a test); `from` is `from_` (a Python keyword); `after` positions are 0-based |
| `gt_fmt_rank` | `text_transform()` | `text_transform()` | ported |
| `gt_fmt_tally` | `.fmt_rows()` (`fmt()` with a vectorized constant), `cols_hide()`, `vec_fmt_percent()` | `fmt()` per distinct string, `cols_hide()`, `vals.fmt_percent` | ported; `share_of` is 0-based (default `0`, R's `1`) |
| `gt_group_stripes` | `_row_groups`, `_stub_df` | `GT._stub.group_rows` (render order) | ported |
| `gt_highlight_cells` | an rlang formula or function per column, or a logical matrix | a callable on each column's pandas/polars Series, or a DataFrame or 2-D sequence mask | ported |
| `gt_highlight_na` | `tab_style()` + `text_transform()` for `missing_text` | `tab_style()` + `fmt()` (`text_transform` skips null cells) | ported; `columns=None` means every column (R: `everything()`) |
| `gt_indicator_boxes` | `text_transform()` with a vectorized rule over the rendered text | `fmt()` per data value; the rule is called per value (and column name) | approximated: a rule that needs the whole column (`x > mean(x)`) must be computed beforehand; `show_only` is validated |

## Wave D: image export and composition

| R function | gt feature | great_tables equivalent | decision |
| --- | --- | --- | --- |
| `gt_save_crop` | `gtExtras::gtsave_extra(zoom, expand)`; magick `image_trim`, `image_border`, `image_resize` | `GT.gtsave(zoom=, expand=)` (headless Chrome through nokap); Pillow ports of the magick steps, measured against ImageMagick 6.9 | ported. `file=None` returns a `PIL.Image` (R: the encoded bytes). JPEG is written at magick's quality 92. A one-color render comes back untrimmed (magick raises). |
| `gt_social_crop` | as `gt_save_crop`, plus `magick::image_extent(gravity=)` | a Pillow canvas with ImageMagick's gravity offsets (measured) | ported. A three-part ratio (`"1:2:3"`) or an infinite one raises (R reads the first two parts, or passes `Inf` on to magick). |
| `gt_save_batch` | a tidyselect `group`; `cli` progress messages; `gtsave_extra(zoom)`; magick | a column name; progress lines on stderr; `GT.gtsave`; Pillow | ported. `fn` gets the caller's frame type (pandas or polars, through narwhals). Two values that make the same file name raise before anything renders (R overwrites one). A browser that cannot start raises at the first group (R records it as a failure of every group). |
| `gt_grid` | an `htmltools` CSS grid; `webshot2::webshot(selector = "body")`; magick | a py-htmltools `Tag` (a great_tables dependency); `nokap.from_html` capturing the page wrapper; Pillow | ported. Returns an `htmltools.Tag` (R: `browsable()`); `tables` may be a dict (its values). A misspelled style key raises (R ignores it). A label font loads without a heading too (R drops the link). The capture is the `bg`-colored wrapper, so a non-white `bg` trims evenly (capturing the page body, as R does, leaves uneven `bg` padding: the even-trim render test fails with it). Deliberate divergence: a plain string in `title`, `subtitle`, `caption`, `source_note` or `labels` is escaped, as great_tables escapes text; `html()` and `md()` pass through as markup. R inserts plain strings as raw HTML (`htmltools::HTML(as.character(x))`), so `"Wins < 5"` loses its tail there. `gap` must be a non-negative number and `zoom` a positive one, and `labels` a non-empty text or list of text (R puts any `gap` into the CSS and hands any `zoom` to webshot). |
| `gt_stack_tables` | an `htmltools` flex column; `webshot2::webshot(selector = "body")`; magick | as `gt_grid` | ported, with `gt_grid`'s notes on the return value, dict input, style keys, the even trim, escaped plain strings and the `gap` / `zoom` checks. |

## Wave C2: legends, layout and annotation (`sdvplot.great_tables._layout`)

All 17 functions keep sdvplotR's names, argument names, order and defaults, with these rules for the whole wave:
`gt_object` is `gt`; an R style `list()` is a `dict` (default `None`), and an unknown style key raises `ValueError`
(R ignores it); `columns`/`rows` take anything great_tables accepts (names, lists, polars selectors; 0-based positions,
polars expressions, functions of a pandas frame) where R takes tidyselect and data-masked expressions with 1-based
indices; colors that feed contrast or ramps must be hex (`#rgb`, `#rrggbb`), where R also takes color names; R's
`cli` warnings are `SdvplotWarning`, its aborts `ValueError`/`TypeError`.

| R function | gt feature | great_tables equivalent | decision |
| --- | --- | --- | --- |
| `gt_legend_continuous` | `scales::col_numeric` ramp (CIELAB interpolation) | piecewise-linear sRGB ramp between evenly spaced stops, the same as `GT.data_color` | ported; segment colors match great_tables' `data_color` cells exactly and R's slightly (different color space) |
| `gt_legend_continuous` | `.recorded_scale()` R attribute; `missing()` for recorded arguments | `_sdvplot_scale` instance attribute on a `copy.copy` of the GT; arguments default to `None`, meaning "recorded, else R's default" | ported |
| `gt_legend_continuous` | paletteer `"pkg::palette"` strings, `pal_type` registry | none (no paletteer in Python) | not ported: palettes are lists of hex colors; `pal_type` is accepted and recorded only |
| `gt_legend_continuous` | `format(round(x, digits), big.mark = ",")` | `f"{x:,.{digits}f}"` | approximated: Python always prints `digits` decimals (R drops trailing zeros shared by every label) |
| `gt_legend_discrete` | `.recorded_key()`; named vector or data frame `key_info` | `_sdvplot_key` attribute; a `{label: color}` mapping or a pandas/polars frame (via narwhals) | ported |
| `gt_marginalia` | `cols_width()` formulas, `cell_text`, `cell_borders` | `cols_width(cases=)`, `style.text`, `style.borders` | ported |
| `gt_outliers` | `stats::quantile` (type 7), `stats::sd` | own type-7 quantile and sample standard deviation | ported |
| `gt_percentile_bar` | `gt::fmt(rows =, fns =)` one constant per row | `GT.fmt(fn, columns, rows)` with a value-to-HTML function bound per column (`functools.partial`) | ported |
| `gt_row_accent` | `cells_stub`/`cells_body` borders; `sort()` of the key levels | `loc.stub`/`loc.body` + `style.borders`; the stub found through the private `GT._boxhead` | ported; levels sort by code point (R's sort is locale-aware) |
| `gt_scale_note` | `fmt_number(scale_by =)`, labels from `_boxhead` | `fmt_number(scale_by=)`, labels from the private `GT._boxhead` | ported |
| `gt_set_font` | one `tab_style` over every `cells_*`; deprecated `gt_table` argument | one `tab_style` over `loc.title`, `loc.subtitle`, `loc.stubhead`, `loc.spanner_labels(ids=...)` (ids from the private `GT._spanners`), `loc.column_labels`, `loc.row_groups`, `loc.stub`, `loc.body`, `loc.footnotes`, `loc.source_notes` | ported; `gt_table` (deprecated in R) not ported |
| `gt_significance` | `text_transform` per distinct mark | `text_transform` per distinct mark, functions bound with `functools.partial` | ported |
| `gt_snake` | rebuild with `gt()`, copy `_heading`/`_source_notes`, edit the `_styles` tibble, `random_id()` | rebuild with `GT(..., id=)`, `GT._replace(_heading=, _source_notes=, _styles=)` with `StyleInfo` dataclass edits (private), own 10-letter id | ported; only the padding rows of the last block are blanked (R blanks every missing cell of the last block) |
| `gt_snake_align` | `as.data.frame(x)`, matrices accepted | pandas or polars frame in, the same kind out | ported; matrices not accepted |
| `gt_social_tag` | `fontawesome::fa()` icons | `faicons.icon_svg()` (a great_tables dependency) | ported; faicons 0.2.2 lacks `x-twitter`, `bluesky`, `threads` and `substack`: `x`/`twitter` fall back to the Twitter bird, the others raise naming the faicons version (as R does); `align` must be left, center or right (R pastes any string into CSS) |
| `gt_social_tag` | `gt_538_caption(..., ...)` for a caption | wave C1's `gt_538_caption(gt, top_caption=, bottom_caption=, **kwargs)` | ported |
| `gt_spotlight` | data-masked `rows` | great_tables row selection | ported; numpy integer positions count as positions here and in `gt_percentile_bar` / `gt_row_accent` (great_tables' own resolver silently skips them) |
| `gt_tiers` | `gt_theme_tier()`, `fmt_image()`, `sub_missing()`, `cols_label(everything() ~ "")`, `.record_key()` | wave B's `gt_theme_tier()`, `fmt_image()`, `sub_missing()`, `cols_label(cases=)`, `_sdvplot_key` | ported |
| `gt_title_header` | `tab_header(html())`, fonts on `cells_title("title")`, `Date` | `tab_header(html())`, fonts on `loc.title()`, `datetime.date` | ported |
| `gt_watermark` | `opt_css` scoped by `.table_id()`, `base64enc`, `URLencode` | `opt_css` scoped by `GT.with_id()`, `base64`, `urllib.parse.quote` | ported; `font` and `color` are escaped inside the SVG's attributes (R pastes them, so a quoted font list such as `"Helvetica Neue", Arial` breaks R's SVG) |
| `gt_wrap_labels` | `strwrap()` (lines shorter than `width`) | `textwrap.wrap(width - 1)` without word or hyphen breaks | ported |
