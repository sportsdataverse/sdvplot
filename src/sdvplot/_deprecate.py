"""Deprecations: one warning category and one way to emit it, so every rename warns the same way (CONTRIBUTING:
Deprecation policy). Nothing in sdvplot is deprecated yet."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from sdvplot._errors import SdvplotDeprecationWarning, warn

F = TypeVar("F", bound=Callable[..., Any])


def deprecate(old: str, *, replacement: str, removal: str) -> None:
    """Warn, at the caller's line, that ``old`` is deprecated: it names ``replacement`` and ``removal``, the release
    that removes it. Call it from the deprecated function or branch, which keeps working."""
    warn(f"{old} is deprecated and will be removed in sdvplot {removal}; use {replacement} instead",
         SdvplotDeprecationWarning)  # fmt: skip


def deprecated_alias(*, removal: str, **renames: str) -> Callable[[F], F]:
    """A decorator for renamed keyword arguments: ``@deprecated_alias(removal="0.3.0", which="kind")`` keeps
    ``fn(which=...)`` working as ``fn(kind=...)``, with one warning per call. Passing both names is a TypeError."""

    def decorate(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for old, new in renames.items():
                if old in kwargs:
                    if new in kwargs:
                        raise TypeError(f"{fn.__name__}() got both {old}= (deprecated) and {new}=; pass only {new}=")
                    deprecate(f"{fn.__name__}({old}=...)", replacement=f"{new}=", removal=removal)
                    kwargs[new] = kwargs.pop(old)
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorate
