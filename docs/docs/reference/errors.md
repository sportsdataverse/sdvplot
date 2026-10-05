---
title: Errors and warnings
sidebar_label: Errors and warnings
sidebar_position: 31
---

# Errors and warnings

| Type | Subclass of | Meaning |
|---|---|---|
| `SdvplotWarning` | `UserWarning` | Something was skipped or degraded (an unresolved team, a stale cache), but the call still returned. |
| `SdvplotDeprecationWarning` | `SdvplotWarning`, `FutureWarning` | A deprecated sdvplot name or argument: it still works, and the message names its replacement and the release that removes it. A FutureWarning, so it shows by default. |
| `SdvplotError` | `Exception` | The base of sdvplot's errors: an unresolved team, a failed or refused download, a missing extra, an unsupported target, and the shared argument checks (``InputError``). A check specific to one helper (an axis name, a column, a chart setting) raises a plain ValueError or TypeError. |
| `InputError` | `SdvplotError`, `ValueError` | An argument sdvplot cannot use: an unknown league, id system, color slot, mark type or variant, a color slot such as ``"secondary"`` passed as a team, a season that is not a year or is outside the ones sdvplot knows, or a height, alpha, image size or candidate count out of range. |
| `UnresolvedTeamError` | `SdvplotError`, `ValueError` | A team value did not resolve and strict=True was set. |
| `OfflineError` | `SdvplotError`, `RuntimeError` | A download failed and no cached copy exists. |
| `DownloadError` | `OfflineError`, `OSError` | A download got an HTTP error status (a 4xx or 5xx response) and no cached copy exists. Also an OSError, so ``except OSError`` catches it. |
| `IntegrityError` | `DownloadError` | A download is not the file the manifest promises: its sha256 differs (it is not cached), or the archived file is not an image PIL can decode. |
| `OptionalDependencyError` | `SdvplotError`, `ModuleNotFoundError` | A feature needs an optional extra that is not installed: an adapter submodule imported without its library (``import sdvplot.plotly`` without plotly), an SVG mark without the svg extra. The message names the extra to install. |
| `UnsupportedTargetError` | `SdvplotError`, `TypeError` | sdvplot cannot draw on this object: no adapter takes its kind of plot or table, or the adapter does not support the verb (axis logos on a map, a table, Bokeh, HoloViews or pygal). |
| `UnsafeDownloadError` | `SdvplotError`, `OSError` | A download was refused: too large, too slow, or redirected away from https. |
| `UnsafeCachePathError` | `SdvplotError`, `ValueError` | A manifest value (sha256, ext) or cache path would reach outside the sdvplot cache directory. |
