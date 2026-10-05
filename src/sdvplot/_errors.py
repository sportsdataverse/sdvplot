"""Warning and exception types. Every error subclasses SdvplotError and the builtin a caller would already catch."""


class SdvplotWarning(UserWarning):
    """Something was skipped or degraded (an unresolved team, a stale cache), but the call still returned."""


class SdvplotError(Exception):
    """The base of sdvplot's errors: an unresolved team, a failed or refused download, a missing extra, an unsupported
    target, and the shared argument checks (``InputError``). A check specific to one helper (an axis name, a column,
    a chart setting) raises a plain ValueError or TypeError."""


class InputError(SdvplotError, ValueError):
    """An argument sdvplot cannot use: an unknown league, id system, color slot or mark type, a color slot such as
    ``"secondary"`` passed as a team, or a height or alpha out of range."""


class UnresolvedTeamError(SdvplotError, ValueError):
    """A team value did not resolve and strict=True was set."""


class OfflineError(SdvplotError, RuntimeError):
    """A download failed and no cached copy exists."""


class OptionalDependencyError(SdvplotError, ImportError):
    """A feature needs an optional extra that is not installed."""


class UnsupportedTargetError(SdvplotError, TypeError):
    """sdvplot cannot draw on this object: no adapter takes its kind of plot or table, or the adapter does not support
    the verb (axis logos on a map, a table, Bokeh, HoloViews or pygal)."""


class UnsafeCachePathError(SdvplotError, ValueError):
    """A manifest value (sha256, ext) or cache path would reach outside the sdvplot cache directory."""


class UnsafeDownloadError(SdvplotError, OSError):
    """A download was refused: too large, too slow, or redirected away from https."""
