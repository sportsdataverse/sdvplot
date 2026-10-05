---
title: Errors and warnings
sidebar_label: Errors and warnings
sidebar_position: 18
---

# Errors and warnings

| Type | Subclass of | Meaning |
|---|---|---|
| `SdvplotWarning` | `UserWarning` | Something was skipped or degraded (an unresolved team, a stale cache), but the call still returned. |
| `SdvplotError` | `Exception` | The base of every sdvplot error: ``except sdvplot.SdvplotError`` catches them all. |
| `UnresolvedTeamError` | `SdvplotError`, `ValueError` | A team value did not resolve and strict=True was set. |
| `OfflineError` | `SdvplotError`, `RuntimeError` | A download failed and no cached copy exists. |
| `OptionalDependencyError` | `SdvplotError`, `ImportError` | A feature needs an optional extra that is not installed. |
| `UnsupportedTargetError` | `SdvplotError`, `TypeError` | sdvplot has no adapter for this kind of plot or table object. |
