"""Warning and exception types. Each subclasses the builtin a caller would already catch."""


class SdvplotWarning(UserWarning):
    """Something was skipped or degraded (an unresolved team, a stale cache), but the call still returned."""


class UnresolvedTeamError(ValueError):
    """A team value did not resolve and strict=True was set."""


class OfflineError(RuntimeError):
    """A download failed and no cached copy exists."""


class OptionalDependencyError(ImportError):
    """A feature needs an optional extra that is not installed."""


class UnsupportedTargetError(TypeError):
    """sdvplot has no adapter for this kind of plot or table object."""
