"""Team logos, wordmarks, headshots and colors for Python plots and tables (SportsDataverse)."""

from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _version

from sdvplot._cache import clear_cache
from sdvplot._colors import palette, team_colors
from sdvplot._court import court_coords
from sdvplot._dispatch import add_headshots, add_logos, add_wordmarks, axis_logos
from sdvplot._errors import (
    InputError,
    OfflineError,
    OptionalDependencyError,
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
from sdvplot._resolve import resolve, suggest
from sdvplot._surface import surface
from sdvplot._versions import versions

try:
    __version__ = _version("sdvplot")
except _PackageNotFoundError:  # running from a source tree without installation
    __version__ = "0.0.0"

__all__ = [
    "resolve",
    "suggest",
    "teams",
    "palette",
    "team_colors",
    "logo_url",
    "logo_image",
    "marks",
    "headshot_url",
    "versions",
    "clear_cache",
    "add_logos",
    "add_wordmarks",
    "add_headshots",
    "axis_logos",
    "surface",
    "court_coords",
    "SdvplotWarning",
    "SdvplotError",
    "InputError",
    "UnresolvedTeamError",
    "OfflineError",
    "OptionalDependencyError",
    "UnsupportedTargetError",
    "UnsafeDownloadError",
    "UnsafeCachePathError",
    "__version__",
]
