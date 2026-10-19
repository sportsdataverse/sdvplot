"""Perspective (``pip install sdvplot[perspective]``, Python 3.11+): team colors, registry fonts and a logo column for a
Perspective viewer.

Both functions return plain data: a viewer config, the keyword arguments of ``perspective.widget.PerspectiveWidget``
and the argument of the JavaScript ``<perspective-viewer>``'s ``restore()``, and a frame with a logo URL column. What
Perspective 5.5 does with each key was checked in Chromium: the Datagrid fills a string column's cells, and a scatter
colors its Color slot's categories, from a palette in the order it first meets each value, and a chart colors its
``split_by`` series from a palette in ascending order of the split values. Perspective's own themes ("Pro Light", "Pro
Dark") draw the grid; a registry theme adds its fonts and its sign colors.
"""

from __future__ import annotations

import re
import sys
from typing import Any, Literal

import narwhals as nw

from sdvplot._errors import InputError, OptionalDependencyError, requires_extra, warn

if sys.version_info < (3, 11):  # the extra installs nothing there: say why, not only which extra
    raise OptionalDependencyError(
        "perspective-python ships wheels for Python 3.11+ only: sdvplot.perspective needs Python 3.11+ and pip install "
        '"sdvplot[perspective]"',
        name="perspective",
    )
with requires_extra("perspective"):
    import perspective as _perspective  # noqa: F401  (the extra guard: this module is for Perspective users)

from sdvplot._colors import team_colors
from sdvplot._contrast import hex6
from sdvplot._normalize import norm_season
from sdvplot._placement import place
from sdvplot._resolve import resolve
from sdvplot._table_themes import table_theme_spec
from sdvplot._team_palette import team_palette
from sdvplot._types import IdSystem

__all__ = ["perspective_logo_column", "perspective_sdv_config"]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


# Perspective's two built-in themes and their --psp--background-color (measured in 5.5.1: #fff, #242526)
_PRO = {"light": ("Pro Light", "#ffffff"), "dark": ("Pro Dark", "#242526")}
_FALLBACK = "#808080"
# A float column whose name says it is a percentage (fg_pct, pct_complete, win_percent) shows 1 decimal; any other
# float (a rate, EPA) shows 3. Perspective 5.5.1's number_format is Intl.NumberFormat's options (checked in Chromium).
_PERCENT = re.compile(r"(?i)(^|_)(pct|percent|perc)(_|$)")
_PLAIN = {"useGrouping": False, "maximumFractionDigits": 0}  # an integer as typed: 1039 and 2024, not 1,039 or 2,024


def _number_format(name: str, dtype: Any) -> dict[str, Any]:
    if dtype.is_integer():
        return dict(_PLAIN)
    n = 1 if _PERCENT.search(name) else 3
    return {"minimumFractionDigits": n, "maximumFractionDigits": n}


def _frame(frame: Any, *cols: str | None) -> nw.DataFrame[Any]:
    """``frame`` (polars, pandas or any narwhals-supported eager frame) with each named column checked."""
    df = nw.from_native(frame, eager_only=True)
    for c in cols:
        if c is not None and c not in df.columns:
            raise InputError(f"the frame has no column {c!r} (columns: {', '.join(df.columns)})")
    return df


def _palette(values: list[Any], *, league: str, season: int | None, background: str, id_system: IdSystem,
             strict: bool) -> list[str]:  # fmt: skip
    """One color per team value, in the given order: the shared team palette on ``background`` (3:1 against it, ΔE 20
    apart). A value that does not resolve (one warning, from the resolver) takes the fallback grey and stays out of the
    palette, so it never moves a real team's color; two values naming one team share its color."""
    ids = resolve(values, league, season=season, id_system=id_system, strict=strict) if values else []
    known = list(dict.fromkeys(i for i in ids if i is not None))
    kw: dict[str, Any] = {"season": season, "id_system": "team_id"}
    main = team_colors(league, known, **kw) if known else []
    other = team_colors(league, known, which="secondary", **kw) if known else []
    colors = [hex6(m or o or _FALLBACK, drop_alpha=True) for m, o in zip(main, other, strict=True)]
    by_id = dict(zip(known, team_palette(colors, other, background, known), strict=True))
    return [_FALLBACK if i is None else by_id[i] for i in ids]


