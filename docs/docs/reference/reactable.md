---
title: sdvplot.reactable
sidebar_label: sdvplot.reactable
sidebar_position: 25
---

# sdvplot.reactable

reactable-py columns (``pip install sdvplot[reactable]``), ported from sdvplotR's ``reactable_sdv_*`` functions.

| Name | What it is |
|---|---|
| [reactable_sdv_cols_label](#reactable_sdv_cols_label) | One reactable column per team-named column of ``data`` (a ``KC`` column, a ``BUF`` column, ...), its header |
| [reactable_sdv_headshots](#reactable_sdv_headshots) | A reactable column that shows each cell's player id as the player's headshot. |
| [reactable_sdv_logos](#reactable_sdv_logos) | A reactable column that shows each cell's team as its logo. |
| [reactable_sdv_team_color_bar](#reactable_sdv_team_color_bar) | A reactable column whose cells hold a bar in the row's team color, as long as the value's share of the maximum. |
| [reactable_sdv_team_color_bg](#reactable_sdv_team_color_bg) | A reactable column whose cells are filled with the row's team color, mostly transparent. |
| [reactable_sdv_wordmarks](#reactable_sdv_wordmarks) | A reactable column that shows each cell's team as its wordmark. |

## reactable_sdv_cols_label

<div class="sdv-signature">

```python
reactable_sdv_cols_label(
    data: Any,
    *,
    league: str,
    variant: str = 'default',
    height: Any = 30,
    season: Any = None,
    mark_type: str = 'logo',
    **column_kwargs: Any,
) -> list[reactable.models.Column]
```

</div>

One reactable column per team-named column of ``data`` (a ``KC`` column, a ``BUF`` column, ...), its header

the team's mark.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable``. Pass only the team-named columns (``df[["KC", "BUF"]]``) to avoid a warning for the others. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `height` | `Any` | The image height in pixels. |
| `season` | `Any` | One season whose marks to show; None for today's. |
| `mark_type` | `str` | "logo" or "wordmark". |
| `**column_kwargs` | `Any` | Passed to every ``reactable.Column``. |

### Returns

`list[reactable.Column]` — A column (``id`` = the column name, an empty ``name``, the mark as ``header``) for each column whose name resolves; the others are left out, with one SdvplotWarning.

### Raises

- `ValueError`: If ``height`` is not a number of pixels of at least 1, ``mark_type`` is not "logo"/"wordmark", or ``season`` is not one year.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_cols_label

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Reactable(df, columns=reactable_sdv_cols_label(df, league="nfl"))
```

### See also

- [Ported from sdvplotR ``reactable_sdv_cols_label()``](https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_cols_label.html)

## reactable_sdv_headshots

<div class="sdv-signature">

```python
reactable_sdv_headshots(
    *,
    league: str,
    height: Any = 40,
    default_img: str | None = None,
    id_system: str = 'espn',
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that shows each cell's player id as the player's headshot.

### Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `Any` | The image height in pixels. |
| `default_img` | `str \| None` | An image URL for ids without a headshot; None keeps their text. |
| `id_system` | `str` | "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column`` (``id`` is required by reactable). |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `ValueError`: If ``height`` is not a number of pixels of at least 1.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_headshots

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Reactable(df, columns=[reactable_sdv_headshots(league="nfl", id="espn_id", name="")])
```

### See also

- [Ported from sdvplotR ``reactable_sdv_headshots()``](https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_images.html)

## reactable_sdv_logos

<div class="sdv-signature">

```python
reactable_sdv_logos(
    *,
    league: str,
    variant: str = 'default',
    height: Any = 30,
    default_img: str | None = None,
    season: Any = None,
    include_name: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that shows each cell's team as its logo.

### Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `height` | `Any` | The image height in pixels. |
| `default_img` | `str \| None` | An image URL for values that do not resolve; None keeps their text. |
| `season` | `Any` | One season whose marks every cell shows; None for today's. |
| `include_name` | `bool` | Keep the cell's text after the logo. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``: ``id`` (the data column, required by reactable), ``name``, ``width``, ... |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `ValueError`: If ``height`` is not a number of pixels of at least 1, or ``season`` is not one year.

### Example

```python
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_logos
import pandas as pd

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Reactable(df, columns=[reactable_sdv_logos(league="nfl", id="team", name="")])
```

### See also

- [Ported from sdvplotR ``reactable_sdv_logos()``](https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_images.html)

## reactable_sdv_team_color_bar

<div class="sdv-signature">

```python
reactable_sdv_team_color_bar(
    data: Any,
    team_col: str,
    *,
    league: str,
    which: str = 'primary',
    max_value: float | None = None,
    na_color: str = '#b3b3b3',
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column whose cells hold a bar in the row's team color, as long as the value's share of the maximum.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (each row's team is read from it). |
| `team_col` | `str` | The column of ``data`` holding the teams. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `which` | `str` | "primary" or "secondary" team color. |
| `max_value` | `float \| None` | The value that fills the whole cell; None for the column's maximum. |
| `na_color` | `str` | The CSS color for teams that do not resolve or have no color. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the styled column. |

### Returns

`reactable.Column` — The column, with a ``style`` function.

### Raises

- `ValueError`: If ``team_col`` is not a column of ``data``, or ``which`` is not "primary"/"secondary".

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_team_color_bar

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Reactable(df, columns=[reactable_sdv_team_color_bar(df, "team", league="nfl", id="wins")])
```

### See also

- [Ported from sdvplotR ``reactable_sdv_team_color_bar()``](https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_team_color.html)

## reactable_sdv_team_color_bg

<div class="sdv-signature">

```python
reactable_sdv_team_color_bg(
    data: Any,
    team_col: str,
    *,
    league: str,
    which: str = 'primary',
    alpha: float = 0.15,
    na_color: str = '#b3b3b3',
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column whose cells are filled with the row's team color, mostly transparent.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (each row's team is read from it). |
| `team_col` | `str` | The column of ``data`` holding the teams. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `which` | `str` | "primary" or "secondary" team color. |
| `alpha` | `float` | The fill's opacity, 0 to 1. |
| `na_color` | `str` | The hex color for teams that do not resolve or have no color. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the styled column. |

### Returns

`reactable.Column` — The column, with a ``style`` function.

### Raises

- `ValueError`: If ``team_col`` is not a column of ``data``, ``which`` is not "primary"/"secondary", ``alpha`` is outside [0, 1], or ``na_color`` is not a hex color.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_team_color_bg

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Reactable(df, columns=[reactable_sdv_team_color_bg(df, "team", league="nfl", id="team")])
```

### See also

- [Ported from sdvplotR ``reactable_sdv_team_color_bg()``](https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_team_color.html)

## reactable_sdv_wordmarks

<div class="sdv-signature">

```python
reactable_sdv_wordmarks(
    *,
    league: str,
    variant: str = 'default',
    height: Any = 30,
    default_img: str | None = None,
    season: Any = None,
    include_name: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that shows each cell's team as its wordmark.

### Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `height` | `Any` | The image height in pixels. |
| `default_img` | `str \| None` | An image URL for values that do not resolve; None keeps their text. |
| `season` | `Any` | One season whose marks every cell shows; None for today's. |
| `include_name` | `bool` | Keep the cell's text after the wordmark. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column`` (``id`` is required by reactable). |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `ValueError`: If ``height`` is not a number of pixels of at least 1, or ``season`` is not one year.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_wordmarks

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Reactable(df, columns=[reactable_sdv_wordmarks(league="nfl", id="team")])
```

### See also

- [Ported from sdvplotR ``reactable_sdv_wordmarks()``](https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_images.html)
