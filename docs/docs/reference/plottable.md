---
title: sdvplot.plottable
sidebar_label: sdvplot.plottable
sidebar_position: 27
---

# sdvplot.plottable

plottable columns of team logos, wordmarks and player headshots.

| Name | What it is |
|---|---|
| [headshot_column](#headshot_column) | A plottable column that shows each row's player as a headshot. |
| [logo_column](#logo_column) | A plottable column that shows each row's team as its logo (or wordmark). |

## headshot_column

<div class="sdv-signature">

```python
headshot_column(
    name: str,
    *,
    league: str,
    id_system: str = 'espn',
    **column_definition_kwargs: Any,
) -> plottable.column_def.ColumnDefinition
```

</div>

A plottable column that shows each row's player as a headshot.

### Arguments

| Name | Type | Description |
|---|---|---|
| `name` | `str` | The data column holding the player ids. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `id_system` | `str` | "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``. |
| `**column_definition_kwargs` | `Any` | Passed to ``plottable.ColumnDefinition``. |

### Returns

`plottable.ColumnDefinition` — The column definition; an unknown id leaves its cell blank, with an SdvplotWarning.

### Raises

- `InputError`: (a ValueError) When the table is drawn, if ``league`` has no ESPN headshots or ``id_system`` is not valid for it.
- `OfflineError`: When the table is drawn, if a headshot, or with ``id_system="gsis"`` the nflverse player table, is neither cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
- `UnsafeDownloadError`: (an OSError) When the table is drawn, if a download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
import pandas as pd
from plottable import Table
from sdvplot.plottable import headshot_column

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Table(df, column_definitions=[headshot_column("espn_id", league="nfl", title="")])
```

### See also

- [sdvplotR geom_nfl_headshots()](https://sdvplotR.sportsdataverse.org/)
- sdvplot.plottable.logo_column: the same with team logos

## logo_column

<div class="sdv-signature">

```python
logo_column(
    name: str,
    *,
    league: str,
    season: Any = None,
    variant: str = 'default',
    mark_type: str = 'logo',
    id_system: str = 'auto',
    **column_definition_kwargs: Any,
) -> plottable.column_def.ColumnDefinition
```

</div>

A plottable column that shows each row's team as its logo (or wordmark).

### Arguments

| Name | Type | Description |
|---|---|---|
| `name` | `str` | The data column holding the teams. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season for every row. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `mark_type` | `str` | "logo" or "wordmark". |
| `id_system` | `str` | The id system of the column's values. |
| `**column_definition_kwargs` | `Any` | Passed to ``plottable.ColumnDefinition`` (``title``, ``width``, ``group``, ...). |

### Returns

`plottable.ColumnDefinition` — The column definition; an unknown team leaves its cell blank, with an SdvplotWarning.

### Raises

- `InputError`: (a ValueError) When the table is drawn, if ``mark_type`` is not "logo" or "wordmark", ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league (the column definition itself is built without checking them).
- `OfflineError`: When the table is drawn, if the logo manifest or a mark's image is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode).
- `UnsafeDownloadError`: (an OSError) When the table is drawn, if a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) When the table is drawn, if the manifest's sha256 or extension for a mark would put the file outside the cache directory.
- `OptionalDependencyError`: When the table is drawn, if a mark is an SVG and the ``svg`` extra is not installed.

### Example

```python
from plottable import Table
from sdvplot.plottable import logo_column
import pandas as pd

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Table(df, column_definitions=[logo_column("team", league="nfl", title="")])
```

### See also

- [plottable](https://plottable.readthedocs.io/)
