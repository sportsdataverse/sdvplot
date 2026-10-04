"""One front door for every library: sdvplot.add_logos(target, ...) routes to the adapter for target's library.

Adapters arrive in sub-projects 2-5 and register here. The table starts empty in the core release.

Adapter module contract (checked by sdvplot.testing.check_adapter_contract): add_logos, add_wordmarks,
add_headshots and axis_logos as in the plan, plus the test hook

    drawn_marks(target) -> list[tuple[str, float, float, float]]

which returns one (team_id, x, y, height) tuple per image the adapter drew, in draw order. team_id is the
canonical string id, x/y are the position values passed in (positional, never index labels), and height is the
fraction of the plot height the adapter actually used.

add_logos must return the object that was drawn on: the target itself when the library mutates in place
(matplotlib), or the new object when it builds one (plotnine, altair, tables). The harness reads drawn_marks from
the returned object when it is not None, and from the target otherwise.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from types import ModuleType
from typing import Any

from sdvplot._errors import OptionalDependencyError, UnsupportedTargetError


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


def add_logos(target: Any, *args: Any, **kwargs: Any) -> Any:
    """Add team logos to a plot or table of any supported library.

    Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
    the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. Every
    adapter takes the same arguments.

    Args:
        target: The plot or table object. Its type picks the adapter.
        *args: Passed to the adapter. By convention ``x``, ``y`` (positions in the target's own coordinates) and
            ``teams`` (the team values to draw), in that order.
        **kwargs: Passed to the adapter: ``league`` (the SDV league key), ``season`` (one season or one per team),
            ``height`` (the mark's height as a fraction of the plot height), ``alpha`` (opacity, 0 to 1) and
            ``variant`` (a mark variant, as in ``logo_url``).

    Returns:
        object: The drawn-on plot or table: ``target`` itself, or the new object the adapter built.

    Raises:
        UnsupportedTargetError: If no adapter is registered for ``target``'s library.
        OptionalDependencyError: If the adapter's optional extra is not installed.

    Example:
        ::

            import sdvplot

            try:
                sdvplot.add_logos(object(), [0.5], [0.5], ["KC"], league="nfl")
            except sdvplot.UnsupportedTargetError:
                pass   # raised: object() is not a plot or table

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    return adapter_for(target).add_logos(target, *args, **kwargs)


def add_wordmarks(target: Any, *args: Any, **kwargs: Any) -> Any:
    """Add team wordmarks to a plot or table of any supported library.

    Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
    the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. Every
    adapter takes the same arguments.

    Args:
        target: The plot or table object. Its type picks the adapter.
        *args: Passed to the adapter. By convention ``x``, ``y`` (positions in the target's own coordinates) and
            ``teams`` (the team values to draw), in that order.
        **kwargs: Passed to the adapter: ``league`` (the SDV league key), ``season`` (one season or one per team),
            ``height`` (the mark's height as a fraction of the plot height), ``alpha`` (opacity, 0 to 1) and
            ``variant`` (a mark variant, as in ``logo_url``).

    Returns:
        object: The drawn-on plot or table: ``target`` itself, or the new object the adapter built.

    Raises:
        UnsupportedTargetError: If no adapter is registered for ``target``'s library.
        OptionalDependencyError: If the adapter's optional extra is not installed.

    Example:
        ::

            import sdvplot

            try:
                sdvplot.add_wordmarks(object(), [0.5], [0.5], ["KC"], league="nfl")
            except sdvplot.UnsupportedTargetError:
                pass   # raised: object() is not a plot or table

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    return adapter_for(target).add_wordmarks(target, *args, **kwargs)


def add_headshots(target: Any, *args: Any, **kwargs: Any) -> Any:
    """Add player headshots to a plot or table of any supported library.

    Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
    the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. Every
    adapter takes the same arguments. For headshots, ``teams`` holds player ids and ``league`` picks the ESPN league.

    Args:
        target: The plot or table object. Its type picks the adapter.
        *args: Passed to the adapter. By convention ``x``, ``y`` (positions in the target's own coordinates) and
            ``teams`` (the team values to draw), in that order.
        **kwargs: Passed to the adapter: ``league`` (the SDV league key), ``season`` (one season or one per team),
            ``height`` (the mark's height as a fraction of the plot height), ``alpha`` (opacity, 0 to 1) and
            ``variant`` (a mark variant, as in ``logo_url``).

    Returns:
        object: The drawn-on plot or table: ``target`` itself, or the new object the adapter built.

    Raises:
        UnsupportedTargetError: If no adapter is registered for ``target``'s library.
        OptionalDependencyError: If the adapter's optional extra is not installed.

    Example:
        ::

            import sdvplot

            try:
                sdvplot.add_headshots(object(), [0.5], [0.5], ["KC"], league="nfl")
            except sdvplot.UnsupportedTargetError:
                pass   # raised: object() is not a plot or table

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    return adapter_for(target).add_headshots(target, *args, **kwargs)


def axis_logos(target: Any, *args: Any, **kwargs: Any) -> Any:
    """Replace an axis' team labels with team logos on a plot of any supported library.

    Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
    the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. Every
    adapter takes the same arguments: ``axis_logos(target, axis, *, league, season=None, height=0.1)``.

    Args:
        target: The plot or table object. Its type picks the adapter.
        *args: Passed to the adapter. By the adapter contract, ``axis`` (which axis' tick labels to replace, ``"x"`` or
            ``"y"``).
        **kwargs: Passed to the adapter: ``league`` (the SDV league key, required), ``season`` (one season or one per
            team, default ``None``) and ``height`` (the mark's height as a fraction of the plot height, default 0.1).

    Returns:
        object: The drawn-on plot or table: ``target`` itself, or the new object the adapter built.

    Raises:
        UnsupportedTargetError: If no adapter is registered for ``target``'s library.
        OptionalDependencyError: If the adapter's optional extra is not installed.

    Example:
        ::

            import sdvplot

            try:
                sdvplot.axis_logos(object(), "x", league="nfl")
            except sdvplot.UnsupportedTargetError:
                pass   # raised: object() is not a plot or table

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    return adapter_for(target).axis_logos(target, *args, **kwargs)


# The adapters sdvplot ships. Registering imports nothing: the adapter module loads on first use.
register_adapter(Adapter("matplotlib", "matplotlib", "sdvplot.matplotlib", "mpl"))
register_adapter(Adapter("seaborn", "seaborn", "sdvplot.matplotlib", "mpl"))
