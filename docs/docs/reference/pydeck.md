---
title: sdvplot.pydeck
sidebar_label: sdvplot.pydeck
sidebar_position: 25
---

# sdvplot.pydeck

The pydeck adapter: team logos, team-colored arcs and sportypy playing surfaces as pydeck layer props.

| Name | What it is |
|---|---|
| [deck](#deck) | A ``pydeck.Deck`` of sdvplot layer props, its view fitted to them. |
| [logo_icon_layer](#logo_icon_layer) | pydeck ``IconLayer`` props drawing each row's team logo at its (x, y). |
| [pass_arc_layer](#pass_arc_layer) | pydeck ``ArcLayer`` props: one arc per row from (x, y) to (xend, yend), in the team's colors. |
| [surface_layer](#surface_layer) | pydeck ``PolygonLayer`` props drawing sportypy's playing surface for ``sport`` and ``league``. |

## deck

<div class="sdv-signature">

```python
deck(
    *layers: collections.abc.Mapping[str, Any],
    height: int = 480,
    width: int = 720,
    **deck_kwargs: Any,
) -> pydeck.bindings.deck.Deck
```

</div>

A ``pydeck.Deck`` of sdvplot layer props, its view fitted to them.

With a ``surface_layer`` among them, the deck has a top-down OrthographicView (y up) fitted to the surface, and
every other layer is drawn in the surface's own coordinates. Without one, it is a map, fitted to the layers'
positions (longitude and latitude). The layers are drawn in the order given.

### Arguments

| Name | Type | Description |
|---|---|---|
| `*layers` | `collections.abc.Mapping[str, Any]` | Props from ``surface_layer``, ``logo_icon_layer``, ``pass_arc_layer`` or any other ``pydeck.Layer`` keyword arguments. |
| `height` | `int` | The deck's height in px. |
| `width` | `int` | The width in px the view is fitted to (the deck itself fills its container's width). |
| `**deck_kwargs` | `Any` | Passed to ``pydeck.Deck`` (``tooltip``, ``map_style``, ...). |

### Returns

`pydeck.Deck` — The deck; show it in a notebook, or ``to_html()`` it.

### Raises

- `InputError`: (a ValueError) If no layer is given, or ``height`` or ``width`` is under 1 px.

### Example

```python
import sdvplot.pydeck

rink = sdvplot.pydeck.surface_layer("hockey", "nhl")
d = sdvplot.pydeck.deck(rink, height=300)
assert d.views[0].type == "OrthographicView"
```

### See also

- [pydeck Deck](https://deckgl.readthedocs.io/en/latest/deck.html)

## logo_icon_layer

<div class="sdv-signature">

```python
logo_icon_layer(
    rows: 'Any',
    *,
    x: 'str',
    y: 'str',
    team: 'str',
    league: 'str',
    season: 'Any' = None,
    variant: 'str' = 'default',
    id_system: 'IdSystem' = 'auto',
    strict: 'bool' = False,
    size: 'float' = 32,
    alpha: 'float' = 1.0,
    id: 'str' = 'sdvplot-logos',
) -> 'dict[str, Any]'
```

</div>

pydeck ``IconLayer`` props drawing each row's team logo at its (x, y).

The logos are deck.gl's auto-packed icons: deck.gl fetches each URL once and packs it into its own atlas, 128 px
tall at the logo's aspect, centred on the point. A team with no logo (or one that does not resolve) is left out
with one warning, as the other adapters do; so is a row with a missing x or y. ``x`` and ``y`` are in the layer's
coordinates: longitude and latitude on a map, or a surface's own units over ``surface_layer`` (``deck`` sets the
coordinate system for you).

### Arguments

| Name | Type | Description |
|---|---|---|
| `rows` | `'Any'` | The rows: a polars or pandas DataFrame, or a sequence of mappings. |
| `x` | `'str'` | The column of each logo's x (a longitude on a map, or a surface's x). |
| `y` | `'str'` | The column of each logo's y. |
| `team` | `'str'` | The column of each row's team (abbreviation, name or id; see ``id_system``). |
| `league` | `'str'` | The SDV league key, e.g. "nhl". |
| `season` | `'Any'` | A season for every row, or the name of a column holding each row's season. |
| `variant` | `'str'` | The logo variant, e.g. "dark". |
| `id_system` | `'IdSystem'` | How the team values are read. |
| `strict` | `'bool'` | Raise UnresolvedTeamError for a team that does not resolve, instead of warning. |
| `size` | `'float'` | The logo's height on screen in px, 1 or more (deck.gl's ``getSize`` in "pixels" units). |
| `alpha` | `'float'` | The layer's opacity in [0, 1]. |
| `id` | `'str'` | The layer id. |

### Returns

`dict` — ``pydeck.Layer`` keyword arguments: ``type`` "IconLayer", ``data`` (one dict per logo: ``position``, ``icon`` with its ``url``, ``width``, ``height``, ``anchorY`` and ``mask``, the resolved ``team`` id and the row's ``index``), the accessors ``get_position`` and ``get_icon``, ``get_size``, ``size_units`` and ``opacity``.

### Raises

- `InputError`: (a ValueError) If a column is not in ``rows``, ``size`` is under 1 px, ``alpha`` is outside [0, 1], or ``league``, ``season``, ``variant`` or ``id_system`` is not valid.
- `UnresolvedTeamError`: With ``strict=True``, for a team that does not resolve.
- `OfflineError`: If the logo manifest is neither cached nor downloadable.

### Example

```python
import sdvplot.pydeck

# Arrowhead and Lincoln Financial Field, by longitude and latitude
stadiums = [
    {"team": "KC", "lon": -94.4839, "lat": 39.0489},
    {"team": "PHI", "lon": -75.1675, "lat": 39.9008},
]
props = sdvplot.pydeck.logo_icon_layer(stadiums, x="lon", y="lat", team="team", league="nfl", size=40)
assert [d["team"] for d in props["data"]] == ["12", "21"]
```

### See also

- [deck.gl IconLayer](https://deck.gl/docs/api-reference/layers/icon-layer)
- [pydeck](https://deckgl.readthedocs.io/)

## pass_arc_layer

<div class="sdv-signature">

```python
pass_arc_layer(
    rows: 'Any',
    *,
    x: 'str',
    y: 'str',
    xend: 'str',
    yend: 'str',
    team: 'str',
    league: 'str',
    season: 'Any' = None,
    id_system: 'IdSystem' = 'auto',
    strict: 'bool' = False,
    which: 'Which' = 'primary',
    background: 'str | None' = None,
    fallback: 'str' = '#808080',
    width: 'float' = 2,
    alpha: 'float' = 1.0,
    height: 'float | None' = None,
    tilt: 'float | None' = None,
    id: 'str' = 'sdvplot-arcs',
) -> 'dict[str, Any]'
```

</div>

pydeck ``ArcLayer`` props: one arc per row from (x, y) to (xend, yend), in the team's colors.

The team's primary color is at the source and its secondary at the target (``which="secondary"`` swaps them), so
where the two colors differ the ends tell the direction. Each team keeps one color per end, the teams taken in the
order they first appear. With ``background``, every color keeps 3:1 contrast against it (dark mode) and stays
distinct (CIE76 ΔE of 20 or more) from the other teams' colors at that end. Caveat: a color that does not read
gives way to the team's other color, so when only one of a team's two colors reads on the background, both ends
take it and the arcs no longer show their direction (France's navy and mint on a dark pitch are both mint); pick a
background on which both read (France's both read on a mid-tone green such as ``#4a7f3a``), or check that
``sourceColor`` and ``targetColor`` differ. A team that does not resolve takes ``fallback`` as given, outside the
palette; a row with a missing coordinate is left out with one warning.

### Arguments

| Name | Type | Description |
|---|---|---|
| `rows` | `'Any'` | The rows: a polars or pandas DataFrame, or a sequence of mappings. |
| `x` | `'str'` | The column of each arc's source x. |
| `y` | `'str'` | The column of each arc's source y. |
| `xend` | `'str'` | The column of each arc's target x. |
| `yend` | `'str'` | The column of each arc's target y. |
| `team` | `'str'` | The column of the team each arc is colored by. |
| `league` | `'str'` | The SDV league key, e.g. "soccer". |
| `season` | `'Any'` | The season the teams are resolved for. |
| `id_system` | `'IdSystem'` | How the team values are read. |
| `strict` | `'bool'` | Raise UnresolvedTeamError for a team that does not resolve, instead of warning (and drawing it in ``fallback``). |
| `which` | `'Which'` | The color at the source end, "primary" or "secondary"; the target end takes the other. |
| `background` | `'str \| None'` | The background the arcs are drawn on; given, each color keeps 3:1 contrast against it and stays distinct from the other teams'. |
| `fallback` | `'str'` | The color of a team that does not resolve, or has no color (an unresolved team's is used as given). |
| `width` | `'float'` | The arc's width in px, 1 or more. |
| `alpha` | `'float'` | The layer's opacity in [0, 1]. |
| `height` | `'float \| None'` | deck.gl's ``getHeight``, how high each arc rises for its length, 0 or more (0 draws a straight line). None (the default) keeps deck.gl's 1; lower, such as 0.3, keeps arcs laid flat (``tilt=90``) close to their chord, inside the surface. |
| `tilt` | `'float \| None'` | deck.gl's ``getTilt``, degrees in [-90, 90]: 90 lays each arc flat on the surface, so a top-down 2D view shows the curve. None (the default) keeps deck.gl's upright arcs, for a pitched 3D view. |
| `id` | `'str'` | The layer id. |

### Returns

`dict` — ``pydeck.Layer`` keyword arguments: ``type`` "ArcLayer", ``data`` (one dict per arc: ``source``, ``target``, ``sourceColor`` and ``targetColor`` as ``[r, g, b, a]``, ``team`` (the resolved id, else the row's value as text) and the row's ``index``), the accessors ``get_source_position``, ``get_target_position``, ``get_source_color`` and ``get_target_color``, ``get_width``, ``width_units``, ``opacity`` and, with ``height`` and ``tilt``, ``get_height`` and ``get_tilt``.

### Raises

- `InputError`: (a ValueError) If a column is not in ``rows``, ``width`` is under 1 px, ``alpha`` is outside [0, 1], ``height`` is negative, ``tilt`` is outside [-90, 90], ``which`` is not "primary" or "secondary", or ``league``, ``season`` or ``id_system`` is not valid.
- `UnresolvedTeamError`: With ``strict=True``, for a team that does not resolve.
- `ValueError`: If ``background`` or ``fallback`` is not a hex color.

### Example

```python
import sdvplot.pydeck

# two of France's passes in the 2018 World Cup final (StatsBomb open data through SPADL, metres)
passes = [
    {"team": "478", "start_x": 54.69, "start_y": 6.38, "end_x": 56.44, "end_y": 1.28},
    {"team": "478", "start_x": 22.31, "start_y": 9.78, "end_x": 6.56, "end_y": 31.88},
]
props = sdvplot.pydeck.pass_arc_layer(
    passes, x="start_x", y="start_y", xend="end_x", yend="end_y", team="team", league="soccer",
    id_system="team_id", tilt=90,
)
assert props["data"][0]["sourceColor"] == [0, 0, 128, 255]  # France's navy at the passer
assert props["data"][0]["targetColor"] != props["data"][0]["sourceColor"]  # its mint at the receiver
```

### See also

- [deck.gl ArcLayer](https://deck.gl/docs/api-reference/layers/arc-layer)
- [sdvplot-js passArcLayer](https://plot.sportsdataverse.org/)

## surface_layer

<div class="sdv-signature">

```python
surface_layer(
    sport: str,
    league: str,
    *,
    id: str = 'sdvplot-surface',
    tolerance: float | None = None,
    **sportypy_kwargs: Any,
) -> dict[str, Any]
```

</div>

pydeck ``PolygonLayer`` props drawing sportypy's playing surface for ``sport`` and ``league``.

The surface is in its own coordinates: deck.gl's "cartesian" coordinate system, in the surface's units (feet for
a rink, metres for a pitch) with the origin at its centre, the frame sportypy draws in and NHL api-web's shot
coordinates are in. Each closed loop of a visible sportypy feature is one data row (a faceoff circle is two: its
half rings; a loop that crosses itself, such as a goaltender trapezoid, is split at the crossing into loops that
do not, and a loop with no area is left out), in sportypy's drawing order (its zorder), filled with its color
(alpha included); a hidden one (a ``#rrggbb00`` fill, or none) is left out. sportypy draws arcs with up to 8,000
points (80,000 before sportypy 1.2.2); each loop is thinned to ``tolerance`` (see below), which leaves an NHL rink
about 14,400 points instead of 123,000, and the coordinates are rounded to 0.0001 of the unit, so a deck stays a
few hundred kilobytes.
sdvplot-js's ``surfaceLayer`` draws sporty's own
geometry, so the two languages' vertices differ (the props, colors and extents agree).

### Arguments

| Name | Type | Description |
|---|---|---|
| `sport` | `str` | The sportypy sport: "hockey", "soccer", "basketball", "football", "baseball", "tennis" or "curling". |
| `league` | `str` | sportypy's league code for the sport, e.g. "nhl", "fifa", "nba". |
| `id` | `str` | The layer id. |
| `tolerance` | `float \| None` | The simplification distance, in the surface's units; None for a 2,000th of the surface's diagonal (about 0.11 ft on an NHL rink), 0 to keep every point. Each loop caps it at its own mean width and keeps both ends of every segment at least that long, so thin lines and rings keep their corners and shape (every loop within 5% of its area unthinned, measured on all seven sports). |
| `**sportypy_kwargs` | `Any` | Passed to the sportypy surface class: ``rink_updates`` / ``pitch_updates`` / ``court_updates`` / ``field_updates``, ``color_updates``, ``units``. |

### Returns

`dict` — ``pydeck.Layer`` keyword arguments: ``type`` "PolygonLayer", ``data`` (one dict per closed loop of a feature: ``name``, sportypy's class name in snake case, ``polygon`` and ``fillColor`` as ``[r, g, b, a]``), the accessors ``get_polygon`` and ``get_fill_color``, ``coordinate_system`` "'cartesian'" (quoted, a constant), ``filled`` and ``stroked``.

### Raises

- `InputError`: (a ValueError) If sportypy has no surface for ``sport``, no ``league`` for it, or ``tolerance`` is negative.
- `OptionalDependencyError`: If the surfaces extra (sportypy) is not installed.

### Example

```python
import sdvplot.pydeck

rink = sdvplot.pydeck.surface_layer("hockey", "nhl")
assert rink["coordinate_system"] == "'cartesian'"  # quoted: a constant, not an expression
assert rink["data"][0]["name"] == "defensive_zone"
```

### See also

- [sportypy](https://sportypy.sportsdataverse.org/)
- [deck.gl PolygonLayer](https://deck.gl/docs/api-reference/layers/polygon-layer)
