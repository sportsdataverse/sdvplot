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
    "sdvplotr",
    "name",
    "nhl_id",
]
# headshot_url()'s id_system: ESPN athlete ids (any ESPN league) or nflverse gsis ids (nfl)
HeadshotIdSystem = Literal["espn", "gsis"]
# palette()'s color slot: _colors._COLUMNS
Which = Literal["primary", "secondary"]
# logo_url() and logo_image()'s mark: _marks.MARK_TYPES
MarkType = Literal["logo", "wordmark"]
