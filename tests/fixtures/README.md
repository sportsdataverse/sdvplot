<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Test fixtures](#test-fixtures)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Test fixtures

| File | Provenance | Used by |
| --- | --- | --- |
| `marks.csv` | Hand-written. A few rows in the sdv-assets logo manifest's schema, chosen to exercise mark selection (variant, then season, then source, plus the OAK/LV relocation). URLs under `https://x/` are placeholders. | `tests/conftest.py` (the offline manifest the marks and logo tests read) |
| `sdvplotr_logo_history.csv` | Real sdvplotR output: its season-logo table, exported by `Rscript tools/export_sdvplotr.R` at the commit recorded in `data-raw/sdvplotr_commit.txt`. | `tests/test_sdvplotr_parity.py` (live) |
| `nba_shotchartdetail_2023.csv` | Real stats.nba.com `shotchartdetail` rows: 40 of the 41,587 in sdv-py's `tests/fixtures/nba_shot_value/shotchart_2023.parquet` (captured 2026-07-08 from stats.nba.com, season 2022-23, columns snake-cased by sdv-py's `parse_nba_stats_result_sets`). Per `shot_zone_basic`: 8 Left Corner 3 (including `loc_x` -249 and -221), 8 Right Corner 3 (including 221 and 248), 8 Restricted Area (including the farthest, 3.996 ft), 6 Above the Break 3, 4 Mid-Range, 4 In The Paint (Non-RA), 2 Backcourt; the rest sampled with seed 2023. Nine columns kept; values as captured. | `tests/test_court.py`, `tests/test_plotnine.py`, `tests/test_images_baseline.py` |
| `sdvplotr_court_coords.csv` | Real sdvplotR output: `sdv_court_coords(shots, "loc_x", "loc_y")` on those rows (sdvplotR `0a6e66d`), doubles at 17 significant digits, exported by `Rscript tools/export_parity_extras.R`. | `tests/test_court.py` |
| `ggpath_ref_lines.csv` | Real ggpath 1.1.1 / ggplot2 4.0.3 output: the per-panel values `geom_mean_lines()` and `geom_median_lines()` draw for `aes(x0 = loc_x, y0 = loc_y)` on those rows with `facet_wrap(~shot_zone_basic)`, checked against the drawn segments, by the same script. | `tests/test_plotnine.py` |

Regenerate the sdvplotR and ggpath fixtures with the export scripts; never edit them by hand.
