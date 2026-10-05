"""A stand-in for ``polars`` that imports it on first attribute access, so ``import sdvplot`` stays fast."""

from __future__ import annotations

from typing import Any


class _LazyPolars:
    def __getattr__(self, name: str) -> Any:
        import polars

        return getattr(polars, name)


pl = _LazyPolars()
