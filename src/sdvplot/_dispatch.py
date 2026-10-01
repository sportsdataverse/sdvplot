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
    except ImportError as e:
        # Only a missing adapter module or target library means "extra not installed"; any other ImportError
        # (a broken transitive import inside the adapter) is a real bug and must surface unchanged.
        name = e.name or ""
        if name == adapter.module or name == adapter.package or name.startswith(adapter.package + "."):
            raise OptionalDependencyError(
                f"{adapter.name} support needs the {adapter.extra} extra: pip install sdvplot[{adapter.extra}]"
            ) from e
        raise


def add_logos(target: Any, *args: Any, **kwargs: Any) -> Any:
    """Add team logos to a plot or table of any supported library (see the adapter contract)."""
    return adapter_for(target).add_logos(target, *args, **kwargs)


def add_wordmarks(target: Any, *args: Any, **kwargs: Any) -> Any:
    return adapter_for(target).add_wordmarks(target, *args, **kwargs)


def add_headshots(target: Any, *args: Any, **kwargs: Any) -> Any:
    return adapter_for(target).add_headshots(target, *args, **kwargs)


def axis_logos(target: Any, *args: Any, **kwargs: Any) -> Any:
    return adapter_for(target).axis_logos(target, *args, **kwargs)