def _team_orders(df: nw.DataFrame[Any], team_col: str) -> tuple[list[Any], list[Any]]:
    """The distinct non-null team values in the order a grid or a scatter's Color slot meets them (first appearance),
    and in a chart's split order (sorted, by codepoint as Perspective sorts). InputError for values of mixed types."""
    first = df[team_col].drop_nulls().unique(maintain_order=True).to_list()
    try:
        return first, sorted(first)
    except TypeError as e:
        kinds = sorted({type(v).__name__ for v in first})
        raise InputError(f"the team column {team_col!r} mixes {' and '.join(kinds)} values: use one id system") from e


def _gradient(colors: list[str]) -> str:
    """Perspective's palette value: ``linear-gradient(to right, #rrggbb, ...)``, with no positions."""
    return f"linear-gradient(to right, {', '.join(colors)})"


def perspective_sdv_config(
    frame: Any,
    *,
    team_col: str,
    league: str,
    plugin: str = "Datagrid",
    theme: str | None = None,
    mode: Literal["light", "dark"] = "light",
    logo_col: str | None = None,
    background: str | None = None,
    formats: dict[str, dict[str, Any] | None] | None = None,
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
) -> dict[str, Any]:
    """A Perspective viewer config that colors each team by its own colors, for the Datagrid or a chart.

    The colors are the shared team palette (as the deck.gl and pydeck adapters use), taken over the teams in sorted
    order: each team's color, made 3:1 against the background and ΔE 20 from every earlier team's, so a team keeps one
    color whatever the frame's order. Perspective takes a palette, not a color per value, so each palette lists those
    colors in the order Perspective hands colors out (checked in Chromium on Perspective 5.5.1):

    - ``plugin="Datagrid"``: the team column's cells are filled (``bg_mode`` "series"; Perspective picks a readable
      text color). The grid gives the palette to the values in the order it first draws them, so it is in the frame's
      order of first appearance: keep the grid's rows in the frame's order (no ``sort``), and keep it to about one row
      per team. In a long grid, scrolling past a team the grid has not drawn yet shifts every later color. Null cells
      take no color and no palette slot. Only a text team column (string, or a pandas category / polars Categorical or
      Enum, which Perspective loads as strings) is filled: Perspective rejects a fill on a number column, so a numeric
      team id column gets none, with one warning.
    - a chart plugin: the view is yours. Split a bar, line or area chart by the team (``split_by=[team_col]``) and
      each team's series takes its color from every numeric column's ``palette``, in sorted order, because Perspective
      sorts split values. Put the team column in an "X/Y Scatter"'s Color slot (its third column) and each team's
      points take theirs from the team column's ``palette``, in the frame's order, the order Perspective meets them (a
      scatter's ``split_by`` draws one panel per team instead). Perspective sorts split values by codepoint (upper
      case first: "LSU" before "Louisiana"), as Python does. Null team values split into a "null" series that comes
      first and takes the first palette entry, so the sorted palette then starts with the fallback grey. Checked on
      "X Bar", "Y Bar", "Y Line" and "X/Y Scatter"; a Treemap or Sunburst hands colors out in drawing order, which
      this does not follow.

    Every numeric column also gets a number format (``number_format``, Intl.NumberFormat options): 3 decimals for a
    float (rates, EPA), 1 for a float whose name says it is a percentage (``pct``, ``percent``), and an integer
    plain (no grouping: 2024, not 2,024). ``formats`` overrides them.

    Args:
        frame: The data the viewer shows: a polars or pandas DataFrame (anything narwhals reads eagerly).
        team_col: The column holding team identifiers (any id system ``resolve`` reads).
        league: The SDV league key, e.g. "nfl".
        plugin: The Perspective plugin: "Datagrid" (the default) or a chart's name.
        theme: A registry table theme (``sdv_table_themes()``). On the Datagrid it sets the font family and size
            (``plugin_config``), each numeric column's sign colors (its ``neg`` and ``pos``) and, when the theme has a
            numeric face of its own, the numeric columns' font. Perspective quotes the value as one family name (no
            fallback stack), so the page must load the font itself (Google Fonts), or the browser draws its default
            font. Charts take no fonts from a config.
        mode: "light" or "dark": the Perspective theme ("Pro Light" or "Pro Dark") and the registry theme's mode.
        logo_col: A logo URL column (``perspective_logo_column``) to show as links on the Datagrid. Perspective 5.5's
            Datagrid draws no images, so a link is the one format a URL column has.
        formats: Per column, a ``number_format`` (Intl.NumberFormat options, e.g. ``{"maximumFractionDigits": 2}``)
            to use instead of the default, or None for none.
        background: The color the teams must read against. Default: the Perspective theme's background (#ffffff for
            "Pro Light", #242526 for "Pro Dark").
        season: One season for every team (the table rule).
        id_system: The id system of the team values, as in ``resolve``.
        strict: Raise UnresolvedTeamError for a team that does not resolve, instead of warning once and giving it
            #808080.

    Returns:
        dict: ``plugin``, ``theme`` and ``columns_config``, plus ``plugin_config`` for the Datagrid with a registry
        theme. Pass it as ``PerspectiveWidget(data, **config)`` or to ``viewer.restore()``;
        merge your own ``group_by``, ``split_by``, ``columns`` and the rest into it.

    Raises:
        InputError: For a column the frame does not have (``team_col``, ``logo_col`` or a ``formats`` key), a team
            column that mixes value types, an unknown ``mode``, ``theme`` or ``id_system``, a season outside the
            league's, or a dark ``mode`` on a light-only theme.
        UnresolvedTeamError: With ``strict=True``, for a team that does not resolve.

    Example:
        ::

            import polars as pl
            from sdvplot.perspective import perspective_sdv_config

            # 2024 regular season, offense: EPA per play (nflverse play-by-play)
            epa = pl.DataFrame({"posteam": ["BAL", "BUF", "DET"], "epa_per_play": [0.218, 0.1885, 0.1592]})
            cfg = perspective_sdv_config(epa, team_col="posteam", league="nfl", theme="datagolf")
            print(cfg["columns_config"]["posteam"]["bg_color"])
            bars = perspective_sdv_config(epa, team_col="posteam", league="nfl", plugin="Y Bar")
            bars |= {"group_by": ["posteam"], "split_by": ["posteam"], "columns": ["epa_per_play"]}
            # in a notebook: PerspectiveWidget(epa, **cfg)

    See Also:
        perspective_logo_column: a logo URL column to show beside the team ;
        table_theme_spec: the registry theme this reads ;
        Perspective: https://perspective-dev.github.io/
    """
    if mode not in _PRO:
        raise InputError(f"mode must be 'light' or 'dark', not {mode!r}")
    df = _frame(frame, team_col, logo_col, *(formats or {}))
    spec = table_theme_spec(theme, mode) if theme is not None else None
    pro, pro_bg = _PRO[mode]
    bg = hex6(background) if background is not None else pro_bg
    s = norm_season(season, league)
    schema = df.schema
    text = not schema[team_col].is_numeric()  # string, categorical, enum or object: Perspective loads them as strings
    numeric = [c for c, d in schema.items() if c != team_col and d.is_numeric()]
    grid = plugin == "Datagrid"
    first, ascending = _team_orders(df, team_col)
    pal = _palette(ascending, league=league, season=s, background=bg, id_system=id_system, strict=strict)
    color = dict(zip(ascending, pal, strict=True))
    nulls = [_FALLBACK] if df[team_col].null_count() else []  # a null split series comes first: palette entry 0
    by_appearance = _gradient([color[v] for v in first])
    by_value = _gradient(nulls + pal)
    cfg: dict[str, Any] = {"plugin": plugin, "theme": pro}
    columns: dict[str, dict[str, Any]] = {c: {} for c in numeric}
    for c in numeric:
        fmt = (formats or {}).get(c, _number_format(c, schema[c]))
        if fmt is not None:
            columns[c]["number_format"] = fmt
    # no teams (a zero-row frame) means no palette entries at all: an empty palette is not a valid CSS value
    if first and not grid:
        for c in numeric:
            columns[c]["palette"] = by_value
        if text:  # a number column in the Color slot is a gradient, not categories
            columns = {team_col: {"palette": by_appearance}, **columns}
    elif first and text:
        columns = {team_col: {"bg_mode": "series", "bg_color": by_appearance}, **columns}
    elif first:
        warn(f"no team colors on the Datagrid: the team column {team_col!r} is numeric, and team colors need a string "
             "or categorical team column (Perspective fills only text cells)")  # fmt: skip
    if grid:
        if spec is not None:
            body = spec.fonts.get("body")
            if body:
                cfg["plugin_config"] = {"font_family": body, "font_size": spec.sizes["body"]}
            num_font = spec.fonts.get("numeric")
            sign = f"linear-gradient(to right, {spec.palette['neg']} 0%, {spec.palette['pos']} 100%)"
            for c in numeric:
                columns[c]["fg_color"] = sign
                if num_font and num_font != body:
                    columns[c]["font_family"] = num_font
        if logo_col is not None:
            columns[logo_col] = {"link": True}
    cfg["columns_config"] = {c: v for c, v in columns.items() if v}
    return cfg


