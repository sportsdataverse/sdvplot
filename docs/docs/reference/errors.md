---
title: Errors and warnings
sidebar_label: Errors and warnings
sidebar_position: 18
---

# Errors and warnings

| Type | Subclass of | Meaning |
|---|---|---|
| `SdvplotWarning` | `UserWarning` | Something was skipped or degraded (an unresolved team, a stale cache), but the call still returned. |
| `UnresolvedTeamError` | `ValueError` | A team value did not resolve and strict=True was set. |
| `OfflineError` | `RuntimeError` | A download failed and no cached copy exists. |
| `OptionalDependencyError` | `ImportError` | A feature needs an optional extra that is not installed. |
| `UnsupportedTargetError` | `TypeError` | sdvplot has no adapter for this kind of plot or table object. |
