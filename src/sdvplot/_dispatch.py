"""One front door for every library: sdvplot.add_logos(target, ...) routes to the adapter for target's library.

Adapters arrive in sub-projects 2-5 and register here. The table starts empty in the core release.
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
    package = type(target).__module__.split(".")[0]
    adapter = ADAPTERS.get(package)
    if adapter is None:
        supported = ", ".join(sorted(a.name for a in ADAPTERS.values())) or "none yet"
        raise UnsupportedTargetError(
            f"sdvplot has no adapter for {type(target).__module__}."
            f"{type(target).__name__} objects; supported: {supported}"
        )
    try:
        return importlib.import_module(adapter.module)
    except ImportError as e:
        raise OptionalDependencyError(
            f"{adapter.name} support needs the {adapter.extra} extra: pip install sdvplot[{adapter.extra}]"
        ) from e


def add_logos(target: Any, *args: Any, **kwargs: Any) -> Any:
    """Add team logos to a plot or table of any supported library (see the adapter contract)."""
    return adapter_for(target).add_logos(target, *args, **kwargs)


def add_wordmarks(target: Any, *args: Any, **kwargs: Any) -> Any:
    return adapter_for(target).add_wordmarks(target, *args, **kwargs)


def add_headshots(target: Any, *args: Any, **kwargs: Any) -> Any:
    return adapter_for(target).add_headshots(target, *args, **kwargs)


def axis_logos(target: Any, *args: Any, **kwargs: Any) -> Any:
    return adapter_for(target).axis_logos(target, *args, **kwargs)
