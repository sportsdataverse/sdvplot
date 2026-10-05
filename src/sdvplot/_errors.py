"""Warning and exception types. Every error subclasses SdvplotError and the builtin a caller would already catch."""

from __future__ import annotations

import contextlib
import os
import sys
import warnings
from collections.abc import Iterator
from types import FrameType

_PACKAGE = os.path.dirname(os.path.abspath(__file__)) + os.sep


class SdvplotWarning(UserWarning):
    """Something was skipped or degraded (an unresolved team, a stale cache), but the call still returned."""


class SdvplotDeprecationWarning(SdvplotWarning, FutureWarning):
    """A deprecated sdvplot name or argument: it still works, and the message names its replacement and the release
    that removes it. A FutureWarning, so it shows by default."""


def warn(message: str, category: type[Warning] = SdvplotWarning) -> None:
    """``warnings.warn`` at the first frame outside the sdvplot package: the caller's own line, however deep inside
    sdvplot the warning is raised (a fixed ``stacklevel`` named sdvplot's files whenever the call chain changed)."""
    frame: FrameType | None = sys._getframe(1)
    level = 2
    while frame is not None and frame.f_code.co_filename.startswith(_PACKAGE):
        frame, level = frame.f_back, level + 1
    warnings.warn(message, category, stacklevel=level)


class SdvplotError(Exception):
    """The base of sdvplot's errors: an unresolved team, a failed or refused download, a missing extra, an unsupported
    target, and the shared argument checks (``InputError``). A check specific to one helper (an axis name, a column,
    a chart setting) raises a plain ValueError or TypeError."""


class InputError(SdvplotError, ValueError):
    """An argument sdvplot cannot use: an unknown league, id system, color slot, mark type or variant, a color slot
    such as ``"secondary"`` passed as a team, a season that is not a year or is outside the ones sdvplot knows, or a
    height, alpha, image size or candidate count out of range."""


class UnresolvedTeamError(SdvplotError, ValueError):
    """A team value did not resolve and strict=True was set."""


class OfflineError(SdvplotError, RuntimeError):
    """A download failed and no cached copy exists."""


class DownloadError(OfflineError, OSError):
    """A download got an HTTP error status (a 4xx or 5xx response) and no cached copy exists. Also an OSError, so
    ``except OSError`` catches it."""


class IntegrityError(DownloadError):
    """A download is not the file the manifest promises: its sha256 differs (it is not cached), or the archived file is
    not an image PIL can decode."""


class OptionalDependencyError(SdvplotError, ModuleNotFoundError):
    """A feature needs an optional extra that is not installed: an adapter submodule imported without its library
    (``import sdvplot.plotly`` without plotly), an SVG mark without the svg extra. The message names the extra to
    install."""


@contextlib.contextmanager
def requires_extra(extra: str) -> Iterator[None]:
    """Around an adapter module's library imports: a missing library is an OptionalDependencyError naming the extra
    (still a ModuleNotFoundError, with the missing module's ``name``) instead of a bare ModuleNotFoundError."""
    try:
        yield
    except ModuleNotFoundError as e:
        raise OptionalDependencyError(
            f'{e.name or "a library"} is not installed: this needs the {extra} extra, pip install "sdvplot[{extra}]"',
            name=e.name,
        ) from e


class UnsupportedTargetError(SdvplotError, TypeError):
    """sdvplot cannot draw on this object: no adapter takes its kind of plot or table, or the adapter does not support
    the verb (axis logos on a map, a table, Bokeh, HoloViews or pygal)."""


class UnsafeCachePathError(SdvplotError, ValueError):
    """A manifest value (sha256, ext) or cache path would reach outside the sdvplot cache directory."""


class UnsafeDownloadError(SdvplotError, OSError):
    """A download was refused: too large, too slow, or redirected away from https."""
