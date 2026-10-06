"""Team logos, wordmarks, headshots and colors for Python plots and tables (SportsDataverse)."""

from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _version

from sdvplot._cache import clear_cache
from sdvplot._colors import palette, team_colors
from sdvplot._court import court_coords
from sdvplot._dispatch import add_headshots, add_logos, add_wordmarks, axis_logos
from sdvplot._errors import (
    DownloadError,
    InputError,
    IntegrityError,
    OfflineError,
    OptionalDependencyError,
    SdvplotDeprecationWarning,
    SdvplotError,
    SdvplotWarning,
    UnresolvedTeamError,
    UnsafeCachePathError,
    UnsafeDownloadError,
    UnsupportedTargetError,
)
from sdvplot._headshots import headshot_url
from sdvplot._images import logo_image
from sdvplot._index import teams
from sdvplot._marks import logo_url, marks
from sdvplot._pitch import pitch_coords
from sdvplot._resolve import resolve, suggest
from sdvplot._surface import surface
from sdvplot._versions import versions

try:
    __version__ = _version("sdvplot")
except _PackageNotFoundError:  # running from a source tree without installation
    __version__ = "0.0.0"

__all__ = [
    "DownloadError",
    "InputError",
    "IntegrityError",
    "OfflineError",
    "OptionalDependencyError",
    "SdvplotDeprecationWarning",
    "SdvplotError",
    "SdvplotWarning",
    "UnresolvedTeamError",
    "UnsafeCachePathError",
    "UnsafeDownloadError",
    "UnsupportedTargetError",
    "__version__",
    "add_headshots",
    "add_logos",
    "add_wordmarks",
    "axis_logos",
    "clear_cache",
    "court_coords",
    "headshot_url",
    "logo_image",
    "logo_url",
    "marks",
    "palette",
    "pitch_coords",
    "resolve",
    "suggest",
    "surface",
    "team_colors",
    "teams",
    "versions",
]
