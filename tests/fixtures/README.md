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

Regenerate the sdvplotR fixture with the export script; never edit it by hand.