def perspective_logo_column(
    frame: Any,
    team_col: str,
    *,
    league: str,
    name: str | None = None,
    season: Any = None,
    variant: str = "default",
    id_system: IdSystem = "auto",
    strict: bool = False,
) -> Any:
    """The frame with a column of each team's logo URL, right after the team column.

    Each distinct team is resolved once. A team that does not resolve, or has no archived logo, gets a null URL, with
    one warning for each reason. Show the column as links with ``perspective_sdv_config(..., logo_col=...)``:
    Perspective 5.5's Datagrid draws no images.

    Args:
        frame: A polars or pandas DataFrame (anything narwhals reads eagerly); the result is of the same library, with
            the same rows (and pandas index).
        team_col: The column holding team identifiers.
        league: The SDV league key, e.g. "nfl".
        name: The new column's name. Default: ``f"{team_col}_logo"``. It must not be a column already.
        season: One season for every team: the logo of that season (relocations and rebrands).
        variant: "default", "dark", or a named variant from ``marks()``.
        id_system: The id system of the team values, as in ``resolve``.
        strict: Raise UnresolvedTeamError for a team that does not resolve, instead of warning.

    Returns:
        The frame, with the logo URLs as a string column (null where there is none).

    Raises:
        InputError: For a missing ``team_col``, a ``name`` the frame already has, or an unknown ``variant``,
            ``id_system`` or season.
        UnresolvedTeamError: With ``strict=True``, for a team that does not resolve.

    Example:
        ::

            import polars as pl
            from sdvplot.perspective import perspective_logo_column, perspective_sdv_config

            epa = pl.DataFrame({"posteam": ["BAL", "BUF", "DET"], "epa_per_play": [0.218, 0.1885, 0.1592]})
            out = perspective_logo_column(epa, "posteam", league="nfl")
            print(out.columns)  # ['posteam', 'posteam_logo', 'epa_per_play']
            cfg = perspective_sdv_config(out, team_col="posteam", league="nfl", logo_col="posteam_logo")

    See Also:
        perspective_sdv_config: the viewer config that shows the column as links ;
        logo_url: one team's logo URL
    """
    name = name or f"{team_col}_logo"
    df = _frame(frame, team_col)
    if name in df.columns:
        raise InputError(f"the frame already has a column {name!r}: pass another name")
    values = df[team_col].drop_nulls().unique(maintain_order=True).to_list()
    n = len(values)
    placed = place(list(range(n)), [0] * n, values, league=league, season=norm_season(season, league), kind="logo",
                   variant=variant, id_system=id_system, strict=strict)  # fmt: skip
    urls = {values[p.x]: p.url for p in placed}
    col = [None if v is None else urls.get(v) for v in df[team_col].to_list()]
    out = df.with_columns(nw.new_series(name, col, nw.String(), backend=nw.get_native_namespace(df)))
    at = df.columns.index(team_col) + 1
    return out.select([*df.columns[:at], name, *df.columns[at:]]).to_native()
