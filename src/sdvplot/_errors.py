"""Warning and exception types. Every error subclasses SdvplotError and the builtin a caller would already catch."""


class SdvplotWarning(UserWarning):
    """Something was skipped or degraded (an unresolved team, a stale cache), but the call still returned."""


class SdvplotError(Exception):
    """The base of every sdvplot error: ``except sdvplot.SdvplotError`` catches them all."""


class UnresolvedTeamError(SdvplotError, ValueError):
    """A team value did not resolve and strict=True was set."""


class OfflineError(SdvplotError, RuntimeError):
    """A download failed and no cached copy exists."""


class OptionalDependencyError(SdvplotError, ImportError):
    """A feature needs an optional extra that is not installed."""


class UnsupportedTargetError(SdvplotError, TypeError):
    """sdvplot has no adapter for this kind of plot or table object."""


class UnsafeCachePathError(SdvplotError, ValueError):
    """A manifest value (sha256, ext) or cache path would reach outside the sdvplot cache directory."""


class UnsafeDownloadError(SdvplotError, OSError):
    """A download was refused: too large, too slow, or redirected away from https."""
