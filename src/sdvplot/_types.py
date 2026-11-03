"""The closed vocabularies of sdvplot's arguments, as ``Literal`` types a type checker can check.

An alias exists only where the runtime accepts exactly that set of strings; ``tests/test_types.py`` keeps each one
equal to the set the code validates against. Two vocabularies stay ``str`` because they are open: ``league`` (the
leagues come from the bundled team index, which grows with each release) and ``variant`` (the names come from the logo
archive's manifest; "default" and "dark" always work).
"""

from typing import Literal

# resolve()'s id_system: "auto", then _resolve.PRIORITY in order, then _resolve.EXPLICIT_ONLY
IdSystem = Literal[
    "auto",
    "team_id",
    "espn",
    "espn_abbr",
    "nhl",
    "nflverse",
    "mlbstats",
    "nba_api",
    "hockeytech",
    "ncaa",
    "pff",
    "cricinfo",
    "cfbd",
    "bref",
    "sportsipy",
    "fangraphs",
    "yahoo",
    "kenpom",
    "torvik",
    "sdvplotr",
    "name",
    "nhl_id",
    "fox",
    "cbs",
    "sports247",
    "on3",
]
# headshot_url()'s id_system: ESPN athlete ids (any ESPN league), nflverse gsis ids (nfl), the league's own player
# id (sdvplotR's id_type="league": nfl gsis, NBA / WNBA Stats PERSON_ID, MLBAM, NHL; _headshots.LEAGUE_HEADSHOT_URLS),
# or another provider's player id, mapped to an ESPN athlete (_headshots.PLAYER_ALIAS_SOURCES)
HeadshotIdSystem = Literal["espn", "gsis", "league", "fox", "yahoo", "cbs", "kenpom", "ncaa", "nba_stats", "wnba_stats"]
# palette()'s color slot: _colors._COLUMNS
Which = Literal["primary", "secondary"]
# logo_url() and logo_image()'s mark: _marks.MARK_TYPES
MarkType = Literal["logo", "wordmark"]
# axis_logos()'s mark_type: _placement.KINDS (a headshot axis holds player ids)
AxisMarkType = Literal["logo", "wordmark", "headshot"]
# hexbin/squarebin/binner's cell shape and add_bins' shape: _bins.SHAPES
BinShape = Literal["hex", "square"]
# add_bins' value, what the fill encodes: _bins.VALUES
BinValue = Literal["count", "weight"]
