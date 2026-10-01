# src/sdvplot/__init__.py
"""Team logos, wordmarks, headshots and colors for Python plots and tables (SportsDataverse)."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("sdvplot")
except PackageNotFoundError:  # running from a source tree without installation
    __version__ = "0.0.0"
