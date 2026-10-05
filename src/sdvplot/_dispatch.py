"""One front door for every library: sdvplot.add_logos(target, ...) routes to the adapter for target's library.

Each adapter registers at the end of this module (registering imports nothing; the adapter module loads on first
use). The full adapter contract, its rules and its test hooks are documented in sdvplot.testing; in short, an adapter
module exposes add_logos, add_wordmarks, add_headshots and axis_logos, plus the test hook

    _drawn_marks(target) -> list[tuple]

which returns one (team_id, x, y, height) or (team_id, x, y, height, url) tuple per image the adapter drew, in draw
order. team_id is the canonical string id, x/y are the position values passed in (positional, never index labels),
height is the fraction of the plot height the image was drawn at (measured, not the value asked for), and url the
image source it drew.

add_logos must return the object that was drawn on: the target itself when the library mutates in place
(matplotlib), or the new object when it builds one (plotnine, altair, tables). The harness reads _drawn_marks from
the returned object when it is not None, and from the target otherwise.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from types import ModuleType
from typing import TYPE_CHECKING, Any, TypeVar, overload

from sdvplot._errors import OptionalDependencyError, UnsupportedTargetError

if TYPE_CHECKING:
    from bokeh.models import Plot
    from folium import Map
    from great_tables import GT
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from plotly.basedatatypes import BaseFigure
    from plotnine import ggplot

# The targets whose verbs return the target itself, or a new object of its type (plotnine, great_tables), so the
# result has the type the target had. Altair is not one: a Chart comes back as a LayerChart.
_Target = TypeVar("_Target", bound="Axes | Figure | BaseFigure | ggplot | GT | Plot | Map")
# The same, for the libraries that draw axis logos
_AxisTarget = TypeVar("_AxisTarget", bound="Axes | Figure | BaseFigure | ggplot")


@dataclass(frozen=True)
class Adapter:
    name: str  # display name, e.g. "Plotly"
    package: str  # top-level package of the target object's type, e.g. "plotly"
    module: str  # adapter module, e.g. "sdvplot.plotly"
    extra: str  # pip extra, e.g. "plotly"


ADAPTERS: dict[str, Adapter] = {}


def register_adapter(adapter: Adapter) -> None:
    ADAPTERS[adapter.package] = adapter


def adapter_for(target: Any) -> ModuleType:
    """The adapter module for target's library.

    Walks type(target).__mro__ and uses the first class whose top-level package is registered, so a user's
    subclass of a library class (even one defined in __main__) still reaches that library's adapter.
    """
    cls = type(target)
    adapter = None
    for klass in cls.__mro__:
        adapter = ADAPTERS.get((klass.__module__ or "").split(".")[0])
        if adapter is not None:
            break
    if adapter is None:
        supported = ", ".join(sorted(a.name for a in ADAPTERS.values())) or "none yet"
        raise UnsupportedTargetError(
            f"sdvplot has no adapter for {cls.__module__}.{cls.__name__} objects; supported: {supported}"
        )
    try:
        return importlib.import_module(adapter.module)
    except ModuleNotFoundError as e:
        # Only a missing adapter module or target library (ModuleNotFoundError) means "extra not installed";
        # any other ImportError (a broken transitive import inside the adapter) is a real bug: surface it unchanged.
        name = e.name or ""
        if name == adapter.module or name == adapter.package or name.startswith(adapter.package + "."):
            raise OptionalDependencyError(
                f"{adapter.name} support needs the {adapter.extra} extra: pip install sdvplot[{adapter.extra}]"
            ) from e
        raise


@overload
def add_logos(target: _Target, *args: Any, **kwargs: Any) -> _Target: ...
@overload
def add_logos(target: Any, *args: Any, **kwargs: Any) -> Any: ...
def add_logos(target: Any, *args: Any, **kwargs: Any) -> Any:
    """Add team logos to a plot or table of any supported library.

    Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
    the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. Plots and
    tables take different arguments. A plot (matplotlib, plotnine, Plotly, Altair, Bokeh, HoloViews, folium and pygal)
    takes ``x``, ``y`` and ``teams``, and a ``height`` that is a fraction of the plot height. A great_tables ``GT``
    takes ``columns`` and a ``height`` in pixels, with no ``alpha`` or ``variant`` (see
    ``sdvplot.great_tables.gt_sdv_logos``).

    Args:
        target: The plot or table object. Its type picks the adapter.
        *args: Passed to the adapter. For a plot: ``x``, ``y`` (positions in the target's own coordinates) and
            ``teams`` (the team values to draw), in that order. For a table: ``columns`` (the columns whose cells
            become marks).
        **kwargs: Passed to the adapter: ``league`` (the SDV league key) and ``season`` (one season or one per team).
            For a plot, also ``height`` (a fraction of the plot height, in (0, 1]), ``alpha`` (opacity, 0 to 1) and
            ``variant`` (a mark variant, as in ``logo_url``); for a table, ``height`` is in pixels (default 30).

    Returns:
        object: The drawn-on plot or table: ``target`` itself, or the new object the adapter built.

    Raises:
        UnsupportedTargetError: If no adapter is registered for ``target``'s library.
        OptionalDependencyError: If the adapter's optional extra is not installed.
        TypeError: If the adapter does not take an argument given (a table takes no ``x``, ``y``, ``alpha``).
        ValueError: If a value is out of range: a plot ``height`` outside (0, 1], or a table ``height`` below 1
            pixel (a fraction such as 0.1 is a plot's unit, not a table's).

    Example:
        ::

            import matplotlib.pyplot as plt
            import sdvplot

            fig, ax = plt.subplots()
            ax.set_xlim(0, 30)
            ax.set_ylim(-10, 0)
            sdvplot.add_logos(ax, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    return adapter_for(target).add_logos(target, *args, **kwargs)


@overload
def add_wordmarks(target: _Target, *args: Any, **kwargs: Any) -> _Target: ...
@overload
def add_wordmarks(target: Any, *args: Any, **kwargs: Any) -> Any: ...
def add_wordmarks(target: Any, *args: Any, **kwargs: Any) -> Any:
    """Add team wordmarks to a plot or table of any supported library.

    Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
    the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. Plots and
    tables take different arguments. A plot (matplotlib, plotnine, Plotly, Altair, Bokeh, HoloViews, folium and pygal)
    takes ``x``, ``y`` and ``teams``, and a ``height`` that is a fraction of the plot height. A great_tables ``GT``
    takes ``columns`` and a ``height`` in pixels, with no ``alpha`` or ``variant`` (see
    ``sdvplot.great_tables.gt_sdv_wordmarks``).

    Args:
        target: The plot or table object. Its type picks the adapter.
        *args: Passed to the adapter. For a plot: ``x``, ``y`` (positions in the target's own coordinates) and
            ``teams`` (the team values to draw), in that order. For a table: ``columns`` (the columns whose cells
            become marks).
        **kwargs: Passed to the adapter: ``league`` (the SDV league key) and ``season`` (one season or one per team).
            For a plot, also ``height`` (a fraction of the plot height, in (0, 1]), ``alpha`` (opacity, 0 to 1) and
            ``variant`` (a mark variant, as in ``logo_url``); for a table, ``height`` is in pixels (default 30).

    Returns:
        object: The drawn-on plot or table: ``target`` itself, or the new object the adapter built.

    Raises:
        UnsupportedTargetError: If no adapter is registered for ``target``'s library.
        OptionalDependencyError: If the adapter's optional extra is not installed.
        TypeError: If the adapter does not take an argument given (a table takes no ``x``, ``y``, ``alpha``).
        ValueError: If a value is out of range: a plot ``height`` outside (0, 1], or a table ``height`` below 1
            pixel (a fraction such as 0.1 is a plot's unit, not a table's).

    Example:
        ::

            import matplotlib.pyplot as plt
            import sdvplot

            fig, ax = plt.subplots()
            sdvplot.add_wordmarks(ax, [0.5], [0.5], ["KC"], league="nfl", height=0.1)

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    return adapter_for(target).add_wordmarks(target, *args, **kwargs)


@overload
def add_headshots(target: _Target, *args: Any, **kwargs: Any) -> _Target: ...
@overload
def add_headshots(target: Any, *args: Any, **kwargs: Any) -> Any: ...
def add_headshots(target: Any, *args: Any, **kwargs: Any) -> Any:
    """Add player headshots to a plot or table of any supported library.

    Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
    the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. For
    headshots, ``teams`` holds player ids and ``league`` picks the ESPN league. Plots and tables take different
    arguments. A plot (matplotlib, plotnine, Plotly, Altair, Bokeh, HoloViews, folium and pygal) takes ``x``, ``y`` and
    ``teams``, and a ``height`` that is a fraction of the plot height. A great_tables ``GT`` takes ``columns`` and a
    ``height`` in pixels, with no ``alpha`` (see ``sdvplot.great_tables.gt_sdv_headshots``).

    Args:
        target: The plot or table object. Its type picks the adapter.
        *args: Passed to the adapter. For a plot: ``x``, ``y`` (positions in the target's own coordinates) and
            ``teams`` (the player ids to draw), in that order. For a table: ``columns`` (the columns whose cells
            become headshots).
        **kwargs: Passed to the adapter: ``league`` (the SDV league key) and ``id_system`` (``"espn"`` or
            ``"gsis"``, as in ``headshot_url``). For a plot, also ``height`` (a fraction of the plot height, in
            (0, 1]) and ``alpha`` (opacity, 0 to 1); for a table, ``height`` is in pixels (default 30). Headshots take
            no ``season`` or ``variant``.

    Returns:
        object: The drawn-on plot or table: ``target`` itself, or the new object the adapter built.

    Raises:
        UnsupportedTargetError: If no adapter is registered for ``target``'s library.
        OptionalDependencyError: If the adapter's optional extra is not installed.
        TypeError: If the adapter does not take an argument given (a table takes no ``x``, ``y``, ``alpha``).
        ValueError: If a value is out of range: a plot ``height`` outside (0, 1], or a table ``height`` below 1
            pixel (a fraction such as 0.1 is a plot's unit, not a table's).

    Example:
        ::

            import matplotlib.pyplot as plt
            import sdvplot

            fig, ax = plt.subplots()
            sdvplot.add_headshots(ax, [0.5], [0.5], ["3139477"], league="nfl", height=0.2)

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    return adapter_for(target).add_headshots(target, *args, **kwargs)


@overload
def axis_logos(target: _AxisTarget, *args: Any, **kwargs: Any) -> _AxisTarget: ...
@overload
def axis_logos(target: Any, *args: Any, **kwargs: Any) -> Any: ...
def axis_logos(target: Any, *args: Any, **kwargs: Any) -> Any:
    """Replace an axis' team labels with team logos on a plot of any supported library.

    Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
    the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. The
    adapters that draw axis logos (matplotlib, plotnine, Plotly and Altair) all take ``axis_logos(target, axis, *,
    league, season=None, height=0.1, variant="default", mark_type="logo", id_system="auto")``, and Plotly and Altair
    also take ``embed``. Bokeh, HoloViews, folium, pygal and great_tables have no axis logos: there it raises TypeError.

    Args:
        target: The plot object. Its type picks the adapter.
        *args: Passed to the adapter: ``axis`` (which axis' tick labels to replace, ``"x"`` or ``"y"``).
        **kwargs: Passed to the adapter: ``league`` (the SDV league key, required), ``season`` (one season or one per
            team, default ``None``), ``height`` (the mark's height as a fraction of the plot height, default 0.1),
            and ``variant``, ``mark_type`` and ``id_system`` as in ``logo_url`` and ``resolve``.

    Returns:
        object: The drawn-on plot: ``target`` itself, or the new object the adapter built.

    Raises:
        UnsupportedTargetError: If no adapter is registered for ``target``'s library.
        OptionalDependencyError: If the adapter's optional extra is not installed.
        TypeError: If ``target``'s library has no axis logos (Bokeh, HoloViews, folium, pygal, great_tables).
        ValueError: If ``height`` is outside (0, 1].

    Example:
        ::

            import matplotlib.pyplot as plt
            import sdvplot

            fig, ax = plt.subplots()
            ax.bar(["KC", "BUF", "BAL"], [12, 10, 9])
            sdvplot.axis_logos(ax, "x", league="nfl", height=0.08)

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    return adapter_for(target).axis_logos(target, *args, **kwargs)


# The adapters sdvplot ships. Registering imports nothing: the adapter module loads on first use.
register_adapter(Adapter("matplotlib", "matplotlib", "sdvplot.matplotlib", "mpl"))
register_adapter(Adapter("seaborn", "seaborn", "sdvplot.matplotlib", "mpl"))
register_adapter(Adapter("plotnine", "plotnine", "sdvplot.plotnine", "plotnine"))
register_adapter(Adapter("great_tables", "great_tables", "sdvplot.great_tables", "tables"))
register_adapter(Adapter("plotly", "plotly", "sdvplot.plotly", "plotly"))
register_adapter(Adapter("altair", "altair", "sdvplot.altair", "altair"))
register_adapter(Adapter("bokeh", "bokeh", "sdvplot.bokeh", "bokeh"))
register_adapter(Adapter("holoviews", "holoviews", "sdvplot.holoviews", "holoviews"))
register_adapter(Adapter("folium", "folium", "sdvplot.folium", "folium"))
register_adapter(Adapter("pygal", "pygal", "sdvplot.pygal", "pygal"))
