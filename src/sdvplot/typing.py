"""Types for annotating code that calls sdvplot: the ``Literal`` aliases of its closed argument vocabularies.

Use them where you keep an argument in a variable, so a type checker accepts it::

    import sdvplot
    from sdvplot.typing import Which

    def team_palette(league: str, which: Which = "primary") -> dict:
        return sdvplot.palette(league, which=which)

``league`` and ``variant`` have no alias: their values come from the bundled team index and the logo archive, so the
set is open (annotate them as ``str``).
"""

from sdvplot._types import AxisMarkType, HeadshotIdSystem, IdSystem, MarkType, Which

__all__ = ["AxisMarkType", "HeadshotIdSystem", "IdSystem", "MarkType", "Which"]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)
